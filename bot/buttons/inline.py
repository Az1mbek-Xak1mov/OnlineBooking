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

def make_inline_btn_azim(btns, sizes, data_list=None):
    builder = InlineKeyboardBuilder()
    if data_list is None:
        data_list = btns
    for text, callback in zip(btns, data_list):
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
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

from datetime import datetime, timedelta

def get_free_slots(service, target_date):
    weekday_name = target_date.strftime("%A").lower()

    # Берём расписание для этого дня
    schedules = service.schedules.filter(weekday=weekday_name)
    if not schedules.exists():
        return []

    duration = service.duration  # timedelta, например 1 час
    free_slots = []

    for sch in schedules:
        start_dt = datetime.combine(target_date, sch.start_time)
        end_dt = datetime.combine(target_date, sch.end_time)

        # Двигаемся кусками по duration
        current = start_dt
        while current + duration <= end_dt:
            slot_start = current.time()
            slot_end = (current + duration).time()
            from app.models import Booking
            # Проверка занятости
            exists = Booking.objects.filter(
                service=service,
                date=target_date,
                start_time=slot_start,
                end_time=slot_end
            ).exists()

            if not exists:
                free_slots.append(f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}")

            current += duration

    return free_slots
