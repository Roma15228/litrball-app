#!/usr/bin/env python3
"""
Всероссийская Федерация Литрбола (ВФЛ)
Официальный Telegram-бот с Детектором Пиздежа, Калькулятором, Дуэлями, Залом Славы и Mini App.
"""

import os
import sys
import asyncio
import random
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

# Импорт логики, базы данных и генератора сертификатов
from app import RANKS, QUIZ_QUESTIONS, TOASTS_COLLECTION, HANGOVER_PROTOCOL, calculate_score
import database
from cert_generator import generate_certificate_image

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

# FSM Состояния
class LitrballStates(StatesGroup):
    choosing_action = State()
    calc_weight = State()
    calc_drinks = State()
    calc_snack = State()
    calc_hours = State()
    # Детектор пиздежа
    detector_math = State()
    detector_reaction = State()
    detector_photo = State()
    # Квиз
    quiz_running = State()

# Кнопки главного меню
def get_main_keyboard():
    buttons = []
    if WEBAPP_URL:
        buttons.append([InlineKeyboardButton(text="📲 Открыть Mini App (ВФЛ Спорт-Портал)", web_app=types.WebAppInfo(url=WEBAPP_URL))])
    
    buttons.extend([
        [InlineKeyboardButton(text="🧮 Сдать норматив (Калькулятор)", callback_data="menu_calc")],
        [InlineKeyboardButton(text="🎯 Детектор Пиздежа (Проверка)", callback_data="menu_detector")],
        [InlineKeyboardButton(text="🪪 Мой Спортивный Паспорт", callback_data="menu_passport")],
        [InlineKeyboardButton(text="⚔️ Застольная Дуэль (PvP)", callback_data="menu_duel")],
        [InlineKeyboardButton(text="🏆 Зал Славы (Топ атлетов)", callback_data="menu_top")],
        [InlineKeyboardButton(text="🥂 Генератор Тостов", callback_data="menu_toast")],
        [InlineKeyboardButton(text="🚑 Антипохмельный SOS", callback_data="menu_sos")],
        [InlineKeyboardButton(text="🎓 Экзамен ВАК (Теория)", callback_data="menu_quiz")],
        [InlineKeyboardButton(text="📜 Таблица разрядов ЕЗСК", callback_data="menu_ranks")]
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# -------------------------------------------------------------
# ХЕНДЛЕРЫ: СТАРТ И ГЛАВНОЕ МЕНЮ
# -------------------------------------------------------------

async def register_handlers(dp: Dispatcher, bot: Bot):

    @dp.message(CommandStart())
    async def cmd_start(message: types.Message, state: FSMContext):
        await state.clear()
        name = message.from_user.first_name or "Атлет"
        text = (
            f"🏆 **Всероссийская Федерация Литрбола (ВФЛ)** приветствует вас, гражданин {name}!\n\n"
            "Здесь проходит официальная аттестация спортсменов по застольному многоборью.\n\n"
            "⚠️ **Внимание:** Введена обязательная система **«Детектор Пиздежа»** — "
            "попытки приписать себе лишние литры или скрыть утренний визит к Ихтиандру "
            "караются судейской коллегией!\n\n"
            "💡 Доступно полноценное **Telegram Mini App** с 3D-паспортом, трезвомером и дуэлями!"
        )
        await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

    @dp.callback_query(F.data == "menu_main")
    async def cb_main(callback: types.CallbackQuery, state: FSMContext):
        await state.clear()
        text = "🏆 Главное меню Федерации Литрбола. Выберите дисциплину:"
        kb = get_main_keyboard()
        if callback.message.photo:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
        else:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

    # -------------------------------------------------------------
    # ДОБАВЛЕНИЕ БОТА В ГРУППОВОЙ ЧАТ
    # -------------------------------------------------------------
    @dp.my_chat_member()
    async def on_my_chat_member(event: types.ChatMemberUpdated):
        chat = event.chat
        if chat.type in ['group', 'supergroup']:
            new_status = event.new_chat_member.status
            if new_status in ["member", "administrator"]:
                member_count = 0
                try:
                    member_count = await bot.get_chat_member_count(chat.id)
                except Exception as e:
                    logger.warning(f"Failed to get member count: {e}")
                
                database.track_or_update_chat(chat.id, chat.title or "Застольный чат", chat.type, member_count)
                
                welcome_kb = []
                if WEBAPP_URL:
                    welcome_kb.append([InlineKeyboardButton(text="📲 Открыть Mini App чата", web_app=types.WebAppInfo(url=f"{WEBAPP_URL}?chat_id={chat.id}"))])
                welcome_kb.append([InlineKeyboardButton(text="🍻 Накатить пива (/drink)", callback_data="drink_act:beer:500:5.0")])
                
                greeting = (
                    f"🏛️ **ВСЕРОССИЙСКАЯ ФЕДЕРАЦИЯ ЛИТРБОЛА (ВФЛ)**\n"
                    f"Официальное региональное отделение открыто в чате **«{chat.title}»**!\n\n"
                    f"👥 Спортсменов в составе: **{member_count}** человек.\n"
                    f"📋 Начинаем официальный учет застольных подвигов и разрядов!\n\n"
                    f"🏆 **Команды филиала:**\n"
                    f"🍺 `/drink` [напиток] [мл] — Зафиксировать подход к снаряду (напр. `/drink пиво 500` или `/drink водка 50`)\n"
                    f"🥇 `/top` — Таблица рекордов участников этого чата\n"
                    f"📊 `/stats` — Общая статистика возлияний чата\n"
                    f"⚔️ `/duel` — Вызов на дуэль (ответом на сообщение собутыльника)\n"
                    f"🥂 `/toast` — Официальный тост от судейской коллегии\n"
                    f"🪪 `/passport` — Спортивный паспорт ВФЛ"
                )
                await bot.send_message(chat.id, greeting, reply_markup=InlineKeyboardMarkup(inline_keyboard=welcome_kb), parse_mode="Markdown")


    # -------------------------------------------------------------
    # WEBAPP ОБРАБОТЧИК ДАННЫХ
    # -------------------------------------------------------------
    @dp.message(F.web_app_data)
    async def handle_webapp_data(message: types.Message):
        """Получение данных из Telegram Mini App"""
        try:
            payload = json.loads(message.web_app_data.data)
            action = payload.get("action")
            user_name = message.from_user.full_name or "Атлет"

            if action == "save_result":
                res = payload.get("result", {})
                rank = res.get("rank", {})
                
                # Сохраняем в SQLite
                saved = database.save_or_update_athlete({
                    "tg_user_id": message.from_user.id,
                    "name": user_name,
                    "username": message.from_user.username,
                    "weight": payload.get("weight", 80),
                    "gender": payload.get("gender", "m"),
                    "rank": rank,
                    "score": res.get("score", 0),
                    "pure_ethanol_g": res.get("pure_ethanol_g", 0),
                    "est_bac_promille": res.get("est_bac_promille", 0),
                    "disciplines": res.get("disciplines", "Застольное многоборье"),
                    "order_num": res.get("order_num", "№ ФЛР-2026"),
                    "verified": payload.get("verified", False)
                })

                # Аватар
                avatar_bytes = None
                try:
                    photos = await bot.get_user_profile_photos(message.from_user.id, limit=1)
                    if photos and photos.photos:
                        photo_file = await bot.get_file(photos.photos[0][-1].file_id)
                        photo_stream = await bot.download_file(photo_file.file_path)
                        avatar_bytes = photo_stream.read()
                except Exception as e:
                    logger.warning(f"Avatar error: {e}")

                cert_png = generate_certificate_image(
                    name=user_name,
                    rank_title=rank.get("title", "Любитель"),
                    weight=float(payload.get("weight", 80)),
                    discipline=res.get("disciplines", "Застольное многоборье"),
                    order_num=res.get("order_num", "№ ФЛР-2026"),
                    pure_ethanol_g=float(res.get("pure_ethanol_g", 0)),
                    est_bac=float(res.get("est_bac_promille", 0)),
                    user_avatar_bytes=avatar_bytes
                )

                caption = (
                    f"🎖️ **РЕЗУЛЬТАТ ИЗ MINI APP ПРИНЯТ КОМИССИЕЙ!**\n\n"
                    f"Атлет: **{user_name}**\n"
                    f"Звание: **{rank.get('title')}** {rank.get('badge', '🏅')}\n"
                    f"Спортивный балл: **{res.get('score')}** очков\n"
                    f"Приказ: `{res.get('order_num')}`\n\n"
                    f"Корочка зарегистрирована в Едином Реестре ВФЛ!"
                )

                await message.answer_photo(
                    photo=BufferedInputFile(cert_png, filename=f"Удостоверение_{user_name}.png"),
                    caption=caption,
                    reply_markup=get_main_keyboard(),
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Error handling webapp data: {e}")
            await message.answer("Произошла ошибка при обработке данных из Mini App.")

    # -------------------------------------------------------------
    # СПОРТИВНЫЙ ПАСПОРТ АТЛЕТА
    # -------------------------------------------------------------
    @dp.message(Command("passport"))
    @dp.callback_query(F.data == "menu_passport")
    async def show_passport(event: types.Message | types.CallbackQuery):
        user = event.from_user
        athlete = database.get_athlete(tg_user_id=user.id)
        
        if isinstance(event, types.CallbackQuery):
            msg = event.message
            await event.answer()
        else:
            msg = event

        if not athlete:
            text = (
                f"🪪 **Спортивный Паспорт ВФЛ: Не оформлен**\n\n"
                f"Гражданин {user.first_name}, вы еще не сдали официальный норматив.\n"
                "Пройдите аттестацию в Калькуляторе или Mini App, чтобы получить персональную корочку!"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🧮 Сдать норматив прямо сейчас »", callback_data="menu_calc")],
                [InlineKeyboardButton(text="« Главное меню", callback_data="menu_main")]
            ])
            await msg.answer(text, reply_markup=kb, parse_mode="Markdown")
            return

        # Иконки ачивок
        ach_icons = ""
        ach_count = len(athlete.get('achievements', []))
        for ach_id in athlete.get('achievements', []):
            ach_item = next((a for a in database.ACHIEVEMENTS_LIST if a['id'] == ach_id), None)
            if ach_item:
                ach_icons += f"{ach_item['icon']} "

        verified_badge = "✅ Проверен Детектором" if athlete.get('verified') else "⚠️ Без полевой проверки"

        text = (
            f"🪪 **СПОРТИВНЫЙ ПАСПОРТ АТЛЕТА ВФЛ**\n\n"
            f"👤 ФИО: **{athlete['name']}**\n"
            f"🎖️ Звание: **{athlete['rank_title']}**\n"
            f"⚖️ Весовая категория: **{athlete['weight']} кг**\n"
            f"🏆 Рекордный балл: **{athlete['score']}** очков\n"
            f"🍺 Коронная дисциплина: **{athlete['discipline']}**\n"
            f"📜 Приказ: `{athlete['order_num']}`\n"
            f"🛡️ Статус: **{verified_badge}**\n\n"
            f"🏅 Награды и достижения ({ach_count}):\n{ach_icons or 'Пока наград нет'}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🖼️ Скачать официальную корочку", callback_data="get_cert_image")],
            [InlineKeyboardButton(text="🔄 Пересдать норматив", callback_data="menu_calc")],
            [InlineKeyboardButton(text="« Главное меню", callback_data="menu_main")]
        ])
        await msg.answer(text, reply_markup=kb, parse_mode="Markdown")

    @dp.callback_query(F.data == "get_cert_image")
    async def cb_get_cert(callback: types.CallbackQuery):
        await callback.answer("Генерируем корочку...")
        athlete = database.get_athlete(tg_user_id=callback.from_user.id)
        if not athlete:
            await callback.message.answer("Сначала сдайте норматив!")
            return
        
        avatar_bytes = None
        try:
            photos = await bot.get_user_profile_photos(callback.from_user.id, limit=1)
            if photos and photos.photos:
                photo_file = await bot.get_file(photos.photos[0][-1].file_id)
                photo_stream = await bot.download_file(photo_file.file_path)
                avatar_bytes = photo_stream.read()
        except Exception as e:
            logger.warning(f"Avatar error: {e}")

        cert_png = generate_certificate_image(
            name=athlete['name'],
            rank_title=athlete['rank_title'],
            weight=athlete['weight'],
            discipline=athlete['discipline'],
            order_num=athlete['order_num'],
            pure_ethanol_g=athlete['pure_ethanol_g'],
            est_bac=athlete['est_bac'],
            user_avatar_bytes=avatar_bytes
        )

        await callback.message.answer_photo(
            photo=BufferedInputFile(cert_png, filename="Удостоверение_ВФЛ.png"),
            caption=f"Удостоверение атлета: **{athlete['name']}**\nПриказ: `{athlete['order_num']}`",
            parse_mode="Markdown"
        )

    # -------------------------------------------------------------
    # ЗАЛ СЛАВЫ / ТОП ЧАТА
    # -------------------------------------------------------------
    @dp.message(Command("top"))
    @dp.callback_query(F.data == "menu_top")
    async def show_top(event: types.Message | types.CallbackQuery):
        if isinstance(event, types.CallbackQuery):
            await event.answer()
            msg = event.message
            is_group = False
            chat_id = msg.chat.id
            chat_title = ""
        else:
            msg = event
            is_group = msg.chat.type in ['group', 'supergroup']
            chat_id = msg.chat.id
            chat_title = msg.chat.title or "Чат"

        if is_group:
            try:
                mc = await bot.get_chat_member_count(chat_id)
                database.track_or_update_chat(chat_id, chat_title, msg.chat.type, mc)
            except Exception:
                pass

            leaders = database.get_chat_leaderboard(chat_id, limit=10)
            if not leaders:
                text = (
                    f"🏆 **РЕЙТИНГ АТЛЕТОВ ЧАТА «{chat_title}»**\n\n"
                    f"В этом чате пока никто не накатил и не сдал норматив!\n"
                    f"Будьте первым: напишите `/drink пиво 500` или откройте Mini App!"
                )
                kb_btns = []
                if WEBAPP_URL:
                    kb_btns.append([InlineKeyboardButton(text="📲 Открыть Mini App чата", web_app=types.WebAppInfo(url=f"{WEBAPP_URL}?chat_id={chat_id}"))])
                await msg.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_btns), parse_mode="Markdown")
                return

            lines = [f"🏆 **РЕЙТИНГ АТЛЕТОВ ЧАТА «{chat_title}» (ТОП-10):**\n"]
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for idx, a in enumerate(leaders):
                m = medals[idx] if idx < len(medals) else "🏅"
                uname = f"@{a['username']}" if a.get('username') else a['user_name']
                lines.append(f"{m} **{a['user_name']}** ({uname}) — **{a['score']}** очков")
                lines.append(f"   _{a['rank_title']} | Спирта: {a['pure_ethanol_g']}г | Подходов: {a['drinks_count']}_\n")

            kb_btns = []
            if WEBAPP_URL:
                kb_btns.append([InlineKeyboardButton(text="📲 Открыть Mini App чата", web_app=types.WebAppInfo(url=f"{WEBAPP_URL}?chat_id={chat_id}"))])
            await msg.answer("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_btns), parse_mode="Markdown")
        else:
            # Личный чат — глобальный Зал Славы (только реальные атлеты)
            leaders = database.get_leaderboard(limit=10)
            if not leaders:
                text = (
                    "🏆 **ЗАЛ СЛАВЫ ФЕДЕРАЦИИ ЛИТРБОЛА**\n\n"
                    "В официальном Зале Славы пока нет атлетов.\n"
                    "Сдайте норматив в Калькуляторе или Mini App и станьте первым чемпионом!"
                )
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🧮 Сдать норматив прямо сейчас", callback_data="menu_calc")],
                    [InlineKeyboardButton(text="« Главное меню", callback_data="menu_main")]
                ])
                await msg.answer(text, reply_markup=kb, parse_mode="Markdown")
                return

            lines = ["🏆 **ЗАЛ СЛАВЫ ФЕДЕРАЦИИ ЛИТРБОЛА (ТОП-10):**\n"]
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for idx, a in enumerate(leaders):
                m = medals[idx] if idx < len(medals) else "🏅"
                check = "✓" if a.get('verified') else ""
                lines.append(f"{m} **{a['name']}** {check} — **{a['score']}** очков")
                lines.append(f"   _{a['rank_title']} | {a['discipline']}_\n")

            lines.append("💡 *Галочка ✓ означает успешное прохождение Детектора Пиздежа.*")
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🧮 Попасть в Зал Славы (Сдать норматив)", callback_data="menu_calc")],
                [InlineKeyboardButton(text="« Главное меню", callback_data="menu_main")]
            ])
            await msg.answer("\n".join(lines), reply_markup=kb, parse_mode="Markdown")

    # -------------------------------------------------------------
    # СТАТИСТИКА ЧАТА (/stats)
    # -------------------------------------------------------------
    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        chat = message.chat
        if chat.type in ['group', 'supergroup']:
            try:
                mc = await bot.get_chat_member_count(chat.id)
                database.track_or_update_chat(chat.id, chat.title, chat.type, mc)
            except Exception:
                pass
            stats = database.get_chat_stats(chat.id)
            if not stats:
                await message.answer("Статистика этого чата еще формируется. Напишите `/drink`!")
                return
            
            vodka_bottles = round(stats['total_ethanol_g'] / (500 * 0.40 * 0.789), 1)
            top = stats.get('top_athlete')
            top_info = f"👑 Чемпион чата: **{top['user_name']}** ({top['rank_title']}, {top['score']} очков)" if top else "👑 Чемпион чата: пока не определен"

            text = (
                f"📊 **СВОДКА АЛКО-АКТИВНОСТИ ЧАТА «{stats['title']}»**\n\n"
                f"👥 Всего людей в чате: **{stats['member_count']}** чел.\n"
                f"🏋️ Зарегистрировано активных бойцов: **{stats['active_athletes_count']}**\n"
                f"🍻 Всего подходов к снаряду: **{stats['drinks_count']}**\n"
                f"🧪 Суммарный объем чистого спирта: **{stats['total_ethanol_g']} г**\n"
                f"🍾 Эквивалент в водке (0.5л 40%): **~{vodka_bottles}** бутылок\n\n"
                f"{top_info}\n\n"
                f"💡 Чтобы зафиксировать напиток, используйте `/drink [напиток] [мл]`"
            )
            kb = []
            if WEBAPP_URL:
                kb.append([InlineKeyboardButton(text="📲 Открыть Mini App чата", web_app=types.WebAppInfo(url=f"{WEBAPP_URL}?chat_id={chat.id}"))])
            await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")
        else:
            await message.answer("📊 Команда `/stats` показывает сводку по чату. Добавьте бота в группу с друзьями!")

    # -------------------------------------------------------------
    # ФИКСАЦИЯ НАПИТКА (/drink)
    # -------------------------------------------------------------
    @dp.message(Command("drink"))
    async def cmd_drink(message: types.Message):
        user = message.from_user
        chat = message.chat
        text_args = message.text.split()[1:] if message.text else []

        if len(text_args) == 0:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🍺 Пиво 0.5л", callback_data="drink_act:beer:500:5.0"),
                    InlineKeyboardButton(text="🍻 IPA 0.5л", callback_data="drink_act:ipa:500:6.8")
                ],
                [
                    InlineKeyboardButton(text="🥃 Водка 50мл", callback_data="drink_act:vodka:50:40.0"),
                    InlineKeyboardButton(text="🥃 Водка 100мл", callback_data="drink_act:vodka:100:40.0")
                ],
                [
                    InlineKeyboardButton(text="🍷 Вино 150мл", callback_data="drink_act:wine:150:12.5"),
                    InlineKeyboardButton(text="🥃 Виски 100мл", callback_data="drink_act:whiskey:100:40.0")
                ],
                [
                    InlineKeyboardButton(text="🍹 Коктейль «Ёрш» 0.5л", callback_data="drink_act:ersh:500:12.0")
                ]
            ])
            await message.answer(f"🍺 Гражданин {user.first_name}, выберите подход к снаряду:", reply_markup=kb)
            return

        raw_input = " ".join(text_args).lower()
        if "водк" in raw_input:
            drink_name, abv, volume_ml = "Водка", 40.0, 50.0
        elif "пив" in raw_input or "пенн" in raw_input:
            drink_name, abv, volume_ml = "Пиво", 5.0, 500.0
        elif "вин" in raw_input:
            drink_name, abv, volume_ml = "Вино", 12.5, 150.0
        elif "виск" in raw_input or "коньяк" in raw_input:
            drink_name, abv, volume_ml = "Виски/Коньяк", 40.0, 100.0
        elif "сидр" in raw_input:
            drink_name, abv, volume_ml = "Сидр", 5.5, 500.0
        elif "текил" in raw_input or "ром" in raw_input:
            drink_name, abv, volume_ml = "Текила/Ром", 40.0, 50.0
        elif "ёрш" in raw_input or "ерш" in raw_input:
            drink_name, abv, volume_ml = "Коктейль «Ёрш»", 12.0, 500.0
        else:
            drink_name, abv, volume_ml = text_args[0].capitalize(), 10.0, 300.0

        for part in text_args:
            if part.isdigit():
                volume_ml = float(part)
                break

        res = database.record_chat_drink(
            chat_id=chat.id,
            tg_user_id=user.id,
            user_name=user.full_name or user.first_name,
            username=user.username,
            drink_name=drink_name,
            volume_ml=volume_ml,
            abv=abv
        )

        referee_comments = [
            "Судейская коллегия засчитала подход! Четкое прижатие бокала к губам.",
            "Технично, уверенно, без проливаний! Спортивная форма на высоте.",
            "Прекрасный темп! Главное — не забывать про плотную закуску.",
            "ВАК фиксирует взятие веса! Движение в сторону звания Мастера Спорта."
        ]
        comment = random.choice(referee_comments)

        resp_text = (
            f"🍺 **ПОДХОД ЗАСЧИТАН!**\n\n"
            f"👤 Атлет: **{res['user_name']}**\n"
            f"🥃 Напиток: **{res['drink']}** ({res['volume_ml']} мл, {res['abv']}%)\n"
            f"🧪 Чистый спирт: **+{res['pure_ethanol_g']} г** (Всего: **{res['user_total_ethanol']} г**)\n"
            f"🎖️ Текущий разряд: **{res['user_rank']}**\n"
            f"🏆 Очков в копилку: **{res['user_score']}**\n\n"
            f"💬 _{comment}_"
        )
        await message.answer(resp_text, parse_mode="Markdown")

    @dp.callback_query(F.data.startswith("drink_act:"))
    async def cb_drink_action(callback: types.CallbackQuery):
        await callback.answer("Подход зафиксирован!")
        parts = callback.data.split(":")
        d_type = parts[1]
        volume_ml = float(parts[2])
        abv = float(parts[3])
        
        name_map = {
            "beer": "Светлое пиво",
            "ipa": "Крафтовое IPA",
            "vodka": "Водка",
            "wine": "Красное вино",
            "whiskey": "Виски/Коньяк",
            "ersh": "Коктейль «Ёрш»"
        }
        drink_name = name_map.get(d_type, "Напиток")
        user = callback.from_user
        chat = callback.message.chat

        res = database.record_chat_drink(
            chat_id=chat.id,
            tg_user_id=user.id,
            user_name=user.full_name or user.first_name,
            username=user.username,
            drink_name=drink_name,
            volume_ml=volume_ml,
            abv=abv
        )

        resp_text = (
            f"🍺 **ПОДХОД ЗАСЧИТАН!**\n\n"
            f"👤 Атлет: **{res['user_name']}**\n"
            f"🥃 Напиток: **{res['drink']}** ({res['volume_ml']} мл, {res['abv']}%)\n"
            f"🧪 Чистый спирт: **+{res['pure_ethanol_g']} г** (Всего: **{res['user_total_ethanol']} г**)\n"
            f"🎖️ Текущий разряд: **{res['user_rank']}**\n"
            f"🏆 Балл: **{res['user_score']}** очков"
        )
        await callback.message.answer(resp_text, parse_mode="Markdown")

    # -------------------------------------------------------------
    # ЗАСТОЛЬНАЯ ДУЭЛЬ (PvP)
    # -------------------------------------------------------------
    @dp.message(Command("duel"))
    @dp.callback_query(F.data == "menu_duel")
    async def run_duel(event: types.Message | types.CallbackQuery):
        user = event.from_user
        if isinstance(event, types.CallbackQuery):
            await event.answer()
            msg = event.message
            reply_user = None
        else:
            msg = event
            reply_user = msg.reply_to_message.from_user if (msg.reply_to_message and msg.reply_to_message.from_user and msg.reply_to_message.from_user.id != user.id) else None

        athlete = database.get_athlete(tg_user_id=user.id)
        user_score = athlete['score'] if athlete else 95.0
        user_name = athlete['name'] if athlete else (user.first_name or "Атлет")
        user_rank = athlete['rank_title'] if athlete else "Любитель"

        opponent_data = None
        if reply_user:
            opp_athlete = database.get_athlete(tg_user_id=reply_user.id)
            opp_score = opp_athlete['score'] if opp_athlete else 90.0
            opp_name = opp_athlete['name'] if opp_athlete else (reply_user.first_name or "Соперник")
            opp_rank = opp_athlete['rank_title'] if opp_athlete else "Любитель"
            opponent_data = {"name": opp_name, "score": opp_score, "rank_title": opp_rank}

        wait_msg = await msg.answer("⚔️ **Вызов на дуэль принят! Судьи наполняют бокалы...**")
        await asyncio.sleep(1.2)

        duel_res = database.create_or_play_duel(
            creator_data={"name": user_name, "score": user_score, "rank_title": user_rank},
            opponent_data=opponent_data
        )

        duel_text = [
            f"⚔️ **ЗАСТОЛЬНАЯ ДУЭЛЬ ВФЛ!**",
            f"🔴 **{duel_res['creator']['name']}** ({duel_res['creator']['score']} очков)",
            f"⚡ ПРОТИВ ⚡",
            f"🔵 **{duel_res['opponent']['name']}** ({duel_res['opponent']['score']} очков)\n"
        ]

        for r in duel_res["rounds"]:
            duel_text.append(f"🥊 **{r['title']}**")
            duel_text.append(f"   {r['creator_points']} vs {r['opponent_points']} ➔ Раунд за: **{r['round_winner']}**\n")

        duel_text.append(f"{duel_res['comment']}")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚔️ Сразиться снова!", callback_data="menu_duel")],
            [InlineKeyboardButton(text="« Главное меню", callback_data="menu_main")]
        ])

        await wait_msg.delete()
        await msg.answer("\n".join(duel_text), reply_markup=kb, parse_mode="Markdown")

    # -------------------------------------------------------------
    # ГЕНЕРАТОР ТОСТОВ
    # -------------------------------------------------------------
    @dp.message(Command("toast"))
    @dp.callback_query(F.data == "menu_toast")
    async def show_toast(event: types.Message | types.CallbackQuery):
        if isinstance(event, types.CallbackQuery):
            await event.answer()
            msg = event.message
        else:
            msg = event

        toast = random.choice(TOASTS_COLLECTION)
        text = (
            f"{toast['icon']} **ОФИЦИАЛЬНЫЙ ТОСТ ВФЛ: «{toast['title']}»**\n\n"
            f"«{toast['text']}»\n\n"
            "🥂 _Поднимите бокал за спорт высших застольных достижений!_"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Еще тост!", callback_data="menu_toast")],
            [InlineKeyboardButton(text="« Главное меню", callback_data="menu_main")]
        ])
        await msg.answer(text, reply_markup=kb, parse_mode="Markdown")

    # -------------------------------------------------------------
    # АНТИПОХМЕЛЬНЫЙ SOS
    # -------------------------------------------------------------
    @dp.message(Command("sos"))
    @dp.callback_query(F.data == "menu_sos")
    async def show_sos(event: types.Message | types.CallbackQuery):
        if isinstance(event, types.CallbackQuery):
            await event.answer()
            msg = event.message
        else:
            msg = event

        text_parts = ["🚑 **АНТИПОХМЕЛЬНЫЙ ПРОТОКОЛ СПАСЕНИЯ ВФЛ**\n"]
        for st in HANGOVER_PROTOCOL["stages"]:
            text_parts.append(f"⏰ **{st['time']} — {st['title']}**")
            text_parts.append(f"{st['action']}\n")

        text_parts.append("🛑 **Главные запреты:**")
        for p in HANGOVER_PROTOCOL["prohibitions"]:
            text_parts.append(p)

        text_parts.append("\n📞 **Фейковый звонок для спасения из бара:**")
        text_parts.append(f"_{HANGOVER_PROTOCOL['rescue_call']['script']}_")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Главное меню", callback_data="menu_main")]
        ])
        await msg.answer("\n".join(text_parts), reply_markup=kb, parse_mode="Markdown")

    # -------------------------------------------------------------
    # ТАБЛИЦА РАЗРЯДОВ
    # -------------------------------------------------------------
    @dp.callback_query(F.data == "menu_ranks")
    async def cb_ranks(callback: types.CallbackQuery):
        lines = ["📜 **Единая Застольная Спортивная Классификация (ЕЗСК):**\n"]
        for r in RANKS:
            lines.append(f"{r['badge']} **{r['title']}** ({r['min_score']}+ очков)")
            lines.append(f"_{r['description']}_\n")
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« В главное меню", callback_data="menu_main")]
        ])
        await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode="Markdown")

    # -------------------------------------------------------------
    # КАЛЬКУЛЯТОР НОРМАТИВА
    # -------------------------------------------------------------
    @dp.message(Command("calc"))
    @dp.callback_query(F.data == "menu_calc")
    async def cb_calc_start(event: types.Message | types.CallbackQuery, state: FSMContext):
        await state.set_state(LitrballStates.calc_weight)
        await state.update_data(drinks=[])
        text = (
            "🧮 **Шаг 1 из 4: Весовая категория**\n\n"
            "Введите ваш боевой вес в килограммах (число от 40 до 200).\n"
            "Например: `80`"
        )
        if isinstance(event, types.CallbackQuery):
            if event.message.photo:
                try:
                    await event.message.delete()
                except Exception:
                    pass
                await event.message.answer(text, parse_mode="Markdown")
            else:
                await event.message.edit_text(text, parse_mode="Markdown")
        else:
            await event.answer(text, parse_mode="Markdown")


    @dp.message(LitrballStates.calc_weight)
    async def process_weight(message: types.Message, state: FSMContext):
        try:
            w = float(message.text.strip().replace(",", "."))
            if w < 40 or w > 250:
                await message.answer("Вес должен быть в пределах от 40 до 250 кг. Попробуйте еще раз:")
                return
        except ValueError:
            await message.answer("Пожалуйста, введите число (например, 75):")
            return

        await state.update_data(weight=w)
        await state.set_state(LitrballStates.calc_drinks)
        await show_drinks_menu(message, state)

    async def show_drinks_menu(message: types.Message, state: FSMContext, edit: bool = False):
        data = await state.get_data()
        drinks = data.get("drinks", [])

        drinks_summary = ""
        if drinks:
            drinks_summary = "\n**Выбранный арсенал:**\n"
            for d in drinks:
                drinks_summary += f"• {d['name']} ({d['count']} шт по {d['volume_ml']} мл, {d['abv']}%)\n"
            drinks_summary += "\n"

        text = (
            f"🍺 **Шаг 2 из 4: Заявленные напитки**\n{drinks_summary}"
            "Добавьте выпитое за соревновательную сессию:"
        )

        buttons = [
            [
                InlineKeyboardButton(text="🍺 Пиво (0.5л, 5%)", callback_data="add_beer"),
                InlineKeyboardButton(text="🍷 Вино (0.2л, 12%)", callback_data="add_wine")
            ],
            [
                InlineKeyboardButton(text="🥃 Водка/Коньяк (50мл, 40%)", callback_data="add_shot"),
                InlineKeyboardButton(text="🍾 Водка бутылка (0.5л, 40%)", callback_data="add_bottle")
            ],
            [
                InlineKeyboardButton(text="🍸 Коктейль (0.3л, 15%)", callback_data="add_cocktail"),
                InlineKeyboardButton(text="🍼 Сидр/Лонг (0.5л, 6%)", callback_data="add_cider")
            ]
        ]
        if drinks:
            buttons.append([InlineKeyboardButton(text="✅ Готово, к закуске! »", callback_data="drinks_done")])
        buttons.append([InlineKeyboardButton(text="❌ Сбросить список", callback_data="drinks_reset")])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        if edit:
            await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=kb, parse_mode="Markdown")

    @dp.callback_query(F.data.startswith("add_"))
    async def cb_add_drink(callback: types.CallbackQuery, state: FSMContext):
        d_type = callback.data.replace("add_", "")
        data = await state.get_data()
        drinks = data.get("drinks", [])

        preset = {
            "beer": {"name": "Пиво светлое", "volume_ml": 500, "abv": 5.0},
            "wine": {"name": "Вино сухое", "volume_ml": 200, "abv": 12.0},
            "shot": {"name": "Стопка водки", "volume_ml": 50, "abv": 40.0},
            "bottle": {"name": "Бутылка водки", "volume_ml": 500, "abv": 40.0},
            "cocktail": {"name": "Коктейль", "volume_ml": 300, "abv": 15.0},
            "cider": {"name": "Сидр", "volume_ml": 500, "abv": 6.0}
        }.get(d_type)

        if preset:
            found = False
            for d in drinks:
                if d["name"] == preset["name"]:
                    d["count"] += 1
                    found = True
                    break
            if not found:
                drinks.append({**preset, "count": 1})

        await state.update_data(drinks=drinks)
        await show_drinks_menu(callback.message, state, edit=True)

    @dp.callback_query(F.data == "drinks_reset")
    async def cb_drinks_reset(callback: types.CallbackQuery, state: FSMContext):
        await state.update_data(drinks=[])
        await show_drinks_menu(callback.message, state, edit=True)

    @dp.callback_query(F.data == "drinks_done")
    async def cb_drinks_done(callback: types.CallbackQuery, state: FSMContext):
        await state.set_state(LitrballStates.calc_snack)
        text = (
            "🥓 **Шаг 3 из 4: Закусочная стратегия**\n\n"
            "Качество и плотность закуски критически влияют на судейский балл:"
        )
        buttons = [
            [InlineKeyboardButton(text="🍖 Плотный обед (сало, борщ, мясо)", callback_data="snack_heavy")],
            [InlineKeyboardButton(text="🥪 Бутерброды / Пицца / Шаверма", callback_data="snack_medium")],
            [InlineKeyboardButton(text="🥜 Чипсы, сухарики, оливки", callback_data="snack_light")],
            [InlineKeyboardButton(text="🕳️ Натощак / Чистый спорт", callback_data="snack_empty")]
        ]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

    @dp.callback_query(F.data.startswith("snack_"))
    async def cb_snack_chosen(callback: types.CallbackQuery, state: FSMContext):
        snack = callback.data.replace("snack_", "")
        await state.update_data(snack=snack)
        await state.set_state(LitrballStates.calc_hours)

        text = (
            "⏱️ **Шаг 4 из 4: Длительность соревнований**\n\n"
            "Сколько часов длилось застолье?"
        )
        buttons = [
            [InlineKeyboardButton(text="⚡ Залповый спринт (до 1 часа)", callback_data="hours_1")],
            [InlineKeyboardButton(text="🍻 Классический вечер (3-4 часа)", callback_data="hours_4")],
            [InlineKeyboardButton(text="🏃 Ночной марафон (6-8 часов)", callback_data="hours_7")],
            [InlineKeyboardButton(text="⛺ Турнир на сутки (12+ часов)", callback_data="hours_14")]
        ]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

    @dp.callback_query(F.data.startswith("hours_"))
    async def cb_hours_chosen(callback: types.CallbackQuery, state: FSMContext):
        hrs = float(callback.data.replace("hours_", ""))
        await state.update_data(hours=hrs)

        text = (
            "🚨 **ВНИМАНИЕ! СУДЕЙСКИЙ КОНТРОЛЬ**\n\n"
            "Ваши результаты зафиксированы в протоколе.\n"
            "Перед присвоением разряда ВАК требует пройти **Детектор Пиздежа**:\n"
            "1. Экспресс-тест на алкогольную математику\n"
            "2. Тест на моторику пальцев\n"
            "3. Фото-фиксацию тары\n\n"
            "Вы готовы подтвердить результат?"
        )
        buttons = [
            [InlineKeyboardButton(text="🎯 Пройти проверку на детекторе »", callback_data="start_detector")],
            [InlineKeyboardButton(text="🙈 Сдать без проверки (Штраф к разряду)", callback_data="skip_detector")]
        ]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

    # -------------------------------------------------------------
    # ДЕТЕКТОР ПИЗДЕЖА
    # -------------------------------------------------------------
    @dp.callback_query(F.data == "start_detector")
    async def cb_detector_start(callback: types.CallbackQuery, state: FSMContext):
        await state.set_state(LitrballStates.detector_math)
        n1 = random.randint(12, 48)
        n2 = random.randint(15, 59)
        ans = n1 + n2
        await state.update_data(math_answer=ans, math_start=datetime.now().timestamp())

        wrong1 = ans + random.choice([-10, -2, 2, 10, -1])
        wrong2 = ans + random.choice([-5, 5, 8, -8])
        options = [ans, wrong1, wrong2]
        random.shuffle(options)

        text = (
            "🎯 **ДЕТЕКТОР: ТЕСТ 1 ИЗ 2 (АЛКО-МАТЕМАТИКА)**\n\n"
            "Ситуация: Вы покупаете шаурму и пиво в 03:00 ночи.\n"
            f"Сколько будет: **{n1} + {n2}**?\n\n"
            "У вас 15 секунд на выбор ответа:"
        )
        buttons = [[InlineKeyboardButton(text=str(opt), callback_data=f"math_ans_{opt}")] for opt in options]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

    @dp.callback_query(F.data.startswith("math_ans_"))
    async def cb_detector_math(callback: types.CallbackQuery, state: FSMContext):
        val = int(callback.data.replace("math_ans_", ""))
        data = await state.get_data()
        correct = data.get("math_answer")
        start_t = data.get("math_start", datetime.now().timestamp())
        elapsed = datetime.now().timestamp() - start_t

        if val != correct:
            await callback.answer("❌ Ошибка в расчете сдачи! Детектор насторожился.", show_alert=True)
            penalties = data.get("penalties", {})
            penalties["lost_items"] = True
            await state.update_data(penalties=penalties)
        else:
            await callback.answer(f"✅ Точно! Расчет сдачи верен за {elapsed:.1f} сек.", show_alert=False)

        await state.set_state(LitrballStates.detector_reaction)
        text = (
            "🎯 **ДЕТЕКТОР: ТЕСТ 2 ИЗ 2 (ТРЕМОР И МОТОРИКА)**\n\n"
            "Проверка координации движений: нажмите ровно на **«ПОЛНЫЙ СТАКАН»** "
            "и не промахнитесь мимо экрана!"
        )
        buttons = [
            [
                InlineKeyboardButton(text="💨 Пусто", callback_data="tremor_miss"),
                InlineKeyboardButton(text="🍺 ПОЛНЫЙ СТАКАН!", callback_data="tremor_hit"),
                InlineKeyboardButton(text="💨 Мимо", callback_data="tremor_miss")
            ]
        ]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

    @dp.callback_query(F.data.startswith("tremor_"))
    async def cb_detector_tremor(callback: types.CallbackQuery, state: FSMContext):
        hit = callback.data == "tremor_hit"
        if not hit:
            await callback.answer("💥 Промах! Моторика пальцев нарушена.", show_alert=True)
        else:
            await callback.answer("🎯 Прямое попадание! Рука атлета тверда как скала.", show_alert=False)

        await state.set_state(LitrballStates.detector_photo)
        text = (
            "📸 **ФОТО-ФИКСАЦИЯ ТАРЫ (НЕЙРОСЕТЬ ВАК)**\n\n"
            "Пришлите фото пустой посуды, бокала или чека из заведения "
            "для завершения верификации.\n\n"
            "_(Или нажмите кнопку ниже, если вся тара уже сдана в пункт приема)_"
        )
        buttons = [
            [InlineKeyboardButton(text="⏩ Тара утилизирована (Завершить)", callback_data="photo_skip")]
        ]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

    @dp.message(LitrballStates.detector_photo, F.photo)
    async def process_detector_photo(message: types.Message, state: FSMContext):
        await message.answer("🔍 Нейросеть ВАК анализирует тару... Распознано: 100% честный спорт!")
        await state.update_data(detector_passed=True)
        await finish_calculation(message, state)

    @dp.callback_query(F.data == "photo_skip")
    @dp.callback_query(F.data == "skip_detector")
    async def cb_finish_without_photo(callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        await finish_calculation(callback.message, state, user=callback.from_user)

    # -------------------------------------------------------------
    # ФИНАЛ: РАСЧЕТ И ВЫДАЧА УДОСТОВЕРЕНИЯ
    # -------------------------------------------------------------
    async def finish_calculation(message: types.Message, state: FSMContext, user: types.User = None):
        data = await state.get_data()
        user = user or message.from_user or message.chat
        user_name = user.full_name or "Атлет"

        wait_msg = await message.answer("⏳ **Заседание Высшей Аттестационной Комиссии... Печатаем корочку...**")

        calc_payload = {
            "name": user_name,
            "weight": data.get("weight", 80),
            "drinks": data.get("drinks", []),
            "hours": data.get("hours", 3),
            "snack": data.get("snack", "medium"),
            "penalties": data.get("penalties", {})
        }
        res = calculate_score(calc_payload)

        # Сохранение в базу данных SQLite
        database.save_or_update_athlete({
            "tg_user_id": user.id,
            "name": user_name,
            "username": getattr(user, 'username', ''),
            "weight": data.get("weight", 80),
            "gender": data.get("gender", "m"),
            "rank": res["rank"],
            "score": res["score"],
            "pure_ethanol_g": res["pure_ethanol_g"],
            "est_bac_promille": res["est_bac_promille"],
            "disciplines": res["disciplines"],
            "order_num": res["order_num"],
            "verified": data.get("detector_passed", False),
            "snack": data.get("snack", "medium"),
            "penalties": data.get("penalties", {})
        })

        # Получаем фото профиля спортсмена
        avatar_bytes = None
        try:
            photos = await bot.get_user_profile_photos(user.id, limit=1)
            if photos and photos.photos:
                photo_file = await bot.get_file(photos.photos[0][-1].file_id)
                photo_stream = await bot.download_file(photo_file.file_path)
                avatar_bytes = photo_stream.read()
        except Exception as e:
            logger.warning(f"Could not fetch avatar: {e}")

        # Генерируем картинку корочки
        cert_png = generate_certificate_image(
            name=user_name,
            rank_title=res["rank"]["title"],
            weight=data.get("weight", 80),
            discipline=res["disciplines"],
            order_num=res["order_num"],
            pure_ethanol_g=res["pure_ethanol_g"],
            est_bac=res["est_bac_promille"],
            user_avatar_bytes=avatar_bytes
        )

        caption = (
            f"🎖️ **ОФИЦИАЛЬНЫЙ ПРИКАЗ ВАК ФЕДЕРАЦИИ ЛИТРБОЛА**\n\n"
            f"Атлету: **{user_name}**\n"
            f"Присвоено звание: **{res['rank']['title']}** {res['rank']['badge']}\n"
            f"Итоговый балл: **{res['score']}** очков\n"
            f"Чистый спирт: **{res['pure_ethanol_g']} г** (промилле: ~{res['est_bac_promille']} ‰)\n"
            f"Время вытрезвления: **{res['sober_hours']} ч.**\n\n"
            f"_{res['rank']['description']}_\n\n"
            f"**Утренний протокол:** {res['rank']['morning_verdict']}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🪪 Мой Спортивный Паспорт", callback_data="menu_passport")],
            [InlineKeyboardButton(text="⚔️ Вызвать на дуэль", callback_data="menu_duel")],
            [InlineKeyboardButton(text="« Главное меню", callback_data="menu_main")]
        ])

        await wait_msg.delete()
        await message.answer_photo(
            photo=BufferedInputFile(cert_png, filename=f"Удостоверение_{user_name}.png"),
            caption=caption,
            reply_markup=kb,
            parse_mode="Markdown"
        )
        await state.clear()

    # -------------------------------------------------------------
    # ТЕОРЕТИЧЕСКИЙ ЭКЗАМЕН ВАК
    # -------------------------------------------------------------
    @dp.callback_query(F.data == "menu_quiz")
    async def cb_start_quiz(callback: types.CallbackQuery, state: FSMContext):
        await state.set_state(LitrballStates.quiz_running)
        await state.update_data(quiz_idx=0, quiz_score=0)
        await show_quiz_question(callback, state)

    async def show_quiz_question(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        idx = data.get("quiz_idx", 0)
        total = len(QUIZ_QUESTIONS)

        if idx >= total:
            score = data.get("quiz_score", 0)
            if score >= 130:
                rank_title = "Магистр Застольных Наук (МЗН)"
                badge = "⭐"
            elif score >= 85:
                rank_title = "КМС по теоретическому литрболу"
                badge = "🥇"
            else:
                rank_title = "3-й Взрослый разряд (Теоретик)"
                badge = "🥉"

            text = (
                f"🎓 **ЭКЗАМЕН ВАК ЗАВЕРШЕН!**\n\n"
                f"Ваш результат: **{score} баллов**.\n"
                f"Присвоено звание: **{rank_title}** {badge}\n\n"
                "Теоретическая база подтверждена Аттестационной Комиссией."
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="« В главное меню", callback_data="menu_main")]
            ])
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
            await state.clear()
            return

        q = QUIZ_QUESTIONS[idx]
        text = f"🎓 **Вопрос {idx + 1} из {total}:**\n\n{q['question']}"

        letters = ["А", "Б", "В", "Г"]
        buttons = []
        for i, opt in enumerate(q["options"]):
            btn_text = f"{letters[i]}) {opt['text'][:35]}..."
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"q_ans_{opt['score']}")])

        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

    @dp.callback_query(F.data.startswith("q_ans_"))
    async def cb_quiz_answer(callback: types.CallbackQuery, state: FSMContext):
        score_val = int(callback.data.replace("q_ans_", ""))
        data = await state.get_data()
        idx = data.get("quiz_idx", 0) + 1
        total_score = data.get("quiz_score", 0) + score_val

        await state.update_data(quiz_idx=idx, quiz_score=total_score)
        await show_quiz_question(callback, state)

    # -------------------------------------------------------------
    # ПРЯМОЙ ВЫЗОВ ДЕТЕКТОРА ПИЗДЕЖА
    # -------------------------------------------------------------
    @dp.callback_query(F.data == "menu_detector")
    async def cb_standalone_detector(callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        text = (
            "🎯 **ДЕТЕКТОР ПИЗДЕЖА (ПОЛЕВОЙ ДОПИНГ-КОНТРОЛЬ)**\n\n"
            "Эта система проверяет:\n"
            "1. Алкогольную кассовую математику (сдачу в ночном ларьке);\n"
            "2. Моторный тремор рук (тест «Поймай огурец»);\n"
            "3. Фото-фиксацию тары и чека нейросетью ВАК.\n\n"
            "Чтобы пройти проверку и получить официальный паспорт с печатью, нажмите **«Сдать норматив»**!"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧮 Начать сдачу норматива »", callback_data="menu_calc")],
            [InlineKeyboardButton(text="« Назад", callback_data="menu_main")]
        ])
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

