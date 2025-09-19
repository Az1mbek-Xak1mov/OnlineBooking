import os
import django
from aiogram import F, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
django.setup()

from authentication.models import User
from app.models import Booking
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



