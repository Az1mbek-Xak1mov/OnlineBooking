from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.const import ENTER_


def make_reply(btns: list, size: list, repeat=False):
    rkb = ReplyKeyboardBuilder()
    rkb.add(*btns)
    if repeat:
        rkb.adjust(*size, repeat=True)
    else:
        rkb.adjust(*size)
    return rkb.as_markup(resize_keyboard=True)


def entr_button():
    menu = KeyboardButton(text=ENTER_)
    buttons = [menu]
    rows = [1]
    return make_reply(buttons, rows)

def main_menu_buttons():
    buttons = [
        KeyboardButton(text="Category"),
        KeyboardButton(text="Talab/Taklif"),
        KeyboardButton(text="Oxirgi xizmat"),
        KeyboardButton(text="My Orders"),
    ]
    rows = [2, 2]
    return make_reply(buttons, rows)