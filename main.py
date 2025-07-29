import asyncio

from bot_set import bot, dp 
from app.handlers import router
from app.slotswork import update_calendar

async def run_calendar_updater():
    while True:
        try:
            update_calendar()
        except Exception as e:
            print(f"Ошибка обновления календаря: {e}")
        await asyncio.sleep(300)

async def main():
    dp.include_router(router)
    asyncio.create_task(run_calendar_updater())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())