"""
Всероссийская Федерация Литрбола (ВФЛ) — Модуль Базы Данных (SQLite)
Управляет профилями атлетов, рекордами, Залом Славы и верификацией.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.environ.get("LITRBALL_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "litrball.db"))

ACHIEVEMENTS_LIST = [
    {"id": "first_sip", "title": "Первый старт", "desc": "Рассчитал свой первый норматив ВФЛ", "icon": "🍼"},
    {"id": "detector_passed", "title": "Честный спортсмен", "desc": "Успешно прошел Детектор Пиздежа", "icon": "🎯"},
    {"id": "math_pro", "title": "Алко-Калькулятор", "desc": "Решил пример без единой ошибки быстрее 5 сек", "icon": "🧮"},
    {"id": "sober_driver", "title": "Трезвый судья", "desc": "Рассчитал время трезвости до 0.00 промилле", "icon": "🚗"},
    {"id": "no_ex_call", "title": "Стальная воля", "desc": "Не звонил бывшим ни разу за карьеру", "icon": "📵"},
    {"id": "snack_master", "title": "Мастер закуски", "desc": "Сдал норматив с правильной плотной закуской", "icon": "🥓"},
    {"id": "biathlon_champ", "title": "Ёрш-Биатлонист", "desc": "Освоил двоеборье: пиво + крепкое", "icon": "🍺"},
    {"id": "kms_rank", "title": "Элита застолья", "desc": "Достиг звания КМС или выше", "icon": "🥇"},
    {"id": "ms_legend", "title": "Мастер Спорта", "desc": "Получил официальное звание МС по Литрболу", "icon": "⭐"},
    {"id": "zms_god", "title": "Живая Легенда (ЗМС)", "desc": "Высшая ступень Единой Спортивной Классификации", "icon": "👑"},
    {"id": "duel_winner", "title": "Гладиатор стола", "desc": "Одержал победу в застольной дуэли", "icon": "⚔️"},
    {"id": "morning_hero", "title": "Утренний огурец", "desc": "Изучил Антипохмельный гид и остался в строю", "icon": "🥒"}
]

def get_connection():
    db_file = os.environ.get("LITRBALL_DB_PATH", DB_PATH)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Таблица спортсменов
    c.execute('''
        CREATE TABLE IF NOT EXISTS athletes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_user_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            username TEXT,
            weight REAL DEFAULT 75.0,
            gender TEXT DEFAULT 'm',
            rank_id TEXT,
            rank_title TEXT,
            score REAL DEFAULT 0,
            pure_ethanol_g REAL DEFAULT 0,
            est_bac REAL DEFAULT 0,
            discipline TEXT,
            order_num TEXT,
            verified INTEGER DEFAULT 0,
            achievements TEXT DEFAULT '[]',
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Таблица истории сдачи нормативов
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            athlete_id INTEGER,
            tg_user_id INTEGER,
            name TEXT,
            score REAL,
            rank_title TEXT,
            pure_ethanol_g REAL,
            est_bac REAL,
            verified INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (athlete_id) REFERENCES athletes(id)
        )
    ''')
    
    # Таблица дуэлей
    c.execute('''
        CREATE TABLE IF NOT EXISTS duels (
            id TEXT PRIMARY KEY,
            creator_name TEXT,
            creator_score REAL,
            creator_rank TEXT,
            opponent_name TEXT,
            opponent_score REAL,
            opponent_rank TEXT,
            winner TEXT,
            created_at TEXT
        )
    ''')

    # Таблица чатов (групп и супергрупп)
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            chat_type TEXT DEFAULT 'group',
            member_count INTEGER DEFAULT 0,
            total_ethanol_g REAL DEFAULT 0,
            drinks_count INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # Таблица участников чатов и их статистики в конкретном чате
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            tg_user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            username TEXT,
            score REAL DEFAULT 0,
            rank_title TEXT DEFAULT '3-й Юношеский разряд',
            pure_ethanol_g REAL DEFAULT 0,
            drinks_count INTEGER DEFAULT 0,
            last_drink TEXT,
            updated_at TEXT,
            UNIQUE(chat_id, tg_user_id)
        )
    ''')

    # Таблица журнала возлияний в чатах
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_drinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            tg_user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            drink_name TEXT NOT NULL,
            volume_ml REAL NOT NULL,
            abv REAL NOT NULL,
            pure_ethanol_g REAL NOT NULL,
            created_at TEXT
        )
    ''')

    # Таблица комнат застольных баттлов (вечеринок)
    c.execute('''
        CREATE TABLE IF NOT EXISTS party_rooms (
            room_id TEXT PRIMARY KEY,
            chat_id INTEGER,
            title TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            creator_name TEXT NOT NULL,
            status TEXT DEFAULT 'waiting',
            duration_min INTEGER DEFAULT 30,
            started_at TEXT,
            ends_at TEXT,
            created_at TEXT,
            winner_name TEXT,
            winner_score REAL,
            summary_json TEXT DEFAULT '{}'
        )
    ''')

    # Таблица участников комнат
    c.execute('''
        CREATE TABLE IF NOT EXISTS party_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            tg_user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            username TEXT,
            avatar_url TEXT,
            is_ready INTEGER DEFAULT 0,
            score REAL DEFAULT 0,
            pure_ethanol_g REAL DEFAULT 0,
            drinks_count INTEGER DEFAULT 0,
            photos_count INTEGER DEFAULT 0,
            confirmed_alive INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ready',
            joined_at TEXT,
            updated_at TEXT,
            UNIQUE(room_id, tg_user_id)
        )
    ''')

    # Таблица выпитых напитков внутри комнат
    c.execute('''
        CREATE TABLE IF NOT EXISTS party_drinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            tg_user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            drink_name TEXT NOT NULL,
            volume_ml REAL NOT NULL,
            abv REAL NOT NULL,
            pure_ethanol_g REAL NOT NULL,
            created_at TEXT
        )
    ''')

    # Таблица фотофиксаций лиц в комнатах
    c.execute('''
        CREATE TABLE IF NOT EXISTS party_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            tg_user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            photo_url TEXT NOT NULL,
            stage TEXT DEFAULT 'active',
            funny_caption TEXT,
            created_at TEXT
        )
    ''')

    # Очистка фейковых записей (только реальные пользователи с tg_user_id)
    c.execute('DELETE FROM athletes WHERE tg_user_id IS NULL')

    conn.commit()
    conn.close()

def save_or_update_athlete(data: dict) -> dict:
    """Сохраняет или обновляет профиль атлета по tg_user_id или имени"""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    tg_id = data.get('tg_user_id')
    name = data.get('name', 'Анонимный Атлет')
    username = data.get('username', '')
    weight = float(data.get('weight', 75))
    gender = data.get('gender', 'm')
    rank = data.get('rank', {})
    rank_id = rank.get('id', 'junior_3')
    rank_title = rank.get('title', '3-й Юношеский разряд')
    score = float(data.get('score', 0))
    pure_ethanol_g = float(data.get('pure_ethanol_g', 0))
    est_bac = float(data.get('est_bac_promille', 0))
    discipline = data.get('discipline', data.get('disciplines', 'Застольное многоборье'))
    order_num = data.get('order_num', f"№ {os.urandom(4).hex().upper()}/ФЛР-{datetime.now().year}")
    verified = 1 if data.get('verified') else 0

    # Определение новых ачивок
    achievements = set(data.get('achievements', []))
    achievements.add("first_sip")
    if verified:
        achievements.add("detector_passed")
    if rank_id in ['kms', 'ms', 'msmk', 'zms']:
        achievements.add("kms_rank")
    if rank_id in ['ms', 'msmk', 'zms']:
        achievements.add("ms_legend")
    if rank_id == 'zms':
        achievements.add("zms_god")
    if "ёрш" in discipline.lower() or "биатлон" in discipline.lower():
        achievements.add("biathlon_champ")
    if data.get('snack') == 'heavy':
        achievements.add("snack_master")
    if not data.get('penalties', {}).get('called_ex'):
        achievements.add("no_ex_call")

    athlete_id = None
    if tg_id:
        c.execute('SELECT id, score, achievements FROM athletes WHERE tg_user_id = ?', (tg_id,))
        existing = c.fetchone()
        if existing:
            athlete_id = existing['id']
            # Объединяем ачивки
            prev_ach = set(json.loads(existing['achievements'] or '[]'))
            achievements = achievements.union(prev_ach)
            # Если новый счет выше, обновляем
            new_score = max(score, float(existing['score']))
            c.execute('''
                UPDATE athletes SET
                    name = ?, username = ?, weight = ?, gender = ?,
                    rank_id = ?, rank_title = ?, score = ?, pure_ethanol_g = ?,
                    est_bac = ?, discipline = ?, order_num = ?, verified = ?,
                    achievements = ?, updated_at = ?
                WHERE id = ?
            ''', (name, username, weight, gender, rank_id, rank_title, new_score, pure_ethanol_g, est_bac, discipline, order_num, verified, json.dumps(list(achievements)), now, athlete_id))
    
    if not athlete_id:
        c.execute('''
            INSERT INTO athletes (tg_user_id, name, username, weight, gender, rank_id, rank_title, score, pure_ethanol_g, est_bac, discipline, order_num, verified, achievements, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (tg_id, name, username, weight, gender, rank_id, rank_title, score, pure_ethanol_g, est_bac, discipline, order_num, verified, json.dumps(list(achievements)), now, now))
        athlete_id = c.lastrowid

    # Запись в историю попыток
    c.execute('''
        INSERT INTO submissions (athlete_id, tg_user_id, name, score, rank_title, pure_ethanol_g, est_bac, verified, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (athlete_id, tg_id, name, score, rank_title, pure_ethanol_g, est_bac, verified, now))

    conn.commit()
    conn.close()

    return {
        "id": athlete_id,
        "name": name,
        "rank_title": rank_title,
        "score": score,
        "order_num": order_num,
        "achievements": list(achievements),
        "verified": bool(verified)
    }

def get_athlete(tg_user_id: int = None, athlete_id: int = None) -> dict:
    conn = get_connection()
    c = conn.cursor()
    if tg_user_id:
        c.execute('SELECT * FROM athletes WHERE tg_user_id = ?', (tg_user_id,))
    elif athlete_id:
        c.execute('SELECT * FROM athletes WHERE id = ?', (athlete_id,))
    else:
        conn.close()
        return None
    
    row = c.fetchone()
    conn.close()
    if row:
        res = dict(row)
        res['achievements'] = json.loads(res.get('achievements') or '[]')
        return res
    return None

def get_leaderboard(limit: int = 20) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, tg_user_id, name, username, rank_title, rank_id, score, discipline, verified, achievements, updated_at
        FROM athletes
        WHERE tg_user_id IS NOT NULL
        ORDER BY score DESC
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        item = dict(r)
        item['achievements'] = json.loads(item.get('achievements') or '[]')
        result.append(item)
    return result

def track_or_update_chat(chat_id: int, title: str, chat_type: str = "group", member_count: int = 0) -> dict:
    """Регистрирует или обновляет чат при добавлении бота или активности"""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id,))
    existing = c.fetchone()
    if existing:
        c.execute('''
            UPDATE chats SET
                title = ?, chat_type = ?, member_count = ?, updated_at = ?
            WHERE chat_id = ?
        ''', (title, chat_type, member_count or existing['member_count'], now, chat_id))
    else:
        c.execute('''
            INSERT INTO chats (chat_id, title, chat_type, member_count, total_ethanol_g, drinks_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, 0, ?, ?)
        ''', (chat_id, title, chat_type, member_count, now, now))
    conn.commit()
    conn.close()
    return get_chat(chat_id)

def get_chat(chat_id: int) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def record_chat_drink(chat_id: int, tg_user_id: int, user_name: str, username: str = None, 
                      drink_name: str = "Пиво", volume_ml: float = 500.0, abv: float = 5.0) -> dict:
    """Фиксирует выпитый напиток участником чата, обновляет баланс спирта и разряд"""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    pure_ethanol = round(volume_ml * (abv / 100.0) * 0.789, 1)

    # 1. Запись в журнал
    c.execute('''
        INSERT INTO chat_drinks (chat_id, tg_user_id, user_name, drink_name, volume_ml, abv, pure_ethanol_g, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (chat_id, tg_user_id, user_name, drink_name, volume_ml, abv, pure_ethanol, now))

    # 2. Обновление общих показателей чата
    c.execute('SELECT chat_id FROM chats WHERE chat_id = ?', (chat_id,))
    if not c.fetchone():
        c.execute('''
            INSERT INTO chats (chat_id, title, chat_type, member_count, total_ethanol_g, drinks_count, created_at, updated_at)
            VALUES (?, ?, 'group', 1, ?, 1, ?, ?)
        ''', (chat_id, "Застольный чат", pure_ethanol, now, now))
    else:
        c.execute('''
            UPDATE chats SET
                total_ethanol_g = total_ethanol_g + ?,
                drinks_count = drinks_count + 1,
                updated_at = ?
            WHERE chat_id = ?
        ''', (pure_ethanol, now, chat_id))

    def calc_chat_rank(total_eth: float) -> str:
        if total_eth >= 250: return "Заслуженный Мастер Спорта (ЗМС)"
        if total_eth >= 180: return "Мастер Спорта по Литрболу (МС)"
        if total_eth >= 120: return "КМС (Кандидат в Мастера Спорта)"
        if total_eth >= 75:  return "1-й Взрослый разряд"
        if total_eth >= 45:  return "2-й Взрослый разряд"
        if total_eth >= 20:  return "3-й Взрослый разряд"
        if total_eth >= 10:  return "1-й Юношеский разряд"
        return "2-й Юношеский разряд"

    # 3. Обновление участника в данном чате
    c.execute('SELECT * FROM chat_members WHERE chat_id = ? AND tg_user_id = ?', (chat_id, tg_user_id))
    member = c.fetchone()
    
    if member:
        new_pure = round(member['pure_ethanol_g'] + pure_ethanol, 1)
        new_drinks = member['drinks_count'] + 1
        new_score = round(member['score'] + (pure_ethanol * 1.2), 1)
        new_rank = calc_chat_rank(new_pure)
        c.execute('''
            UPDATE chat_members SET
                user_name = ?, username = ?, score = ?, rank_title = ?,
                pure_ethanol_g = ?, drinks_count = ?, last_drink = ?, updated_at = ?
            WHERE chat_id = ? AND tg_user_id = ?
        ''', (user_name, username, new_score, new_rank, new_pure, new_drinks, f"{drink_name} ({volume_ml} мл)", now, chat_id, tg_user_id))
    else:
        new_pure = pure_ethanol
        new_drinks = 1
        new_score = round(pure_ethanol * 1.2, 1)
        new_rank = calc_chat_rank(new_pure)
        c.execute('''
            INSERT INTO chat_members (chat_id, tg_user_id, user_name, username, score, rank_title, pure_ethanol_g, drinks_count, last_drink, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, tg_user_id, user_name, username, new_score, new_rank, new_pure, new_drinks, f"{drink_name} ({volume_ml} мл)", now))

    # 4. Синхронизируем пользователя в глобальной таблице athletes
    c.execute('SELECT * FROM athletes WHERE tg_user_id = ?', (tg_user_id,))
    global_user = c.fetchone()
    if global_user:
        g_new_score = max(global_user['score'], new_score)
        c.execute('''
            UPDATE athletes SET
                name = ?, username = ?, score = ?, pure_ethanol_g = pure_ethanol_g + ?, updated_at = ?
            WHERE tg_user_id = ?
        ''', (user_name, username, g_new_score, pure_ethanol, now, tg_user_id))
    else:
        c.execute('''
            INSERT INTO athletes (tg_user_id, name, username, score, pure_ethanol_g, rank_title, discipline, order_num, verified, achievements, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, '["first_sip"]', ?, ?)
        ''', (tg_user_id, user_name, username, new_score, pure_ethanol, new_rank, "Застолье в чате", f"№ ЧАТ-{tg_user_id % 10000}", now, now))

    conn.commit()
    conn.close()

    return {
        "user_name": user_name,
        "drink": drink_name,
        "volume_ml": volume_ml,
        "abv": abv,
        "pure_ethanol_g": pure_ethanol,
        "user_total_ethanol": new_pure,
        "user_drinks_count": new_drinks,
        "user_rank": new_rank,
        "user_score": new_score
    }

def get_chat_leaderboard(chat_id: int, limit: int = 20) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, chat_id, tg_user_id, user_name, username, score, rank_title, pure_ethanol_g, drinks_count, last_drink, updated_at
        FROM chat_members
        WHERE chat_id = ?
        ORDER BY score DESC, pure_ethanol_g DESC
        LIMIT ?
    ''', (chat_id, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_chat_stats(chat_id: int) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM chats WHERE chat_id = ?', (chat_id,))
    chat = c.fetchone()
    if not chat:
        c.execute('SELECT COUNT(*) as cnt, SUM(pure_ethanol_g) as eth, SUM(drinks_count) as drk FROM chat_members WHERE chat_id = ?', (chat_id,))
        agg = c.fetchone()
        if agg and agg['cnt'] > 0:
            chat_dict = {
                "chat_id": chat_id,
                "title": "Застольный чат",
                "chat_type": "group",
                "member_count": agg['cnt'],
                "total_ethanol_g": round(agg['eth'] or 0, 1),
                "drinks_count": agg['drk'] or 0,
            }
        else:
            conn.close()
            return None
    else:
        chat_dict = dict(chat)

    c.execute('''
        SELECT user_name, score, rank_title, pure_ethanol_g, drinks_count
        FROM chat_members
        WHERE chat_id = ?
        ORDER BY score DESC
        LIMIT 1
    ''', (chat_id,))
    top_row = c.fetchone()
    chat_dict['top_athlete'] = dict(top_row) if top_row else None

    c.execute('SELECT COUNT(*) as active_count FROM chat_members WHERE chat_id = ?', (chat_id,))
    chat_dict['active_athletes_count'] = c.fetchone()['active_count']

    conn.close()
    return chat_dict

def create_or_play_duel(creator_data: dict, opponent_data: dict = None) -> dict:
    """Создает или разыгрывает дуэль между двумя атлетами"""
    import random
    
    c_score = float(creator_data.get('score', 100))
    c_name = creator_data.get('name', 'Атлет 1')
    c_rank = creator_data.get('rank_title', 'Любитель')
    
    if opponent_data:
        o_score = float(opponent_data.get('score', 100))
        o_name = opponent_data.get('name', 'Атлет 2')
        o_rank = opponent_data.get('rank_title', 'Любитель')
    else:
        # Симуляция случайного бота-соперника
        opponents_bot = [
            {"name": "Михалыч (Гаражная Лига)", "score": random.randint(80, 160), "rank": "1-й Взрослый разряд"},
            {"name": "Степан «Без Закуски»", "score": random.randint(120, 210), "rank": "КМС"},
            {"name": "Артём «Тройной Сидр»", "score": random.randint(40, 95), "rank": "3-й Взрослый разряд"},
            {"name": "Магистр Геннадий (ЗМС)", "score": random.randint(220, 310), "rank": "Мастер Спорта"}
        ]
        bot_choice = random.choice(opponents_bot)
        o_name = bot_choice['name']
        o_score = bot_choice['score']
        o_rank = bot_choice['rank']

    # Раундовый бой (3 раунда)
    rounds = []
    c_round_wins = 0
    o_round_wins = 0
    
    round_descriptions = [
        ("Раунд 1: Разминочный пенный слалом", "Оценка темпа и чистоты бокала"),
        ("Раунд 2: Основное блюдо (двоеборье с тостами)", "Проверка связности речи и глубины мысли"),
        ("Раунд 3: Финальный суперспринт", "Стрессоустойчивость перед закрытием заведения")
    ]
    
    for r_title, r_desc in round_descriptions:
        c_roll = c_score * random.uniform(0.85, 1.15)
        o_roll = o_score * random.uniform(0.85, 1.15)
        if c_roll >= o_roll:
            winner_round = c_name
            c_round_wins += 1
        else:
            winner_round = o_name
            o_round_wins += 1
        rounds.append({
            "title": r_title,
            "desc": r_desc,
            "creator_points": round(c_roll, 1),
            "opponent_points": round(o_roll, 1),
            "round_winner": winner_round
        })
    
    if c_round_wins >= o_round_wins:
        final_winner = c_name
        winner_comment = f"🏆 Победил {c_name} со счетом {c_round_wins}:{o_round_wins}! Зал аплодирует стоя!"
    else:
        final_winner = o_name
        winner_comment = f"🏆 Победил {o_name} со счетом {o_round_wins}:{c_round_wins}! Реванш неизбежен!"

    duel_id = os.urandom(6).hex()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO duels (id, creator_name, creator_score, creator_rank, opponent_name, opponent_score, opponent_rank, winner, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (duel_id, c_name, c_score, c_rank, o_name, o_score, o_rank, final_winner, now))
    conn.commit()
    conn.close()

    return {
        "duel_id": duel_id,
        "creator": {"name": c_name, "score": c_score, "rank": c_rank},
        "opponent": {"name": o_name, "score": o_score, "rank": o_rank},
        "rounds": rounds,
        "winner": final_winner,
        "score_str": f"{c_round_wins}:{o_round_wins}",
        "comment": winner_comment
    }

# =============================================================
# СИСТЕМА КОМНАТ ЗАСТОЛЬНОГО БАТТЛА (ВЕЧЕРИНКИ / ЗАРУБЫ)
# =============================================================

import random
import string
import base64
from datetime import timedelta

FUNNY_PHOTO_CAPTIONS = [
    "🔥 Боевой румянец чемпиона! Концентрация на бокале 100%.",
    "😎 Автопилот включен, полёт проходит в штатном режиме.",
    "🥂 Взгляд человека, готового поднять тост за квантовую физику.",
    "⚡ ВАК фиксирует идеальную координацию и блеск в глазах!",
    "🫡 Стойкость титана: ни одного лишнего движения.",
    "🎭 Судейская коллегия единогласно ставит 10 баллов за артистизм!",
    "🎯 Фокус слегка уплыл, но дух бойца несокрушим!",
    "🚀 Готовность к следующему раунду: максимальная.",
    "🍺 Лицо истинного мастера спорта застольного многоборья."
]

def save_party_photo_file(room_id: str, user_id: int, data_url_or_b64: str) -> str:
    """Декодирует base64 фото и сохраняет файл в static/uploads/rooms/"""
    try:
        if "," in data_url_or_b64:
            _, encoded = data_url_or_b64.split(",", 1)
        else:
            encoded = data_url_or_b64
        
        img_bytes = base64.b64decode(encoded)
        filename = f"room_{room_id}_{user_id}_{int(datetime.now().timestamp())}_{random.randint(100,999)}.jpg"
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads", "rooms")
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        return f"/uploads/rooms/{filename}"
    except Exception as e:
        print(f"Error saving party photo: {e}")
        return None

def generate_room_code() -> str:
    letters = "".join(random.choices(string.ascii_uppercase, k=3))
    digits = "".join(random.choices(string.digits, k=3))
    return f"{letters}{digits}"

def create_party_room(creator_id: int, creator_name: str, title: str = "Застольная Заруба", 
                      chat_id: int = None, duration_min: int = 30) -> dict:
    conn = get_connection()
    c = conn.cursor()
    now_dt = datetime.now()
    now = now_dt.strftime('%Y-%m-%d %H:%M:%S')

    room_id = generate_room_code()
    # Гарантируем уникальность
    c.execute('SELECT room_id FROM party_rooms WHERE room_id = ?', (room_id,))
    if c.fetchone():
        room_id = generate_room_code()

    c.execute('''
        INSERT INTO party_rooms (room_id, chat_id, title, creator_id, creator_name, status, duration_min, created_at)
        VALUES (?, ?, ?, ?, ?, 'waiting', ?, ?)
    ''', (room_id, chat_id, title, creator_id, creator_name, duration_min, now))

    # Создатель автоматически становится первым участником (готов)
    c.execute('''
        INSERT INTO party_participants (room_id, tg_user_id, user_name, is_ready, score, pure_ethanol_g, drinks_count, status, joined_at, updated_at)
        VALUES (?, ?, ?, 1, 0, 0, 0, 'ready', ?, ?)
    ''', (room_id, creator_id, creator_name, now, now))

    conn.commit()
    conn.close()

    return get_party_room_state(room_id)

def join_party_room(room_id: str, tg_user_id: int, user_name: str, username: str = None, avatar_url: str = None) -> dict:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    c.execute('SELECT status FROM party_rooms WHERE room_id = ?', (room_id,))
    room = c.fetchone()
    if not room:
        conn.close()
        return {"error": "Комната не найдена"}
    if room['status'] == 'finished':
        conn.close()
        return {"error": "Эта вечеринка уже завершена"}

    # Проверяем, есть ли уже в комнате
    c.execute('SELECT id FROM party_participants WHERE room_id = ? AND tg_user_id = ?', (room_id, tg_user_id))
    existing = c.fetchone()
    if existing:
        c.execute('''
            UPDATE party_participants SET
                user_name = ?, username = ?, avatar_url = ?, updated_at = ?
            WHERE room_id = ? AND tg_user_id = ?
        ''', (user_name, username, avatar_url, now, room_id, tg_user_id))
    else:
        init_status = 'active' if room['status'] == 'active' else 'waiting'
        c.execute('''
            INSERT INTO party_participants (room_id, tg_user_id, user_name, username, avatar_url, is_ready, score, pure_ethanol_g, drinks_count, status, joined_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, ?, ?, ?)
        ''', (room_id, tg_user_id, user_name, username, avatar_url, init_status, now, now))

    conn.commit()
    conn.close()

    return get_party_room_state(room_id)

def toggle_party_ready(room_id: str, tg_user_id: int) -> dict:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    c.execute('SELECT is_ready FROM party_participants WHERE room_id = ? AND tg_user_id = ?', (room_id, tg_user_id))
    p = c.fetchone()
    if not p:
        conn.close()
        return {"error": "Участник не найден"}

    new_ready = 0 if p['is_ready'] == 1 else 1
    new_status = 'ready' if new_ready == 1 else 'waiting'
    c.execute('''
        UPDATE party_participants SET
            is_ready = ?, status = ?, updated_at = ?
        WHERE room_id = ? AND tg_user_id = ?
    ''', (new_ready, new_status, now, room_id, tg_user_id))

    conn.commit()
    conn.close()
    return get_party_room_state(room_id)

def start_party_room(room_id: str, host_id: int = None) -> dict:
    conn = get_connection()
    c = conn.cursor()
    now_dt = datetime.now()
    now = now_dt.strftime('%Y-%m-%d %H:%M:%S')

    c.execute('SELECT * FROM party_rooms WHERE room_id = ?', (room_id,))
    room = c.fetchone()
    if not room:
        conn.close()
        return {"error": "Комната не найдена"}

    duration_min = room['duration_min'] or 30
    ends_dt = now_dt + timedelta(minutes=duration_min)
    ends_at = ends_dt.strftime('%Y-%m-%d %H:%M:%S')

    c.execute('''
        UPDATE party_rooms SET
            status = 'active', started_at = ?, ends_at = ?
        WHERE room_id = ?
    ''', (now, ends_at, room_id))

    # Всех переводим в активный статус
    c.execute('''
        UPDATE party_participants SET
            status = 'active', updated_at = ?
        WHERE room_id = ?
    ''', (now, room_id))

    conn.commit()
    conn.close()
    return get_party_room_state(room_id)

def add_party_drink(room_id: str, tg_user_id: int, drink_name: str = "Пиво", volume_ml: float = 500.0, abv: float = 5.0) -> dict:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    c.execute('SELECT user_name FROM party_participants WHERE room_id = ? AND tg_user_id = ?', (room_id, tg_user_id))
    p = c.fetchone()
    user_name = p['user_name'] if p else "Атлет"

    pure_ethanol = round(volume_ml * (abv / 100.0) * 0.789, 1)

    c.execute('''
        INSERT INTO party_drinks (room_id, tg_user_id, user_name, drink_name, volume_ml, abv, pure_ethanol_g, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (room_id, tg_user_id, user_name, drink_name, volume_ml, abv, pure_ethanol, now))

    # Обновляем участника
    c.execute('''
        UPDATE party_participants SET
            pure_ethanol_g = pure_ethanol_g + ?,
            drinks_count = drinks_count + 1,
            score = ROUND((pure_ethanol_g + ?) * 1.5 + (drinks_count + 1) * 5, 1),
            updated_at = ?
        WHERE room_id = ? AND tg_user_id = ?
    ''', (pure_ethanol, pure_ethanol, now, room_id, tg_user_id))

    # Синхронизируем с чатом, если комната привязана к чату
    c.execute('SELECT chat_id FROM party_rooms WHERE room_id = ?', (room_id,))
    r_chat = c.fetchone()
    if r_chat and r_chat['chat_id']:
        record_chat_drink(r_chat['chat_id'], tg_user_id, user_name, None, drink_name, volume_ml, abv)

    conn.commit()
    conn.close()
    return get_party_room_state(room_id)

def add_party_photo(room_id: str, tg_user_id: int, photo_data: str, stage: str = "active") -> dict:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    c.execute('SELECT user_name FROM party_participants WHERE room_id = ? AND tg_user_id = ?', (room_id, tg_user_id))
    p = c.fetchone()
    user_name = p['user_name'] if p else "Атлет"

    photo_url = save_party_photo_file(room_id, tg_user_id, photo_data)
    if not photo_url:
        # Если не получилось сохранить файл, используем data_url напрямую
        photo_url = photo_data if len(photo_data) < 50000 else ""

    caption = random.choice(FUNNY_PHOTO_CAPTIONS)

    c.execute('''
        INSERT INTO party_photos (room_id, tg_user_id, user_name, photo_url, stage, funny_caption, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (room_id, tg_user_id, user_name, photo_url, stage, caption, now))

    c.execute('''
        UPDATE party_participants SET
            photos_count = photos_count + 1,
            score = score + 10,
            updated_at = ?
        WHERE room_id = ? AND tg_user_id = ?
    ''', (now, room_id, tg_user_id))

    conn.commit()
    conn.close()
    return get_party_room_state(room_id)

def confirm_party_alive(room_id: str, tg_user_id: int) -> dict:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    c.execute('''
        UPDATE party_participants SET
            confirmed_alive = 1,
            status = 'survived',
            updated_at = ?
        WHERE room_id = ? AND tg_user_id = ?
    ''', (now, room_id, tg_user_id))

    conn.commit()
    conn.close()
    return get_party_room_state(room_id)

def finish_party_room(room_id: str) -> dict:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Все, кто не подтвердил (confirmed_alive = 0), получают статус 'knocked_out' (ОТРУБИЛСЯ)
    c.execute('''
        UPDATE party_participants SET
            status = 'knocked_out'
        WHERE room_id = ? AND confirmed_alive = 0
    ''', (room_id,))

    # Ищем победителя среди выживших (confirmed_alive = 1)
    c.execute('''
        SELECT tg_user_id, user_name, score
        FROM party_participants
        WHERE room_id = ? AND confirmed_alive = 1
        ORDER BY score DESC
        LIMIT 1
    ''', (room_id,))
    winner = c.fetchone()

    winner_name = winner['user_name'] if winner else "Никто не выжил 💀"
    winner_score = winner['score'] if winner else 0.0

    if winner:
        c.execute('''
            UPDATE party_participants SET
                status = 'winner'
            WHERE room_id = ? AND tg_user_id = ?
        ''', (room_id, winner['tg_user_id']))

    # Закрываем комнату
    c.execute('''
        UPDATE party_rooms SET
            status = 'finished',
            winner_name = ?,
            winner_score = ?
        WHERE room_id = ?
    ''', (winner_name, winner_score, room_id))

    conn.commit()
    conn.close()
    return get_party_room_state(room_id)

def get_party_room_state(room_id: str) -> dict:
    conn = get_connection()
    c = conn.cursor()

    c.execute('SELECT * FROM party_rooms WHERE room_id = ?', (room_id,))
    room_row = c.fetchone()
    if not room_row:
        conn.close()
        return None

    room = dict(room_row)
    now_dt = datetime.now()

    # Проверка таймера для активной комнаты
    if room['status'] == 'active' and room.get('ends_at'):
        try:
            ends_dt = datetime.strptime(room['ends_at'], '%Y-%m-%d %H:%M:%S')
            seconds_left = int((ends_dt - now_dt).total_seconds())
            if seconds_left <= 0:
                # Переводим в стадию переклички (finishing)
                c.execute("UPDATE party_rooms SET status = 'finishing' WHERE room_id = ?", (room_id,))
                conn.commit()
                room['status'] = 'finishing'
                room['seconds_left'] = 0
            else:
                room['seconds_left'] = seconds_left
        except Exception:
            room['seconds_left'] = 0
    else:
        room['seconds_left'] = 0

    # Список участников
    c.execute('''
        SELECT id, room_id, tg_user_id, user_name, username, avatar_url, is_ready, score, pure_ethanol_g, drinks_count, photos_count, confirmed_alive, status
        FROM party_participants
        WHERE room_id = ?
        ORDER BY (confirmed_alive = 1) DESC, score DESC
    ''', (room_id,))
    participants = [dict(r) for r in c.fetchall()]

    # Последние напитки
    c.execute('''
        SELECT id, tg_user_id, user_name, drink_name, volume_ml, abv, pure_ethanol_g, created_at
        FROM party_drinks
        WHERE room_id = ?
        ORDER BY id DESC
        LIMIT 20
    ''', (room_id,))
    drinks = [dict(r) for r in c.fetchall()]

    # Фотогалерея
    c.execute('''
        SELECT id, tg_user_id, user_name, photo_url, stage, funny_caption, created_at
        FROM party_photos
        WHERE room_id = ?
        ORDER BY id ASC
    ''', (room_id,))
    photos = [dict(r) for r in c.fetchall()]

    conn.close()

    room['participants'] = participants
    room['drinks'] = drinks
    room['photos'] = photos
    room['participants_count'] = len(participants)
    room['ready_count'] = sum(1 for p in participants if p['is_ready'] == 1)
    room['knocked_out_count'] = sum(1 for p in participants if p['status'] == 'knocked_out')
    room['survived_count'] = sum(1 for p in participants if p['confirmed_alive'] == 1)

    return room

def get_active_room_for_chat(chat_id: int) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT room_id FROM party_rooms
        WHERE chat_id = ? AND status IN ('waiting', 'active', 'finishing')
        ORDER BY created_at DESC
        LIMIT 1
    ''', (chat_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return get_party_room_state(row['room_id'])
    return None

# Инициализируем БД при загрузке модуля
init_db()

