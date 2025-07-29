# google_sheet_manager.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta, date
from threading import Timer

from config import CREDENTIALS_FILE, SPREADSHEET_ID
from app.utils import continuety

class GoogleSheetsManager:
    def __init__(self):
        self.scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, self.scope)
        self.client = gspread.authorize(self.creds)
        self.spreadsheet = self.client.open_by_key(SPREADSHEET_ID)
        self._create_month_sheets()
        self.create_weekly_summary_sheet()

    #     self._start_auto_update()

    # def _start_auto_update(self):
    #     """Запускает таймер для автообновления каждое полчаса"""
    #     def _update_loop():
    #         self.create_weekly_summary_sheet()
    #         print(f"[{datetime.now()}] Сводный календарь обновлен")

    #         Timer(300, _update_loop).start()

    #     _update_loop()  # первый вызов сразу
        
        
    def _create_month_sheets(self):
        """Создает листы для текущего месяца и двух следующих"""
        now = datetime.now()
        months = []
        
        for i in range(3):
            month_date = now + timedelta(days=30*i)
            sheet_name = month_date.strftime("%Y-%m")
            months.append(sheet_name)
        
        existing_sheets = [sheet.title for sheet in self.spreadsheet.worksheets()]
        
        for sheet_name in months:
            if sheet_name not in existing_sheets:
                worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=200, cols=12)
                self._initialize_sheet(worksheet)
    
    def _initialize_sheet(self, worksheet):
        """Инициализирует новый лист таблицы с чередующейся подсветкой дат"""
        # Заголовки столбцов
        headers = [
            "Число", "Номер", "Время", "Длит", 
            "Площадь", "Тип", "ЭМИ", "Радиация",
            "Обмер", "Оценка", "Контакты", "Адрес"
        ]
        
        # Форматирование заголовков
        worksheet.update('A1:L1', [headers])
        worksheet.format('A1:L1', {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })
        
        # Создаем 31 набор строк (по 4 строки на каждый день)
        data = []
        format_ranges = []  # Будем хранить диапазоны для форматирования
        
        for day in range(1, 32):
            for slot_num in range(1, 5):
                data.append([day, slot_num] + [""]*10)
            
            # Определяем, нужно ли подсвечивать эту дату (каждое второе число)
            if (day % 2) == 0:
                start_row = 2 + (day-1)*4  # Первая строка дня
                end_row = start_row + 3    # Последняя строка дня
                format_ranges.append(f"A{start_row}:L{end_row}")
        
        # Записываем данные, начиная со 2-й строки
        worksheet.update(f'A2:L{1 + len(data)}', data)
        
        # Применяем серый фон для выделенных диапазонов
        if format_ranges:
            worksheet.format(format_ranges, {
                "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95},
                "borders": {
                    "top": {"style": "SOLID"},
                    "bottom": {"style": "SOLID"},
                    "left": {"style": "SOLID"},
                    "right": {"style": "SOLID"}
                }
            })
        
        # Форматируем границы для всех ячеек
        all_data_range = f"A2:L{1 + len(data)}"
        worksheet.format(all_data_range, {
            "borders": {
                "top": {"style": "SOLID", "width": 1},
                "bottom": {"style": "SOLID", "width": 1},
                "left": {"style": "SOLID", "width": 1},
                "right": {"style": "SOLID", "width": 1}
            }
        })
        
        # Закрепляем заголовки
        worksheet.freeze(rows=1)

    def create_months(self):
        self._create_month_sheets()

    def _get_worksheet(self, date):
        """Возвращает рабочий лист для указанной даты"""
        sheet_name = date.strftime("%Y-%m")
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            return None
    
    def get_busy_slots(self, date):
        """Возвращает список занятых слотов на указанную дату"""
        worksheet = self._get_worksheet(date)
        if not worksheet:
            return []
        
        day = date.day
        records = worksheet.get_all_records()
        busy_slots = []
        
        for record in records:
            if record["Число"] == day and record["Время"] != "":
                start_hour = record["Время"]
                duration = record["Длит"]
                busy_slots.append((start_hour, duration))
                
        return busy_slots
    
    def add_appointment(self, data):
        """Добавляет новую запись в таблицу"""
        date_obj = data["date"]
        worksheet = self._get_worksheet(date_obj)
        if not worksheet:
            return False, "Лист для этого месяца не найден"
        
        day = date_obj.day
        records = worksheet.get_all_records()
        row_index = None
        
        # Ищем первую свободную строку для этого дня
        for i, record in enumerate(records):
            if record["Число"] == day and record["Время"] == "":
                row_index = i + 2  # +2 из-за заголовка
                break
        
        if row_index is None:
            return False, "Нет свободных слотов в этот день"
        
        # Подготавливаем данные для записи
        values = [
            day,
            records[i]["Номер"],
            data["start_hour"],
            continuety(data),
            data["area"],
            data["apartment_type"],
            "Да" if data["em_screening"] else "Нет",
            "Да" if data["radiation_check"] else "Нет",
            data["measurement_type"],
            "Да" if data["valuation"] else "Нет",
            data["contacts"],
            data["housing_estate_address"]
        ]
        
        # Обновляем строку
        worksheet.update(f'A{row_index}:L{row_index}', [values])
        self.create_weekly_summary_sheet()

        return True, "Запись успешно добавлена"
    
    def update_appointment(self, date, start_hour, new_data):
        """Обновляет существующую запись по дате и времени"""
        worksheet = self._get_worksheet(date)
        if not worksheet:
            return False, "Лист для этого месяца не найден"
        
        day = date.day
        records = worksheet.get_all_records()
        row_index = None
        
        # Ищем запись с указанным днем и временем
        for i, record in enumerate(records):
            if record["Число"] == day and record["Время"] == start_hour:
                row_index = i + 2  # +2 из-за заголовка
                break
        
        if row_index is None:
            return False, "Запись не найдена"
        
        # Подготавливаем новые значения
        values = [
            day,
            records[i]["Номер"],
            new_data.get("start_hour", start_hour),
            continuety(new_data),
            new_data.get("area", ""),
            new_data.get("apartment_type", ""),
            "Да" if new_data.get("em_screening", False) else "Нет",
            "Да" if new_data.get("radiation_check", False) else "Нет",
            new_data.get("measurement_type", ""),
            "Да" if new_data.get("valuation", False) else "Нет",
            new_data.get("contacts", ""),
            new_data.get("housing_estate_address", "")
        ]
        
        # Обновляем строку
        worksheet.update(f'A{row_index}:L{row_index}', [values])
        self.create_weekly_summary_sheet()
        
        return True, "Запись успешно обновлена"
    
    def create_weekly_summary_sheet(self):
        """Создает сводный лист с календарной сеткой по неделям"""
        try:
            # Удаляем старый сводный лист, если он существует
            try:
                summary_sheet = self.spreadsheet.worksheet("Сводный календарь")
                self.spreadsheet.del_worksheet(summary_sheet)
            except gspread.WorksheetNotFound:
                pass
            
            # Создаем новый сводный лист
            summary_sheet = self.spreadsheet.add_worksheet(
                title="Сводный календарь", 
                rows=100,  # Достаточно для 3 месяцев по неделям
                cols=8    # День недели + 7 дней
            )
            
            # Получаем данные за 3 месяца
            now = datetime.now()
            months_data = []
            
            for i in range(3):
                month_date = now + timedelta(days=30*i)
                sheet_name = month_date.strftime("%Y-%m")
                try:
                    worksheet = self.spreadsheet.worksheet(sheet_name)
                    months_data.append({
                        "month": month_date,
                        "data": worksheet.get_all_records()
                    })
                except gspread.WorksheetNotFound:
                    continue
            
            # Создаем календарную сетку по неделям
            grid = self._build_weekly_calendar_grid(months_data)
            
            # Записываем данные в сводный лист
            summary_sheet.update('A1', grid)
            
            # Форматируем сводный лист
            self._format_weekly_summary_sheet(summary_sheet)
            
            return True
        except Exception as e:
            print(f"Ошибка создания сводного листа: {str(e)}")
            return False

    def _build_weekly_calendar_grid(self, months_data):
        """Строит календарную сетку по неделям"""
        # Заголовки столбцов (дни недели)
        weekdays = ["Неделя", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        grid = [weekdays]
        
        # Собираем все события за 3 месяца
        all_events = []
        for month_info in months_data:
            for record in month_info["data"]:
                if record["Время"]:
                    event_date = date(
                        month_info["month"].year,
                        month_info["month"].month,
                        record["Число"]
                    )
                    event_info = (
                        f"{record['Время']}:00-{record['Время']+record['Длит']}:00 "
                        f"{record['Тип']} {record['Площадь']}м²"
                    )
                    all_events.append((event_date, event_info))
        
        # Группируем по неделям
        current_week = None
        week_events = {}
        
        for event_date, event_info in sorted(all_events, key=lambda x: x[0]):
            year, week_num, _ = event_date.isocalendar()
            week_key = f"{year}-W{week_num}"
            
            if week_key != current_week:
                if current_week:
                    # Добавляем завершенную неделю в grid
                    grid.append(self._format_week_row(current_week, week_events))
                current_week = week_key
                week_events = {i: [] for i in range(7)}  # 0=Пн, 6=Вс
            
            weekday = event_date.weekday()  # 0=Пн, 6=Вс
            week_events[weekday].append(event_info)
        
        # Добавляем последнюю неделю
        if current_week:
            grid.append(self._format_week_row(current_week, week_events))
        
        return grid

    def _format_week_row(self, week_key, week_events):
        """Форматирует строку с данными за неделю"""

        year, week_num = map(int, week_key.split('-W'))
        monday = datetime.fromisocalendar(year, week_num, 1)

        start_date = datetime.fromisocalendar(year, week_num, 1).strftime('%d.%m')
        end_date = datetime.fromisocalendar(year, week_num, 7).strftime('%d.%m')        
        week_title = f"{start_date}-{end_date}"
        row = [week_title]
        for day in range(7):
            current_date = monday + timedelta(days=day)
            day_num = current_date.day  # ← вот он, только число
            events = "\n".join([str(e) for e in week_events.get(day, [])])
            row.append(f"{day_num}\n{events}")
        
        return row

    def _format_weekly_summary_sheet(self, worksheet):
        """Форматирует сводный лист с неделями"""
        # Форматирование заголовков
        worksheet.format('A1:H1', {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
            "horizontalAlignment": "CENTER"
        })
        
        # Форматирование данных
        worksheet.format('A2:H100', {
            "wrapStrategy": "WRAP",
            "verticalAlignment": "TOP"
        })
        
        # Настраиваем ширину столбцов
        body = {
            "requests": [
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": worksheet.id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 1
                        },
                        "properties": {
                            "pixelSize": 120  # Ширина для колонки с датами недели
                        },
                        "fields": "pixelSize"
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": worksheet.id,
                            "dimension": "COLUMNS",
                            "startIndex": 1,
                            "endIndex": 8
                        },
                        "properties": {
                            "pixelSize": 150  # Ширина для дней недели
                        },
                        "fields": "pixelSize"
                    }
                }
            ]
        }
        
        self.spreadsheet.batch_update(body)
        
        # Закрепляем заголовки
        worksheet.freeze(rows=1, cols=1)