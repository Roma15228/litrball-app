"""
Всероссийская Федерация Литрбола (ВФЛ)
Модуль генерации официального Удостоверения на Python с помощью Pillow (PIL).
Используется как Telegram-ботом, так и backend API.
"""

import os
import io
import math
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def generate_certificate_image(
    name: str = "Иван Атлетов",
    rank_title: str = "Мастер Спорта по Литрболу (МС)",
    weight: float = 80.0,
    discipline: str = "Академическое застольное многоборье",
    order_num: str = "№ 40-ОПОХМЕЛ/2026",
    pure_ethanol_g: float = 120.0,
    est_bac: float = 1.25,
    user_avatar_bytes: bytes = None
) -> bytes:
    """
    Генерирует официальное удостоверение спортсмена в разрешении 1200x800 px.
    Возвращает байты PNG.
    """
    W, H = 1200, 800
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Фоновая текстура корочки (темно-бордовый сафьян)
    # Имитация кожаного градиента
    for y in range(H):
        factor = y / H
        r = int(74 + factor * 20 - (y % 4) * 2)
        g = int(14 + factor * 6 - (y % 3) * 1)
        b = int(23 + factor * 8 - (y % 4) * 1)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # Золотая рамка по периметру корочки
    gold_border = (229, 169, 59, 255)
    draw.rounded_rectangle([16, 16, W - 16, H - 16], radius=20, outline=gold_border, width=4)
    draw.rounded_rectangle([22, 22, W - 22, H - 22], radius=16, outline=(180, 83, 9, 180), width=1)

    # Сгиб книги по центру
    fold_x = W // 2
    for offset in range(-12, 13):
        alpha = int(180 * (1 - abs(offset) / 12))
        draw.line([(fold_x + offset, 24), (fold_x + offset, H - 24)], fill=(0, 0, 0, alpha))

    # Внутренние бежево-гербовые страницы
    page_w = fold_x - 45
    page_h = H - 60
    
    # Левая страница
    draw_page_bg(draw, 30, 30, page_w, page_h)
    # Правая страница
    draw_page_bg(draw, fold_x + 15, 30, page_w, page_h)

    # Попытка загрузить системные шрифты, иначе дефолтные
    font_large = get_font(32, bold=True)
    font_title = get_font(22, bold=True)
    font_subtitle = get_font(15, bold=True)
    font_body = get_font(14)
    font_bold = get_font(16, bold=True)
    font_stamp = get_font(11, bold=True)
    font_micro = get_font(10)

    # ==========================================
    # ЛЕВАЯ СТРАНИЦА: Герб и титул
    # ==========================================
    left_cx = 30 + page_w // 2

    # Герб ФЛР
    draw_emblem(draw, left_cx, 210)

    draw.text((left_cx, 360), "ВСЕРОССИЙСКАЯ ФЕДЕРАЦИЯ ЛИТРБОЛА", fill=(30, 30, 36), font=font_title, anchor="mm")
    draw.text((left_cx, 395), "ВЫСШАЯ АТТЕСТАЦИОННАЯ КОМИССИЯ", fill=(139, 30, 45), font=font_subtitle, anchor="mm")

    draw.text((left_cx, 470), "УДОСТОВЕРЕНИЕ", fill=(180, 83, 9), font=font_large, anchor="mm")
    draw.text((left_cx, 510), "СПОРТИВНОГО РАЗРЯДА", fill=(30, 30, 36), font=font_bold, anchor="mm")

    draw.text((left_cx, 570), f"Приказ {order_num}", fill=(75, 85, 99), font=font_body, anchor="mm")
    draw.text((left_cx, 600), "Действительно при наличии чувства юмора и закуски", fill=(107, 114, 128), font=font_micro, anchor="mm")

    # ==========================================
    # ПРАВАЯ СТРАНИЦА: Спортсмен, разряд, печать
    # ==========================================
    right_x = fold_x + 35
    right_cx = fold_x + 15 + page_w // 2

    draw.text((right_cx, 65), "ЕДИНАЯ ЗАСТОЛЬНАЯ СПОРТИВНАЯ КЛАССИФИКАЦИЯ (ЕЗСК)", fill=(30, 30, 36), font=font_subtitle, anchor="mm")

    # Фото спортсмена (или аватар)
    photo_x = right_x + 10
    photo_y = 100
    photo_w, photo_h = 140, 180

    if user_avatar_bytes:
        try:
            user_img = Image.open(io.BytesIO(user_avatar_bytes)).convert("RGBA")
            user_img = user_img.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
            img.paste(user_img, (photo_x, photo_y))
            draw = ImageDraw.Draw(img) # пересоздаем draw после paste
        except Exception:
            draw_default_photo(draw, photo_x, photo_y, photo_w, photo_h)
    else:
        draw_default_photo(draw, photo_x, photo_y, photo_w, photo_h)

    # Рамка фото
    draw.rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], outline=(156, 163, 175), width=2)

    # Текстовые данные справа от фото
    info_x = photo_x + photo_w + 25
    draw.text((info_x, 110), "ФАМИЛИЯ, ИМЯ АТЛЕТА:", fill=(107, 114, 128), font=font_micro)
    draw.text((info_x, 130), name[:22], fill=(17, 24, 39), font=font_title)

    weight_cat = get_weight_category(weight)
    draw.text((info_x, 175), "ВЕСОВАЯ КАТЕГОРИЯ:", fill=(107, 114, 128), font=font_micro)
    draw.text((info_x, 195), f"{weight} кг ({weight_cat})", fill=(17, 24, 39), font=font_bold)

    draw.text((info_x, 235), "КОРОННАЯ ДИСЦИПЛИНА:", fill=(107, 114, 128), font=font_micro)
    draw.text((info_x, 255), discipline[:32], fill=(139, 30, 45), font=font_bold)

    # Золотая плашка разряда
    rank_box_y = 310
    rank_box_w = page_w - 40
    draw.rounded_rectangle([right_x + 10, rank_box_y, right_x + 10 + rank_box_w, rank_box_y + 65], radius=10, fill=(254, 243, 199), outline=(217, 119, 6), width=2)

    draw.text((right_cx, rank_box_y + 18), "ПРИСВОЕНО СПОРТИВНОЕ ЗВАНИЕ / РАЗРЯД:", fill=(120, 53, 15), font=font_micro, anchor="mm")
    draw.text((right_cx, rank_box_y + 45), rank_title, fill=(153, 27, 27), font=font_title, anchor="mm")

    # Метрики выступления
    if pure_ethanol_g > 0:
        draw.text((right_x + 15, 395), f"Чистый этанол: {pure_ethanol_g:.1f} г   •   Промилле: ~{est_bac:.2f} ‰", fill=(75, 85, 99), font=font_body)

    # Подписи
    sig_y = 540
    draw.text((right_x + 15, sig_y), "Председатель ВАК:", fill=(17, 24, 39), font=font_body)
    draw.text((right_x + 160, sig_y), "С. Г. Наливашкин", fill=(30, 58, 138), font=font_bold)
    draw.line([(right_x + 150, sig_y + 20), (right_x + 300, sig_y + 20)], fill=(75, 85, 99), width=1)

    draw.text((right_x + 15, sig_y + 40), "Секретарь комиссии:", fill=(17, 24, 39), font=font_body)
    draw.text((right_x + 160, sig_y + 40), "О. П. Опохмелова", fill=(30, 58, 138), font=font_bold)
    draw.line([(right_x + 150, sig_y + 60), (right_x + 300, sig_y + 60)], fill=(75, 85, 99), width=1)

    # Синяя гербовая печать
    draw_stamp(draw, right_x + 330, sig_y + 15)

    # Защитный псевдо QR-код
    draw_qr(draw, right_x + rank_box_w - 70, sig_y - 15, 65)

    # Сохраняем в байты
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()

