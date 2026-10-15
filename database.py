"""
Всероссийская Федерация Литрбола (ВФЛ) — Модуль Базы Данных (SQLite)
Управляет профилями атлетов, рекордами, Залом Славы и верификацией.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "litrball.db")

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
    conn = sqlite3.connect(DB_PATH)
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
    
    # Предустановленные топ-атлеты для Зала Славы, если база пустая
    c.execute('SELECT COUNT(*) as count FROM athletes')
    row = c.fetchone()
    if row['count'] == 0:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        seed_athletes = [
            ("Василий «Турбо-Шот»", "vasya_turbo", 85.0, "m", "zms", "Заслуженный Мастер Спорта (ЗМС)", 340.5, 320.0, 1.85, "Академическое застольное многоборье", "№ ЗМС-001/ФЛР-2026", 1, json.dumps(["first_sip", "kms_rank", "ms_legend", "zms_god", "snack_master"]), now, now),
            ("Елена Прекрасная", "elena_craft", 58.0, "f", "msmk", "МСМК (Международный класс)", 275.0, 190.0, 1.45, "Классический пенный слалом", "№ МСМК-014/ФЛР-2026", 1, json.dumps(["first_sip", "kms_rank", "ms_legend"]), now, now),
            ("Дмитрий «Автопилот»", "dima_pilot", 92.0, "m", "ms", "Мастер Спорта по Литрболу (МС)", 215.0, 240.0, 1.60, "Двоеборье «Ёрш-Биатлон» (пиво + водка)", "№ МС-089/ФЛР-2026", 1, json.dumps(["first_sip", "biathlon_champ", "kms_rank", "ms_legend"]), now, now),
            ("Сергей Николаевич", "serge_pro", 105.0, "m", "kms", "КМС (Кандидат в Мастера Спорта)", 175.0, 200.0, 1.30, "Стайерский многочасовой марафон", "№ КМС-102/ФЛР-2026", 1, json.dumps(["first_sip", "kms_rank", "no_ex_call"]), now, now),
            ("Антон «Кефир»", "anton_junior", 70.0, "m", "adult_1", "1-й Взрослый разряд", 130.0, 140.0, 1.10, "Скоростной спринт по шотам", "№ ВЗР-412/ФЛР-2026", 0, json.dumps(["first_sip", "detector_passed"]), now, now)
        ]
        c.executemany('''
            INSERT INTO athletes (name, username, weight, gender, rank_id, rank_title, score, pure_ethanol_g, est_bac, discipline, order_num, verified, achievements, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', seed_athletes)
    
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

# Инициализируем БД при загрузке модуля
init_db()
