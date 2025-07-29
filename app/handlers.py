#headers.py

import json
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand

from app.calculations import calculate_total
from datetime import datetime, timedelta, date

from config import *
from app.keyboards import *
from app.slotswork import *
from app.admin_work import *
from app.utils import continuety

router = Router()

from config import TELEPHONE

class Form(StatesGroup):
    apartment_type = State()
    area = State()
    em_screening = State()
    radiation_check = State()
    measurement_type = State()
    valuation = State()
    contacts = State()
    housing_estate_address = State()  # Новое состояние для адреса ЖК
    booking_month = State()
    booking_day = State()
    booking_time = State()

MONTH_NAME_RU = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
        7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }

async def set_main_menu():
    # Создаем список с командами и их описанием
    main_menu_commands = [
        BotCommand(command='/start', description='Рестарт'),
        BotCommand(command='/count', description='Запись'),
    ]
    
    await bot.set_my_commands(main_menu_commands)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):

    # Приветственное сообщение
    await message.answer(
        "Добро пожаловать в сервис приемки квартир \"Эксперт комплекс\"",
        reply_markup=get_inline_record_keyboard()
    )
    
    # Инлайн кнопка
    await message.answer(
        f"Мы рады вас видеть) Запишитесь прямо сейчас!",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(Form.booking_day, F.data == "back_to_months")
async def back_to_months(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.booking_month)
    await callback.message.edit_text(
        "Выберите месяц для записи:",
        reply_markup=get_months_keyboard()
    )
    await callback.answer()
    
@router.message(F.text == "Запись")
@router.message(Command("count"))
async def cmd_record(message: Message, state: FSMContext):
    await state.set_state(Form.apartment_type)
    await message.answer(
        "В какоим состоянии ваша квартира?",
        reply_markup=get_apartment_type_keyboard()
    )


@router.callback_query(F.data.startswith("record"))
async def process_apartment_type(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Form.apartment_type)
    await callback.message.answer(
        "В какоим состоянии ваша квартира?",
        reply_markup=get_apartment_type_keyboard()
    )

@router.callback_query(F.data.startswith("apartment_"), Form.apartment_type)
async def process_apartment_type(callback: CallbackQuery, state: FSMContext):
    apartment_type = callback.data.split("_", 1)[1]
    await state.update_data(apartment_type=apartment_type)
    await state.set_state(Form.area)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)  # Удаляем клавиатуру
    await callback.message.answer("Какая площадь вашей квартиры? (введите число)")

@router.message(Form.contacts)
async def process_contacts(message: Message, state: FSMContext):
    contacts = message.text
    await state.update_data(contacts=contacts)
    
    # Переходим к вводу адреса ЖК
    await state.set_state(Form.housing_estate_address)
    await message.answer("Пожалуйста, укажите адрес жилого комплекса (ЖК):")


@router.message(Form.housing_estate_address)
async def process_housing_estate_address(message: Message, state: FSMContext):
    address = message.text
    await state.update_data(housing_estate_address=address)
    
    # Теперь переходим к выбору месяца для бронирования
    await state.set_state(Form.booking_month)
    await message.answer(
        "Отлично! Теперь выберите месяц для записи:",
        reply_markup=get_months_keyboard()
    )


@router.message(Form.area)
async def process_area(message: Message, state: FSMContext):
    try:
        area = float(message.text.replace(',', '.'))
        if area <= 0:
            raise ValueError
        await state.update_data(area=area)
        await state.set_state(Form.em_screening)
        await message.answer(
            "Желаете проверить квартиру на отсутствие на электромагнитное излучение?",
            reply_markup=get_yes_no_keyboard()
        )
    except:
        await message.answer("Пожалуйста, введите корректное значение площади (число больше 0)")

@router.callback_query(Form.em_screening, F.data.in_(["yes", "no"]))
async def process_em_screening(callback: CallbackQuery, state: FSMContext):
    em_screening = callback.data == "yes"
    await state.update_data(em_screening=em_screening)
    await state.set_state(Form.radiation_check)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)  # Удаляем клавиатуру
    await callback.message.answer(
        "Желаете проверить квартиру на отсутствие радиоактивного излучения?",
        reply_markup=get_yes_no_keyboard()
    )

@router.callback_query(Form.radiation_check, F.data.in_(["yes", "no"]))
async def process_radiation_check(callback: CallbackQuery, state: FSMContext):
    radiation_check = callback.data == "yes"
    await state.update_data(radiation_check=radiation_check)
    await state.set_state(Form.measurement_type)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)  # Удаляем клавиатуру
    await callback.message.answer(
        "Желаете заказать обмер квартиры? Есть следующие варианты:\n- обычный (информационный) обмер\n- обмер в ArchiCAD (для дизайнера)",
        reply_markup=get_measurement_keyboard()
    )

