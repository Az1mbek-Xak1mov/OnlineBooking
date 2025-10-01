import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from asgiref.sync import sync_to_async
from users.models import User

from bot.buttons.reply import main_menu_buttons, phone_request_button
from bot.const import ENTER_

router = Router()


class AuthState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_password = State()


@router.message(F.text == ENTER_)
async def process_entry(message: Message, state: FSMContext):
    user = await User.objects.filter(telegram_id=message.from_user.id).afirst()
    if user:
        await message.answer("✅ Tizimga muvaffaqiyatli kirdingiz! Xush kelibsiz.", reply_markup=main_menu_buttons())
    else:
        await message.answer("📞 Iltimos, telefon raqamingizni yuboring:", reply_markup=phone_request_button())
        await state.set_state(AuthState.waiting_for_phone)


@router.message(AuthState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text.strip()
    phone = re.sub(r"\D", "", phone)

    if not re.fullmatch(r"\d{9,15}", phone):
        await message.answer("❌ Noto‘g‘ri telefon raqami. Iltimos, qayta urinib ko‘ring:")
        return

    user = await User.objects.filter(phone_number=phone).afirst()
    if user:
        user.telegram_id = message.from_user.id
        await user.asave()
        await message.answer("✅ Telefon raqami topildi, akkauntingizga kirdingiz!", reply_markup=main_menu_buttons())
        await state.clear()
    else:
        await state.update_data(phone=phone)
        await message.answer("🔑 Yangi akkaunt yaratish uchun parolingizni kiriting:")
        await state.set_state(AuthState.waiting_for_password)


@router.message(AuthState.waiting_for_password)
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
