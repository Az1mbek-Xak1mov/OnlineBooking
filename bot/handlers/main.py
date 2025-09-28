import os
import re
from datetime import date as date_cls, datetime, time as time_cls, timedelta

import django
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from asgiref.sync import sync_to_async
from django.utils import timezone

from bot.buttons.inline import build_services_markup, get_free_slots, make_inline_btn_azim
from bot.buttons.reply import entr_button, main_menu_buttons, phone_request_button
from bot.const import CATEGORY_, ENTER_, LAST_SERVICE_, MY_ORDERS_, FEEDBACK_

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
django.setup()

from app.models import Booking, Service, ServiceCategory, Demand
from authentication.models import User

online_booking = Dispatcher()


class AuthState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_password = State()


@online_booking.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Salom! Kirish uchun tugmani bosing:", reply_markup=entr_button())


@online_booking.message(F.text == ENTER_)
async def process_entry(message: Message, state: FSMContext):
    user = await User.objects.filter(telegram_id=message.from_user.id).afirst()
    if user:
        await message.answer("✅ Kirish muvaffaqiyatli! Xush kelibsiz.", reply_markup=main_menu_buttons())
    else:
        await message.answer("📞 Telefon raqamingizni yuboring:", reply_markup=phone_request_button())
        await state.set_state(AuthState.waiting_for_phone)


