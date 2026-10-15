#!/usr/bin/env bash
# Скрипт запуска Telegram-бота Всероссийской Федерации Литрбола

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Проверка venv
if [ ! -d "venv" ]; then
    echo "Создаем виртуальное окружение..."
    python3 -m venv venv
    venv/bin/pip install --upgrade pip aiogram pillow
fi

# Проверка токена
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "================================================================"
    echo "❌ ОШИБКА: TELEGRAM_BOT_TOKEN не обнаружен!"
    echo "Как получить токен за 1 минуту:"
    echo "1. Откройте Telegram и найдите бота @BotFather"
    echo "2. Отправьте команду /newbot"
    echo "3. Введите название (например: Литрбол Бот) и юзернейм (например: litrball_super_bot)"
    echo "4. Скопируйте выданный токен и вставьте сюда:"
    read -p "Введите TELEGRAM_BOT_TOKEN: " USER_TOKEN
    if [ -n "$USER_TOKEN" ]; then
        echo "TELEGRAM_BOT_TOKEN=\"$USER_TOKEN\"" > .env
        export TELEGRAM_BOT_TOKEN="$USER_TOKEN"
        echo "Токен сохранен в .env!"
    else
        echo "Токен не введен. Запуск отменен."
        exit 1
    fi
    echo "================================================================"
fi

echo "🚀 Запуск Telegram-бота..."
./venv/bin/python bot.py
