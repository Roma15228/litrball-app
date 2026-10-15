#!/usr/bin/env python3
"""
Шаблон Telegram-бота для запуска приложения «Федерация Литрбола» в виде Telegram Mini App (TMA).
Требуется: pip install aiogram (или pyTelegramBotAPI)
Использование:
  export TELEGRAM_BOT_TOKEN="ВАШ_ТОКЕН_ОТ_BOTFATHER"
  python3 bot_example.py
"""

import os
import sys

# Проверка наличия токена
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# URL развернутого веб-приложения (например, на Render, Railway, ngrok или VPS)
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")

if not BOT_TOKEN:
    print("ВНИМАНИЕ: Переменная окружения TELEGRAM_BOT_TOKEN не задана.")
    print("Пример запуска:")
    print("  export TELEGRAM_BOT_TOKEN=\"123456789:ABCdef...\"")
    print("  export WEBAPP_URL=\"https://my-litrball-app.com\"")
    print("  python3 bot_example.py")
    sys.exit(0)

try:
    import asyncio
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import CommandStart
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🏆 Получить разряд по литрболу",
                        web_app=WebAppInfo(url=WEBAPP_URL)
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🎓 Сдать экзамен ВАК",
                        web_app=WebAppInfo(url=f"{WEBAPP_URL}#quiz")
                    )
                ]
            ]
        )

        greeting = (
            f"Приветствуем вас, атлет {message.from_user.first_name}! 🍺\n\n"
            "Добро пожаловать в официальный бот **Всероссийской Федерации Литрбола (ВФЛ)**.\n\n"
            "Здесь вы можете:\n"
            "• Рассчитать свой спортивный разряд по формуле Видмарка;\n"
            "• Сдать теоретический экзамен Высшей Аттестационной Комиссии;\n"
            "• Получить и скачать официальную корочку с золотым тиснением и печатью!\n\n"
            "Нажмите кнопку ниже, чтобы открыть приложение:"
        )

        await message.answer(greeting, reply_markup=keyboard, parse_mode="Markdown")

    async def main():
        print("🤖 Бот Федерации Литрбола запущен и ожидает спортсменов...")
        await dp.start_polling(bot)

    if __name__ == "__main__":
        asyncio.run(main())

except ImportError:
    print("Для запуска Telegram-бота установите библиотеку aiogram:")
    print("  pip install aiogram")