@online_booking.message(AuthState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text.strip()
    phone = re.sub(r"\D", "", phone)

    if not re.fullmatch(r"\d{9,15}", phone):
        await message.answer("❌ Notog‘ri telefon raqam. Iltimos, qaytadan yuboring:")
        return

    user = await User.objects.filter(phone_number=phone).afirst()

    if user:
        user.telegram_id = message.from_user.id
        await user.asave()
        await message.answer("✅ Telefon raqam topildi va akkauntingizga kirildi!", reply_markup=main_menu_buttons())
        await state.clear()
    else:
        await state.update_data(phone=phone)
        await message.answer("🔑 Yangi akkaunt uchun parolingizni kiriting:")
        await state.set_state(AuthState.waiting_for_password)


@online_booking.message(AuthState.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    phone = data.get("phone")

    user = await User.objects.filter(phone_number=phone).afirst()
    if user:
        await message.answer("❌ Bu telefon raqami allaqachon ro‘yxatdan o‘tgan.")
        await state.clear()
        return

    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    user = User(phone_number=phone, telegram_id=message.from_user.id, first_name=first_name, last_name=last_name)
    await sync_to_async(user.set_password)(password)
    await user.asave()

    await message.answer("✅ Akkaunt yaratildi va tizimga kirdingiz! Xush kelibsiz.", reply_markup=main_menu_buttons())


@online_booking.message(F.text == LAST_SERVICE_)
async def last_orders(message: Message):
    user = await User.objects.filter(telegram_id=message.from_user.id).afirst()
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz!")
        return

    orders = await sync_to_async(lambda: list(
        Booking.objects.filter(user=user).order_by("-id").select_related("service")[:5]
    ))()

    if orders:
        text = "\n".join([
            f"📌 {o.service.name} | {o.date} {o.start_time.strftime('%H:%M')} - "
            f"{(datetime.combine(o.date, o.start_time) + o.duration).time().strftime('%H:%M')}"
            for o in orders
        ])
    else:
        text = "Sizda hali buyurtmalar yo'q."

    await message.answer(text, reply_markup=main_menu_buttons())


@online_booking.message(F.text == MY_ORDERS_)
async def process_orders(message: Message):
    now = timezone.localtime()
    user = await User.objects.filter(telegram_id=message.from_user.id).afirst()
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz!")
        return

    orders = await sync_to_async(lambda: list(
        Booking.objects.filter(user=user).select_related("service")
    ))()

    active_orders = []
    for o in orders:
        end_dt = datetime.combine(o.date, o.start_time) + o.duration
        if end_dt > now:
            active_orders.append((o, end_dt))

    if not active_orders:
        await message.answer("Sizda faol buyurtmalar yo‘q.")
    else:
        text = "\n".join([
            f"📌 {o.service.name} | {o.date} {o.start_time.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
            for o, end_dt in active_orders
        ])
        await message.answer(text)


@online_booking.message(F.text == CATEGORY_)
async def process_categories(message: Message):
    categories = await sync_to_async(lambda: list(ServiceCategory.objects.all()))()
    buttons = [i.name for i in categories]
    await message.answer("Categorylar", reply_markup=make_inline_btn_azim(buttons, [3]))


@online_booking.callback_query()
async def process_category_callback(callback: CallbackQuery):
    categories = await sync_to_async(lambda: list(ServiceCategory.objects.all()))()
    category_names = [c.name for c in categories]

    if callback.data in category_names:
        category = await ServiceCategory.objects.aget(name=callback.data)
        services = await sync_to_async(lambda: list(category.services.all()))()

        if not services:
            await callback.message.edit_text("❌ Bu kategoriyada hozircha xizmatlar yo‘q")
            return

        markup = build_services_markup(services, category.id, page=0)
        await callback.message.edit_text(
            f"Siz kategoriya tanladingiz: {category.name}\nXizmatni tanlang:",
            reply_markup=markup
        )
        await callback.answer()

    elif callback.data.startswith("service_page_"):
        payload = callback.data.replace("service_page_", "", 1)
        cat_id, page = payload.rsplit("_", 1)
        page = int(page)
        category = await ServiceCategory.objects.aget(id=cat_id)
        services = await category.services.all().aall()
        markup = build_services_markup(services, cat_id, page=page)
        await callback.message.edit_reply_markup(reply_markup=markup)
        await callback.answer()

    elif callback.data.startswith("service_"):
        service_id = callback.data.replace("service_", "", 1)
        service = await Service.objects.aget(id=service_id)

        today = timezone.localdate()
        days = [today + timedelta(days=i) for i in range(14)]

        buttons, data_list = [], []
        for d in days:
            weekday_name = d.strftime("%A").lower()
            exists = await service.schedules.filter(weekday=weekday_name).aexists()
            if exists:
                buttons.append(d.strftime("%d-%m %A"))
                data_list.append(f"day_{service.id}_{d.isoformat()}")
                if len(buttons) == 7:
                    break

        if not buttons:
            await callback.message.edit_text("❌ Нет доступных дней для этой услуги")
            await callback.answer()
            return

        markup = make_inline_btn_azim(buttons, sizes=[2], data_list=data_list)
        await callback.message.edit_text(
            f"📌 {service.name}\n"
            f"Manzil: {service.address}\n"
            f"Narx: {service.price}\n"
            f"Sig‘im: {service.capacity} odam\n\n"
            f"👉 Quyidagi kunlardan birini tanlang:",
            reply_markup=markup
        )
        await callback.answer()

    elif callback.data.startswith("day_"):
        _, service_id, date_str = callback.data.split("_", 2)
        service = await Service.objects.aget(id=service_id)
        target_date = datetime.fromisoformat(date_str).date()
        free_slots = await sync_to_async(get_free_slots)(service, target_date)
        if not free_slots:
            await callback.message.edit_text("❌ Bu kunda bo'sh vaqt yo'q.")
            return

        markup = make_inline_btn_azim(
            free_slots, sizes=[2],
            data_list=[f"slot_{service.id}_{target_date}_{s.split()[0]}" for s in free_slots]
        )

        await callback.message.edit_text(
            f"📅 Mavjud slotlar {target_date.strftime('%d-%m-%Y')}:",
            reply_markup=markup
        )

    elif callback.data.startswith("slot_"):
        _, service_id, date_str, start_str = callback.data.split("_")
        service = await Service.objects.aget(id=service_id)
        target_date = date_cls.fromisoformat(date_str)
        start_time = time_cls.fromisoformat(start_str)
        duration: timedelta = service.duration

        end_time = (datetime.combine(target_date, start_time) + duration).time()
        user = await User.objects.aget(telegram_id=callback.from_user.id)

        exists = await Booking.objects.filter(
            service=service, date=target_date, start_time=start_time
        ).aexists()
        if exists:
            await callback.message.edit_text("❌ Afsuski, slot endigina olingan.")
            return

        booking = Booking(
            user=user,
            service=service,
            date=target_date,
            weekday=target_date.strftime("%A").lower(),
            start_time=start_time,
            duration=duration,
            seats=1
        )
        await booking.asave()

        await callback.message.edit_text(
            f"✅ Вы забронировали {service.name}\n"
            f"📅 {target_date.strftime('%d-%m-%Y')}\n"
            f"🕒 {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        )


class DemandState(StatesGroup):
    waiting_for_text = State()


@online_booking.message(F.text == FEEDBACK_)
async def start_demand(message: Message, state: FSMContext):
    await message.answer("✍️ Введите описание:")
    await state.set_state(DemandState.waiting_for_text)


@online_booking.message(DemandState.waiting_for_text)
async def process_demand(message: Message, state: FSMContext):
    user_tg_id = message.from_user.id
    main_text = message.text

    async def save_demand():
        user = await sync_to_async(User.objects.get)(telegram_id=user_tg_id)
        return await sync_to_async(Demand.objects.create)(
            user=user,
            main_text=main_text
        )

    demand = await save_demand()

    await message.answer(f"✅ Спрос сохранён")
    await state.clear()


