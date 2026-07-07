from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


W, H = 1600, 900
OUT = Path(r"D:\download\Backend(Psycho2)\use_case_requirements_slide.png")
FONT = r"C:\Windows\Fonts\arial.ttf"
BOLD = r"C:\Windows\Fonts\arialbd.ttf"

img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

blue = "#3d3a91"
accent = "#335CFF"
light_blue = "#eef2ff"
line = "#111111"
gray = "#6b7280"
soft = "#f7f8fb"

font_title = ImageFont.truetype(BOLD, 28)
font_label = ImageFont.truetype(FONT, 22)
font_small = ImageFont.truetype(FONT, 18)
font_uc = ImageFont.truetype(FONT, 20)
font_uc_bold = ImageFont.truetype(BOLD, 20)
font_actor = ImageFont.truetype(FONT, 20)


def text_size(text, font):
    bbox = d.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if text_size(candidate, font)[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def centered_text(box, text, font, fill=line, max_width=None, line_gap=4):
    x1, y1, x2, y2 = box
    width = x2 - x1
    if max_width is None:
        max_width = width - 24
    lines = wrap_text(text, font, max_width)
    heights = [text_size(item, font)[1] for item in lines]
    total_h = sum(heights) + line_gap * (len(lines) - 1)
    y = y1 + (y2 - y1 - total_h) / 2 - 1
    for item, height in zip(lines, heights):
        tw, _ = text_size(item, font)
        d.text((x1 + (width - tw) / 2, y), item, font=font, fill=fill)
        y += height + line_gap


def ellipse(cx, cy, w, h, text, fill="white", outline=line, width=2, font=font_uc):
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    d.ellipse(box, fill=fill, outline=outline, width=width)
    centered_text(box, text, font, max_width=w - 28)
    return box


def rect(x1, y1, x2, y2, text, fill="white", outline=line, width=2, font=font_uc):
    d.rounded_rectangle((x1, y1, x2, y2), radius=14, fill=fill, outline=outline, width=width)
    centered_text((x1, y1, x2, y2), text, font, max_width=x2 - x1 - 20)
    return (x1, y1, x2, y2)


def actor(cx, cy, label):
    d.ellipse((cx - 14, cy - 48, cx + 14, cy - 20), outline=line, width=2, fill="white")
    d.line((cx, cy - 20, cx, cy + 28), fill=line, width=2)
    d.line((cx - 34, cy - 2, cx + 34, cy - 2), fill=line, width=2)
    d.line((cx, cy + 28, cx - 28, cy + 66), fill=line, width=2)
    d.line((cx, cy + 28, cx + 28, cy + 66), fill=line, width=2)
    lines = wrap_text(label, font_actor, 170)
    y = cy + 76
    for item in lines:
        tw, th = text_size(item, font_actor)
        d.text((cx - tw / 2, y), item, font=font_actor, fill=line)
        y += th + 3


def line_between(p1, p2, dashed=False, arrow=False, fill=line, width=2):
    x1, y1 = p1
    x2, y2 = p2
    if dashed:
        dash = 12
        gap = 8
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        ux = dx / dist
        uy = dy / dist
        t = 0
        while t < dist:
            t2 = min(t + dash, dist)
            d.line((x1 + ux * t, y1 + uy * t, x1 + ux * t2, y1 + uy * t2), fill=fill, width=width)
            t += dash + gap
    else:
        d.line((x1, y1, x2, y2), fill=fill, width=width)

    if arrow:
        angle = math.atan2(y2 - y1, x2 - x1)
        size = 12
        a1 = angle + math.pi * 0.84
        a2 = angle - math.pi * 0.84
        p3 = (x2 + size * math.cos(a1), y2 + size * math.sin(a1))
        p4 = (x2 + size * math.cos(a2), y2 + size * math.sin(a2))
        d.polygon([(x2, y2), p3, p4], fill=fill)


def relation_label(text, x, y):
    tw, th = text_size(text, font_small)
    pad = 4
    d.rounded_rectangle(
        (x - tw / 2 - pad, y - th / 2 - pad, x + tw / 2 + pad, y + th / 2 + pad),
        radius=5,
        fill="white",
    )
    d.text((x - tw / 2, y - th / 2), text, font=font_small, fill=gray)


d.text((60, 38), "Диаграмма прецедентов backend-приложения", font=font_title, fill=blue)

system = (210, 105, 1340, 820)
d.rounded_rectangle(system, radius=75, fill="white", outline=line, width=2)
d.text((275, 122), "Серверная часть программной системы «Одеяло»", font=font_label, fill=line)

actor(90, 310, "Сотрудник")
actor(1490, 210, "Администратор")
actor(1490, 405, "HR-специалист")
actor(1490, 605, "Корпоративный психолог")
rect(1368, 78, 1555, 145, "YooKassa", fill=soft, outline=line, font=font_uc_bold)
d.text((1398, 150), "внешний сервис", font=font_small, fill=gray)

uc_auth = ellipse(410, 230, 235, 86, "Авторизация / регистрация")
uc_tests = ellipse(410, 375, 235, 86, "Прохождение психологических тестов")
uc_ex = ellipse(410, 525, 235, 86, "Прохождение терапевтических упражнений")
uc_train = ellipse(410, 680, 235, 86, "Прохождение обучающих упражнений")

uc_sub = ellipse(720, 230, 235, 86, "Оформление подписки")
uc_risk = ellipse(720, 375, 250, 86, "Расчет риска выгорания", fill=light_blue, outline=accent)
uc_score = ellipse(720, 605, 235, 86, "Начисление баллов геймификации", fill=light_blue, outline=accent)
uc_pay = ellipse(1040, 230, 235, 86, "Оплата через YooKassa", fill=light_blue, outline=accent)
uc_analysis = ellipse(780, 505, 250, 86, "Анализ активности и результатов")

uc_content = ellipse(1070, 435, 250, 86, "Управление контентом")
uc_info = ellipse(1070, 575, 250, 86, "Получение служебной информации")
uc_export = ellipse(1070, 710, 250, 86, "Экспорт данных")

# Associations: employee
line_between((124, 310), (292, 230))
line_between((124, 310), (292, 375))
line_between((124, 310), (292, 525))
line_between((124, 310), (292, 680))
line_between((124, 310), (602, 230))

# Associations: external service
line_between((1368, 112), (1158, 230), dashed=True)

# Associations: organization roles
line_between((1456, 210), (1195, 435))
line_between((1456, 210), (1195, 575))
line_between((1456, 405), (1195, 575))
line_between((1456, 405), (1195, 710))
line_between((1456, 605), (1195, 575))
line_between((1456, 605), (910, 505))
line_between((1456, 605), (1195, 435))

# Include and extend relationships
line_between((528, 375), (595, 375), dashed=True, arrow=True, fill=gray)
relation_label("<<include>>", 562, 355)
line_between((838, 230), (922, 230), dashed=True, arrow=True, fill=gray)
relation_label("<<include>>", 880, 210)
line_between((528, 525), (610, 590), dashed=True, arrow=True, fill=gray)
relation_label("<<include>>", 575, 545)
line_between((528, 680), (610, 625), dashed=True, arrow=True, fill=gray)
relation_label("<<include>>", 575, 665)
line_between((1070, 667), (1070, 618), dashed=True, arrow=True, fill=gray)
relation_label("<<extend>>", 1135, 645)

note = (
    "На слайде показаны основные роли и функциональные требования; "
    "технические детали реализации вынесены на следующие слайды."
)
d.rounded_rectangle((250, 835, 1340, 875), radius=10, fill=soft, outline="#d1d5db")
d.text((270, 845), note, font=font_small, fill=gray)

img.save(OUT)
print(OUT)
