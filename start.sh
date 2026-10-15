#!/usr/bin/env bash
set -e

echo "=================================================="
echo "🍺 Запуск Всероссийской Федерации Литрбола (ВФЛ)"
echo "📍 WebApp сервер на порту: ${PORT:-8080}"
echo "=================================================="

# Запуск WebApp сервера в фоне
python3 app.py "${PORT:-8080}" &
WEB_PID=$!

# Запуск Telegram-бота в фоне
python3 bot.py &
BOT_PID=$!

# Обработка сигналов завершения
trap 'kill $WEB_PID $BOT_PID; exit' SIGINT SIGTERM

# Ожидание процессов
wait -n $WEB_PID $BOT_PID
