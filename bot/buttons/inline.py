from math import ceil

from aiogram.utils.keyboard import InlineKeyboardBuilder


def make_inline_btn(btns: list, size: list, repeat=False):
    rkb = InlineKeyboardBuilder()
    rkb.add(*btns)
    if repeat:
        rkb.adjust(*size, repeat=True)
    else:
        rkb.adjust(*size)
    return rkb.as_markup()

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def make_inline_btn_azim(btns, sizes):
    builder = InlineKeyboardBuilder()
    for text in btns:
        builder.add(InlineKeyboardButton(text=text, callback_data=text))
    builder.adjust(*sizes)
    return builder.as_markup()


SERVICES_PER_PAGE = 6

def build_services_markup(services, category_id, page=0):
    total = len(services)
    start = page * SERVICES_PER_PAGE
    end = start + SERVICES_PER_PAGE
    page_services = services[start:end]
    buttons = [
        InlineKeyboardButton(text=s.name, callback_data=f"service_{s.id}")
        for s in page_services
    ]
    nav_buttons = []
    total_pages = ceil(total / SERVICES_PER_PAGE)
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅ Orqaga", callback_data=f"service_page_{category_id}_{page - 1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="➡ Keyingi", callback_data=f"service_page_{category_id}_{page + 1}")
        )
    builder = InlineKeyboardBuilder()
    builder.add(*buttons)
    builder.adjust(2)
    if nav_buttons:
        builder.row(*nav_buttons)
    return builder.as_markup()