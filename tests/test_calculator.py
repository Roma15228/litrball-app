import pytest
from app import calculate_score, suggest_disciplines, RANKS

def test_calculate_score_pure_ethanol_single_beer():
    """Тест расчета чистой массы этанола для 1 пива 500мл 5%"""
    data = {
        "weight": 75,
        "gender": "m",
        "drinks": [
            {"name": "Пиво светлое", "volume_ml": 500, "abv": 5.0, "count": 1}
        ],
        "hours": 1.0,
        "snack": "medium"
    }
    res = calculate_score(data)
    # Масса спирта = 500 * 0.05 * 0.789 = 19.725 г -> 19.7 г
    assert res["pure_ethanol_g"] == pytest.approx(19.7, abs=0.1)
    assert res["score"] > 0
    assert "№ " in res["order_num"]
    assert "/ФЛР-" in res["order_num"]

def test_calculate_score_widmark_bac_gender_difference():
    """Тест редукции Видмарка: у женщин при одинаковом весе промилле выше"""
    male_data = {
        "weight": 70,
        "gender": "m",
        "drinks": [{"name": "Водка", "volume_ml": 100, "abv": 40.0, "count": 1}],
        "hours": 0.5
    }
    female_data = {
        "weight": 70,
        "gender": "f",
        "drinks": [{"name": "Водка", "volume_ml": 100, "abv": 40.0, "count": 1}],
        "hours": 0.5
    }
    res_m = calculate_score(male_data)
    res_f = calculate_score(female_data)
    # Фактор r у женщин 0.55 против 0.68 у мужчин, следовательно est_bac_promille у женщин выше
    assert res_f["est_bac_promille"] > res_m["est_bac_promille"]

def test_calculate_score_snack_multiplier():
    """Тест влияния закуски: натощак ('empty') дает бонус очков за сложность"""
    base_data = {
        "weight": 75,
        "gender": "m",
        "drinks": [{"name": "Пиво", "volume_ml": 1000, "abv": 5.0, "count": 1}],
        "hours": 2.0
    }
    res_empty = calculate_score({**base_data, "snack": "empty"})
    res_heavy = calculate_score({**base_data, "snack": "heavy"})
    
    # Empty (1.35x) против Heavy (0.85x)
    assert res_empty["score"] > res_heavy["score"]

def test_calculate_score_penalties_and_vomit_downgrade():
    """Тест штрафов: рвота снижает разряд до юношеского и списывает 150 очков"""
    heavy_drinking = {
        "weight": 80,
        "gender": "m",
        "experience": "veteran",
        "drinks": [
            {"name": "Водка", "volume_ml": 500, "abv": 40.0, "count": 1}
        ],
        "hours": 2.0,
        "penalties": {
            "vomited": True,
            "called_ex": True,
            "lost_items": True,
            "fell_asleep": True
        }
    }
    res = calculate_score(heavy_drinking)
    
    # Все штрафные заметки зафиксированы
    assert len(res["penalty_notes"]) == 4
    # Разряд принудительно понижен до 2-го юношеского при визите к Ихтиандру
    assert res["rank"]["id"] in ["junior_3", "junior_2"]

def test_suggest_disciplines():
    """Тест определения коронной дисциплины застолья"""
    # 1. Биатлон (пиво + водка)
    d1 = suggest_disciplines([
        {"name": "Пиво Светлое", "abv": 4.5},
        {"name": "Водка Столичная", "abv": 40.0}
    ], hours=2)
    assert "Ёрш-Биатлон" in d1

    # 2. Марафон (hours >= 5)
    d2 = suggest_disciplines([{"name": "Вино", "abv": 12.0}], hours=6)
    assert "марафон" in d2.lower()

    # 3. Спринт по шотам (hours <= 1, abv >= 35)
    d3 = suggest_disciplines([{"name": "Текила", "abv": 38.0}], hours=0.8)
    assert "спринт по шотам" in d3.lower()

    # 4. Пенный слалом
    d4 = suggest_disciplines([{"name": "Крафтовый лагер", "abv": 5.0}], hours=2)
    assert "пенный слалом" in d4.lower()