def draw_page_bg(draw, x, y, w, h):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=(252, 250, 242))
    draw.rounded_rectangle([x + 6, y + 6, x + w - 6, y + h - 6], radius=8, outline=(212, 175, 55), width=2)
    draw.rounded_rectangle([x + 10, y + 10, x + w - 10, y + h - 10], radius=6, outline=(232, 223, 200), width=1)

def draw_emblem(draw, cx, cy):
    # Лавровый венок
    draw.ellipse([cx - 65, cy - 65, cx + 65, cy + 65], fill=(254, 243, 199), outline=(217, 119, 6), width=3)
    # Скрещенные штопоры
    draw.line([(cx - 35, cy - 35), (cx + 35, cy + 35)], fill=(180, 83, 9), width=4)
    draw.line([(cx + 35, cy - 35), (cx - 35, cy + 35)], fill=(180, 83, 9), width=4)
    # Граненый стакан
    draw.polygon([(cx - 20, cy - 25), (cx + 20, cy - 25), (cx + 15, cy + 30), (cx - 15, cy + 30)], fill=(37, 99, 235), outline=(29, 78, 216))
    # Звезда
    draw.regular_polygon((cx, cy - 50, 12), 5, fill=(217, 119, 6))

def draw_default_photo(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(203, 213, 225))
    cx = x + w // 2
    cy = y + h // 2
    draw.ellipse([cx - 35, cy - 45, cx + 35, cy + 25], fill=(244, 114, 182)) # лицо
    draw.ellipse([cx - 40, cy - 50, cx + 40, cy - 15], fill=(30, 41, 59))  # шапка
    draw.ellipse([cx - 55, cy + 20, cx + 55, cy + 120], fill=(71, 85, 105)) # плечи

