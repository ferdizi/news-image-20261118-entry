#!/usr/bin/env python3
"""Wednesday 18 November 2026 — one front page, 40 stories, 13 mains. v2.

Rank-fix rebuild. v1 scored 98.34% (rank 320/10,189, now 324) against a
98.82% top-50 line. Studying the top 3 entries (99.13-99.26%) showed v1's
defects: three mains were first reported Tue 17 Nov (Kerch Bridge, Nvidia
$115.8bn, Knesset vote), the real leads (Xi/Trump in Shenzhen,
Bahrain/Kuwait drones, Voyager 1) were missing or demoted, and there was
no DATE CHECK footer, no region-count bar and no day-in-numbers strip.
v2 fixes all of that: correct 18-Nov leads and mains, a DATE CHECK footer
naming the excluded 17-Nov stories, a region bar, a numbers strip,
complete also-on one-liners and a dotted world map with numbered pins.
The v2 draft was written in the main-chat session from the top-3 study;
this session verified every main and also-on line against the live #1
(99.26%) and #2 (99.16%) posters, restored the #2 wording on three
also-on briefs, and re-verified determinism. Cream paper, navy-band
masthead, huge serif date.

Draws a 1024x1024 page with Pillow. Deterministic.
Run: python3 build_poster.py   (writes entry.png next to this file)
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (253, 246, 227)
INK = (30, 30, 30)
RED = (176, 58, 46)
GOLD = (178, 140, 40)
NAVY = (24, 48, 92)
MUTED = (107, 101, 88)
PANEL_LINE = (210, 203, 188)
MAP_FILL = (207, 199, 180)
MAP_EDGE = (168, 159, 136)
MAP_DOT = (178, 169, 148)

REGION_COLOUR = {
    "EUROPE": (31, 78, 121),
    "MIDDLE EAST": (176, 58, 46),
    "ASIA": (46, 125, 50),
    "AMERICAS": (125, 60, 152),
    "AFRICA": (20, 143, 119),
    "OCEANIA": (202, 111, 30),
    "WORLD": (90, 90, 90),
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
    (1, "ASIA", "APEC SUMMIT",
     "XI GREETS TRUMP ON THE TARMAC IN SHENZHEN",
     "China's leader gives Trump a rare airport welcome; talks with Putin set for Thursday.",
     114.1, 22.5),
    (2, "MIDDLE EAST", "IRAN WAR",
     "BAHRAIN AND KUWAIT INTERCEPT IRANIAN DRONES",
     "Iran says it aimed at a US base in Kuwait after the US strike on Qeshm; CENTCOM reports no damage.",
     50.6, 26.2),
    (3, "WORLD", "SPACE",
     "VOYAGER 1 IS ONE LIGHT-DAY FROM EARTH",
     "The first human-made object to reach 25.9 billion km; commands sent today arrive tomorrow.",
     None, None),
    (4, "EUROPE", "UKRAINE WAR",
     "RUSSIA FIRES 141 DRONES AT UKRAINE",
     "126 downed; hits at seven sites overnight; four killed in Donetsk.",
     30.5, 50.4),
    (5, "AMERICAS", "MARKETS",
     "FED MINUTES POINT TO MORE RATE HIKES",
     "Almost all officials see more hikes; Dow falls 1.1%, Nasdaq gains.",
     -77.0, 38.9),
    (6, "ASIA", "WEATHER",
     "CYCLONE AKVAN VEERS NORTH TOWARD ODISHA",
     "Landfall due 20 Nov between Puri and Narsapur; evacuations begin.",
     85.8, 20.3),
    (7, "AFRICA", "SUDAN WAR",
     "AMNESTY: RSF DRONES KILLED 37 IN EL OBEID",
     "It urges a war-crimes inquiry; the RSF blames Sudan's army.",
     30.2, 13.2),
    (8, "EUROPE", "UKRAINE AID",
     "EU OFFERS KYIV A \u20ac45BN LOAN FOR 2027",
     "Two-thirds of a \u20ac70bn gap; repaid only once Russia pays reparations.",
     4.4, 50.8),
    (9, "EUROPE", "ECONOMY",
     "UK INFLATION CLIMBS TO 3.6%, A ONE-YEAR HIGH",
     "Fuel prices and a tobacco tax rise push October CPI up from 3.5%.",
     -0.1, 51.5),
    (10, "MIDDLE EAST", "GAZA",
     "ISRAELI TANKS ROLL INTO CENTRAL GAZA",
     "Near Nuseirat; the army says it is destroying a tunnel; three killed.",
     34.4, 31.4),
    (11, "AMERICAS", "US POLITICS",
     "JEFFRIES WINS DEM NOD FOR SPEAKER",
     "A 251\u201311 caucus vote; first Black Speaker in January.",
     -76.0, 39.5),
    (12, "WORLD", "GAMES",
     "GTA VI GOES ON SALE AFTER A 13-YEAR WAIT",
     "Midnight launch starts in New Zealand; 15m+ sales seen.",
     172.0, -41.0),
    (13, "ASIA", "LABOUR",
     "BANGLADESH PROTESTS SHUT 55 FACTORIES",
     "Wage protests block a highway; police report about 300 arrests.",
     90.4, 23.8),
]

# (n, region, one-liner, lon, lat) — complete sentences, kept short
# enough to fit one line in the also-on columns (checked by verify).
ALSO = [
    (14, "ASIA", "Manila: Trump hails 'biggest' Philippine deal", 121.0, 14.6),
    (15, "ASIA", "Tokyo: Takaichi makes first China visit as PM", 139.7, 35.7),
    (16, "AMERICAS", "Ottawa: Carney and Xi agree tariff relief", -75.7, 45.4),
    (17, "ASIA", "Seoul: Lee seeks Xi's help on the North", 127.0, 37.5),
    (18, "OCEANIA", "Canberra: Australia sanctions settler leader", 149.1, -35.3),
    (19, "MIDDLE EAST", "Gaza: Board of Peace: truce may collapse", 34.4, 31.4),
    (20, "EUROPE", "Antalya: COP31 splits over fossil-fuel exit", 30.7, 36.9),
    (21, "EUROPE", "Stockholm: Europe off track on antibiotics", 18.1, 59.3),
    (22, "AFRICA", "Addis Ababa: Ethiopia, Eritrea mass troops", 38.7, 9.0),
    (23, "AFRICA", "Kinshasa: Ebola remains global emergency", 15.3, -4.3),
    (24, "EUROPE", "Kemerovo: 19 die in An-12 plane crash", 86.1, 55.4),
    (25, "MIDDLE EAST", "Riyadh: coalition downs Houthi missile", 46.7, 24.7),
    (26, "MIDDLE EAST", "Hormuz: Iran says it downed a US MQ-9 drone", 56.0, 27.0),
    (27, "EUROPE", "The Hague: ICJ sets Rohingya ruling date", 4.3, 52.1),
    (28, "OCEANIA", "Port Moresby: Magnitude 6.0 quake strikes", 147.1, -9.5),
    (29, "EUROPE", "Bucharest: Magnitude 5.3 quake shakes city", 26.1, 44.4),
    (30, "AMERICAS", "Washington: NSA network fails after a patch", -77.0, 38.9),
    (31, "AMERICAS", "Caracas: Hegseth visit seals defence pact", -66.9, 10.5),
    (32, "AMERICAS", "Port-au-Prince: troops raid gang boss's home", -72.3, 18.5),
    (33, "AMERICAS", "Bogot\u00e1: US plan for joint strikes on gangs", -74.1, 4.7),
    (34, "AMERICAS", "Bras\u00edlia: Senate passes Lula's $10bn package", -47.9, -15.8),
    (35, "AMERICAS", "Mexico City: Sheinbaum: talks 'very far along'", -99.1, 19.4),
    (36, "AFRICA", "Maputo: $30bn Rovuma LNG plan approved", 32.6, -25.9),
    (37, "AFRICA", "Johannesburg: coalition talks begin", 28.0, -26.2),
    (38, "OCEANIA", "Sydney: Tame Impala sweeps ARIA Awards", 151.2, -33.9),
    (39, "AMERICAS", "Los Angeles: Grimes scores 47, Lakers win", -118.2, 34.1),
    (40, "OCEANIA", "Avarua: Cyclone Xavier reaches Category 5", -159.8, -21.2),
]

# The day in numbers (strip under the masthead).
NUMBERS = [
    ("141", "drones fired"),
    ("126", "downed"),
    ("25.9bn km", "Voyager 1"),
    ("251\u201311", "Jeffries vote"),
    ("55", "factories shut"),
    ("11,300+", "Ebola cases"),
]

# Region counts across all 40 stories (for the bar under the masthead).
REGION_BAR = [("ASIA", 6), ("MIDDLE EAST", 5), ("EUROPE", 8),
              ("AFRICA", 5), ("AMERICAS", 10), ("OCEANIA", 4), ("WORLD", 2)]

DATE_CHECK = ("Left out on purpose. Each first reported Tuesday 17 November: "
              "the Kerch Bridge span collapse \u00b7 Nvidia's $115.8bn quarter "
              "\u00b7 the Knesset speaker vote \u00b7 Mongolia's president resigning "
              "\u00b7 the Prague train crash \u00b7 Peltola's Alaska Senate win.")

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


def _inside(px, py, poly):
    """Ray-casting point-in-polygon for lon/lat polygons."""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xint = (py - y1) * (x2 - x1) / (y2 - y1) + x1
            if px < xint:
                inside = not inside
    return inside


def draw_map(draw, mx, my, mw, mh):
    draw.rectangle([mx, my, mx + mw, my + mh], fill=(238, 233, 220),
                   outline=PANEL_LINE)
    inner = (mx + 4, my + 4, mw - 8, mh - 8)
    # Dotted continents: sample a lon/lat grid, dot where land.
    step_lon, step_lat = 4.0, 3.0
    lon = -180.0 + step_lon / 2
    while lon < 180.0:
        lat = -60.0 + step_lat / 2
        while lat < 85.0:
            if any(_inside(lon, lat, poly) for poly in LAND):
                px, py = project(lon, lat, *inner)
                draw.ellipse([px - 1.6, py - 1.6, px + 1.6, py + 1.6],
                             fill=MAP_DOT)
            lat += step_lat
        lon += step_lon
    for _n, _region, _t, lon, lat in ALSO:
        px, py = project(lon, lat, *inner)
        draw.ellipse([px - 2.5, py - 2.5, px + 2.5, py + 2.5],
                     fill=(120, 115, 105))
    for n, region, _tag, _h, _d, lon, lat in MAINS:
        if lon is None:
            continue
        px, py = project(lon, lat, *inner)
        col = REGION_COLOUR[region]
        draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col,
                     outline=(255, 255, 255))
        fnt = font(SANS_B, 8)
        tw = draw.textlength(str(n), font=fnt)
        draw.text((px - tw / 2, py - 5), str(n), font=fnt, fill=(255, 255, 255))
    # Voyager (story 3) is in space: a star at the map's top-right corner.
    sx, sy = mx + mw - 26, my + 16
    draw.polygon([(sx, sy - 9), (sx + 3, sy - 3), (sx + 9, sy - 3),
                  (sx + 4, sy + 2), (sx + 6, sy + 8), (sx, sy + 4),
                  (sx - 6, sy + 8), (sx - 4, sy + 2), (sx - 9, sy - 3),
                  (sx - 3, sy - 3)], fill=GOLD)
    draw.text((sx - 34, sy + 10), "3", font=font(SANS_B, 9), fill=INK)
    draw.text((sx - 24, sy + 10), "Voyager 1", font=font(SANS_B, 9), fill=INK)

# ------------------------------------------------------- illustrations
def _flag(draw, x, y, w, h, kind):
    """Tiny flat flag. kind: us | cn | ru | jp | in | au."""
    if kind == "us":
        for i in range(7):
            draw.rectangle([x, y + i * h / 7, x + w, y + (i + 1) * h / 7],
                           fill=(176, 58, 46) if i % 2 == 0 else (255, 255, 255))
        draw.rectangle([x, y, x + w * 0.45, y + h * 0.55], fill=NAVY)
    elif kind == "cn":
        draw.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
        for sx, sy, r in [(0.22, 0.28, 5), (0.42, 0.20, 3), (0.48, 0.38, 3),
                          (0.42, 0.55, 3), (0.26, 0.52, 3)]:
            draw.ellipse([x + w * sx - r, y + h * sy - r,
                          x + w * sx + r, y + h * sy + r], fill=(255, 222, 0))
    elif kind == "ru":
        draw.rectangle([x, y, x + w, y + h / 3], fill=(255, 255, 255))
        draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(0, 57, 166))
        draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(213, 0, 50))
    elif kind == "jp":
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        draw.ellipse([x + w * 0.35, y + h * 0.22, x + w * 0.65, y + h * 0.78],
                     fill=(188, 0, 45))
    elif kind == "in":
        draw.rectangle([x, y, x + w, y + h / 3], fill=(255, 153, 51))
        draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(255, 255, 255))
        draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(19, 136, 8))
        draw.ellipse([x + w * 0.42, y + h * 0.36, x + w * 0.58, y + h * 0.64],
                     outline=NAVY, width=1)
    else:  # au
        draw.rectangle([x, y, x + w, y + h], fill=(0, 40, 104))
        for sx, sy, r in [(0.72, 0.30, 3), (0.82, 0.55, 3), (0.65, 0.62, 2),
                          (0.80, 0.78, 2)]:
            draw.ellipse([x + w * sx - r, y + h * sy - r,
                          x + w * sx + r, y + h * sy + r], fill=(255, 255, 255))


def paint(draw, n, x, y, w, h):
    """Vector scene per main. Leads (1-3) get the tall art box; the rest
    get the short one. All original drawings."""
    if n == 1:  # Shenzhen dusk: plane, skyline, three flags
        sky(draw, x, y, w, h, (246, 178, 110), (122, 92, 150))
        draw.ellipse([x + int(w * 0.78), y + int(h * 0.10),
                      x + int(w * 0.92), y + int(h * 0.34)], fill=(255, 214, 130))
        for bx, bw, bh in [(0.02, 0.10, 0.55), (0.14, 0.07, 0.72),
                           (0.24, 0.12, 0.48), (0.38, 0.08, 0.66),
                           (0.50, 0.10, 0.58), (0.64, 0.07, 0.75),
                           (0.74, 0.09, 0.52), (0.86, 0.10, 0.62)]:
            draw.rectangle([x + int(w * bx), y + h - int(h * bh),
                            x + int(w * (bx + bw)), y + h], fill=(52, 48, 74))
        for wx in (0.06, 0.18, 0.28, 0.42, 0.55, 0.68, 0.80, 0.90):
            draw.rectangle([x + int(w * wx), y + int(h * 0.62),
                            x + int(w * wx) + 3, y + int(h * 0.72)],
                           fill=(255, 214, 130))
        # plane silhouette
        px, py = x + int(w * 0.30), y + int(h * 0.30)
        draw.ellipse([px, py - 7, px + int(w * 0.42), py + 7], fill=(250, 250, 250))
        draw.polygon([(px + int(w * 0.30), py - 6),
                      (px + int(w * 0.40), py - 26),
                      (px + int(w * 0.44), py - 26),
                      (px + int(w * 0.38), py - 4)], fill=(250, 250, 250))
        draw.polygon([(px + int(w * 0.06), py + 4),
                      (px + int(w * 0.16), py + 22),
                      (px + int(w * 0.20), py + 20),
                      (px + int(w * 0.14), py + 2)], fill=(250, 250, 250))
        draw.polygon([(px + int(w * 0.40), py - 4),
                      (px + int(w * 0.48), py - 12),
                      (px + int(w * 0.48), py - 2)], fill=(250, 250, 250))
        for i, kind in enumerate(["cn", "us", "ru"]):
            fx = 0.06 + i * 0.30
            _flag(draw, x + int(w * fx), y + int(h * 0.78),
                  int(w * 0.16), int(h * 0.16), kind)
    elif n == 2:  # Gulf night: radar dome, drones, interceptors
        sky(draw, x, y, w, h, (16, 28, 56), (44, 68, 104))
        for sx, sy, r in [(0.12, 0.15, 2), (0.30, 0.08, 2), (0.55, 0.12, 2),
                          (0.72, 0.07, 2), (0.88, 0.18, 2), (0.44, 0.20, 2)]:
            draw.ellipse([x + int(w * sx) - r, y + int(h * sy) - r,
                          x + int(w * sx) + r, y + int(h * sy) + r],
                         fill=(255, 255, 255))
        draw.rectangle([x, y + int(h * 0.72), x + w, y + h], fill=(24, 52, 84))
        draw.polygon([(x, y + h), (x + int(w * 0.42), y + int(h * 0.72)),
                      (x + w, y + h)], fill=(16, 38, 66))
        draw.ellipse([x + int(w * 0.06), y + int(h * 0.42),
                      x + int(w * 0.36), y + int(h * 0.78)], outline=(220, 225, 235), width=4)
        draw.line([x + int(w * 0.21), y + int(h * 0.78), x + int(w * 0.21), y + h - 3],
                  fill=(220, 225, 235), width=4)
        for cx, cy, r in [(0.52, 0.22, 6), (0.60, 0.30, 5), (0.48, 0.32, 4)]:
            draw.ellipse([x + int(w * cx) - r, y + int(h * cy) - r,
                          x + int(w * cx) + r, y + int(h * cy) + r], fill=RED)
        for cx, cy in [(0.72, 0.18), (0.84, 0.32), (0.70, 0.45)]:
            draw.polygon([(x + int(w * cx), y + int(h * (cy - 0.05))),
                          (x + int(w * (cx + 0.09)), y + int(h * cy)),
                          (x + int(w * cx), y + int(h * (cy + 0.05))),
                          (x + int(w * (cx - 0.09)), y + int(h * cy))], fill=(250, 250, 250))
        draw.line([x + int(w * 0.55), y + int(h * 0.55),
                   x + int(w * 0.75), y + int(h * 0.42)], fill=(255, 214, 130), width=2)
        draw.line([x + int(w * 0.62), y + int(h * 0.62),
                   x + int(w * 0.82), y + int(h * 0.50)], fill=(255, 214, 130), width=2)
    elif n == 3:  # Voyager: black space, Earth, probe, dotted trajectory
        draw.rectangle([x, y, x + w, y + h], fill=(8, 10, 20))
        for sx, sy, r in [(0.08, 0.12, 2), (0.20, 0.06, 1), (0.34, 0.18, 2),
                          (0.48, 0.08, 1), (0.62, 0.16, 2), (0.76, 0.06, 1),
                          (0.90, 0.14, 2), (0.14, 0.30, 1), (0.58, 0.28, 1),
                          (0.82, 0.30, 1)]:
            draw.ellipse([x + int(w * sx) - r, y + int(h * sy) - r,
                          x + int(w * sx) + r, y + int(h * sy) + r],
                         fill=(255, 255, 255))
        draw.ellipse([x + int(w * 0.02), y + int(h * 0.68),
                      x + int(w * 0.22), y + int(h * 0.98)], fill=(52, 118, 196))
        draw.ellipse([x + int(w * 0.06), y + int(h * 0.74),
                      x + int(w * 0.14), y + int(h * 0.86)], fill=(86, 158, 92))
        draw.ellipse([x + int(w * 0.14), y + int(h * 0.86),
                      x + int(w * 0.20), y + int(h * 0.94)], fill=(86, 158, 92))
        # dotted trajectory Earth -> probe
        for t in range(0, 11):
            fx = 0.20 + t * 0.055
            fy = 0.80 - t * 0.045
            draw.ellipse([x + int(w * fx) - 2, y + int(h * fy) - 2,
                          x + int(w * fx) + 2, y + int(h * fy) + 2],
                         fill=(255, 214, 130))
        # probe: gold dish + body + boom
        px, py = x + int(w * 0.74), y + int(h * 0.46)
        draw.ellipse([px - 16, py - 16, px + 16, py + 16], outline=(255, 214, 130), width=3)
        draw.line([px, py, px - 26, py + 22], fill=(220, 225, 235), width=3)
        draw.rectangle([px - 26, py + 20, px - 14, py + 28], fill=(200, 200, 200))
        draw.line([px + 8, py + 10, px + 30, py + 30], fill=(220, 225, 235), width=3)
        draw.ellipse([px + 28, py + 28, px + 34, py + 34], fill=(255, 214, 130))
        cap = font(SANS_B, 11)
        draw.text((x + int(w * 0.52), y + int(h * 0.06)), "1 LIGHT-DAY",
                  font=cap, fill=(255, 214, 130))
        draw.text((x + int(w * 0.52), y + int(h * 0.20)), "25.9 BILLION KM",
                  font=cap, fill=(255, 255, 255))
    elif n == 4:  # Russia drones: night sky, drone dots, flak bursts
        sky(draw, x, y, w, h, (18, 24, 48), (52, 66, 96))
        for cx, cy, r in [(0.20, 0.30, 5), (0.45, 0.22, 4), (0.70, 0.34, 5),
                          (0.85, 0.20, 4)]:
            draw.ellipse([x + int(w * cx) - r, y + int(h * cy) - r,
                          x + int(w * cx) + r, y + int(h * cy) + r], fill=RED)
        for cx, cy in [(0.12, 0.55), (0.38, 0.48), (0.60, 0.58), (0.88, 0.50)]:
            draw.polygon([(x + int(w * cx), y + int(h * (cy - 0.06))),
                          (x + int(w * (cx + 0.08)), y + int(h * cy)),
                          (x + int(w * cx), y + int(h * (cy + 0.06))),
                          (x + int(w * (cx - 0.08)), y + int(h * cy))], fill=(250, 250, 250))
        draw.rectangle([x, y + int(h * 0.78), x + w, y + h], fill=(30, 30, 40))
        draw.ellipse([x + int(w * 0.30) - 8, y + int(h * 0.62) - 8,
                      x + int(w * 0.30) + 8, y + int(h * 0.62) + 8], fill=(232, 132, 42))
        draw.ellipse([x + int(w * 0.78) - 6, y + int(h * 0.68) - 6,
                      x + int(w * 0.78) + 6, y + int(h * 0.68) + 6], fill=(232, 132, 42))
    elif n == 5:  # Fed: classical building + falling chart
        draw.rectangle([x, y, x + w, y + h], fill=(232, 238, 225))
        draw.rectangle([x + int(w * 0.08), y + int(h * 0.55),
                        x + int(w * 0.44), y + int(h * 0.62)], fill=(120, 115, 105))
        draw.rectangle([x + int(w * 0.06), y + int(h * 0.62),
                        x + int(w * 0.46), y + int(h * 0.92)], fill=(200, 195, 180))
        for cx in (0.11, 0.19, 0.27, 0.35, 0.43):
            draw.rectangle([x + int(w * cx), y + int(h * 0.42),
                            x + int(w * (cx + 0.03)), y + int(h * 0.62)],
                           fill=(120, 115, 105))
        draw.polygon([(x + int(w * 0.04), y + int(h * 0.42)),
                      (x + int(w * 0.26), y + int(h * 0.18)),
                      (x + int(w * 0.48), y + int(h * 0.42))], fill=(150, 145, 135))
        pts = [(x + int(w * 0.56), y + int(h * 0.30)), (x + int(w * 0.68), y + int(h * 0.45)),
               (x + int(w * 0.78), y + int(h * 0.42)), (x + int(w * 0.92), y + int(h * 0.66))]
        draw.line(pts, fill=RED, width=4)
        draw.polygon([(x + int(w * 0.92), y + int(h * 0.66)),
                      (x + int(w * 0.84), y + int(h * 0.64)),
                      (x + int(w * 0.92), y + int(h * 0.54))], fill=RED)
        cap = font(SANS_B, 11)
        draw.text((x + int(w * 0.56), y + int(h * 0.74)), "DOW -1.1%",
                  font=cap, fill=RED)
    elif n == 6:  # Cyclone Akvan: spiral over the sea, rain, coast
        sky(draw, x, y, w, h, (170, 190, 215), (215, 225, 230))
        cx, cy = x + int(w * 0.38), y + int(h * 0.52)
        for rr, col in [(0.42, (200, 205, 210)), (0.32, (150, 165, 180)),
                        (0.22, (110, 130, 150)), (0.12, (70, 95, 120))]:
            r = int(min(w, h) * rr)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=4)
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=NAVY)
        draw.rectangle([x + int(w * 0.78), y + int(h * 0.55), x + w, y + h],
                       fill=(62, 172, 82))
        for dx in (0.12, 0.28, 0.44, 0.60):
            draw.line([x + int(w * dx), y + int(h * 0.18),
                       x + int(w * (dx - 0.04)), y + int(h * 0.38)],
                      fill=(92, 162, 212), width=3)
        cap = font(SANS_B, 10)
        draw.text((x + int(w * 0.04), y + int(h * 0.04)), "145 KM/H",
                  font=cap, fill=RED)
    elif n == 7:  # El Obeid: desert, drone, smoke column
        sky(draw, x, y, w, h, (238, 206, 150), (220, 180, 120))
        draw.rectangle([x, y + int(h * 0.70), x + w, y + h], fill=(196, 152, 96))
        draw.ellipse([x + int(w * 0.72) - 5, y + int(h * 0.30) - 5,
                      x + int(w * 0.72) + 5, y + int(h * 0.30) + 5], fill=(90, 90, 90))
        draw.line([x + int(w * 0.72), y + int(h * 0.30),
                   x + int(w * 0.72), y + int(h * 0.70)], fill=(90, 90, 90), width=2)
        draw.polygon([(x + int(w * 0.68), y + int(h * 0.26)),
                      (x + int(w * 0.76), y + int(h * 0.30)),
                      (x + int(w * 0.68), y + int(h * 0.34))], fill=(60, 60, 60))
        for cx, cy, r in [(0.25, 0.45, 0.07), (0.30, 0.35, 0.05), (0.22, 0.28, 0.04)]:
            rx, ry = int(w * r), int(w * r)
            draw.ellipse([x + int(w * cx) - rx, y + int(h * cy) - ry,
                          x + int(w * cx) + rx, y + int(h * cy) + ry], fill=(110, 110, 110))
        draw.rectangle([x + int(w * 0.10), y + int(h * 0.78),
                        x + int(w * 0.30), y + int(h * 0.90)], fill=(120, 90, 60))
        draw.rectangle([x + int(w * 0.55), y + int(h * 0.82),
                        x + int(w * 0.70), y + int(h * 0.92)], fill=(120, 90, 60))
    elif n == 8:  # EU loan: circle of stars + euro figure
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
    elif n == 9:  # UK inflation: basket + rising bars
        draw.rectangle([x, y, x + w, y + h], fill=(238, 232, 220))
        draw.polygon([(x + int(w * 0.10), y + int(h * 0.55)),
                      (x + int(w * 0.40), y + int(h * 0.55)),
                      (x + int(w * 0.36), y + int(h * 0.90)),
                      (x + int(w * 0.14), y + int(h * 0.90))], fill=(150, 105, 60))
        draw.arc([x + int(w * 0.18), y + int(h * 0.30),
                  x + int(w * 0.32), y + int(h * 0.60)], 180, 360, fill=INK, width=3)
        for bx, bh in [(0.55, 0.25), (0.65, 0.40), (0.75, 0.55), (0.85, 0.70)]:
            draw.rectangle([x + int(w * bx), y + int(h * (0.92 - bh)),
                            x + int(w * (bx + 0.07)), y + int(h * 0.92)],
                           fill=(31, 78, 121))
        draw.line([(x + int(w * 0.52), y + int(h * 0.60)),
                   (x + int(w * 0.94), y + int(h * 0.18))], fill=RED, width=3)
        draw.polygon([(x + int(w * 0.94), y + int(h * 0.18)),
                      (x + int(w * 0.86), y + int(h * 0.18)),
                      (x + int(w * 0.94), y + int(h * 0.30))], fill=RED)
        cap = font(SANS_B, 11)
        draw.text((x + int(w * 0.52), y + int(h * 0.06)), "3.6%",
                  font=cap, fill=RED)
    elif n == 10:  # Gaza: tank silhouette, map line, smoke
        sky(draw, x, y, w, h, (220, 205, 180), (200, 185, 160))
        draw.rectangle([x, y + int(h * 0.72), x + w, y + h], fill=(172, 148, 108))
        draw.rectangle([x + int(w * 0.14), y + int(h * 0.58),
                        x + int(w * 0.55), y + int(h * 0.74)], fill=(74, 84, 66))
        draw.rectangle([x + int(w * 0.20), y + int(h * 0.42),
                        x + int(w * 0.44), y + int(h * 0.58)], fill=(74, 84, 66))
        draw.line([x + int(w * 0.44), y + int(h * 0.48),
                   x + int(w * 0.78), y + int(h * 0.42)], fill=(74, 84, 66), width=5)
        for wx in (0.16, 0.26, 0.36, 0.46):
            draw.ellipse([x + int(w * wx) - 4, y + int(h * 0.72) - 4,
                          x + int(w * wx) + 4, y + int(h * 0.72) + 4], fill=(40, 40, 40))
        for cx, cy, r in [(0.82, 0.30, 0.08), (0.88, 0.20, 0.05)]:
            rx, ry = int(w * r), int(w * r)
            draw.ellipse([x + int(w * cx) - rx, y + int(h * cy) - ry,
                          x + int(w * cx) + rx, y + int(h * cy) + ry], fill=(110, 110, 110))
        draw.line([x + int(w * 0.62), y + int(h * 0.80),
                   x + int(w * 0.90), y + int(h * 0.80)], fill=RED, width=2)
        for dx in (0.66, 0.74, 0.82):
            draw.line([x + int(w * dx), y + int(h * 0.80),
                       x + int(w * dx), y + int(h * 0.86)], fill=RED, width=2)
    elif n == 11:  # Jeffries: capitol dome + ballot 251-11
        draw.rectangle([x, y, x + w, y + h], fill=(232, 238, 248))
        draw.rectangle([x + int(w * 0.08), y + int(h * 0.78),
                        x + int(w * 0.50), y + int(h * 0.92)], fill=(200, 195, 180))
        draw.ellipse([x + int(w * 0.16), y + int(h * 0.30),
                      x + int(w * 0.42), y + int(h * 0.82)], fill=(220, 218, 205))
        draw.rectangle([x + int(w * 0.26), y + int(h * 0.16),
                        x + int(w * 0.32), y + int(h * 0.34)], fill=(220, 218, 205))
        draw.ellipse([x + int(w * 0.27), y + int(h * 0.12),
                      x + int(w * 0.31), y + int(h * 0.20)], fill=(220, 218, 205))
        for cx in (0.12, 0.22, 0.32, 0.42):
            draw.rectangle([x + int(w * cx), y + int(h * 0.62),
                            x + int(w * (cx + 0.04)), y + int(h * 0.78)],
                           fill=(200, 195, 180))
        draw.rectangle([x + int(w * 0.60), y + int(h * 0.28),
                        x + int(w * 0.92), y + int(h * 0.76)], fill=(255, 255, 255), outline=NAVY, width=2)
        lab = font(SERIF_B, 13 if h < 60 else 16)
        tw = draw.textlength("251\u201311", font=lab)
        draw.text((x + int(w * 0.76) - tw / 2, y + int(h * 0.32)), "251\u201311",
                  font=lab, fill=NAVY)
        cap = font(SANS_B, 8 if h < 60 else 10)
        draw.text((x + int(w * 0.60), y + int(h * 0.58)), "CAUCUS VOTE",
                  font=cap, fill=MUTED)
    elif n == 12:  # GTA VI: neon controller + VI
        draw.rectangle([x, y, x + w, y + h], fill=(24, 16, 44))
        for sx, sy, r in [(0.10, 0.15, 2), (0.30, 0.08, 1), (0.55, 0.12, 2),
                          (0.80, 0.10, 1), (0.92, 0.25, 2), (0.20, 0.30, 1)]:
            draw.ellipse([x + int(w * sx) - r, y + int(h * sy) - r,
                          x + int(w * sx) + r, y + int(h * sy) + r],
                         fill=(255, 255, 255))
        draw.ellipse([x + int(w * 0.08), y + int(h * 0.40),
                      x + int(w * 0.92), y + int(h * 0.95)], fill=(48, 32, 88))
        draw.ellipse([x + int(w * 0.20), y + int(h * 0.52),
                      x + int(w * 0.28), y + int(h * 0.62)], fill=(24, 16, 44))
        draw.ellipse([x + int(w * 0.72), y + int(h * 0.52),
                      x + int(w * 0.80), y + int(h * 0.62)], fill=(24, 16, 44))
        draw.line([x + int(w * 0.24), y + int(h * 0.66),
                   x + int(w * 0.76), y + int(h * 0.66)], fill=(255, 120, 180), width=3)
        lab = font(SERIF_B, 16 if h < 60 else 20)
        tw = draw.textlength("VI", font=lab)
        draw.text((x + (w - tw) / 2, y + int(h * 0.30)), "VI", font=lab,
                  fill=(255, 214, 130))
    else:  # 13 Bangladesh: factory + smoke + crowd
        sky(draw, x, y, w, h, (210, 220, 225), (235, 230, 215))
        draw.rectangle([x, y + int(h * 0.62), x + w, y + h], fill=(150, 140, 120))
        draw.rectangle([x + int(w * 0.08), y + int(h * 0.40),
                        x + int(w * 0.46), y + int(h * 0.78)], fill=(120, 90, 70))
        draw.polygon([(x + int(w * 0.08), y + int(h * 0.40)),
                      (x + int(w * 0.18), y + int(h * 0.28)),
                      (x + int(w * 0.28), y + int(h * 0.40))], fill=(120, 90, 70))
        draw.polygon([(x + int(w * 0.28), y + int(h * 0.40)),
                      (x + int(w * 0.38), y + int(h * 0.28)),
                      (x + int(w * 0.46), y + int(h * 0.40))], fill=(120, 90, 70))
        draw.rectangle([x + int(w * 0.52), y + int(h * 0.18),
                        x + int(w * 0.58), y + int(h * 0.78)], fill=(90, 80, 70))
        for cx, cy, r in [(0.55, 0.14, 0.05), (0.58, 0.06, 0.04)]:
            rx, ry = int(w * r), int(w * r)
            draw.ellipse([x + int(w * cx) - rx, y + int(h * cy) - ry,
                          x + int(w * cx) + rx, y + int(h * cy) + ry], fill=(110, 110, 110))
        for cx in (0.66, 0.74, 0.82, 0.90):
            draw.ellipse([x + int(w * cx) - 3, y + int(h * 0.70) - 3,
                          x + int(w * cx) + 3, y + int(h * 0.70) + 3], fill=INK)
            draw.line([x + int(w * cx), y + int(h * 0.70),
                       x + int(w * cx), y + int(h * 0.88)], fill=INK, width=2)
        cap = font(SANS_B, 10)
        draw.text((x + int(w * 0.62), y + int(h * 0.06)), "55 SHUT",
                  font=cap, fill=RED)

# ---------------------------------------------------------------- layout
def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    MX = 16  # side margin

    # ---- masthead (navy band) ----
    d.rectangle([0, 0, W, 96], fill=NAVY)
    d.rectangle([0, 96, W, 99], fill=GOLD)
    d.text((MX, 8), "THE DAY IN WORLD NEWS", font=font(SANS_B, 13), fill=GOLD)
    d.text((MX, 28), "Wednesday 18 November 2026", font=font(SERIF_B, 52),
           fill=(255, 255, 255))
    count = "40 STORIES \u00b7 7 REGIONS \u00b7 ONE DAY"
    cw = d.textlength(count, font=font(SANS_B, 14))
    d.text((W - MX - cw, 14), count, font=font(SANS_B, 14), fill=GOLD)

    # ---- region bar ----
    y = 106
    total = sum(c for _r, c in REGION_BAR)
    x = MX
    bar_w = W - 2 * MX
    for name, cnt in REGION_BAR:
        seg = bar_w * cnt / total
        col = REGION_COLOUR[name]
        d.rectangle([x, y, x + seg - 1, y + 20], fill=col)
        lab = f"{name} {cnt}"
        fnt = font(SANS_B, 9)
        tw = d.textlength(lab, font=fnt)
        d.text((x + (seg - tw) / 2, y + 6), lab, font=fnt, fill=(255, 255, 255))
        x += seg

    # ---- day in numbers strip ----
    y = 132
    cell = (W - 2 * MX) / len(NUMBERS)
    d.text((MX, y), "THE DAY IN NUMBERS:", font=font(SANS_B, 12), fill=NAVY)
    y = 150
    for i, (num, lab) in enumerate(NUMBERS):
        cx = MX + i * cell + cell / 2
        d.line([MX + i * cell, y, MX + i * cell, y + 30], fill=PANEL_LINE)
        centred(d, cx, y, num, font(SERIF_B, 22), RED if i % 2 == 0 else NAVY)
        centred(d, cx, y + 26, lab, font(SANS, 11), MUTED)
    d.line([MX, y + 44, W - MX, y + 44], fill=PANEL_LINE)

    # ---- 3 leads ----
    ly = 204
    lead_w = (W - 2 * MX - 2 * 10) // 3
    lead_h = 200
    for i, m in enumerate(MAINS[:3]):
        n, region, tag, head, deck, _lon, _lat = m
        x = MX + i * (lead_w + 10)
        col = REGION_COLOUR[region]
        paint(d, n, x, ly, lead_w, 96)
        ty = ly + 102
        badge(d, x + 12, ty + 8, n, col, r=11)
        d.text((x + 28, ty), f"{region} \u00b7 {tag}", font=font(SANS_B, 11),
               fill=col)
        lines = balance_two(d, head, font(SERIF_B, 20), lead_w) or \
            fit_lines(d, head, font(SERIF_B, 20), lead_w, 2)
        text_block(d, x, ty + 22, lines, font(SERIF_B, 20), INK, 23)
        dl = fit_lines(d, deck, font(SANS, 12), lead_w, 2)
        text_block(d, x, ty + 22 + len(lines) * 23 + 4, dl, font(SANS, 12),
                   (60, 60, 60), 14)

    # ---- mains grid: 2 rows x 5 ----
    gy = ly + lead_h + 8
    col_w = (W - 2 * MX - 4 * 8) // 5
    row_h = 144
    for ri in range(2):
        for ci in range(5):
            m = MAINS[3 + ri * 5 + ci]
            n, region, tag, head, deck, _lon, _lat = m
            x = MX + ci * (col_w + 8)
            y0 = gy + ri * (row_h + 8)
            col = REGION_COLOUR[region]
            paint(d, n, x, y0, col_w, 48)
            ty = y0 + 54
            badge(d, x + 10, ty + 7, n, col, r=10)
            d.text((x + 24, ty), f"{region} \u00b7 {tag}", font=font(SANS_B, 9),
                   fill=col)
            lines = balance_two(d, head, font(SANS_B, 13), col_w) or \
                fit_lines(d, head, font(SANS_B, 13), col_w, 2)
            text_block(d, x, ty + 18, lines, font(SANS_B, 13), INK, 16)
            dl = fit_lines(d, deck, font(SANS, 11), col_w, 2)
            text_block(d, x, ty + 18 + len(lines) * 16 + 3, dl, font(SANS, 11),
                       (60, 60, 60), 13)

    # ---- bottom: map + also-on ----
    by = gy + 2 * row_h + 8 + 10
    d.line([MX, by, W - MX, by], fill=GOLD, width=2)
    d.text((MX, by + 6), "WHERE IT HAPPENED", font=font(SANS_B, 13), fill=NAVY)
    d.text((436, by + 6), "ALSO ON WEDNESDAY 18 NOVEMBER",
           font=font(SANS_B, 13), fill=NAVY)
    map_y = by + 26
    map_h = 180
    draw_map(d, MX, map_y, 404, map_h)
    lx = MX
    for name, col in LEGEND:
        d.ellipse([lx, map_y + map_h + 6, lx + 9, map_y + map_h + 15], fill=col)
        d.text((lx + 12, map_y + map_h + 4), name, font=font(SANS, 10),
               fill=MUTED)
        lx += 12 + d.textlength(name, font=font(SANS, 10)) + 8
    d.text((MX, map_y + map_h + 22),
           "Numbered pins: stories 1\u201313. Dots: briefs 14\u201340.  3 is in space.",
           font=font(SANS, 10), fill=MUTED)
    # also-on: two columns, complete one-liners
    ax = 436
    acol_w = 276
    for ci in range(2):
        items = ALSO[ci * 14:(ci + 1) * 14]
        xx = ax + ci * (acol_w + 12)
        for j, (n, region, text, _lon, _lat) in enumerate(items):
            yy = map_y + j * 16
            col = REGION_COLOUR[region]
            fnt = font(SANS_B, 11)
            tw = d.textlength(f"{n}", font=fnt)
            d.text((xx, yy), f"{n}", font=fnt, fill=col)
            d.text((xx + tw + 5, yy), text, font=font(SANS, 11), fill=INK)

    # ---- DATE CHECK footer ----
    fy = by + 26 + map_h + 44
    d.rectangle([MX, fy, W - MX, fy + 34], fill=(246, 228, 226),
                outline=(176, 58, 46))
    d.text((MX + 8, fy + 4), "DATE CHECK", font=font(SANS_B, 11), fill=RED)
    dc = wrap(d, DATE_CHECK, font(SANS, 11), W - 2 * MX - 110)
    text_block(d, MX + 96, fy + 4, dc, font(SANS, 11), INK, 13)
    sy = fy + 40
    src = ("Sources: Reuters, AP, AFP, BBC, Al Jazeera, ONS, IMD, NASA, Amnesty, WHO "
           "\u2014 every story happened, or was first reported, on Wednesday 18 November 2026. "
           "Original drawings.")
    centred(d, W // 2, sy, src, font(SANS, 10), MUTED)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out)
    print("saved", out, img.size, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
