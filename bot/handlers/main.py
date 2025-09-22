import os

import django
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async
from django.utils import timezone

from bot.buttons.inline import make_inline_btn_azim, build_services_markup

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
django.setup()

from app.models import Booking, ServiceCategory
from authentication.models import User

from bot.buttons.reply import entr_button, main_menu_buttons

online_booking = Dispatcher()


class AuthState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_password = State()


@online_booking.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Salom! Kirish uchun tugmani bosing:", reply_markup=entr_button())


@online_booking.message(F.text == "Krish/Entr")
async def process_entry(message: Message, state: FSMContext):
    user = await sync_to_async(lambda: User.objects.filter(telegram_id=message.from_user.id).first())()
    if user:
        await message.answer("✅ Kirish muvaffaqiyatli! Xush kelibsiz.", reply_markup=main_menu_buttons())
    else:
        await message.answer("Telefon raqamingizni yuboring:")
        await state.set_state(AuthState.waiting_for_phone)


@online_booking.message(AuthState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)
    await message.answer("Endi parolingizni kiriting:")
    await state.set_state(AuthState.waiting_for_password)


@online_booking.message(AuthState.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    password = message.text
    data = await state.get_data()
    phone = data.get("phone")

    user = await sync_to_async(lambda: User.objects.filter(phone_number=phone).first())()

    if not user:
        await message.answer("❌ Bunday telefon raqami bilan foydalanuvchi topilmadi!")
        await state.clear()
        return

    is_valid = False
    if hasattr(user, "check_password") and user.check_password(password):
        is_valid = True
    elif user.password == password:
        is_valid = True

    if is_valid:
        user.telegram_id = message.from_user.id
        await sync_to_async(user.save)()
        await message.answer("✅ Kirish muvaffaqiyatli! Xush kelibsiz.", reply_markup=main_menu_buttons())
    else:
        await message.answer("❌ Notogri parol!")

    await state.clear()


@online_booking.message(F.text == "Oxirgi xizmat")
async def last_orders(message: Message):
    user = await sync_to_async(lambda: User.objects.filter(telegram_id=message.from_user.id).first())()
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz!")
        return

    orders = await sync_to_async(lambda: list(Booking.objects.filter(user=user)[:5]))()
    if orders:
        text = "\n".join([f"📌 Order #{o.id} - {o.status}" for o in orders])
    else:
        text = "Sizda hali buyurtmalar yo'q."

    await message.answer(text, reply_markup=main_menu_buttons())

@online_booking.message(F.text == "My Orders")
async def process_orders(message: Message):
    user = await sync_to_async(lambda: User.objects.filter(telegram_id=message.from_user.id))()
    now_time = timezone.now()
    orders = await sync_to_async(lambda: list(Booking.objects.filter(user=user, end_time__gt=now_time)))()
    if not orders:
        await message.answer("Sizda faol buyurtmalar yo‘q.")
    else:
        text = "\n".join([f"Buyurtma #{o.id} tugash vaqti: {o.end_time}" for o in orders])
        await message.answer(text)


@online_booking.message(F.text == "Category")
async def process_categories(message: Message):
    categories = await sync_to_async(lambda: list(ServiceCategory.objects.all()))()

    buttons = [i.name for i in categories]
    print(buttons,type(buttons))
    rows = [3]
    await message.answer('Categorylar', reply_markup=make_inline_btn_azim(buttons, rows))




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