async def main():
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не задан!")
        sys.exit(1)

    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    await register_handlers(dp, bot)

    # Регистрация меню команд бота в Telegram
    try:
        commands = [
            types.BotCommand(command="start", description="🏆 Главное меню Федерации"),
            types.BotCommand(command="drink", description="🍺 Зафиксировать напиток"),
            types.BotCommand(command="top", description="🥇 Рейтинг чата / Зал Славы"),
            types.BotCommand(command="stats", description="📊 Статистика застолья"),
            types.BotCommand(command="duel", description="⚔️ Застольная Дуэль (PvP)"),
            types.BotCommand(command="passport", description="🪪 Спортивный Паспорт"),
            types.BotCommand(command="calc", description="🧮 Сдать норматив (Калькулятор)"),
            types.BotCommand(command="toast", description="🥂 Генератор Тостов"),
            types.BotCommand(command="sos", description="🚑 Антипохмельный SOS")
        ]
        await bot.set_my_commands(commands)

        if WEBAPP_URL:
            await bot.set_chat_menu_button(
                menu_button=types.MenuButtonWebApp(
                    text="🏅 Литрбол App",
                    web_app=types.WebAppInfo(url=WEBAPP_URL)
                )
            )
            print(f"📱 Меню Telegram Mini App настроено: {WEBAPP_URL}")
    except Exception as e:
        logger.warning(f"Could not set bot commands or menu button: {e}")

    print(f"🚀 Бот Всероссийской Федерации Литрбола успешно запущен!")
    print(f"🤖 Ожидаем атлетов в Telegram...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nБот остановлен.")
