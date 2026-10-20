import pytest
import database

def test_export_chat_infographics_empty_chat():
    """Тест: пустой чат без подходов к снаряду возвращает None и корректное предупреждение"""
    res = database.export_chat_infographics_data(chat_id=-9999999)
    assert res is None

    warning_text = database.format_chat_infographic_text(None)
    assert "не может быть сформирован" in warning_text

def test_export_chat_infographics_data_and_formatting():
    """Тест сбора данных инфографики и рендеринга официального протокола ВФЛ"""
    chat_id = -100777888999
    database.track_or_update_chat(chat_id=chat_id, title="Кубок Застольных Мастеров", member_count=20)

    # Записываем подходы атлетов
    # 1. Иван: 2 раза пиво IPA
    database.record_chat_drink(chat_id, tg_user_id=1, user_name="Иван Грозный", username="ivan_king", drink_name="Крафтовое IPA", volume_ml=500, abv=6.8)
    database.record_chat_drink(chat_id, tg_user_id=1, user_name="Иван Грозный", username="ivan_king", drink_name="Крафтовое IPA", volume_ml=500, abv=6.8)

    # 2. Петр: 1 раз Абсент
    database.record_chat_drink(chat_id, tg_user_id=2, user_name="Петр Великий", username="petr1", drink_name="Абсент ритуальный", volume_ml=50, abv=70.0)

    # 3. Денис: 1 раз пиво
    database.record_chat_drink(chat_id, tg_user_id=3, user_name="Денис Скромный", username=None, drink_name="Крафтовое IPA", volume_ml=500, abv=6.8)

    # 4. Олег: 1 стопка водки
    database.record_chat_drink(chat_id, tg_user_id=4, user_name="Олег Бывалый", username="oleg_pro", drink_name="Стопка водки", volume_ml=50, abv=40.0)

    data = database.export_chat_infographics_data(chat_id)
    assert data is not None
    assert data["title"] == "Кубок Застольных Мастеров"
    assert data["drinks_count"] == 5
    assert data["active_athletes_count"] == 4
    assert data["total_ethanol_g"] > 100.0
    assert data["vodka_bottles"] > 0
    assert data["beer_crates"] >= 0

    # Самый популярный напиток — Крафтовое IPA (3 подхода)
    fav = data["favorite_drink"]
    assert fav is not None
    assert fav["name"] == "Крафтовое IPA"
    assert fav["count"] == 3

    # Проверка текстового форматирования инфографики
    text = database.format_chat_infographic_text(data)
    assert "ВФЛ: ОФИЦИАЛЬНЫЙ ПРОТОКОЛ ЗАСТОЛЬЯ" in text
    assert "Кубок Застольных Мастеров" in text
    assert "🥇" in text
    assert "🥈" in text
    assert "🥉" in text
    assert "Иван Грозный" in text
    assert "@ivan_king" in text
    assert "Петр Великий" in text
    assert "Денис Скромный" in text
    assert "Крафтовое IPA" in text
    assert "ВАК ВФЛ" in text
