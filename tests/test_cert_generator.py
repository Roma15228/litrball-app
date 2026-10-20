import io
import pytest
from PIL import Image
from cert_generator import generate_certificate_image

def test_generate_certificate_image_valid_png():
    """Тест генерации корочки: возвращает валидный PNG 1200x800"""
    img_bytes = generate_certificate_image(
        name="Сергей Наливашкин",
        rank_title="Заслуженный Мастер Спорта (ЗМС)",
        weight=85.0,
        discipline="Двоеборье «Ёрш-Биатлон»",
        order_num="№ 77-ВАК/2026",
        pure_ethanol_g=180.0,
        est_bac=2.15
    )
    
    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 10000
    # Проверка магических байт PNG
    assert img_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    # Открытие через Pillow и проверка разрешения
    pil_img = Image.open(io.BytesIO(img_bytes))
    assert pil_img.size == (1200, 800)
    assert pil_img.format == "PNG"

def test_generate_certificate_with_custom_avatar():
    """Тест генерации удостоверения с аватаром пользователя"""
    # Создаем тестовую мини-картинку аватара
    avatar_io = io.BytesIO()
    sample_avatar = Image.new("RGB", (100, 100), color=(200, 50, 50))
    sample_avatar.save(avatar_io, format="PNG")
    avatar_bytes = avatar_io.getvalue()

    img_bytes = generate_certificate_image(
        name="Ольга Штопорова",
        rank_title="Мастер Спорта (МС)",
        user_avatar_bytes=avatar_bytes
    )
    
    assert img_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    pil_img = Image.open(io.BytesIO(img_bytes))
    assert pil_img.size == (1200, 800)

def test_generate_certificate_corrupted_avatar_fallback():
    """Тест отказоустойчивости: битые байты аватара не приводят к падению"""
    corrupted_bytes = b"NOT_AN_IMAGE_RANDOM_CORRUPTED_BYTES_123456"
    
    img_bytes = generate_certificate_image(
        name="Тестовый Сбойный Атлет",
        user_avatar_bytes=corrupted_bytes
    )
    
    # Генератор должен успешно обработать ошибку и нарисовать дефолтную рамку
    assert img_bytes[:8] == b"\x89PNG\r\n\x1a\n"