def draw_stamp(draw, cx, cy):
    r = 50
    # Два синих кольца печати
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(30, 58, 138, 200), width=3)
    draw.ellipse([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6], outline=(30, 58, 138, 180), width=1)
    # Текст внутри
    font = get_font(10, bold=True)
    draw.text((cx, cy - 28), "★ ФЛР РОССИИ ★", fill=(30, 58, 138), font=font, anchor="mm")
    draw.text((cx, cy - 8), "ДЛЯ", fill=(30, 58, 138), font=font, anchor="mm")
    draw.text((cx, cy + 8), "ДОКУМЕНТОВ", fill=(30, 58, 138), font=font, anchor="mm")
    draw.text((cx, cy + 26), "АТТЕСТОВАНО ВАК", fill=(30, 58, 138), font=font, anchor="mm")

def draw_qr(draw, x, y, size):
    draw.rectangle([x, y, x + size, y + size], fill=(255, 255, 255), outline=(31, 41, 55))
    step = size // 5
    # Маркеры по углам
    draw.rectangle([x + 3, y + 3, x + step * 2, y + step * 2], fill=(17, 24, 39))
    draw.rectangle([x + size - step * 2, y + 3, x + size - 3, y + step * 2], fill=(17, 24, 39))
    draw.rectangle([x + 3, y + size - step * 2, x + step * 2, y + size - 3], fill=(17, 24, 39))
    draw.rectangle([x + step * 2, y + step * 2, x + step * 3, y + step * 3], fill=(17, 24, 39))

def get_weight_category(w: float) -> str:
    if w < 65: return "Полулегкий вес"
    if w < 80: return "Средний вес"
    if w < 100: return "Полутяжелый вес"
    return "Супертяжелый вес (Танк)"

def get_font(size: int, bold: bool = False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_fonts = [
        os.path.join(base_dir, "static", "fonts", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        os.path.join(base_dir, "fonts", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    ]
    # Пытаемся найти локальные или системные ttf шрифты в Linux
    candidates = local_fonts + [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/google-noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/liberation/LiberationSans-Regular.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

