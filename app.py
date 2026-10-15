#!/usr/bin/env python3
"""
Всероссийская Федерация Литрбола (ВФЛ) — Сервер Приложения
Запуск: python3 app.py [порт, по умолчанию 8080]
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import hashlib
from datetime import datetime

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# Данные разрядов
RANKS = [
    {
        "id": "junior_3",
        "title": "3-й Юношеский разряд",
        "short": "3-й Юн.",
        "badge": "🥉",
        "min_score": 0,
        "max_score": 15,
        "description": "Кефирный атлет. Один бокал сидра или половина пива вызывают философскую задумчивость и желание прилечь.",
        "morning_verdict": "Легкое удивление от вчерашнего, готов к пробежке.",
        "icon": "🍼"
    },
    {
        "id": "junior_2",
        "title": "2-й Юношеский разряд",
        "short": "2-й Юн.",
        "badge": "🥉",
        "min_score": 16,
        "max_score": 30,
        "description": "Начинающий боец. Способен осилить 2 бутылки пенного или пару бокалов полусладкого без потери паспорта.",
        "morning_verdict": "Легкая сушь во рту, лечится стаканом воды.",
        "icon": "🍺"
    },
    {
        "id": "junior_1",
        "title": "1-й Юношеский разряд",
        "short": "1-й Юн.",
        "badge": "🥉",
        "min_score": 31,
        "max_score": 50,
        "description": "Уверенный юниор. Три кружки пива или 150г беленькой. Начинает рассказывать анекдоты и объяснять, как устроен мир.",
        "morning_verdict": "Сушняк средней силы, поиск минералочки.",
        "icon": "🍻"
    },
    {
        "id": "adult_3",
        "title": "3-й Взрослый разряд",
        "short": "3-й Взр.",
        "badge": "🥈",
        "min_score": 51,
        "max_score": 75,
        "description": "Боец массового спорта. Около 2.5л пива или 250г крепкого. Способен поддержать любой разговор в курилке.",
        "morning_verdict": "Тяжеловато вставать, но мысль о кофе спасает положение.",
        "icon": "🍷"
    },
    {
        "id": "adult_2",
        "title": "2-й Взрослый разряд",
        "short": "2-й Взр.",
        "badge": "🥈",
        "min_score": 76,
        "max_score": 105,
        "description": "Крепкий середняк. 3.5л пива или 350г крепкого. Поет «Седую ночь» или «Батарейку», знает всех барменов в округе.",
        "morning_verdict": "Голова гудит, спасает холодный душ и горячий суп.",
        "icon": "🍸"
    },
    {
        "id": "adult_1",
        "title": "1-й Взрослый разряд",
        "short": "1-й Взр.",
        "badge": "🥈",
        "min_score": 106,
        "max_score": 140,
        "description": "Опытный стайер. Честная «пол-литра» в одно лицо или 5 литров пенного. Автопилот настроен идеально: ключи, телефон и честь на месте.",
        "morning_verdict": "Похмелье классическое. Рекомендуется борщ и постельный режим.",
        "icon": "🥃"
    },
    {
        "id": "kms",
        "title": "КМС (Кандидат в Мастера Спорта)",
        "short": "КМС",
        "badge": "🥇",
        "min_score": 141,
        "max_score": 185,
        "description": "Элита застольного многоборья. До 0.7л крепкого. Ни одного звонка бывшим, способность вспомнить пин-код в 22:58 без очков.",
        "morning_verdict": "Банка огуречного рассола, аспирин и фраза: «Славно посидели».",
        "icon": "🏆"
    },
    {
        "id": "ms",
        "title": "Мастер Спорта по Литрболу (МС)",
        "short": "МС",
        "badge": "⭐",
        "min_score": 186,
        "max_score": 240,
        "description": "Гроссмейстер хмельных баталий. От 0.7л до 1л крепкого или марафон на двое суток. В 3 ночи ведет философские дискуссии о Канте и квантовой механике.",
        "morning_verdict": "Просыпается в 11:00, готовит яичницу с беконом, не моргая смотрит в зеркало.",
        "icon": "🎖️"
    },
    {
        "id": "msmk",
        "title": "МСМК (Международный класс)",
        "short": "МСМК",
        "badge": "👑",
        "min_score": 241,
        "max_score": 300,
        "description": "Легенда международных сборов. Смешивает крафт с текилой, выдерживает турецкий All-Inclusive и свадьбу в деревне без потери человеческого облика.",
        "morning_verdict": "Утренняя регенерация терминатора. Готов к повторной тренировке.",
        "icon": "🌟"
    },
    {
        "id": "zms",
        "title": "Заслуженный Мастер Спорта (ЗМС)",
        "short": "ЗМС",
        "badge": "🔥",
        "min_score": 301,
        "max_score": 9999,
        "description": "Живая легенда Федерации. Стаж 20+ лет. Открывает бутылки взглядом, определяет крепость самогона на слух, наставник молодого поколения.",
        "morning_verdict": "Похмелье отсутствует как класс. Судейская коллегия аплодирует стоя.",
        "icon": "👑"
    }
]

# Вопросы теоретического экзамена ВАК Литрбола
QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "Вам предлагают запить крепкий напиток сладкой газировкой. Ваши действия?",
        "options": [
            {"text": "С радостью соглашусь, так ведь вкуснее и слаще", "score": 2, "comment": "Юношеская ошибка — пузырьки углекислого газа ускорят опьянение вдвое!"},
            {"text": "Откажусь и запью простой чистой водой или томатным соком", "score": 10, "comment": "Грамотный подход профессионала: гидратация сохранит ясность мысли."},
            {"text": "Запивать? Настоящие атлеты только закусывают соленым огурцом!", "score": 15, "comment": "Золотая классика застольного спорта!"},
            {"text": "Запью светлым нефильтрованным пивом («Ёрш-стайл»)", "score": 12, "comment": "Рискованный двоеборческий трюк, доступный только опытным бойцам."}
        ]
    },
    {
        "id": 2,
        "question": "Время 22:56. До закрытия магазина 4 минуты, перед вами 3 человека. Ваша тактика?",
        "options": [
            {"text": "Развернусь и пойду спать, здоровье дороже", "score": 5, "comment": "Здорово, но спортивный характер не проявлен."},
            {"text": "Громко и вежливо крикну: «Мужики, мне только одну, горю! Пропустите мастера!»", "score": 15, "comment": "Проверенный спортивный авторитет открывает любые двери!"},
            {"text": "Начну нервно переминаться с ноги на ногу и надеяться на чудо", "score": 3, "comment": "Слабая тактическая подготовка."},
            {"text": "Вспомню, что в круглосуточном баре за углом наливают навынос", "score": 12, "comment": "Превосходное знание соревновательной инфраструктуры района."}
        ]
    },
    {
        "id": 3,
        "question": "Друг за столом в 02:30 достает телефон и открывает переписку с бывшей. Что делать?",
        "options": [
            {"text": "Включу микрофон и помогу ему сформулировать мысли", "score": -10, "comment": "Дисквалификация! Это грубейшее нарушение кодекса спортсмена."},
            {"text": "Немедленно отберу телефон, спрячу в карман и налью ему чаю", "score": 15, "comment": "Поступок настоящего товарища по команде. Медаль за спасение чести!"},
            {"text": "Сделаю вид, что не заметил, каждый сам кузнец своего позора", "score": 2, "comment": "Равнодушие в спорте наказуемо."},
            {"text": "Предложу спеть хором «Знаешь ли ты» или «Седую ночь» вместо звонка", "score": 14, "comment": "Гениальный отвлекающий маневр!"}
        ]
    },
    {
        "id": 4,
        "question": "Каково главное золотое правило перехода между напитками?",
        "options": [
            {"text": "Градус можно только повышать, понижать — табу!", "score": 15, "comment": "Аксиома номер 1 любого застольного классификатора."},
            {"text": "Главное, чтобы цвет напитков совпадал", "score": 4, "comment": "Мистицизм вместо биохимии."},
            {"text": "Можно всё смешивать в одном бокале, в животе всё равно перемешается", "score": 1, "comment": "Прямой путь к досрочному нокауту до полуночи."},
            {"text": "Чередовать стопку с бокалом воды в соотношении 1:1", "score": 12, "comment": "Шведская методика безопасного спорта."}
        ]
    },
    {
        "id": 5,
        "question": "Что является идеальной закуской перед первым стартовым тостом?",
        "options": [
            {"text": "Пачка чипсов со вкусом краба", "score": 3, "comment": "Слишком легкомысленно для тяжелой атлетики."},
            {"text": "Плотный горячий суп, бутерброд с салом или кусочек сливочного масла", "score": 15, "comment": "Создает идеальную защитную пленку в желудке. Профессиональный ход!"},
            {"text": "Ничего, натощак веселее и быстрее берет", "score": 0, "comment": "Грубая ошибка новичка, ведущая к дисквалификации."},
            {"text": "Долька лимона с сахаром", "score": 8, "comment": "Французский стиль, годится под коньяк."}
        ]
    },
    {
        "id": 6,
        "question": "Как вы относитесь к безалкогольному пиву («нулёвке»)?",
        "options": [
            {"text": "Прекрасный напиток, когда я за рулем или на сушке", "score": 12, "comment": "Ответственный спортсмен за рулем — гордость автодрома!"},
            {"text": "Первый шаг к резиновой женщине", "score": 10, "comment": "Фольклорный консерватизм ветеранов литрбола."},
            {"text": "Пью исключительно его, алкоголь вообще не употребляю", "score": 15, "comment": "Почетный статус «Трезвый судья соревнований и водитель сборной»!"},
            {"text": "Использую его, чтобы незаметно заменить другу, который уже поплыл", "score": 15, "comment": "Тактическая хитрость высшей тренерской категории!"}
        ]
    },
    {
        "id": 7,
        "question": "Утро после чемпионата: сушняк, в холодильнике банка рассола, бутылка минералки и вчерашняя пицца. С чего начать?",
        "options": [
            {"text": "Опохмелиться холодным пивом", "score": 4, "comment": "Опасно! Похмелье — это не повод открывать второй сезон без паузы."},
            {"text": "Сделать три жадных глотка рассола, затем запить минералкой без газа", "score": 15, "comment": "Идеальное восстановление водно-солевого баланса и электролитов."},
            {"text": "Скушать холодную пиццу целиком", "score": 5, "comment": "ЖКТ может выразить решительный протест."},
            {"text": "Пойти на турники выбивать дурь", "score": 1, "comment": "Удар по сердечно-сосудистой системе, кардиологи в ужасе."}
        ]
    },
    {
        "id": 8,
        "question": "Какой тост считается эталоном мастерства в приличном обществе?",
        "options": [
            {"text": "«Ну... вздрогнули!» (сопровождается стуком по столу)", "score": 8, "comment": "Кратко, емко, по-спартански."},
            {"text": "Притча на 15 минут про птичку, которая летела к солнцу, пока все держат бокалы", "score": 2, "comment": "Штрафные 2 минуты за затягивание игры и остывшее горячее."},
            {"text": "Искренний, остроумный тост за присутствующих людей длиной в 30-40 секунд", "score": 15, "comment": "Высший пилотаж спортивной дипломатии."},
            {"text": "«Чтобы все!» с цитированием Шарикова", "score": 10, "comment": "Классика советского кинематографа."}
        ]
    },
    {
        "id": 9,
        "question": "Вы потеряли ориентацию по пути домой. Ваши действия по возвращению на базу?",
        "options": [
            {"text": "Закажу такси через приложение без лишних разговоров", "score": 15, "comment": "Самый надежный автопилот 21 века."},
            {"text": "Лягу на лавочке в парке поспать до рассвета", "score": -10, "comment": "Прямая дисквалификация, риск проснуться без кроссовок."},
            {"text": "Пойду по синусоиде навстречу огням ночного города", "score": 6, "comment": "Дисциплина «Фигурное шатание» в действии."},
            {"text": "Позвоню другу, с которым только что разошелся: «Брат, а где я?»", "score": 8, "comment": "Традиционная навигация по собутыльникам."}
        ]
    },
    {
        "id": 10,
        "question": "Что отличает настоящего Заслуженного Мастера Спорта (ЗМС) по литрболу?",
        "options": [
            {"text": "Он может выпить ведро водки и залезть на фонарный столб", "score": 0, "comment": "Это не мастерство, это дебош."},
            {"text": "Культура пития: знает меру, никогда не буянит, бережет друзей и всегда помнит вчерашний вечер", "score": 20, "comment": "Истинная мудрость! Спорт высших достижений — это самоконтроль и уважение."},
            {"text": "Умение открывать пиво любым предметом в радиусе двух метров", "score": 12, "comment": "Полезный прикладной навык мастера."},
            {"text": "Всегда имеет при себе штопор и пачку активированного угля", "score": 14, "comment": "Экипировка настоящего профи."}
        ]
    }
]

def calculate_score(data):
    """
    Расчет спортивного балла и разряда на основе параметров застолья:
    - weight (кг)
    - gender ('m' или 'f')
    - experience ('junior', 'amateur', 'experienced', 'veteran')
    - drinks: list of {name, volume_ml, abv, count}
    - hours: длительность в часах
    - snack: 'empty', 'light', 'medium', 'heavy'
    - penalties: dict of boolean flags (called_ex, lost_items, vomited, fell_asleep)
    """
    weight = float(data.get('weight', 75))
    gender = data.get('gender', 'm')
    experience = data.get('experience', 'amateur')
    drinks = data.get('drinks', [])
    hours = float(data.get('hours', 3))
    snack = data.get('snack', 'medium')
    penalties = data.get('penalties', {})

    # Расчет чистой массы этанола в граммах
    total_pure_ethanol_g = 0.0
    for d in drinks:
        vol = float(d.get('volume_ml', 0)) * float(d.get('count', 1))
        abv = float(d.get('abv', 0))
        # Масса спирта = объем * % спирта / 100 * плотность 0.8
        total_pure_ethanol_g += vol * (abv / 100.0) * 0.789

    # Фактор редукции Видмарка
    r = 0.68 if gender == 'm' else 0.55

    # Теоретический пиковый промилле в крови по Видмарку
    # С учетом выведения спирта печенью (~0.15 промилле в час)
    raw_bac = total_pure_ethanol_g / (weight * r) if weight > 0 else 0
    eliminated_bac = max(0, (hours - 0.5) * 0.15) if hours > 0.5 else 0
    est_bac = max(0.0, raw_bac - eliminated_bac)

    # Время полного вытрезвления (часов)
    sober_hours = round(raw_bac / 0.15, 1) if raw_bac > 0 else 0.0

    # Коэффициенты для спортивного балла
    snack_mult = {
        'empty': 1.35,      # Без закуски — повышенная сложность
        'light': 1.10,      # Чипсы, орешки
        'medium': 1.00,     # Бутерброды, пицца
        'heavy': 0.85       # Плотный ужин, борщ, сало
    }.get(snack, 1.0)

    exp_mult = {
        'junior': 0.85,
        'amateur': 1.00,
        'experienced': 1.15,
        'veteran': 1.30
    }.get(experience, 1.0)

    # Базовые очки на основе чистого этанола и веса
    # Нормализуем к эталону 75 кг
    weight_factor = 75.0 / max(40.0, weight)
    base_points = (total_pure_ethanol_g * 0.95) * weight_factor

    # Модификаторы темпа
    pace_factor = 1.0
    if hours < 1.0 and total_pure_ethanol_g > 30:
        pace_factor = 1.25 # Залповый спринт
    elif hours > 6.0:
        pace_factor = 0.85 # Марафон

    final_score = base_points * snack_mult * exp_mult * pace_factor

    # Штрафы за неспортивное поведение
    penalty_points = 0
    penalty_notes = []
    if penalties.get('vomited'):
        penalty_points += 150
        penalty_notes.append("Красная карточка: досрочный визит к Ихтиандру (-150 очков)")
    if penalties.get('fell_asleep'):
        penalty_points += 40
        penalty_notes.append("Желтая карточка: салатный нокаут до окончания вечера (-40 очков)")
    if penalties.get('called_ex'):
        penalty_points += 50
        penalty_notes.append("Дисквалификация: звонок бывшим после полуночи (-50 очков)")
    if penalties.get('lost_items'):
        penalty_points += 30
        penalty_notes.append("Штраф: потеря ключей, карты или чести мундира (-30 очков)")

    final_score = max(0, final_score - penalty_points)

    # Определение разряда
    assigned_rank = RANKS[0]
    for r_entry in RANKS:
        if final_score >= r_entry['min_score']:
            assigned_rank = r_entry

    # Если была рвота — максимальный разряд снижается до юношеского
    if penalties.get('vomited') and assigned_rank['id'] not in ['junior_3', 'junior_2']:
        assigned_rank = RANKS[1]

    # Генерация уникального номера удостоверения
    seed_str = f"{data.get('name', 'Атлет')}_{total_pure_ethanol_g}_{datetime.now().strftime('%Y%m%d%H%M')}"
    order_num = hashlib.md5(seed_str.encode()).hexdigest()[:8].upper()
    order_full = f"№ {order_num}/ФЛР-{datetime.now().year}"

    return {
        "score": round(final_score, 1),
        "pure_ethanol_g": round(total_pure_ethanol_g, 1),
        "est_bac_promille": round(est_bac, 2),
        "sober_hours": sober_hours,
        "rank": assigned_rank,
        "penalty_notes": penalty_notes,
        "order_num": order_full,
        "disciplines": suggest_disciplines(drinks, hours)
    }

def suggest_disciplines(drinks, hours):
    """Определение коронной дисциплины на основе напитков"""
    has_beer = any('пив' in d.get('name', '').lower() or d.get('abv', 0) <= 8 for d in drinks)
    has_vodka = any('водк' in d.get('name', '').lower() or d.get('abv', 0) >= 38 for d in drinks)
    
    if has_beer and has_vodka:
        return "Двоеборье «Ёрш-Биатлон» (пиво + водка)"
    elif hours >= 5:
        return "Стайерский многочасовой марафон"
    elif hours <= 1 and any(d.get('abv', 0) >= 35 for d in drinks):
        return "Скоростной спринт по шотам (Shot Put)"
    elif any(d.get('abv', 0) <= 8 for d in drinks):
        return "Классический пенный слалом"
    else:
        return "Академическое застольное многоборье"

# Подключение базы данных и генератора удостоверений
import database
from cert_generator import generate_certificate_image

# Коллекция официальных тостов ВФЛ
TOASTS_COLLECTION = [
    {"category": "sport", "title": "За чистый спорт", "text": "Поднимем бокалы за то, чтобы наш спорт оставался честным, закуска — сытной, а судейская коллегия никогда не путала пиво с лимонадом! За ВФЛ!", "icon": "🏆"},
    {"category": "sport", "title": "За стойкость печени", "text": "Железо ржавеет, дерево гниет, а печень спортсмена-литрболиста крепнет от тренировки к тренировке! За стальной характер!", "icon": "🥇"},
    {"category": "short", "title": "Спартанский", "text": "Ну... вздрогнули, чтобы не упали!", "icon": "⚡"},
    {"category": "short", "title": "Артиллерийский", "text": "По рюмочкам — огонь!", "icon": "🎯"},
    {"category": "humor", "title": "За автопилот", "text": "Выпьем за самую надежную спутниковую систему на Земле — за внутренний автопилот, который всегда находит дорогу домой!", "icon": "🧭"},
    {"category": "humor", "title": "За телефон в кармане", "text": "Пусть руки тянутся к бокалам, а не к перепискам с бывшими в 3 часа ночи! За мужскую выдержку!", "icon": "📵"},
    {"category": "friends", "title": "За верную команду", "text": "С кем попало литрболом не занимаются. Выпьем за команду мастеров за этим столом, готовых подставить плечо и налить стакан!", "icon": "🤝"},
    {"category": "friends", "title": "За понимание", "text": "За то, чтобы утро было добрым, голова — легкой, а воспоминания — теплыми и без цензуры!", "icon": "🌅"},
    {"category": "wisdom", "title": "Философский", "text": "Алкоголь в малых дозах безвреден в любых количествах. Но мы — профессионалы, поэтому пьем за меру, которую каждый определяет сам!", "icon": "🍷"}
]

# Антипохмельный протокол
HANGOVER_PROTOCOL = {
    "stages": [
        {"time": "08:00 - 09:30", "title": "Фаза Пробуждения «Зомби-Старт»", "action": "Не делать резких движений. 500 мл минералки без газа (Ессентуки-4 или Боржоми) + 2 таблетки янтарной кислоты. Горизонтальное положение."},
        {"time": "10:00 - 11:30", "title": "Фаза Электролитного Удара", "action": "Стакан рассола (соленые, не маринованные огурцы/капуста) или Регидрон. Пакет сорбента (Полисорб / Энтеросгель). Теплый душ без перепадов температур."},
        {"time": "12:00 - 14:00", "title": "Фаза Термоядерного Бульона", "action": "Горячий куриный бульон, хаш или солянка с лимоном. Чай с медом и мятой. Просмотр добрых советских комедий."},
        {"time": "15:00 - 18:00", "title": "Фаза Возвращения в Человеческий Облик", "action": "Легкая прогулка на свежем воздухе. Витамин C (1000 мг), крепкий сон на 2 часа. К вечеру организм готов к анализу ошибок."}
    ],
    "prohibitions": [
        "❌ Не пейте крепкий кофе натощак — это спазм сосудов и лишняя нагрузка на сердце.",
        "❌ Никаких тяжелых силовых тренировок и бани — обезвоживание может привести к кризу.",
        "❌ Опохмел пивом переносит похмелье на завтра, превращая спорт в запой."
    ],
    "rescue_call": {
        "caller_name": "Шеф / Работа (Срочно)",
        "caller_number": "+7 (999) 000-ФЕДЕРАЦИЯ",
        "script": "«Алло, срочно приезжай в офис, сервер лег, без тебя катастрофа!» — идеальный повод встать и уйти из любого бара."
    }
}

class LitrballHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/api/ranks':
            self.send_json(RANKS)
        elif path == '/api/questions':
            self.send_json(QUIZ_QUESTIONS)
        elif path == '/api/achievements':
            self.send_json(database.ACHIEVEMENTS_LIST)
        elif path == '/api/leaderboard':
            limit = int(query.get('limit', [20])[0])
            chat_id = query.get('chat_id', [None])[0]
            if chat_id:
                try:
                    self.send_json(database.get_chat_leaderboard(int(chat_id), limit))
                except Exception as e:
                    self.send_json({"error": str(e)}, status=400)
            else:
                self.send_json(database.get_leaderboard(limit))
        elif path == '/api/chat/stats':
            chat_id = query.get('chat_id', [None])[0]
            if chat_id:
                try:
                    res = database.get_chat_stats(int(chat_id))
                    if res:
                        self.send_json(res)
                    else:
                        self.send_json({"error": "Chat not found"}, status=404)
                except Exception as e:
                    self.send_json({"error": str(e)}, status=400)
            else:
                self.send_json({"error": "chat_id parameter required"}, status=400)
        elif path == '/api/athlete':
            tg_id = int(query['tg_id'][0]) if 'tg_id' in query else None
            athlete_id = int(query['id'][0]) if 'id' in query else None
            athlete = database.get_athlete(tg_user_id=tg_id, athlete_id=athlete_id)
            if athlete:
                self.send_json(athlete)
            else:
                self.send_json({"error": "Athlete not found"}, status=404)
        elif path == '/api/toasts':
            self.send_json(TOASTS_COLLECTION)
        elif path == '/api/hangover':
            self.send_json(HANGOVER_PROTOCOL)
        elif path == '/api/certificate':
            # Динамическая генерация корочки в PNG
            name = query.get('name', ['Иван Атлетов'])[0]
            rank_title = query.get('rank', ['Мастер Спорта по Литрболу (МС)'])[0]
            weight = float(query.get('weight', [80.0])[0])
            order_num = query.get('order_num', ['№ 001/ФЛР-2026'])[0]
            discipline = query.get('discipline', ['Академическое застольное многоборье'])[0]
            pure_ethanol_g = float(query.get('pure', [120.0])[0])
            est_bac = float(query.get('bac', [1.2])[0])
            
            try:
                img_bytes = generate_certificate_image(
                    name=name,
                    rank_title=rank_title,
                    weight=weight,
                    discipline=discipline,
                    order_num=order_num,
                    pure_ethanol_g=pure_ethanol_g,
                    est_bac=est_bac
                )
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(img_bytes)))
                self.send_header('Content-Disposition', f'inline; filename="litrball_certificate.png"')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(img_bytes)
            except Exception as e:
                self.send_json({"error": f"Failed to generate certificate: {str(e)}"}, status=500)
        elif path == '/api/health':
            self.send_json({"status": "ok", "app": "Всероссийская Федерация Литрбола", "version": "3.0 (Ультимативный Фарш)"})
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"

        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if path == '/api/calculate':
            try:
                result = calculate_score(data)
                # Автосохранение результата, если передан tg_user_id
                if data.get('tg_user_id'):
                    save_payload = {**data, **result}
                    saved = database.save_or_update_athlete(save_payload)
                    result['saved_profile'] = saved
                self.send_json(result)
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
        elif path == '/api/athlete/save':
            try:
                saved = database.save_or_update_athlete(data)
                self.send_json(saved)
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
        elif path == '/api/duel':
            try:
                creator = data.get('creator', {"name": data.get('name', 'Атлет'), "score": data.get('score', 100), "rank_title": data.get('rank_title', 'Любитель')})
                opponent = data.get('opponent')
                duel_res = database.create_or_play_duel(creator, opponent)
                self.send_json(duel_res)
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
        elif path == '/api/bac':
            # Детальный калькулятор промилле и времени до трезвости (Видмарк)
            try:
                weight = float(data.get('weight', 75))
                gender = data.get('gender', 'm')
                pure_ethanol = float(data.get('pure_ethanol_g', 50))
                hours_passed = float(data.get('hours_passed', 0))
                r = 0.68 if gender == 'm' else 0.55
                peak_bac = pure_ethanol / (weight * r) if weight > 0 else 0
                elimination_rate = 0.15 # 0.15 промилле в час
                current_bac = max(0.0, peak_bac - (hours_passed * elimination_rate))
                
                # Допустимая норма в РФ: 0.16 мг/л в выдыхаемом воздухе (~0.35 промилле в крови)
                drive_hours = max(0.0, round((current_bac - 0.35) / elimination_rate, 1)) if current_bac > 0.35 else 0.0
                full_sober_hours = max(0.0, round(current_bac / elimination_rate, 1))
                
                # Стадия
                if current_bac == 0:
                    stage = "Абсолютная трезвость"
                    stage_desc = "Реакция 100%, готов к вождению и защите диссертации."
                    stage_color = "#10b981"
                elif current_bac < 0.5:
                    stage = "Легкая эйфория"
                    stage_desc = "Подъем настроения, расслабленность, разговорчивость."
                    stage_color = "#3b82f6"
                elif current_bac < 1.0:
                    stage = "Среднее опьянение"
                    stage_desc = "Снижение концентрации, эмоциональные тосты, громкий смех."
                    stage_color = "#f59e0b"
                elif current_bac < 1.5:
                    stage = "Заметное опьянение"
                    stage_desc = "Шаткая походка, автопилот включен, тяга к караоке."
                    stage_color = "#f97316"
                elif current_bac < 2.5:
                    stage = "Тяжелое опьянение"
                    stage_desc = "Глубокая философия, потеря связи с реальностью, нужен чай и кровать."
                    stage_color = "#ef4444"
                else:
                    stage = "Космическая перегрузка"
                    stage_desc = "Опасная зона! Срочно сорбенты, вода и сон."
                    stage_color = "#7f1d1d"

                self.send_json({
                    "peak_bac": round(peak_bac, 2),
                    "current_bac": round(current_bac, 2),
                    "drive_hours": drive_hours,
                    "full_sober_hours": full_sober_hours,
                    "stage": stage,
                    "stage_desc": stage_desc,
                    "stage_color": stage_color
                })
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
        elif path == '/api/chat/drink':
            try:
                chat_id = int(data.get('chat_id'))
                tg_user_id = int(data.get('tg_user_id'))
                user_name = data.get('user_name', 'Атлет')
                username = data.get('username')
                drink_name = data.get('drink_name', 'Пиво')
                volume_ml = float(data.get('volume_ml', 500))
                abv = float(data.get('abv', 5.0))
                res = database.record_chat_drink(chat_id, tg_user_id, user_name, username, drink_name, volume_ml, abv)
                self.send_json(res)
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
        else:
            self.send_error(404, "Endpoint not found")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), LitrballHandler) as httpd:
        print(f"==================================================")
        print(f"🍺 Сервер Всероссийской Федерации Литрбола v3.0 запущен!")
        print(f"📍 Локальный адрес: http://localhost:{PORT}")
        print(f"📁 Статические файлы: {STATIC_DIR}")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nСмена судейской бригады. Сервер остановлен.")

if __name__ == '__main__':
    run_server()

