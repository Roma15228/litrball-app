# 🚀 Руководство по Бесплатному Деплою (24/7) — ВФЛ Литрбол

Приложение «Всероссийская Федерация Литрбола» включает в себя:
1. **Telegram-бот** на `aiogram 3.x`
2. **Web-сервер с REST API** на Python 3
3. **Telegram Mini App (TMA)** с поддержкой мобильных устройств и десктопа
4. **Базу данных SQLite** (`litrball.db`) для Зала Славы и удостоверений

Ниже представлены самые простые и надежные способы запуска 24/7 без затрат.

---

## 🏆 Вариант 1 (Рекомендуемый): Бесплатный хостинг Render.com

Render предоставляет **бесплатный тариф Web Service** с автоматическим HTTPS доменом (`https://your-app.onrender.com`), который идеально подходит для Telegram Mini Apps.

### Пошаговая инструкция (2 минуты):
1. Зарегистрируйтесь на [Render.com](https://render.com/) (через GitHub или почту).
2. Создайте новый публичный или приватный репозиторий на GitHub и загрузите файлы из папки `projects/litrball-app`.
3. В панели Render нажмите **New +** ➔ **Web Service**.
4. Выберите ваш GitHub репозиторий с проектом.
5. Render автоматически обнаружит `render.yaml` или настройки:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `./start.sh`
   - **Plan:** `Free`
6. В разделе **Environment Variables** добавьте:
   - `TELEGRAM_BOT_TOKEN` = `8754238743:AAFEnocqZVPyxuiECPrMagLFILJltfPxGRo`
7. Нажмите **Deploy Web Service**.
8. Через минуту вы получите постоянный HTTPS адрес, например:
   `https://litrball-federation.onrender.com`
9. Добавьте в Environment Variables переменную:
   - `WEBAPP_URL` = `https://litrball-federation.onrender.com`
10. Готово! Бот и Mini App будут работать круглосуточно в облаке.

---

## 🥈 Вариант 2: Бесплатный хостинг Koyeb.com

Koyeb дает бесплатный микро-инстанс и автоматический SSL:
1. Зарегистрируйтесь на [Koyeb.com](https://www.koyeb.com/).
2. Нажмите **Create App** ➔ **GitHub**.
3. Выберите репозиторий, укажите порт `8080` и команду запуска `./start.sh`.
4. Задайте переменную `TELEGRAM_BOT_TOKEN`.
5. Получите бесплатный домен вида `https://xxx-yourname.koyeb.app`.

---

## 🥉 Вариант 3: Запуск на собственном VPS / Сервере через Docker

Если у вас есть любой VPS (Ubuntu, Debian, ALT Linux):

```bash
cd projects/litrball-app

# Запуск в фоновом режиме через Docker Compose
docker compose up -d --build

# Проверка логов
docker compose logs -f
```

---

## 📱 Как привязать Mini App к боту через @BotFather

Чтобы в самом Telegram внизу чата появилась кнопка **«Меню» / «Открыть приложение»**:

1. Откройте в Telegram диалог с **[@BotFather](https://t.me/BotFather)**.
2. Отправьте команду:
   ```
   /setmenubutton
   ```
3. Выберите вашего бота `@gamumuFILMS_bot`.
4. Введите URL вашего развернутого приложения (например `https://litrball-federation.onrender.com`).
5. Введите название кнопки:
   ```
   🏅 Литрбол ВФЛ
   ```
6. Теперь у всех пользователей прямо в окне ввода появится кнопка Mini App!
