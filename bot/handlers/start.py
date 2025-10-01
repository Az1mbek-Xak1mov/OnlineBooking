from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.buttons.reply import entr_button

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 Salom! Tizimga kirish uchun tugmani bosing:", reply_markup=entr_button())
