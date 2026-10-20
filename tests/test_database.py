import pytest
import database

def test_athlete_save_and_get():
    """Тест создания профиля атлета и сохранения ачивок"""
    data = {
        "tg_user_id": 12345678,
        "name": "Алексей Стаканов",
        "username": "stakanov",
        "weight": 82.5,
        "gender": "m",
        "rank": {"id": "kms", "title": "Кандидат в Мастера Спорта (КМС)"},
        "score": 145.0,
        "pure_ethanol_g": 95.0,
        "est_bac_promille": 1.45,
        "verified": True,
        "snack": "heavy",
        "disciplines": "Ёрш-Биатлон"
    }
    saved = database.save_or_update_athlete(data)
    assert saved["id"] is not None
    assert saved["verified"] is True
    assert "first_sip" in saved["achievements"]
    assert "detector_passed" in saved["achievements"]
    assert "kms_rank" in saved["achievements"]

    # Проверка извлечения
    loaded = database.get_athlete(tg_user_id=12345678)
    assert loaded is not None
    assert loaded["name"] == "Алексей Стаканов"
    assert loaded["score"] == 145.0

def test_athlete_update_preserves_best_score_and_unions_achievements():
    """Тест: повторная сдача норматива обновляет ачивки и сохраняет максимальный балл"""
    user_id = 998877
    first_data = {
        "tg_user_id": user_id,
        "name": "Петр",
        "score": 100.0,
        "rank": {"id": "adult_1", "title": "1-й Взрослый разряд"},
        "achievements": ["first_sip"]
    }
    database.save_or_update_athlete(first_data)

    # Вторая сдача с меньшим баллом, но новым званием МС
    second_data = {
        "tg_user_id": user_id,
        "name": "Петр",
        "score": 85.0,
        "rank": {"id": "ms", "title": "Мастер Спорта"},
        "verified": True
    }
    res = database.save_or_update_athlete(second_data)
    
    # Максимальный счет сохранился (100.0)
    athlete = database.get_athlete(tg_user_id=user_id)
    assert athlete["score"] == 100.0
    # Ачивки объединились (first_sip + detector_passed + ms_legend)
    achievements = set(athlete["achievements"])
    assert "first_sip" in achievements
    assert "ms_legend" in achievements

def test_leaderboard_sorting():
    """Тест правильной сортировки Зала Славы по убыванию очков"""
    database.save_or_update_athlete({"tg_user_id": 1, "name": "Бронзовый", "score": 50})
    database.save_or_update_athlete({"tg_user_id": 2, "name": "Золотой", "score": 250})
    database.save_or_update_athlete({"tg_user_id": 3, "name": "Серебряный", "score": 150})

    top = database.get_leaderboard(limit=10)
    assert len(top) == 3
    assert top[0]["name"] == "Золотой"
    assert top[1]["name"] == "Серебряный"
    assert top[2]["name"] == "Бронзовый"

def test_chat_group_drink_tracking():
    """Тест учета напитков в групповом чате"""
    chat_id = -100123456789
    database.track_or_update_chat(chat_id=chat_id, title="Флудилка Литрбола", member_count=15)

    # Первый подход
    database.record_chat_drink(
        chat_id=chat_id,
        tg_user_id=111,
        user_name="Иван",
        drink_name="Пиво IPA",
        volume_ml=500,
        abv=6.0
    )
    # Второй подход
    database.record_chat_drink(
        chat_id=chat_id,
        tg_user_id=222,
        user_name="Олег",
        drink_name="Водка",
        volume_ml=100,
        abv=40.0
    )

    stats = database.get_chat_stats(chat_id)
    assert stats["drinks_count"] == 2
    assert stats["active_athletes_count"] == 2
    assert stats["total_ethanol_g"] > 0

def test_party_room_complete_workflow():
    """Тест полного жизненного цикла комнаты Застольной Зарубы"""
    creator_id = 555
    room = database.create_party_room(creator_id=creator_id, creator_name="Капитан Застолья", title="Битва Титанов")
    room_id = room["room_id"]
    assert room_id is not None
    assert room["status"] == "waiting"

    # Второй участник заходит в комнату
    database.join_party_room(room_id, tg_user_id=777, user_name="Второй Боец")

    # Участники подтверждают готовность
    database.toggle_party_ready(room_id, tg_user_id=creator_id)
    database.toggle_party_ready(room_id, tg_user_id=777)

    # Старт вечеринки
    started = database.start_party_room(room_id, host_id=creator_id)
    assert started["status"] == "active"

    # Добавляем напитки
    database.add_party_drink(room_id, tg_user_id=creator_id, drink_name="Пиво", volume_ml=500, abv=5.0)
    database.add_party_drink(room_id, tg_user_id=777, drink_name="Коньяк", volume_ml=150, abv=40.0)

    # Капитан подтверждает явку на финальной перекличке («Я в строю!»), а второй участник заснул
    database.confirm_party_alive(room_id, tg_user_id=creator_id)

    # Завершение баттла
    finished = database.finish_party_room(room_id)
    assert finished["status"] == "finished"

    # Проверка итогового состояния
    state = database.get_party_room_state(room_id)
    participants = state["participants"]
    
    # Капитан в строю и победил
    captain = next(p for p in participants if p["tg_user_id"] == creator_id)
    assert captain["confirmed_alive"] == 1
    assert captain["status"] == "winner"
    assert state["winner_name"] == "Капитан Застолья"

    # Второй боец не подтвердил и получил статус нокаута
    second = next(p for p in participants if p["tg_user_id"] == 777)
    assert second["confirmed_alive"] == 0
    assert second["status"] == "knocked_out"
