import asyncio

from bot_set import bot
from config import ADMIN_CHAT_ID

async def send_to_admin(message: str):
    """Отправляет сообщение администратору."""
    try:
        await bot.send_message(ADMIN_CHAT_ID, message)
    except Exception as e:
        print(f"Ошибка при отправке сообщения администратору: {e}")