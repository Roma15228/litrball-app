import pytest
from app import DRINK_PRESETS, calculate_score, suggest_disciplines

def test_drink_presets_structure_and_values():
    """Тест валидности структуры и диапазонов параметров библиотеки напитков ВФЛ"""
    assert len(DRINK_PRESETS) >= 15
    
    preset_ids = {p["id"] for p in DRINK_PRESETS}
    required_ids = {
        "beer_light", "beer_ipa", "cider", "wine_glass", "sparkling",
        "vodka_shot", "whiskey", "tequila_shot", "nastoyka",
        "cocktail_ersh", "cocktail_severnoe", "cocktail_tequila_boom",
        "cocktail_gin_tonic", "shot_boyarsky", "extreme_absinthe"
    }
    assert required_ids.issubset(preset_ids), f"Отсутствуют обязательные пресеты: {required_ids - preset_ids}"

    for preset in DRINK_PRESETS:
        assert preset["volume_ml"] > 0
        assert 0 < preset["abv"] <= 100
        assert len(preset["icon"]) > 0
        assert len(preset["name"]) > 0
        assert preset["category"] in ["beer", "wine", "spirits", "cocktails", "shots", "extreme"]

def test_extreme_and_cocktail_ethanol_calculation():
    """Тест точного расчета чистого спирта для экстремальных шотов и коктейлей"""
    # 1. Абсент ритуальный: 50 мл * 70% ABV * 0.789 плотность = 27.6 г
    absinthe_data = {
        "weight": 80,
        "gender": "m",
        "drinks": [{"name": "Абсент ритуальный", "volume_ml": 50, "abv": 70.0, "count": 1}],
        "hours": 1.0
    }
    res_absinthe = calculate_score(absinthe_data)
    assert res_absinthe["pure_ethanol_g"] == pytest.approx(27.6, abs=0.2)

    # 2. Шот «Боярский»: 50 мл * 32% ABV * 0.789 плотность = 12.6 г
    boyarsky_data = {
        "weight": 80,
        "gender": "m",
        "drinks": [{"name": "Шот «Боярский»", "volume_ml": 50, "abv": 32.0, "count": 1}],
        "hours": 1.0
    }
    res_boyarsky = calculate_score(boyarsky_data)
    assert res_boyarsky["pure_ethanol_g"] == pytest.approx(12.6, abs=0.2)

    # 3. «Северное сияние»: 200 мл * 22% ABV * 0.789 = 34.7 г
    severnoe_data = {
        "weight": 80,
        "gender": "m",
        "drinks": [{"name": "«Северное сияние»", "volume_ml": 200, "abv": 22.0, "count": 1}],
        "hours": 1.0
    }
    res_severnoe = calculate_score(severnoe_data)
    assert res_severnoe["pure_ethanol_g"] == pytest.approx(34.7, abs=0.2)

def test_legendary_cocktail_disciplines():
    """Тест присвоения уникальных дисциплин под легендарные напитки"""
    # Абсент
    disc_absinthe = suggest_disciplines([{"name": "Абсент", "abv": 70.0}], hours=1.0)
    assert "Абсент" in disc_absinthe

    # Северное сияние
    disc_severnoe = suggest_disciplines([{"name": "Коктейль Северное сияние", "abv": 22.0}], hours=2.0)
    assert "Северное сияние" in disc_severnoe

    # Боярский
    disc_boyarsky = suggest_disciplines([{"name": "Шот Боярский", "abv": 32.0}], hours=0.5)
    assert "Тысяча чертей" in disc_boyarsky
