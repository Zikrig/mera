# slotswork.py

from app.google_sheet_manager import GoogleSheetsManager
from datetime import datetime
from config import WORK_HOURS, APPOINTMENT_DURATION

# Создаем экземпляр менеджера таблиц
sheet_manager = GoogleSheetsManager()

def get_busy_slots(date):
    """Возвращает список занятых временных слотов на указанную дату"""
    return sheet_manager.get_busy_slots(date)

def get_available_slots(date, dur_now=APPOINTMENT_DURATION):
    """
    Возвращает список доступных временных слотов для начала процедуры
    на указанную дату с учетом:
    - рабочего времени (9-21)
    - длительности процедуры (4 часа)
    - уже занятых слотов
    """
    busy_slots = get_busy_slots(date)
    
    # Создаем список всех возможных слотов по часу
    all_slots = list(range(WORK_HOURS[0], WORK_HOURS[1]))
    
    # Помечаем занятые слоты
    occupied = []
    for start, duration in busy_slots:
        occupied.extend(range(start, start + duration))
    
    # Находим доступные 4-часовые интервалы
    available_starts = []
    for start in all_slots:
        # Проверяем, что интервал помещается в рабочий день
        if start + dur_now > WORK_HOURS[1]:
            continue
            
        # Проверяем, что все слоты в интервале свободны
        if all(slot not in occupied for slot in range(start, start + dur_now)):
            available_starts.append(start)
    
    return available_starts

def is_slot_available(date, start_hour, dur_now=APPOINTMENT_DURATION):
    """Проверяет, свободен ли слот для бронирования"""
    if start_hour < WORK_HOURS[0] or start_hour + dur_now > WORK_HOURS[1]:
        return False
        
    busy_slots = get_busy_slots(date)
    occupied = []
    for start, duration in busy_slots:
        occupied.extend(range(start, start + duration))
    return all(slot not in occupied for slot in range(start_hour, start_hour + dur_now))

def add_appointment(data):
    """Добавляет запись в Google Таблицу"""
    res, txt = sheet_manager.add_appointment(data)
    sheet_manager.create_weekly_summary_sheet()
    return res

def update_appointment(date, start_hour, new_data):
    """Обновляет существующую запись в Google Таблице"""
    res, txt = sheet_manager.update_appointment(date, start_hour, new_data)
    sheet_manager.create_weekly_summary_sheet()
    return res

def update_calendar():
    """Обновляет сводный календарь в Google Таблице"""
    sheet_manager.create_weekly_summary_sheet()
