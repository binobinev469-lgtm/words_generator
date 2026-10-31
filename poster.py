#!/usr/bin/env python3
"""Typographic word posters.

Turns a topic into a portrait poster: one huge title, then the words
that belong to it, set like a gallery print.

Examples
--------
python poster.py
python poster.py ocean
python poster.py coffee --style cream
python poster.py "night shift" --words lamp,quiet,radio,window,ink,street
python poster.py --list
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1800
HEIGHT = 2400

# Built-in topics. Each list is the vocabulary that fills the poster.
# The topic itself is always the title, so it is not repeated here.
TOPICS: dict[str, list[str]] = {
    "ocean": [
        "tide", "salt", "horizon", "current", "foam", "depth", "harbor",
        "gull", "swell", "anchor", "reef", "pearl", "storm", "drift",
        "compass", "wave", "brine", "keel", "cove", "shell", "moonlight",
        "sailor", "abyss", "spray", "coral", "lagoon", "blue", "wind",
        "chart", "rope", "dusk", "island", "calm", "mariner",
    ],
    "forest": [
        "moss", "canopy", "fern", "trail", "cedar", "shade", "brook",
        "root", "mist", "owl", "bark", "glen", "pine", "thicket",
        "fox", "lichen", "path", "grove", "amber", "needle", "quiet",
        "deer", "hollow", "rain", "branch", "soil", "dusk", "wild",
    ],
    "city": [
        "neon", "subway", "crowd", "stoop", "alley", "taxi", "roof",
        "siren", "block", "window", "steam", "crosswalk", "night",
        "vendor", "bridge", "lamp", "rush", "concrete", "skyline",
        "metro", "rain", "corner", "glass", "traffic", "dawn",
    ],
    "coffee": [
        "steam", "crema", "bitter", "cup", "morning", "roast", "saucer",
        "aroma", "milk", "grind", "warmth", "bean", "spoon", "ritual",
        "dark", "pour", "cocoa", "quiet", "kitchen", "ceramic", "amber",
        "sip", "hour", "bloom",
    ],
    "space": [
        "orbit", "void", "comet", "star", "silent", "nebula", "dust",
        "moon", "gravity", "flare", "apollo", "dark", "satellite",
        "light", "year", "cosmos", "ring", "pulsar", "horizon", "cold",
        "voyage", "eclipse", "silver", "infinite",
    ],
    "music": [
        "chord", "rhythm", "brass", "echo", "verse", "tempo", "vinyl",
        "chorus", "bass", "melody", "stage", "hum", "minor", "drum",
        "solo", "harmony", "night", "reed", "waltz", "amp", "silence",
        "note", "groove", "encore",
    ],
    "winter": [
        "frost", "hearth", "snow", "wool", "breath", "quiet", "ice",
        "window", "pine", "ember", "coat", "pale", "road", "glove",
        "still", "lantern", "silver", "dusk", "chimney", "crystal",
        "north", "blanket", "thaw",
    ],
    "garden": [
        "bloom", "soil", "petal", "thorn", "bee", "vine", "shade",
        "seed", "iris", "dew", "herb", "gravel", "rose", "noon",
        "stem", "moss", "lavender", "gate", "yellow", "shears",
        "fruit", "path", "summer",
    ],
    "mountain": [
        "ridge", "stone", "alpine", "wind", "pass", "snow", "cliff",
        "echo", "goat", "thin", "air", "summit", "trail", "cloud",
        "granite", "camp", "cold", "valley", "switchback", "peak",
        "lichen", "dawn", "high",
    ],
    "night": [
        "lamp", "velvet", "owl", "hush", "moon", "window", "ink",
        "street", "shadow", "star", "radio", "late", "blue", "key",
        "quiet", "alley", "candle", "dream", "roof", "silver", "hour",
        "moth", "still",
    ],
    "rain": [
        "glass", "coat", "puddle", "grey", "umbrella", "drip", "street",
        "slick", "cloud", "gutter", "mist", "window", "silver", "roof",
        "storm", "wet", "lantern", "river", "quiet", "thunder", "leaf",
    ],
    "library": [
        "spine", "dust", "margin", "lamp", "quiet", "index", "page",
        "oak", "folio", "aisle", "ink", "whisper", "stack", "cloth",
        "chapter", "chair", "gold", "silence", "archive", "note",
        "evening", "paper", "shelf",
    ],
    "desert": [
        "dune", "heat", "ochre", "salt", "sun", "shadow", "camel",
        "wind", "mesa", "thorn", "mirage", "bone", "horizon", "dry",
        "canyon", "gold", "night", "stone", "vast", "star", "silence",
    ],
    "summer": [
        "heat", "peach", "noon", "salt", "field", "cicada", "linen",
        "river", "gold", "porch", "melon", "dust", "long", "light",
        "grass", "barefoot", "shade", "blue", "August", "window",
    ],
    "cinema": [
        "reel", "dark", "frame", "silver", "aisle", "cut", "score",
        "closeup", "noir", "title", "grain", "screen", "seat", "light",
        "scene", "shadow", "credits", "still", "lens", "night",
    ],
    "kitchen": [
        "steam", "knife", "bread", "salt", "copper", "herbs", "bowl",
        "heat", "lemon", "oil", "table", "garlic", "noon", "plate",
        "sugar", "pan", "wood", "supper", "cloth", "orange",
    ],
    "jazz": [
        "brass", "smoke", "blue", "solo", "night", "piano", "swing",
        "club", "reed", "late", "bass", "amber", "horn", "room",
        "improv", "velvet", "note", "city", "hush", "chorus",
    ],
}

STYLES: dict[str, dict] = {
    "cream": {
        "bg": (244, 236, 223),
        "ink": (28, 24, 20),
        "muted": (104, 82, 62),
        "accent": (166, 52, 36),
        "faint": (214, 198, 174),
        "grain": 11,
        "vignette": 26,
    },
    "press": {
        "bg": (248, 246, 241),
        "ink": (14, 14, 14),
        "muted": (68, 68, 66),
        "accent": (186, 28, 36),
        "faint": (226, 222, 214),
        "grain": 7,
        "vignette": 18,
    },
    "ink": {
        "bg": (17, 17, 20),
        "ink": (242, 236, 226),
        "muted": (168, 160, 148),
        "accent": (224, 164, 72),
        "faint": (42, 42, 48),
        "grain": 8,
        "vignette": 16,
    },
    "sea": {
        "bg": (12, 48, 58),
        "ink": (236, 244, 242),
        "muted": (150, 190, 186),
        "accent": (232, 186, 104),
        "faint": (24, 78, 92),
        "grain": 8,
        "vignette": 18,
    },
    "forest": {
        "bg": (24, 38, 28),
        "ink": (238, 232, 214),
        "muted": (164, 174, 140),
        "accent": (214, 168, 72),
        "faint": (40, 62, 46),
        "grain": 8,
        "vignette": 18,
    },
    "bloom": {
        "bg": (244, 226, 218),
        "ink": (58, 26, 34),
        "muted": (132, 78, 84),
        "accent": (148, 42, 58),
        "faint": (224, 196, 188),
        "grain": 10,
        "vignette": 22,
    },
}

TOPIC_STYLE = {
    "ocean": "sea",
    "forest": "forest",
    "garden": "bloom",
    "night": "ink",
    "space": "ink",
    "jazz": "ink",
    "cinema": "ink",
    "winter": "ink",
    "city": "ink",
    "desert": "cream",
    "coffee": "cream",
    "library": "cream",
    "summer": "cream",
    "kitchen": "cream",
    "rain": "sea",
    "mountain": "forest",
    "music": "press",
}

FONT_CANDIDATES = {
    "serif": [
        "/usr/share/fonts/truetype/msttcorefonts/Georgia.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
    "serif_bold": [
        "/usr/share/fonts/truetype/msttcorefonts/Georgia_Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ],
    "serif_italic": [
        "/usr/share/fonts/truetype/msttcorefonts/Georgia_Italic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
    ],
    "sans": [
        "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "sans_bold": [
        "/usr/share/fonts/truetype/msttcorefonts/arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "display": [
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "narrow": [
        "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
}


def load_fonts() -> dict[str, str]:
    found = {}
    missing = []
    for key, paths in FONT_CANDIDATES.items():
        path = next((p for p in paths if Path(p).is_file()), None)
        if path is None:
            missing.append(key)
        else:
            found[key] = path
    if missing:
        raise SystemExit(
            "Missing fonts for: " + ", ".join(missing) +
            ". Install a serif and a sans (DejaVu or Liberation is enough)."
        )
    return found


FONTS = load_fonts()
_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(key: str, size: int) -> ImageFont.FreeTypeFont:
    size = max(8, int(size))
    cache_key = (key, size)
    if cache_key not in _FONT_CACHE:
        _FONT_CACHE[cache_key] = ImageFont.truetype(FONTS[key], size)
    return _FONT_CACHE[cache_key]


def ink_box(text: str, face: ImageFont.FreeTypeFont, tracking: float = 0) -> tuple[int, int, int]:
    """Return width, top offset, bottom offset of the ink, origin at the pen."""
    if not text:
        return 0, 0, 0
    if tracking and len(text) > 1:
        width = 0
        top = 0
        bottom = 0
        for index, ch in enumerate(text):
            box = face.getbbox(ch)
            width += box[2] - box[0]
            if index < len(text) - 1:
                width += tracking
            top = min(top, box[1])
            bottom = max(bottom, box[3])
        return int(round(width)), top, bottom
    box = face.getbbox(text)
    return int(round(box[2] - box[0])), box[1], box[3]


def draw_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    face: ImageFont.FreeTypeFont,
    x: float,
    y_top: float,
    fill: tuple,
    tracking: float = 0,
    stroke: int = 0,
    stroke_fill: tuple | None = None,
) -> None:
    """Draw text so the top of the ink sits on y_top."""
    if tracking and len(text) > 1 and stroke == 0:
        top = min(face.getbbox(ch)[1] for ch in text)
        cursor = x
        for ch in text:
            box = face.getbbox(ch)
            draw.text((cursor - box[0], y_top - top), ch, font=face, fill=fill)
            cursor += (box[2] - box[0]) + tracking
        return
    box = face.getbbox(text)
    kwargs = {}
    if stroke:
        kwargs["stroke_width"] = stroke
        kwargs["stroke_fill"] = stroke_fill or fill
    draw.text((x - box[0], y_top - box[1]), text, font=face, fill=fill, **kwargs)


def fit_size(
    text: str,
    face_key: str,
    max_width: float,
    max_size: int,
    min_size: int = 18,
    tracking: float = 0,
) -> int:
    low, high = min_size, max_size
    best = min_size
    while low <= high:
        mid = (low + high) // 2
        width, _, _ = ink_box(text, font(face_key, mid), tracking)
        if width <= max_width:
            best = mid
            low = mid + 1
        else:
            high = mid - 1
    return best


def clean_word(raw: str) -> str:
    word = raw.strip().strip(".,;:!?\"'`")
    word = re.sub(r"\s+", " ", word)
    return word


def parse_word_list(raw: str) -> list[str]:
    parts = re.split(r"[,;\n]+", raw)
    words = []
    seen = set()
    for part in parts:
        word = clean_word(part)
        key = word.casefold()
        if word and key not in seen:
            seen.add(key)
            words.append(word)
    return words


def slug(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")
    return cleaned or "poster"


@dataclass
class Solo:
    text: str
    size: int
    face_key: str
    color_key: str
    align: str
    outline: bool
    index: int | None


@dataclass
class Band:
    words: list[str]
    size: int
    tracking: float


@dataclass
class ItalicLine:
    text: str
    size: int


Row = Solo | Band | ItalicLine


def prepare_words(topic: str, words: list[str], rng: random.Random) -> tuple[list[str], list[str], list[str]]:
    title_key = topic.casefold()
    pool = []
    seen = set()
    for word in words:
        cleaned = clean_word(word)
        key = cleaned.casefold()
        if not cleaned or key == title_key or key in seen:
            continue
        seen.add(key)
        pool.append(cleaned)
    rng.shuffle(pool)

    italics = [w for w in pool if 5 <= len(w) <= 11][:3]
    used = {w.casefold() for w in italics}
    rest = [w for w in pool if w.casefold() not in used]
    # Short words read best at the largest sizes.
    solos = sorted([w for w in rest if len(w) <= 12], key=len)[:7]
    used.update(w.casefold() for w in solos)
    bands = [w for w in rest if w.casefold() not in used]
    # If the topic came with only a few words, reuse nothing — just
    # promote band words into solos so the poster still has a hierarchy.
    if len(solos) < 3:
        extra = [w for w in bands if len(w) <= 14]
        need = 3 - len(solos)
        solos.extend(extra[:need])
        bands = bands[need:]
    return solos, italics, bands


def compose_rows(
    solos: list[str],
    italics: list[str],
    bands: list[str],
    content_width: int,
    scale: float,
) -> list[Row]:
    rows: list[Row] = []
    solo_sizes = [168, 118, 146, 92, 128, 78, 104]
    solo_faces = ["display", "serif_bold", "display", "serif_bold", "display", "narrow", "serif_bold"]
    solo_aligns = ["left", "right", "left", "right", "left", "right", "center"]
    band_index = 0
    italic_index = 0
    solo_n = 0
    pattern = ["solo", "band", "solo", "italic", "solo", "band"]

    def take_band() -> list[str] | None:
        nonlocal band_index
        if band_index >= len(bands):
            return None
        size = max(22, int(34 * scale))
        tracking = max(1.0, 2.2 * scale)
        face = font("narrow", size)
        sep = max(18, int(28 * scale))
        chosen = []
        width = 0
        while band_index < len(bands):
            word = bands[band_index].upper()
            word_width, _, _ = ink_box(word, face, tracking)
            extra = word_width if not chosen else sep + word_width
            if chosen and width + extra > content_width:
                break
            if not chosen and word_width > content_width:
                band_index += 1
                continue
            chosen.append(bands[band_index])
            width += extra
            band_index += 1
            if len(chosen) >= 6:
                break
        return chosen or None

    def append_solo(word: str, size_hint: float, face_key: str) -> None:
        nonlocal solo_n
        size = fit_size(word.upper(), face_key, content_width, max(46, int(size_hint)), min_size=36)
        rows.append(Solo(
            text=word,
            size=size,
            face_key=face_key,
            color_key="accent" if solo_n % 3 == 1 else "ink",
            align=solo_aligns[solo_n % len(solo_aligns)],
            outline=solo_n % 4 == 3,
            index=solo_n + 1,
        ))
        solo_n += 1

    def append_italic() -> bool:
        nonlocal italic_index
        if italic_index >= len(italics):
            return False
        word = italics[italic_index]
        italic_index += 1
        size = max(36, int(72 * scale))
        size = fit_size(word.lower(), "serif_italic", int(content_width * 0.8), size, min_size=32)
        rows.append(ItalicLine(text=word, size=size))
        return True

    step = 0
    while solos or band_index < len(bands) or italic_index < len(italics):
        kind = pattern[step % len(pattern)]
        step += 1
        if kind == "solo" and solos:
            word = solos.pop(0)
            hint = solo_sizes[min(solo_n, len(solo_sizes) - 1)] * scale
            append_solo(word, hint, solo_faces[solo_n % len(solo_faces)])
            continue
        if kind == "italic" and append_italic():
            continue
        if kind == "band":
            chosen = take_band()
            if chosen:
                rows.append(Band(
                    words=chosen,
                    size=max(22, int(34 * scale)),
                    tracking=max(1.0, 2.2 * scale),
                ))
                continue
        if solos:
            word = solos.pop(0)
            append_solo(word, 100 * scale, "serif_bold")
            continue
        chosen = take_band()
        if chosen:
            rows.append(Band(
                words=chosen,
                size=max(22, int(32 * scale)),
                tracking=max(1.0, 2.0 * scale),
            ))
            continue
        if append_italic():
            continue
        break
    return rows


def row_height(row: Row, palette: dict) -> int:
    if isinstance(row, Solo):
        face = font(row.face_key, row.size)
        _, top, bottom = ink_box(row.text.upper(), face)
        stroke = max(2, row.size // 26) if row.outline else 0
        index_h = int(row.size * 0.16) + 8 if row.index else 0
        return (bottom - top) + stroke * 2 + index_h
    if isinstance(row, ItalicLine):
        face = font("serif_italic", row.size)
        _, top, bottom = ink_box(row.text.lower(), face)
        return bottom - top
    face = font("narrow", row.size)
    _, top, bottom = ink_box("H", face, row.tracking)
    return bottom - top


def row_gap(row: Row, scale: float) -> int:
    if isinstance(row, Band):
        return max(16, int(26 * scale))
    if isinstance(row, ItalicLine):
        return max(14, int(22 * scale))
    return max(18, int(30 * scale))


def paint_background(palette: dict, seed: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), palette["bg"])
    array = np.asarray(image).astype(np.int16)
    rng = np.random.default_rng(seed)
    noise = rng.integers(-palette["grain"], palette["grain"] + 1, size=array.shape[:2], dtype=np.int16)
    array += noise[..., None]
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    dist = np.sqrt(((yy - HEIGHT / 2) / (HEIGHT * 0.75)) ** 2 + ((xx - WIDTH / 2) / (WIDTH * 0.75)) ** 2)
    shade = np.clip(dist - 0.45, 0, 1) ** 1.35
    array = array - (shade * palette["vignette"])[..., None]
    np.clip(array, 0, 255, out=array)
    return Image.fromarray(array.astype(np.uint8), "RGB")


def split_title(topic: str) -> list[str]:
    parts = [clean_word(p) for p in topic.split() if clean_word(p)]
    if len(parts) <= 2:
        return [p.upper() for p in parts] or [topic.upper()]
    best: tuple[int, list[str]] | None = None
    for cut in range(1, len(parts)):
        left = " ".join(parts[:cut]).upper()
        right = " ".join(parts[cut:]).upper()
        score = abs(len(left) - len(right))
        if best is None or score < best[0]:
            best = (score, [left, right])
    return best[1] if best else [topic.upper()]


def draw_tracked_label(
    draw: ImageDraw.ImageDraw,
    text: str,
    face: ImageFont.FreeTypeFont,
    x: float,
    y_top: float,
    fill: tuple,
    tracking: float,
    align_right_at: float | None = None,
) -> None:
    width, _, _ = ink_box(text, face, tracking)
    if align_right_at is not None:
        x = align_right_at - width
    draw_text(draw, text, face, x, y_top, fill, tracking=tracking)


def render(topic: str, words: list[str], palette: dict, seed: int) -> Image.Image:
    rng = random.Random(seed)
    image = paint_background(palette, seed)
    draw = ImageDraw.Draw(image)

    margin = 108
    content_left = margin
    content_right = WIDTH - margin
    content_width = content_right - content_left

    # Faint oversized title sitting behind the type.
    ghost_line = split_title(topic)[0]
    ghost_size = fit_size(ghost_line, "serif_bold", int(WIDTH * 1.05), 760, min_size=200)
    ghost_font = font("serif_bold", ghost_size)
    ghost_w, ghost_top, ghost_bottom = ink_box(ghost_line, ghost_font)
    ghost_x = (WIDTH - ghost_w) / 2
    ghost_y = HEIGHT * 0.56 - (ghost_bottom - ghost_top) / 2
    ghost_ink = tuple(
        int(palette["bg"][i] * 0.25 + palette["faint"][i] * 0.75) for i in range(3)
    )
    draw_text(draw, ghost_line, ghost_font, ghost_x, ghost_y - ghost_top, ghost_ink)

    inset = 46
    draw.rectangle([inset, inset, WIDTH - 1 - inset, HEIGHT - 1 - inset], outline=palette["ink"], width=3)
    draw.rectangle(
        [inset + 10, inset + 10, WIDTH - 1 - inset - 10, HEIGHT - 1 - inset - 10],
        outline=palette["ink"],
        width=1,
    )

    label = font("sans", 22)
    label_tracking = 4.0
    meta_top = 78
    draw_tracked_label(draw, "A WORD POSTER", label, content_left, meta_top, palette["muted"], label_tracking)
    draw_tracked_label(
        draw, topic.upper(), label, 0, meta_top, palette["accent"], label_tracking, align_right_at=content_right,
    )

    rule_y = 128
    draw.line([(content_left, rule_y), (content_right, rule_y)], fill=palette["ink"], width=2)

    # Title.
    lines = split_title(topic)
    y = 156
    if len(lines) == 2 and len(lines[0].split()) == 1 and len(lines[1].split()) == 1:
        first_size = fit_size(lines[0], "serif_bold", content_width, int(HEIGHT * 0.145), min_size=80)
        second_size = fit_size(lines[1], "serif_italic", int(content_width * 0.78), int(first_size * 0.48), min_size=48)
        for text, key, size, color in (
            (lines[0], "serif_bold", first_size, palette["ink"]),
            (lines[1], "serif_italic", second_size, palette["accent"]),
        ):
            face = font(key, size)
            width, _, bottom = ink_box(text, face)
            _, top, _ = ink_box(text, face)
            x = content_left + (content_width - width) / 2
            draw_text(draw, text, face, x, y, color)
            y += (bottom - top) + int(size * 0.08)
    else:
        for text in lines:
            size = fit_size(text, "serif_bold", content_width, int(HEIGHT * 0.16), min_size=64)
            # Open the tracking a little when a short word would otherwise look lost.
            face = font("serif_bold", size)
            natural, _, _ = ink_box(text, face)
            tracking = 0.0
            if len(text) <= 6 and natural < content_width * 0.92:
                spare = content_width * 0.92 - natural
                gaps = max(len(text) - 1, 1)
                tracking = min(spare / gaps, size * 0.16)
            width, top, bottom = ink_box(text, face, tracking)
            if width >= content_width * 0.86:
                x = content_left
            else:
                x = content_left + (content_width - width) / 2
            draw_text(draw, text, face, x, y, palette["ink"], tracking=tracking)
            y += (bottom - top) + int(size * 0.06)

    y += 18
    draw.line([(content_left, y), (content_right, y)], fill=palette["ink"], width=1)
    body_top = y + 36
    footer_rule = HEIGHT - 118
    body_bottom = footer_rule - 28
    available = body_bottom - body_top

    solos, italics, bands = prepare_words(topic, words, rng)

    fitted: list[Row] = []
    scale = 1.0
    for _ in range(14):
        trial_solos = list(solos)
        trial_italics = list(italics)
        trial_bands = list(bands)
        trial = compose_rows(trial_solos, trial_italics, trial_bands, content_width, scale)
        if not trial:
            break
        height = 0
        for index, row in enumerate(trial):
            height += row_height(row, palette)
            if index < len(trial) - 1:
                height += row_gap(row, scale)
        if height <= available or scale <= 0.62:
            fitted = trial
            break
        scale *= 0.9
        fitted = trial

    if fitted:
        used = 0
        for index, row in enumerate(fitted):
            used += row_height(row, palette)
            if index < len(fitted) - 1:
                used += row_gap(row, scale)
        spare = max(0, available - used)
        extra = min(34, spare / max(len(fitted) - 1, 1)) if len(fitted) > 1 else 0
        cursor = body_top + (spare - extra * (len(fitted) - 1)) / 2
        cursor = max(body_top, cursor)
        for index, row in enumerate(fitted):
            paint_row(draw, row, cursor, content_left, content_right, palette)
            cursor += row_height(row, palette)
            if index < len(fitted) - 1:
                cursor += row_gap(row, scale) + extra

    draw.line([(content_left, footer_rule), (content_right, footer_rule)], fill=palette["ink"], width=1)
    foot = font("sans", 20)
    plate = f"NO. {seed % 100:02d}"
    count = f"{len(words):02d} WORDS"
    draw_tracked_label(draw, plate, foot, content_left, footer_rule + 22, palette["muted"], 3.0)
    draw_tracked_label(draw, count, foot, 0, footer_rule + 22, palette["muted"], 3.0, align_right_at=content_right)
    return image


def paint_row(
    draw: ImageDraw.ImageDraw,
    row: Row,
    y: float,
    left: int,
    right: int,
    palette: dict,
) -> None:
    width_box = right - left
    if isinstance(row, Solo):
        text = row.text.upper()
        face = font(row.face_key, row.size)
        stroke = max(2, row.size // 26) if row.outline else 0
        index_h = 0
        if row.index:
            index_face = font("sans", max(15, int(row.size * 0.15)))
            index_text = f"{row.index:02d}"
            index_w, _, index_b = ink_box(index_text, index_face)
            _, index_t, _ = ink_box(index_text, index_face)
            index_h = (index_b - index_t) + 6
        word_w, _, _ = ink_box(text, face)
        word_w += stroke * 2
        if row.align == "right":
            x = right - word_w
        elif row.align == "center":
            x = left + (width_box - word_w) / 2
        else:
            x = left
        if row.index:
            index_face = font("sans", max(15, int(row.size * 0.15)))
            index_text = f"{row.index:02d}"
            index_w, _, _ = ink_box(index_text, index_face)
            if row.align == "right":
                index_x = right - index_w
            elif row.align == "center":
                index_x = x
            else:
                index_x = x
            draw_text(draw, index_text, index_face, index_x, y, palette["accent"])
        color = palette[row.color_key]
        if row.outline:
            draw_text(
                draw, text, face, x + stroke, y + index_h + stroke,
                palette["bg"], stroke=stroke, stroke_fill=color,
            )
        else:
            draw_text(draw, text, face, x, y + index_h, color)
        return

    if isinstance(row, ItalicLine):
        text = row.text.lower()
        face = font("serif_italic", row.size)
        word_w, _, _ = ink_box(text, face)
        x = left + (width_box - word_w) / 2
        draw_text(draw, text, face, x, y, palette["ink"])
        return

    face = font("narrow", row.size)
    sep = max(18, int(row.size * 0.85))
    pieces = []
    total = 0
    for word in row.words:
        shown = word.upper()
        word_w, _, _ = ink_box(shown, face, row.tracking)
        pieces.append((shown, word_w))
        total += word_w
    total += sep * (len(pieces) - 1)
    # Keep a short line together instead of stretching it edge to edge.
    if total < width_box * 0.72:
        x = left + (width_box - total) / 2
        gap = sep
    else:
        x = left
        gap = sep + (width_box - total) / max(len(pieces) - 1, 1)
        gap = min(gap, row.size * 1.8)
        extra = width_box - (sum(w for _, w in pieces) + gap * (len(pieces) - 1))
        x = left + max(0, extra) / 2
    for index, (shown, word_w) in enumerate(pieces):
        draw_text(draw, shown, face, x, y, palette["muted"], tracking=row.tracking)
        x += word_w
        if index < len(pieces) - 1:
            dot_face = font("sans", max(12, int(row.size * 0.55)))
            dot_w, _, _ = ink_box("·", dot_face)
            draw_text(draw, "·", dot_face, x + (gap - dot_w) / 2, y + row.size * 0.18, palette["accent"])
            x += gap


def resolve_words(topic: str, given: str | None, word_file: str | None) -> list[str]:
    if word_file:
        text = Path(word_file).read_text(encoding="utf-8")
        return parse_word_list(text.replace("\n", ","))
    if given:
        return parse_word_list(given)
    key = topic.casefold()
    if key in TOPICS:
        return list(TOPICS[key])
    known = ", ".join(sorted(TOPICS))
    raise SystemExit(
        f"No word list for “{topic}”.\n"
        f"Pass your own with --words salt,tide,harbor\n"
        f"Or pick a built-in topic: {known}"
    )


def default_style(topic: str) -> str:
    return TOPIC_STYLE.get(topic.casefold(), "cream")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a typographic word poster for a topic.",
    )
    parser.add_argument("topic", nargs="?", default="ocean", help="poster title, for example ocean")
    parser.add_argument("--words", help="comma-separated words to set on the poster")
    parser.add_argument("--words-file", help="text file of words, commas or one per line")
    parser.add_argument("--style", choices=[*STYLES.keys(), "auto"], default="auto")
    parser.add_argument("--seed", type=int, default=None, help="layout seed; omit for a steady one per topic")
    parser.add_argument("-o", "--output", help="png path (default: output/<topic>.png)")
    parser.add_argument("--list", action="store_true", help="print built-in topics and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        for name in sorted(TOPICS):
            print(f"{name:12} {TOPIC_STYLE.get(name, 'cream'):8} {len(TOPICS[name])} words")
        return 0

    topic = clean_word(args.topic)
    if not topic:
        raise SystemExit("Give a topic, for example: python poster.py ocean")

    words = resolve_words(topic, args.words, args.words_file)
    if len(words) < 4:
        raise SystemExit("Give at least four words so the poster has something to set.")

    style_name = default_style(topic) if args.style == "auto" else args.style
    if args.seed is None:
        seed = sum(ord(ch) for ch in topic.casefold()) * 17 + len(words) * 3
    else:
        seed = args.seed

    output = Path(args.output) if args.output else Path("output") / f"{slug(topic)}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    image = render(topic, words, STYLES[style_name], seed)
    image.save(output, "PNG")
    print(f"Wrote {output}  ({style_name}, seed {seed}, {len(words)} words)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
