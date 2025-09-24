import os
import re
from datetime import datetime, timedelta, date as date_cls,time as time_cls

import django
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from asgiref.sync import sync_to_async
from django.utils import timezone

from bot.buttons.inline import build_services_markup, make_inline_btn_azim, get_free_slots
from bot.const import ENTER_
from bot.buttons.reply import entr_button, main_menu_buttons, phone_request_button

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
django.setup()

from app.models import Booking, Service, ServiceCategory
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
        await message.answer(
            "📞 Telefon raqamingizni yuboring:",
            reply_markup=phone_request_button()
        )
        await state.set_state(AuthState.waiting_for_phone)

@online_booking.message(AuthState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()

    if not re.fullmatch(r"^\+?\d{9,15}$", phone):
        await message.answer("❌ Notog‘ri telefon raqam. Iltimos, qaytadan yuboring:")
        return

    await state.update_data(phone=phone)
    await message.answer("Endi parolingizni kiriting:", reply_markup=None)
    await state.set_state(AuthState.waiting_for_password)




@online_booking.message(AuthState.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    password = message.text
    data = await state.get_data()
    phone = data.get("phone")

    user = await User.objects.filter(phone_number=phone).afirst()
    if not user:
        await message.answer("❌ Bunday telefon raqami bilan foydalanuvchi topilmadi!")
        await state.clear()
        return

    is_valid = await sync_to_async(user.check_password)(password)
    if is_valid:
        user.telegram_id = message.from_user.id
        await sync_to_async(user.save)()
        await message.answer("✅ Kirish muvaffaqiyatli! Xush kelibsiz.", reply_markup=main_menu_buttons())
    else:
        await message.answer("❌ Notog‘ri parol!")

    await state.clear()



@online_booking.message(F.text == "Oxirgi xizmat")
async def last_orders(message: Message):
    user = await sync_to_async(lambda: User.objects.filter(telegram_id=message.from_user.id).first())()
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz!")
        return

    orders = await sync_to_async(lambda: list(Booking.objects.filter(user=user).order_by("-id")[:5]))()
    if orders:
        text = "\n".join([f"📌 Order #{o.id} - {o.name}" for o in orders])
    else:
        text = "Sizda hali buyurtmalar yo'q."

    await message.answer(text, reply_markup=main_menu_buttons())


@online_booking.message(F.text == "My Orders")
async def process_orders(message: Message):
    now_time = timezone.now()
    orders = await sync_to_async(
        lambda: list(Booking.objects.filter(user__telegram_id=message.from_user.id, end_time__gt=now_time))
    )()
    if not orders:
        await message.answer("Sizda faol buyurtmalar yo‘q.")
    else:
        text = "\n".join([f"Buyurtma #{o.id} tugash vaqti: {o.end_time}" for o in orders])
        await message.answer(text)


@online_booking.message(F.text == "Category")
async def process_categories(message: Message):
    categories = await sync_to_async(lambda: list(ServiceCategory.objects.all()))()
    buttons = [i.name for i in categories]
    await message.answer("Categorylar", reply_markup=make_inline_btn_azim(buttons, [3]))



@online_booking.callback_query()
async def process_category_callback(callback: CallbackQuery):
    categories = await sync_to_async(lambda: list(ServiceCategory.objects.all()))()
    category_names = [c.name for c in categories]

    if callback.data in category_names:
        category = await sync_to_async(lambda: ServiceCategory.objects.get(name=callback.data))()
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
        services = await sync_to_async(
            lambda: list(ServiceCategory.objects.get(id=cat_id).services.all())
        )()
        markup = build_services_markup(services, cat_id, page=page)
        await callback.message.edit_reply_markup(reply_markup=markup)
        await callback.answer()

    elif callback.data.startswith("service_"):

        service_id = callback.data.replace("service_", "", 1)
        service = await sync_to_async(lambda: Service.objects.get(id=service_id))()

        today = timezone.localdate()


        days = [today + timedelta(days=i) for i in range(14)]
        print(days)
        buttons, data_list = [], []
        for d in days:
            weekday_name = d.strftime("%A").lower()
            exists = await sync_to_async(service.schedules.filter(weekday=weekday_name).exists)()
            if exists:
                buttons.append(d.strftime("%d-%m %A"))  # Формат: 20-09 Monday
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
        service = await sync_to_async(lambda: Service.objects.get(id=service_id))()
        target_date = datetime.fromisoformat(date_str).date()

        free_slots = await sync_to_async(get_free_slots)(service, target_date)

        if not free_slots:
            await callback.message.edit_text("❌ Нет свободных времён в этот день")
            return

        markup = make_inline_btn_azim(free_slots, sizes=[2],
            data_list=[f"slot_{service.id}_{target_date}_{s.split()[0]}" for s in free_slots])

        await callback.message.edit_text(
            f"📅 Доступные слоты на {target_date.strftime('%d-%m-%Y')}:",
            reply_markup=markup
        )
    elif callback.data.startswith("slot_"):
        # Распаковка 4 частей, без end_time
        _, service_id, date_str, start_str = callback.data.split("_")
        service = await sync_to_async(lambda: Service.objects.get(id=service_id))()

        target_date = date_cls.fromisoformat(date_str)
        start_time = time_cls.fromisoformat(start_str)

        # Вычисляем end_time через длительность услуги
        end_time = (datetime.combine(target_date, start_time) + service.duration).time()

        user = await sync_to_async(lambda: User.objects.get(telegram_id=callback.from_user.id))()

        exists = await sync_to_async(
            lambda: Booking.objects.filter(
                service=service, date=target_date,
                start_time=start_time, end_time=end_time
            ).exists()
        )()
        if exists:
            await callback.message.edit_text("❌ К сожалению, слот только что заняли")
            return

        booking = Booking(
            user=user,
            service=service,
            date=target_date,
            start_time=start_time,
            end_time=end_time
        )
        await sync_to_async(booking.save)()

        await callback.message.edit_text(
            f"✅ Вы забронировали {service.name}\n"
            f"📅 {target_date.strftime('%d-%m-%Y')}\n"
            f"🕒 {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        )
