from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.const import ENTER_, CATEGORY_, FEEDBACK_, LAST_SERVICE_, MY_ORDERS_


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
        KeyboardButton(text=CATEGORY_),
        KeyboardButton(text=FEEDBACK_),
        KeyboardButton(text=LAST_SERVICE_),
        KeyboardButton(text=MY_ORDERS_),
    ]
    rows = [2, 2]
    return make_reply(buttons, rows)

def phone_request_button():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return kb