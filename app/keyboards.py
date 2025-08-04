from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
import calendar

from config import *


def get_restart_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Заполнить заново", callback_data="restart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Запись")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_inline_record_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Запись", callback_data="record")]
        ]
    )
    return keyboard

def get_months_keyboard():
    today = datetime.now()
    month_names_ru = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
        7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    
    buttons = []
    day = int(today.month)
    year = int(today.year)
    day2 = day + 1
    if day2 > 12:
        day2 = 1
    day3 = day2 + 1
    if day3 > 12:
        day3 = 1
    
    ret = []
    for i in range(3):
        d = [day, day2, day3][i]
        if i == 2 and d == 1:
            year +=1
        if i == 1 and d == 1:
            year +=1
        # ret.append((d, year))
        month_name = month_names_ru[d]
        month = d
        yr = str(year)
        buttons.append(
            [InlineKeyboardButton(text=f"{month_name} {yr}", callback_data=f"month_{yr}_{month}")]
        )
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_days_keyboard(year, month):
    _, num_days = calendar.monthrange(year, month)  # сколько дней в месяце, и день недели первого числа
    first_weekday = calendar.monthrange(year, month)[0]  # 0=Пн, 6=Вс

    today = datetime.now()
    buttons = []
    row = []

    # Для текущего месяца показываем только будущие дни
    start_day = 1
    if year == today.year and month == today.month:
        start_day = today.day

    # Добавляем пустые кнопки перед первым числом (чтобы сдвинуть первый день на нужный день недели)
    # first_weekday — индекс дня недели первого числа (0=Пн)
    # Добавим пустые кнопки ровно столько, чтобы первый день был на правильном месте
    for _ in range(first_weekday):
        row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    # Добавляем кнопки с числами
    for day in range(start_day, num_days + 1):
        row.append(InlineKeyboardButton(text=str(day), callback_data=f"day_{day}"))
        if len(row) == 7:
            buttons.append(row)
            row = []

    # Если после добавления всех дней остались кнопки, дополним пустыми, чтобы заполнить последнюю строку до 7
    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_months")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_time_slots_keyboard(available_slots, dur_now=APPOINTMENT_DURATION):
    """Создает клавиатуру с доступными временными слотами"""
    buttons = []
    
    for start in available_slots:
        end = start + dur_now
        time_slot = f"{start:02d}:00"
        buttons.append(
            [InlineKeyboardButton(text=time_slot, callback_data=f"time_{start}")]
        )
    
    # Добавляем кнопку для выбора другого дня, если нет доступных слотов
    if not buttons:
        buttons.append([InlineKeyboardButton(text="Выбрать другой день", callback_data="choose_other_day")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_apartment_type_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="С ремонтом", callback_data="apartment_с ремонтом"),
            InlineKeyboardButton(text="Вайт бокс", callback_data="apartment_вайт бокс"),
        ],
        [InlineKeyboardButton(text="В бетоне", callback_data="apartment_в бетоне")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_yes_no_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Да", callback_data="yes"),
            InlineKeyboardButton(text="Нет", callback_data="no"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_measurement_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Обычный", callback_data="measurement_regular"),
            InlineKeyboardButton(text="В архикаде", callback_data="measurement_archicad"),
        ],
        [InlineKeyboardButton(text="Не нужно", callback_data="measurement_none")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="Заполнить заново", callback_data="restart")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)