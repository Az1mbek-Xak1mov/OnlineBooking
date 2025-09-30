from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.buttons.reply import entr_button

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Hello! Please press the button to log in:", reply_markup=entr_button())