@router.callback_query(Form.measurement_type, F.data.startswith("measurement_"))
async def process_measurement(callback: CallbackQuery, state: FSMContext):
    measurement_type = callback.data.split("_")[1]
    await state.update_data(measurement_type=measurement_type)
    await state.set_state(Form.valuation)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)  # Удаляем клавиатуру
    await callback.message.answer(
        "Желаете оценить стоимость недвижимости?",
        reply_markup=get_yes_no_keyboard()
    )

@router.callback_query(Form.valuation, F.data.in_(["yes", "no"]))
async def process_valuation(callback: CallbackQuery, state: FSMContext):
    valuation = callback.data == "yes"
    await state.update_data(valuation=valuation)
    await state.set_state(Form.contacts)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)  # Удаляем клавиатуру
    await callback.message.answer("Как вас зовут и как с вами связаться? (телефон, email или другой контакт)")

@router.message(Form.contacts)
async def process_contacts(message: Message, state: FSMContext):
    contacts = message.text
    await state.update_data(contacts=contacts)
    
    # Переходим к выбору месяца для бронирования
    await state.set_state(Form.booking_month)
    await message.answer(
        "Отлично! Теперь выберите месяц для записи:",
        reply_markup=get_months_keyboard()
    )

@router.callback_query(Form.booking_month, F.data.startswith("month_"))
async def process_month_selection(callback: CallbackQuery, state: FSMContext):
    _, year_str, month_str = callback.data.split('_')
    year = int(year_str)
    month = int(month_str)
    
    await state.update_data(booking_year=year, booking_month=month)
    await state.set_state(Form.booking_day)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"Выберите день в {MONTH_NAME_RU[month]}:",
        reply_markup=get_days_keyboard(year, month)
    )

@router.callback_query(Form.booking_day, F.data.startswith("day_"))
async def process_day_selection(callback: CallbackQuery, state: FSMContext):
    day = int(callback.data.split('_')[1])
    data = await state.get_data()
    
    # Создаем объект даты для проверки доступности
    selected_date = date(data['booking_year'], data['booking_month'], day)
    dur_of = continuety(data)

    # Получаем доступные слоты
    available_slots = get_available_slots(selected_date, dur_of)
    
    # Если нет доступных слотов, предлагаем выбрать другой день
    if not available_slots:
        await callback.message.answer(
            "К сожалению, на выбранный день нет свободных слотов. "
            "Пожалуйста, выберите другой день.",
            reply_markup=get_days_keyboard(data['booking_year'], data['booking_month'])
        )
        return
    
    await state.update_data(booking_day=day)
    await state.set_state(Form.booking_time)
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Форматируем дату для отображения
    month_name_ru = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
        7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    month_name = month_name_ru.get(data['booking_month'], f"месяца {data['booking_month']}")
    
    await callback.message.answer(
        f"Вы выбрали {day} {month_name} {data['booking_year']} года.\n"
        f"Доступные временные слоты (процедура занимает {str(continuety(data))} часа):",
        reply_markup=get_time_slots_keyboard(available_slots, dur_of)
    )
@router.callback_query(Form.booking_time, F.data.startswith("time_"))
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    start_hour = int(callback.data.split('_')[1])
    data = await state.get_data()
    
    # Создаем объект даты для проверки доступности
    selected_date = date(data['booking_year'], data['booking_month'], data['booking_day'])
    
    # Проверяем, свободен ли выбранный слот
    if not is_slot_available(selected_date, start_hour, continuety(data)):
        await callback.answer("Этот слот уже занят, пожалуйста, выберите другое время", show_alert=True)
        dur_of = continuety(data)
        # Получаем доступные слоты
        available_slots = get_available_slots(selected_date, dur_of)
        
        # Обновляем сообщение с новыми доступными слотами
        await callback.message.edit_text(
            f"Доступные временные слоты на {selected_date.day} {selected_date.month} {selected_date.year}:",
            reply_markup=get_time_slots_keyboard(available_slots, dur_of)
        )
        return
    
    await state.update_data(booking_time_start=start_hour)
    data = await state.get_data()
    
    # Форматированный вывод с информацией о брони
    result_text = format_result(data)
    
    # Рассчет стоимости
    total = str(int(calculate_total(data)))
    
    await callback.message.answer(
        result_text + f"\n\nИтоговая стоимость: {total} руб.",
        reply_markup=get_confirmation_keyboard()  # Используем новую клавиатуру
    )

