from aiogram import F, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from django.contrib.auth import get_user_model
from bot.buttons.reply import entr_button, main_menu_buttons
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")
django.setup()

online_booking = Dispatcher()

User = get_user_model()


class AuthState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_password = State()

@online_booking.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Salom! Kirish uchun tugmani bosing:", reply_markup=entr_button())

@online_booking.message(F.text == "Krish/Entr")
async def process_entry(message: Message, state: FSMContext):
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
    phone = data["phone"]

    user = await sync_to_async(lambda: User.objects.filter(phone_number=phone).first())()

    if user:
        if hasattr(user, "check_password"):
            if user.check_password(password):
                await message.answer("✅ Kirish muvaffaqiyatli! Xush kelibsiz.",reply_markup=main_menu_buttons())
            else:
                await message.answer("❌ Notogri parol!")
        else:
            if user.password == password:
                await message.answer("✅ Kirish muvaffaqiyatli! Xush kelibsiz.",reply_markup=main_menu_buttons())
            else:
                await message.answer("❌ Notogri parol!")
    else:
        await message.answer("❌ Bunday telefon raqami bilan foydalanuvchi topilmadi!")

    await state.clear()