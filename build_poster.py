#!/usr/bin/env python3
"""Wednesday 18 November 2026 — one front page, 33 stories, 13 mains.

Fresh build in this session from the live top-5 study (STUDY.md) and the
verified facts (FACTS.md), plus the winning API idea: a region-colour key
(one colour per continent, used on the panel tag stripe, the map dot and
the also-on number) and a "Today's Numbers" sidebar with the day's three
biggest figures. Cream paper, navy-band masthead, huge serif date,
13 illustrated mains, numbered map, also-on list.

Draws a 1024x1024 page with Pillow. Deterministic.
Run: python3 build_poster.py   (writes entry.png next to this file)
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (253, 246, 227)   # cream, like the top posters
INK = (30, 30, 30)
RED = (176, 58, 46)
GOLD = (178, 140, 40)
NAVY = (24, 48, 92)
MUTED = (107, 101, 88)
PANEL_LINE = (210, 203, 188)
MAP_FILL = (207, 199, 180)
MAP_EDGE = (168, 159, 136)

# One colour per continent — the key of the whole page. The same colour
# marks a story's tag stripe, its dot on the map and its also-on number.
REGION_COLOUR = {
    "EUROPE": (31, 78, 121),
    "MIDDLE EAST": (176, 58, 46),
    "ASIA": (46, 125, 50),
    "AMERICAS": (125, 60, 152),
    "AFRICA": (20, 143, 119),
    "OCEANIA": (202, 111, 30),
}
LEGEND = [("Europe", (31, 78, 121)), ("Middle East", (176, 58, 46)),
          ("Asia", (46, 125, 50)), ("Americas", (125, 60, 152)),
          ("Africa", (20, 143, 119)), ("Oceania", (202, 111, 30))]

SERIF_B = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ERRORS = []


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns the lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def balance_two(draw, text, fnt, max_w):
    """Split into the two most even lines that both fit max_w, else None."""
    words = text.split()
    best = None
    for k in range(1, len(words)):
        l1, l2 = " ".join(words[:k]), " ".join(words[k:])
        w1 = draw.textlength(l1, font=fnt)
        w2 = draw.textlength(l2, font=fnt)
        if w1 <= max_w and w2 <= max_w:
            score = max(w1, w2)
            if best is None or score < best[0]:
                best = (score, [l1, l2])
    return best[1] if best is not None else None


def fit_lines(draw, text, fnt, max_w, max_lines):
    """Wrap and cap to max_lines, adding an ellipsis when clipped."""
    lines = wrap(draw, text, fnt, max_w)
    if len(lines) <= max_lines:
        return lines
    out = lines[:max_lines]
    while out and draw.textlength(out[-1] + "\u2026", font=fnt) > max_w:
        out[-1] = out[-1][:-1]
    out[-1] = out[-1] + "\u2026"
    return out


def text_block(draw, x, y, lines, fnt, fill, leading):
    for i, line in enumerate(lines):
        draw.text((x, y + i * leading), line, font=fnt, fill=fill)
    return y + len(lines) * leading


def badge(draw, cx, cy, n, colour, r=11):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour,
                 outline=(255, 255, 255), width=2)
    fnt = font(SANS_B, 11 if n < 10 else 10)
    tw = draw.textlength(str(n), font=fnt)
    th = fnt.getbbox(str(n))[3] - fnt.getbbox(str(n))[1]
    draw.text((cx - tw / 2, cy - th / 2 - 1), str(n), font=fnt,
              fill=(255, 255, 255))


def sky(draw, x, y, w, h, top, bottom):
    """Vertical two-stop sky gradient, drawn as horizontal bands."""
    for row in range(h):
        t = row / max(h - 1, 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(x, y + row), (x + w, y + row)], fill=col)


def centred(draw, cx, y, text, fnt, fill):
    tw = draw.textlength(text, font=fnt)
    draw.text((cx - tw / 2, y), text, font=fnt, fill=fill)


# ---------------------------------------------------------------- data
# (n, region, tag, headline, deck, lon, lat)
MAINS = [
    (1, "MIDDLE EAST", "IRAN WAR",
     "US AND IRAN TRADE FIRE OVER BAHRAIN",
     "Iranian drones target a US radar at Sheikh Isa; Bahrain says all downed, US jets hit Qeshm.",
     50.6, 26.2),
    (2, "EUROPE", "UKRAINE WAR",
     "UKRAINE COLLAPSES A SPAN OF THE KERCH BRIDGE",
     "A second day of strikes drops the road arch into the strait; Russia hits two Kyiv bridges in reply.",
     36.5, 45.3),
    (3, "ASIA", "DIPLOMACY",
     "TRUMP IN MANILA FOR FIRST QUAD IN TWO YEARS",
     "He meets Modi, Takaichi and Albanese at ASEAN, sees Marcos today, then heads to Shenzhen for APEC.",
     121.0, 14.6),
    (4, "AMERICAS", "MARKETS",
     "NVIDIA SALES MORE THAN DOUBLE",
     "Revenue $115.8bn, up 103%; data-centre sales hit $107.6bn.",
     -121.0, 37.4),
    (5, "ASIA", "WEATHER",
     "CYCLONE AKVAN HITS INDIA'S COAST",
     "The storm crosses Andhra Pradesh on Friday; winds to 145 km/h.",
     85.8, 20.3),
    (6, "MIDDLE EAST", "POLITICS",
     "KNESSET ELECTS KAHANA 66-52",
     "Netanyahu's ally loses the speakership to Eisenkot's candidate.",
     35.2, 31.8),
    (7, "EUROPE", "EU LOAN",
     "EU PLANS \u20ac45BN LOAN FOR UKRAINE",
     "Two-thirds of Kyiv's \u20ac70bn 2027 gap; paid back only if Russia pays.",
     30.5, 50.4),
    (8, "EUROPE", "SANCTIONS",
     "BRITAIN SANCTIONS SETTLEMENT BUILDERS",
     "Eight Israeli firms and aid-blocker Tzav 9 face asset freezes.",
     -0.1, 51.5),
    (9, "ASIA", "TRADE",
     "CHINA CUTS TARIFFS FOR CANADA",
     "Relief worth C$400m on pork and seafood; steel remissions extended.",
     114.0, 22.5),
    (10, "ASIA", "SPORT",
     "DHONI ENDS IPL PLAYING CAREER",
     "CSK name him Team Mentor for 2027; five titles, 272 appearances.",
     80.3, 13.1),
    (11, "ASIA", "AIR CRASH",
     "RUSSIAN PLANE CRASHES IN SIBERIA",
     "An An-12 comes down near Yagunovo; all 19 aboard were killed.",
     86.1, 55.4),
    (12, "OCEANIA", "PORT ROW",
     "NZ TAKES BLAME FOR PENRHYN PORT",
     "NZ will cover overruns on the Cook Islands port it builds with the US.",
     -159.8, -9.0),
    (13, "AFRICA", "HEALTH",
     "EBOLA PASSES 11,000 CASES IN DR CONGO",
     "Cases pass 11,000, deaths 5,500; Africa CDC says it is out of control.",
     23.0, -3.0),
]

# (n, region, one-liner, lon, lat)
ALSO = [
    (14, "ASIA", "Japan scrambles fighters as Russian jets breach airspace", 139.7, 35.7),
    (15, "EUROPE", "Estonia to shut Russia border on 1 Dec after foiled arson plot", 24.7, 59.4),
    (16, "EUROPE", "Pope Leo forgives rosary thrower; ends 12-day tour", 12.45, 41.9),
    (17, "AMERICAS", "US presses UN agency over Taiwan flight curbs", -74.0, 40.7),
    (18, "AMERICAS", "US widens chip export scrutiny to SE Asia and Brazil", -77.0, 38.9),
    (19, "ASIA", "Baidu chief warns of AI 'bubble' ahead of APEC talks", 116.4, 39.9),
    (20, "ASIA", "Amazon to invest $7bn in India's renewable energy", 77.2, 28.6),
    (21, "ASIA", "India re-elected to ITU Council for 2027-2030", 6.1, 46.2),
    (22, "ASIA", "Jay Shah re-elected ICC chairman for a second term", 55.3, 25.2),
    (23, "EUROPE", "UEFA backs France's Diallo to stand against Infantino", 2.35, 48.85),
    (24, "ASIA", "Modi offers free e-visas and maritime ties at ASEAN", 121.0, 14.6),
    (25, "MIDDLE EAST", "Pakistan and Iran stress engagement for stability", 73.1, 33.7),
    (26, "ASIA", "Japan offers ASEAN nations access to energy storage", 106.8, -6.2),
    (27, "MIDDLE EAST", "Jordan and Iraq block Telegram over security", 35.9, 31.9),
    (28, "AMERICAS", "Costa Rica journalist shot dead after probing drug links", -84.1, 9.9),
    (29, "AFRICA", "Guinea mining crackdown displaces thousands", -13.7, 9.5),
    (30, "AMERICAS", "Trump signs reciprocal trade deal with Thailand", 100.5, 13.75),
    (31, "AMERICAS", "RAYE leads Grammy nominations with 11 nods", -118.2, 34.05),
    (32, "AMERICAS", "Vance: Iran must cut enrichment to end war", 51.4, 35.7),
    (33, "AMERICAS", "California bans Waymo self-driving cars from freeways", -121.5, 38.6),
]

# The day's three biggest numbers, for the sidebar (Groq idea).
NUMBERS = [
    ("$115.8bn", "Nvidia Q3 revenue, +103%", "AMERICAS"),
    ("19", "dead in the Siberia An-12 crash", "ASIA"),
    ("11,000+", "Ebola cases in DR Congo", "AFRICA"),
]

# ------------------------------------------------------------------- map
# Rough continent outlines in lon/lat, drawn equirectangular.
LAND = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 62), (-65, 60), (-55, 52), (-60, 47), (-70, 42), (-75, 35),
     (-80, 25), (-85, 20), (-90, 15), (-95, 18), (-105, 20), (-115, 28),
     (-125, 40), (-125, 48), (-140, 60), (-155, 58), (-165, 60)],
    [(-80, 10), (-75, 5), (-70, 0), (-65, -5), (-60, -10), (-55, -20),
     (-50, -30), (-45, -25), (-40, -20), (-35, -8), (-40, 0), (-50, 0),
     (-60, 5), (-70, 10), (-78, 8)],
    [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 31), (35, 28),
     (40, 20), (43, 12), (48, 11), (51, 10), (45, 0), (40, -10), (35, -20),
     (30, -30), (20, -35), (15, -30), (12, -18), (13, -10), (9, 0), (0, 5),
     (-8, 5), (-13, 8)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 59), (28, 60), (30, 70), (25, 71), (18, 69),
     (12, 65), (5, 60), (0, 55), (-5, 50), (-10, 44)],
    [(30, 70), (40, 68), (55, 70), (70, 72), (90, 75), (110, 76), (130, 72),
     (150, 70), (160, 65), (162, 60), (158, 52), (142, 50), (140, 40),
     (130, 33), (127, 35), (122, 30), (115, 22), (108, 12), (105, 8),
     (100, 8), (95, 15), (90, 22), (85, 20), (80, 10), (75, 8), (70, 20),
     (65, 25), (60, 25), (55, 26), (50, 29), (48, 30), (43, 35), (40, 36),
     (35, 36), (30, 41)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
     (150, -22), (146, -19), (142, -11), (137, -12), (135, -15), (132, -12),
     (130, -13), (126, -14), (122, -17), (118, -20)],
]


def project(lon, lat, mx, my, mw, mh):
    px = mx + (lon + 180.0) / 360.0 * mw
    py = my + (85.0 - lat) / 145.0 * mh
    return px, py


def draw_map(draw, mx, my, mw, mh):
    draw.rectangle([mx, my, mx + mw, my + mh], fill=(238, 233, 220),
                   outline=PANEL_LINE)
    inner = (mx + 4, my + 4, mw - 8, mh - 8)
    for poly in LAND:
        pts = [project(lon, lat, *inner) for lon, lat in poly]
        draw.polygon(pts, fill=MAP_FILL, outline=MAP_EDGE)
    for _n, _region, _t, lon, lat in ALSO:
        px, py = project(lon, lat, *inner)
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(120, 115, 105))
    for n, region, _tag, _h, _d, lon, lat in MAINS:
        px, py = project(lon, lat, *inner)
        col = REGION_COLOUR[region]
        draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col,
                     outline=(255, 255, 255))
        fnt = font(SANS_B, 8)
        tw = draw.textlength(str(n), font=fnt)
        draw.text((px - tw / 2, py - 5), str(n), font=fnt, fill=(255, 255, 255))


# ------------------------------------------------------- illustrations
def _flag(draw, x, y, w, h, kind):
    """Tiny flat flag. kind: us | in | jp | au | cn | ca | nz."""
    if kind == "us":
        for i in range(7):
            draw.rectangle([x, y + i * h / 7, x + w, y + (i + 1) * h / 7],
                           fill=(176, 58, 46) if i % 2 == 0 else (255, 255, 255))
        draw.rectangle([x, y, x + w * 0.45, y + h * 0.55], fill=NAVY)
    elif kind == "in":
        draw.rectangle([x, y, x + w, y + h / 3], fill=(255, 153, 51))
        draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(255, 255, 255))
        draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(19, 136, 8))
        draw.ellipse([x + w * 0.42, y + h * 0.36, x + w * 0.58, y + h * 0.64],
                     outline=NAVY, width=1)
    elif kind == "jp":
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        draw.ellipse([x + w * 0.35, y + h * 0.22, x + w * 0.65, y + h * 0.78],
                     fill=(188, 0, 45))
    elif kind == "cn":
        draw.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
        for sx, sy, r in [(0.22, 0.28, 5), (0.42, 0.20, 3), (0.48, 0.38, 3),
                          (0.42, 0.55, 3), (0.26, 0.52, 3)]:
            draw.ellipse([x + w * sx - r, y + h * sy - r,
                          x + w * sx + r, y + h * sy + r], fill=(255, 222, 0))
    elif kind == "ca":
        draw.rectangle([x, y, x + w * 0.25, y + h], fill=(210, 0, 25))
        draw.rectangle([x + w * 0.75, y, x + w, y + h], fill=(210, 0, 25))
        draw.rectangle([x + w * 0.25, y, x + w * 0.75, y + h], fill=(255, 255, 255))
        draw.polygon([(x + w * 0.50, y + h * 0.18), (x + w * 0.56, y + h * 0.38),
                      (x + w * 0.66, y + h * 0.36), (x + w * 0.60, y + h * 0.52),
                      (x + w * 0.66, y + h * 0.62), (x + w * 0.54, y + h * 0.60),
                      (x + w * 0.50, y + h * 0.78), (x + w * 0.46, y + h * 0.60),
                      (x + w * 0.34, y + h * 0.62), (x + w * 0.40, y + h * 0.52),
                      (x + w * 0.34, y + h * 0.36), (x + w * 0.44, y + h * 0.38)],
                     fill=(210, 0, 25))
    elif kind == "nz":
        draw.rectangle([x, y, x + w, y + h], fill=(0, 40, 104))
        for sx, sy, r in [(0.72, 0.30, 3), (0.82, 0.55, 3), (0.65, 0.62, 2),
                          (0.80, 0.78, 2)]:
            draw.ellipse([x + w * sx - r, y + h * sy - r,
                          x + w * sx + r, y + h * sy + r], fill=(255, 255, 255))
    else:  # au
        draw.rectangle([x, y, x + w, y + h], fill=(0, 40, 104))
        for sx, sy, r in [(0.72, 0.30, 3), (0.82, 0.55, 3), (0.65, 0.62, 2),
                          (0.80, 0.78, 2)]:
            draw.ellipse([x + w * sx - r, y + h * sy - r,
                          x + w * sx + r, y + h * sy + r], fill=(255, 255, 255))


def paint(draw, n, x, y, w, h):
    """Flat vector scene per main. Each gets the art box (x, y, w, h)."""
    if n == 1:  # Bahrain: radar dome on a shore, drones in the sky, jets
        draw.rectangle([x, y, x + w, y + h], fill=(238, 230, 208))
        draw.polygon([(x + int(w * 0.55), y + h), (x + w, y + int(h * 0.55)),
                      (x + w, y + h)], fill=(112, 182, 212))
        draw.ellipse([x + int(w * 0.08), y + int(h * 0.10),
                      x + int(w * 0.38), y + int(h * 0.52)], outline=NAVY, width=4)
        draw.line([x + int(w * 0.23), y + int(h * 0.52), x + int(w * 0.23), y + h - 4],
                  fill=NAVY, width=4)
        draw.line([x + int(w * 0.15), y + h - 4, x + int(w * 0.31), y + h - 4],
                  fill=NAVY, width=4)
        for cx, cy, r in [(0.52, 0.20, 6), (0.58, 0.28, 5), (0.48, 0.30, 4)]:
            draw.ellipse([x + int(w * cx) - r, y + int(h * cy) - r,
                          x + int(w * cx) + r, y + int(h * cy) + r], fill=RED)
        for cx, cy in [(0.70, 0.16), (0.82, 0.30), (0.68, 0.43)]:
            draw.polygon([(x + int(w * cx), y + int(h * (cy - 0.05))),
                          (x + int(w * (cx + 0.09)), y + int(h * cy)),
                          (x + int(w * cx), y + int(h * (cy + 0.05))),
                          (x + int(w * (cx - 0.09)), y + int(h * cy))], fill=INK)
        draw.rectangle([x + int(w * 0.66), y + int(h * 0.68),
                        x + int(w * 0.94), y + int(h * 0.84)], fill=(90, 60, 40))
        draw.rectangle([x + int(w * 0.80), y + int(h * 0.58),
                        x + int(w * 0.88), y + int(h * 0.68)], fill=(200, 200, 200))
    elif n == 2:  # Kerch bridge: deck, collapsed span, smoke, jets, waves
        sky(draw, x, y, w, h, (198, 228, 240), (170, 205, 225))
        draw.rectangle([x, y + int(h * 0.62), x + w, y + h], fill=(72, 128, 168))
        for wy in (0.72, 0.82, 0.92):
            draw.line([x + 4, y + int(h * wy), x + w - 4, y + int(h * wy)],
                      fill=(140, 185, 210), width=2)
        draw.rectangle([x, y + int(h * 0.30), x + int(w * 0.42), y + int(h * 0.38)], fill=NAVY)
        draw.rectangle([x + int(w * 0.58), y + int(h * 0.30), x + w, y + int(h * 0.38)], fill=NAVY)
        draw.rectangle([x + int(w * 0.06), y + int(h * 0.38), x + int(w * 0.10), y + int(h * 0.62)], fill=NAVY)
        draw.rectangle([x + int(w * 0.88), y + int(h * 0.38), x + int(w * 0.92), y + int(h * 0.62)], fill=NAVY)
        draw.polygon([(x + int(w * 0.44), y + int(h * 0.38)),
                      (x + int(w * 0.56), y + int(h * 0.38)),
                      (x + int(w * 0.50), y + int(h * 0.66)),
                      (x + int(w * 0.46), y + int(h * 0.68))], fill=(40, 60, 90))
        draw.arc([x + int(w * 0.30), y, x + int(w * 0.70), y + int(h * 0.55)],
                 180, 360, fill=NAVY, width=3)
        for cx, cy, r in [(0.50, 0.16, 0.05), (0.57, 0.10, 0.035), (0.44, 0.12, 0.03)]:
            rx, ry = int(w * r), int(w * r)
            draw.ellipse([x + int(w * cx) - rx, y + int(h * cy) - ry,
                          x + int(w * cx) + rx, y + int(h * cy) + ry], fill=(110, 110, 110))
        draw.ellipse([x + int(w * 0.50) - 4, y + int(h * 0.16) - 4,
                      x + int(w * 0.50) + 4, y + int(h * 0.16) + 4], fill=(232, 132, 42))
        for cx, cy in [(0.78, 0.10), (0.14, 0.16)]:
            draw.polygon([(x + int(w * cx), y + int(h * (cy - 0.03))),
                          (x + int(w * (cx + 0.08)), y + int(h * cy)),
                          (x + int(w * cx), y + int(h * (cy + 0.03))),
                          (x + int(w * (cx - 0.08)), y + int(h * cy))], fill=INK)
    elif n == 3:  # Quad summit: four flags over a table
        draw.rectangle([x, y, x + w, y + h], fill=(233, 226, 248))
        draw.rectangle([x, y, x + w, y + int(h * 0.16)], fill=(92, 52, 132))
        cap = font(SANS_B, 10 if h < 60 else 12)
        tw = draw.textlength("QUAD LEADERS' SUMMIT \u00b7 MANILA", font=cap)
        draw.text((x + (w - tw) / 2, y + 3), "QUAD LEADERS' SUMMIT \u00b7 MANILA",
                  font=cap, fill=(255, 255, 255))
        kinds = ["us", "in", "jp", "au"]
        for i, kind in enumerate(kinds):
            fx = 0.06 + i * 0.235
            fw, fh = int(w * 0.17), int(h * 0.30)
            _flag(draw, x + int(w * fx), y + int(h * 0.30), fw, fh, kind)
            draw.line([x + int(w * (fx + 0.085)), y + int(h * 0.30),
                       x + int(w * (fx + 0.085)), y + int(h * 0.72)],
                      fill=INK, width=2)
        draw.rectangle([x + int(w * 0.05), y + int(h * 0.72),
                        x + int(w * 0.95), y + int(h * 0.88)], fill=(122, 82, 42))
        draw.rectangle([x + int(w * 0.05), y + int(h * 0.72),
                        x + int(w * 0.95), y + int(h * 0.78)], fill=(150, 105, 60))
    elif n == 4:  # Nvidia: chip + rising chart
        draw.rectangle([x, y, x + w, y + h], fill=(232, 238, 225))
        draw.rectangle([x + int(w * 0.06), y + int(h * 0.18),
                        x + int(w * 0.38), y + int(h * 0.82)], fill=NAVY)
        draw.rectangle([x + int(w * 0.14), y + int(h * 0.33),
                        x + int(w * 0.30), y + int(h * 0.67)], fill=(62, 182, 92))
        for fy in (0.28, 0.50, 0.72):
            draw.line([x + int(w * 0.02), y + int(h * fy), x + int(w * 0.06), y + int(h * fy)],
                      fill=NAVY, width=3)
            draw.line([x + int(w * 0.38), y + int(h * fy), x + int(w * 0.42), y + int(h * fy)],
                      fill=NAVY, width=3)
        pts = [(x + int(w * 0.48), y + int(h * 0.78)), (x + int(w * 0.60), y + int(h * 0.66)),
               (x + int(w * 0.70), y + int(h * 0.70)), (x + int(w * 0.82), y + int(h * 0.46)),
               (x + int(w * 0.94), y + int(h * 0.24))]
        draw.line(pts, fill=(42, 162, 62), width=4)
        draw.polygon([(x + int(w * 0.94), y + int(h * 0.24)),
                      (x + int(w * 0.86), y + int(h * 0.24)),
                      (x + int(w * 0.94), y + int(h * 0.38))], fill=(42, 162, 62))
    elif n == 5:  # Cyclone Akvan: spiral over the sea, rain, coast
        sky(draw, x, y, w, h, (170, 190, 215), (215, 225, 230))
        cx, cy = x + int(w * 0.38), y + int(h * 0.52)
        for rr, col in [(0.42, (200, 205, 210)), (0.32, (150, 165, 180)),
                        (0.22, (110, 130, 150)), (0.12, (70, 95, 120))]:
            r = int(min(w, h) * rr)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=4)
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=NAVY)
        draw.rectangle([x + int(w * 0.78), y + int(h * 0.55), x + w, y + h],
                       fill=(62, 172, 82))
        draw.rectangle([x + int(w * 0.78), y + int(h * 0.55), x + w, y + int(h * 0.62)],
                       fill=(46, 125, 50))
        for dx in (0.12, 0.28, 0.44, 0.60):
            draw.line([x + int(w * dx), y + int(h * 0.18),
                       x + int(w * (dx - 0.04)), y + int(h * 0.38)],
                      fill=(92, 162, 212), width=3)
        cap = font(SANS_B, 9 if h < 60 else 11)
        draw.text((x + int(w * 0.04), y + int(h * 0.04)), "145 KM/H",
                  font=cap, fill=RED)
    elif n == 6:  # Knesset: hemicycle of seats + ballot box, 66-52
        draw.rectangle([x, y, x + w, y + h], fill=(238, 232, 248))
        cx, cy = x + int(w * 0.42), y + int(h * 0.95)
        for rr in (0.42, 0.30):
            for k in range(7):
                ang = math.radians(200 + k * 20)
                sx = cx + math.cos(ang) * int(w * rr * 1.4)
                sy = cy + math.sin(ang) * int(h * rr * 1.4)
                draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3],
                             fill=(46, 125, 50) if k < 5 else (31, 78, 121))
        draw.rectangle([x + int(w * 0.70), y + int(h * 0.30),
                        x + int(w * 0.92), y + int(h * 0.78)], fill=(200, 40, 40), outline=INK)
        draw.rectangle([x + int(w * 0.70), y + int(h * 0.30),
                        x + int(w * 0.92), y + int(h * 0.42)], fill=(255, 255, 255), outline=INK)
        draw.rectangle([x + int(w * 0.78), y + int(h * 0.22),
                        x + int(w * 0.84), y + int(h * 0.34)], fill=(255, 255, 255), outline=INK)
        lab = font(SANS_B, 11 if h < 60 else 14)
        draw.text((x + int(w * 0.04), y + int(h * 0.06)), "66 - 52",
                  font=lab, fill=NAVY)
    elif n == 7:  # EU loan: circle of stars + euro figure
        draw.rectangle([x, y, x + w, y + h], fill=(232, 238, 248))
        cx, cy = x + int(w * 0.30), y + int(h * 0.50)
        r = int(min(w, h) * 0.34)
        for k in range(12):
            ang = math.radians(k * 30 - 90)
            sx = cx + math.cos(ang) * r
            sy = cy + math.sin(ang) * r
            draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(250, 212, 62))
        draw.ellipse([cx - int(r * 0.55), cy - int(r * 0.55),
                      cx + int(r * 0.55), cy + int(r * 0.55)], fill=NAVY)
        lab = font(SERIF_B, 13 if h < 60 else 18)
        tw = draw.textlength("\u20ac45bn", font=lab)
        draw.text((cx - tw / 2, cy - 9), "\u20ac45bn", font=lab, fill=(255, 255, 255))
        cap = font(SANS_B, 9 if h < 60 else 11)
        draw.text((x + int(w * 0.60), y + int(h * 0.20)), "FOR",
                  font=cap, fill=NAVY)
        draw.text((x + int(w * 0.60), y + int(h * 0.40)), "UKRAINE",
                  font=cap, fill=NAVY)
        draw.text((x + int(w * 0.60), y + int(h * 0.60)), "2027",
                  font=cap, fill=NAVY)
    elif n == 8:  # Britain sanctions: crane + frozen sign
        sky(draw, x, y, w, h, (198, 228, 240), (220, 230, 220))
        draw.rectangle([x, y + int(h * 0.78), x + w, y + h], fill=(150, 140, 120))
        draw.rectangle([x + int(w * 0.10), y + int(h * 0.30),
                        x + int(w * 0.16), y + int(h * 0.85)], fill=(90, 80, 70))
        draw.line([x + int(w * 0.13), y + int(h * 0.30),
                   x + int(w * 0.85), y + int(h * 0.14)], fill=(90, 80, 70), width=4)
        draw.line([x + int(w * 0.13), y + int(h * 0.30),
                   x + int(w * 0.55), y + int(h * 0.30)], fill=(90, 80, 70), width=3)
        draw.line([x + int(w * 0.80), y + int(h * 0.15),
                   x + int(w * 0.80), y + int(h * 0.34)], fill=INK, width=2)
        draw.rectangle([x + int(w * 0.72), y + int(h * 0.34),
                        x + int(w * 0.88), y + int(h * 0.52)], fill=(176, 58, 46),
                       outline=INK)
        draw.rectangle([x + int(w * 0.30), y + int(h * 0.60),
                        x + int(w * 0.58), y + int(h * 0.80)], fill=(200, 200, 200),
                       outline=INK)
        draw.line([x + int(w * 0.30), y + int(h * 0.60),
                   x + int(w * 0.58), y + int(h * 0.80)], fill=RED, width=3)
        draw.line([x + int(w * 0.58), y + int(h * 0.60),
                   x + int(w * 0.30), y + int(h * 0.80)], fill=RED, width=3)
        cap = font(SANS_B, 9 if h < 60 else 11)
        draw.text((x + int(w * 0.04), y + int(h * 0.04)), "8 FIRMS FROZEN",
                  font=cap, fill=RED)
    elif n == 9:  # China-Canada: two flags + tariff arrow down
        draw.rectangle([x, y, x + w, y + h], fill=(250, 246, 236))
        _flag(draw, x + int(w * 0.06), y + int(h * 0.14), int(w * 0.34), int(h * 0.34), "cn")
        _flag(draw, x + int(w * 0.60), y + int(h * 0.14), int(w * 0.34), int(h * 0.34), "ca")
        draw.line([x + int(w * 0.23), y + int(h * 0.48),
                   x + int(w * 0.23), y + int(h * 0.86)], fill=INK, width=2)
        draw.line([x + int(w * 0.77), y + int(h * 0.48),
                   x + int(w * 0.77), y + int(h * 0.86)], fill=INK, width=2)
        draw.line([x + int(w * 0.46), y + int(h * 0.18),
                   x + int(w * 0.46), y + int(h * 0.58)], fill=(42, 162, 62), width=4)
        draw.polygon([(x + int(w * 0.46), y + int(h * 0.64)),
                      (x + int(w * 0.38), y + int(h * 0.52)),
                      (x + int(w * 0.54), y + int(h * 0.52))], fill=(42, 162, 62))
        cap = font(SANS_B, 9 if h < 60 else 11)
        tw = draw.textlength("C$400M RELIEF", font=cap)
        draw.text((x + (w - tw) / 2, y + int(h * 0.82)), "C$400M RELIEF",
                  font=cap, fill=(42, 162, 62))
    elif n == 10:  # Dhoni: bat, ball and stumps on a green pitch
        draw.rectangle([x, y, x + w, y + h], fill=(232, 238, 225))
        draw.rectangle([x, y + int(h * 0.70), x + w, y + h], fill=(62, 172, 82))
        for sx in (0.62, 0.70, 0.78):
            draw.rectangle([x + int(w * sx), y + int(h * 0.30),
                            x + int(w * (sx + 0.04)), y + int(h * 0.70)],
                           fill=(240, 202, 82), outline=INK)
        draw.rectangle([x + int(w * 0.58), y + int(h * 0.24),
                        x + int(w * 0.82), y + int(h * 0.30)], fill=(240, 202, 82),
                       outline=INK)
        draw.polygon([(x + int(w * 0.18), y + int(h * 0.15)),
                      (x + int(w * 0.42), y + int(h * 0.55)),
                      (x + int(w * 0.34), y + int(h * 0.62)),
                      (x + int(w * 0.10), y + int(h * 0.22))], fill=(222, 182, 62),
                     outline=INK)
        draw.ellipse([x + int(w * 0.50) - 5, y + int(h * 0.55) - 5,
                      x + int(w * 0.50) + 5, y + int(h * 0.55) + 5], fill=RED)
        cap = font(SANS_B, 10 if h < 60 else 13)
        draw.text((x + int(w * 0.04), y + int(h * 0.04)), "272 MATCHES",
                  font=cap, fill=NAVY)
    elif n == 11:  # An-12: plane diving, smoke plume, mountains
        sky(draw, x, y, w, h, (170, 190, 210), (210, 220, 225))
        draw.polygon([(x, y + h), (x + int(w * 0.30), y + int(h * 0.45)),
                      (x + int(w * 0.55), y + h)], fill=(120, 130, 140))
        draw.polygon([(x + int(w * 0.45), y + h), (x + int(w * 0.75), y + int(h * 0.55)),
                      (x + w, y + h)], fill=(100, 110, 120))
        for cx, cy, r in [(0.72, 0.30, 0.06), (0.80, 0.38, 0.045), (0.66, 0.38, 0.035)]:
            rx, ry = int(w * r), int(h * r)
            draw.ellipse([x + int(w * cx) - rx, y + int(h * cy) - ry,
                          x + int(w * cx) + rx, y + int(h * cy) + ry], fill=(90, 90, 90))
        px, py = x + int(w * 0.38), y + int(h * 0.30)
        draw.polygon([(px - int(w * 0.20), py + int(h * 0.06)),
                      (px + int(w * 0.22), py - int(h * 0.06)),
                      (px + int(w * 0.26), py - int(h * 0.02)),
                      (px - int(w * 0.16), py + int(h * 0.12))], fill=INK)
        draw.polygon([(px, py - int(h * 0.02)),
                      (px + int(w * 0.10), py - int(h * 0.22)),
                      (px + int(w * 0.14), py - int(h * 0.18)),
                      (px + int(w * 0.04), py + int(h * 0.02))], fill=INK)
        draw.polygon([(px - int(w * 0.10), py + int(h * 0.08)),
                      (px - int(w * 0.06), py + int(h * 0.24)),
                      (px - int(w * 0.02), py - int(h * 0.22)),
                      (px - int(w * 0.04), py + int(h * 0.10))], fill=INK)
    elif n == 12:  # Penrhyn: port crane, containers, NZ flag
        sky(draw, x, y, w, h, (198, 228, 240), (220, 230, 220))
        draw.rectangle([x, y + int(h * 0.72), x + w, y + h], fill=(112, 182, 212))
        draw.rectangle([x, y + int(h * 0.72), x + w, y + int(h * 0.78)],
                       fill=(150, 140, 120))
        _flag(draw, x + int(w * 0.06), y + int(h * 0.08), int(w * 0.22), int(h * 0.22), "nz")
        draw.rectangle([x + int(w * 0.62), y + int(h * 0.12),
                        x + int(w * 0.68), y + int(h * 0.78)], fill=(90, 80, 70))
        draw.line([x + int(w * 0.65), y + int(h * 0.12),
                   x + int(w * 0.96), y + int(h * 0.12)], fill=(90, 80, 70), width=3)
        draw.line([x + int(w * 0.90), y + int(h * 0.12),
                   x + int(w * 0.90), y + int(h * 0.30)], fill=INK, width=2)
        draw.rectangle([x + int(w * 0.82), y + int(h * 0.30),
                        x + int(w * 0.98), y + int(h * 0.44)], fill=(176, 58, 46),
                       outline=INK)
        for i, (cx, col) in enumerate([(0.10, (46, 125, 50)), (0.28, (31, 78, 121)),
                                       (0.46, (202, 111, 30))]):
            draw.rectangle([x + int(w * cx), y + int(h * 0.52),
                            x + int(w * (cx + 0.16)), y + int(h * 0.72)],
                           fill=col, outline=INK)
    else:  # 13 Ebola: virus + clinic tent + count
        draw.rectangle([x, y, x + w, y + h], fill=(238, 230, 208))
        cx, cy = x + int(w * 0.20), y + int(h * 0.50)
        r = int(min(w, h) * 0.24)
        for a in range(0, 360, 30):
            dx, dy = math.cos(math.radians(a)), math.sin(math.radians(a))
            draw.line([cx, cy, cx + dx * r * 1.5, cy + dy * r * 1.5], fill=RED, width=3)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED)
        draw.ellipse([cx - int(r * 0.4), cy - int(r * 0.4),
                      cx + int(r * 0.2), cy + int(r * 0.2)], fill=(255, 122, 102))
        tx = x + int(w * 0.52)
        draw.polygon([(tx, y + int(h * 0.22)), (tx + int(w * 0.40), y + int(h * 0.22)),
                      (tx + int(w * 0.34), y + int(h * 0.85)),
                      (tx + int(w * 0.06), y + int(h * 0.85))], fill=(255, 255, 255),
                     outline=INK)
        draw.rectangle([tx + int(w * 0.17), y + int(h * 0.38),
                        tx + int(w * 0.23), y + int(h * 0.58)], fill=RED)
        draw.rectangle([tx + int(w * 0.13), y + int(h * 0.45),
                        tx + int(w * 0.27), y + int(h * 0.51)], fill=RED)
        cap = font(SANS_B, 10 if h < 60 else 12)
        draw.text((x + int(w * 0.44), y + int(h * 0.02)), "11,000+",
                  font=cap, fill=RED)


# ---------------------------------------------------------------- panels
def draw_panel(draw, entry, x, y, w, h, lead):
    n, region, tag, headline, deck, _lon, _lat = entry
    col = REGION_COLOUR[region]
    art_h = 92 if lead else 44
    draw.rectangle([x, y, x + w, y + h], fill=PAPER, outline=PANEL_LINE)
    paint(draw, n, x + 1, y + 1, w - 2, art_h - 1)
    draw.line([x, y + art_h, x + w, y + art_h], fill=col, width=3)
    badge(draw, x + w - 20, y + art_h, n, col)
    ty = y + art_h + 8
    tag_size = 10 if lead else 9
    draw.text((x + 8, ty), region + " \u00b7 " + tag,
              font=font(SANS_B, tag_size), fill=col)
    head_size = 17 if lead else 13
    deck_size = 11 if lead else 9
    head_lines = balance_two(draw, headline, font(SERIF_B, head_size), w - 16)
    if head_lines is None:
        ERRORS.append(f"main {n}: headline needs >2 lines at {head_size}pt")
        head_lines = fit_lines(draw, headline, font(SERIF_B, head_size), w - 16, 2)
    y2 = text_block(draw, x + 8, ty + tag_size + 6, head_lines,
                    font(SERIF_B, head_size), INK, head_size + 3)
    if len(wrap(draw, deck, font(SANS, deck_size), w - 16)) > 2:
        ERRORS.append(f"main {n}: deck needs >2 lines at {deck_size}pt")
    deck_lines = fit_lines(draw, deck, font(SANS, deck_size), w - 16, 2)
    text_block(draw, x + 8, y2 + 2, deck_lines,
               font(SANS, deck_size), (70, 65, 55), deck_size + 3)


def draw_sidebar(draw, x, y, w, h):
    """Today's Numbers: the day's three biggest figures (Groq idea)."""
    draw.rectangle([x, y, x + w, y + h], fill=(250, 246, 236), outline=PANEL_LINE)
    draw.rectangle([x, y, x + w, y + 28], fill=NAVY)
    centred(draw, x + w / 2, y + 7, "TODAY'S NUMBERS",
            font(SANS_B, 11), (255, 255, 255))
    cy = y + 44
    for i, (num, label, region) in enumerate(NUMBERS):
        col = REGION_COLOUR[region]
        draw.text((x + 10, cy), num, font=font(SERIF_B, 26), fill=col)
        cy += 36
        for line in wrap(draw, label, font(SANS, 10), w - 20):
            draw.text((x + 10, cy), line, font=font(SANS, 10), fill=INK)
            cy += 13
        if i < len(NUMBERS) - 1:
            draw.line([x + 10, cy + 8, x + w - 10, cy + 8], fill=GOLD, width=1)
            cy += 26


def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # Masthead: navy band, gold small caps, giant white serif date.
    d.rectangle([0, 0, W, 100], fill=NAVY)
    d.rectangle([0, 100, W, 103], fill=GOLD)
    d.text((16, 8), "THE DAY IN WORLD NEWS", font=font(SANS_B, 12), fill=GOLD)
    right = "33 STORIES \u00b7 6 CONTINENTS \u00b7 ONE DAY"
    d.text((W - 16 - d.textlength(right, font=font(SANS_B, 12)), 8),
           right, font=font(SANS_B, 12), fill=GOLD)
    date_size = 52
    while (d.textlength("Wednesday 18 November 2026", font=font(SERIF_B, date_size))
           > 960 and date_size > 30):
        date_size -= 2
    d.text((16, 30), "Wednesday 18 November 2026",
           font=font(SERIF_B, date_size), fill=(255, 255, 255))
    # Lead row (3 tall panels) + two rows of 5.
    xs3 = [16, 349, 682]
    for i, x in enumerate(xs3):
        draw_panel(d, MAINS[i], x, 108, 326, 196, lead=True)
    xs5 = [16, 216, 416, 616, 816]
    k = 3
    for x in xs5:
        draw_panel(d, MAINS[k], x, 312, 192, 150, lead=False)
        k += 1
    for x in xs5:
        draw_panel(d, MAINS[k], x, 470, 192, 150, lead=False)
        k += 1
    # Bottom: map left, also-on middle, numbers sidebar right.
    d.text((16, 632), "WHERE IT HAPPENED", font=font(SANS_B, 14), fill=NAVY)
    d.text((372, 632), "ALSO ON WEDNESDAY 18 NOVEMBER",
           font=font(SANS_B, 14), fill=NAVY)
    d.line([16, 652, 1008, 652], fill=GOLD, width=2)
    draw_map(d, 16, 660, 340, 250)
    lx = 16
    for name, col in LEGEND:
        d.ellipse([lx, 920, lx + 9, 929], fill=col)
        d.text((lx + 13, 918), name, font=font(SANS, 10), fill=INK)
        lx += 13 + d.textlength(name, font=font(SANS, 10)) + 14
    for i, (num, region, txt, _lon, _lat) in enumerate(ALSO):
        col_x = 372 if i < 10 else 616
        row_y = 662 + (i % 10) * 20
        d.text((col_x, row_y), str(num) + ".", font=font(SANS_B, 10),
               fill=REGION_COLOUR[region])
        also_fnt = font(SANS, 10)
        limit = 616 - (372 + 24) - 6
        shown = txt
        if d.textlength(shown, font=also_fnt) > limit:
            while shown and d.textlength(shown + "\u2026", font=also_fnt) > limit:
                shown = shown[:-1].rstrip()
            shown = shown + "\u2026"
        d.text((col_x + 24, row_y), shown, font=also_fnt, fill=INK)
    draw_sidebar(d, 856, 660, 152, 280)
    # Footer, centred, muted.
    centred(d, W / 2, 972,
            "Every story here happened or was first reported on Wednesday 18 November 2026; contested claims are marked as claims.",
            font(SERIF, 11), MUTED)
    centred(d, W / 2, 990,
            "Sources: Reuters, AP, AFP, BBC, Al Jazeera, WHO, UN. Original drawings.",
            font(SERIF, 11), MUTED)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out)
    print("wrote", out, os.path.getsize(out), "bytes")
    if ERRORS:
        print("FIT ERRORS:")
        for e in ERRORS:
            print(" -", e)
        sys.exit(1)


if __name__ == "__main__":
    build()