@router.callback_query(F.data == "confirm")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    # Получаем данные из состояния
    data = await state.get_data()
    
    # Формируем данные для добавления в таблицу
    appointment_data = {
        "date": date(data['booking_year'], data['booking_month'], data['booking_day']),
        "start_hour": data['booking_time_start'],
        "area": data['area'],
        "apartment_type": data['apartment_type'],
        "em_screening": data['em_screening'],
        "radiation_check": data['radiation_check'],
        "measurement_type": data['measurement_type'],
        "valuation": data['valuation'],
        "contacts": data['contacts'],
        "housing_estate_address": data['housing_estate_address']
    }
    
    await callback.message.answer(
        "🔄 Подтверждение записи...\n"
        "Пожалуйста, подождите, идет добавление в календарь..."
    )
    
    # Добавляем событие в календарь
    success = add_appointment(appointment_data)
    message = callback.message

    if success:
        # Форматируем дату для сообщения

        await callback.message.edit_reply_markup(inline_markup=None)

        month_name = MONTH_NAME_RU.get(data['booking_month'])
        start = data['booking_time_start']
        end = start + continuety(data)
        time_slot = f"{start:02d}:00 - {end:02d}:00"
        
        # Сообщение пользователю
        await callback.message.answer(
            "✅ Ваша запись подтверждена!\n"
            f"📅 Дата: {data['booking_day']} {month_name} {data['booking_year']} г.\n"
            f"⏰ Время: {time_slot}\n"
            f"📍 Адрес: {data['housing_estate_address']}\n\n"
            "Ожидайте нашего специалиста в указанное время!"
        )
        
        # Уведомление администратору
        admin_message = (
            "🔥 Новая запись!\n\n"
            f"👤 Клиент: {data['contacts']}\n"
            f"📅 Дата: {data['booking_day']} {month_name} {data['booking_year']} г.\n"
            f"⏰ Время: {time_slot}\n"
            f"📍 Адрес: {data['housing_estate_address']}\n\n"
            f"💸 Стоимость: {int(calculate_total(data))} руб.\n"
            f"📏 Площадь: {data['area']} м²\n"
            f"🏠 Тип: {data['apartment_type']}"
        )
        
        try:
            await send_to_admin(admin_message)
        except Exception as e:
            print(f"Ошибка отправки сообщения администратору: {str(e)}")
    else:
        await callback.message.answer(
            "⚠️ Произошла ошибка при подтверждении записи:\n"
            f"{message}\n\n"
            "Пожалуйста, попробуйте еще раз.",
            reply_markup=get_confirmation_keyboard()
        )
        return
    
    # Очищаем состояние
    await state.clear()

def format_result(data):
    """Форматирует результат в читаемый вид"""
    apartment_types = {
        "с ремонтом": "Квартира с ремонтом",
        "вайт бокс": "Квартира Вайт бокс",
        "в бетоне": "Квартира в бетоне"
    }
    
    measurement_types = {
        "regular": "Обычный обмер",
        "archicad": "Обмер в архикаде",
        "none": "Без обмера"
    }
    
    lines = [
        f"🏠 Тип квартиры: {apartment_types.get(data['apartment_type'], data['apartment_type'])}",
        f"📏 Площадь: {data['area']} м²",
        f"⚡ Скрининг ЭМИ: {'Да' if data['em_screening'] else 'Нет'}",
        f"☢️ Проверка радиации: {'Да' if data['radiation_check'] else 'Нет'}",
        f"📐 Обмер: {measurement_types.get(data['measurement_type'], data['measurement_type'])}",
        f"💰 Оценка недвижимости: {'Да' if data['valuation'] else 'Нет'}",
        f"📞 Контакты: {data['contacts']}",
        f"📍 Адрес ЖК: {data.get('housing_estate_address', 'не указан')}"  # Добавляем адрес ЖК
    ]
    
    # Добавляем информацию о бронировании
    if 'booking_year' in data:
        month_name = MONTH_NAME_RU.get(data['booking_month'], f"месяца {data['booking_month']}")
        start = data['booking_time_start']
        end = start + continuety(data)
        time_slot = f"{start:02d}:00 - {end:02d}:00"
        
        lines.append(
            f"📅 Дата и время: {data['booking_day']} {month_name} {data['booking_year']} г., {time_slot}"
        )
    
    return "\n".join(lines)


@router.callback_query(Form.booking_time, F.data == "choose_other_day")
async def choose_other_day(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    await state.set_state(Form.booking_day)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"Выберите другой день в {MONTH_NAME_RU[data['booking_month']]}:",
        reply_markup=get_days_keyboard(data['booking_year'], data['booking_month'])
    )


@router.callback_query(F.data == "restart")
async def restart_process(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await cmd_start(callback.message, state)


