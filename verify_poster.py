#!/usr/bin/env python3
"""Shape-check the 18 November poster v2 against every hard cap in RULES.txt.

Checks the built entry.png next to this file: it is a whole PNG, exactly
1024 by 1024 pixels, at most 1 MiB; the masthead names Wednesday
18 November 2026; all 13 numbered mains and the 27 also-on items are
present in the data the poster was drawn from; the DATE CHECK footer, the
day-in-numbers strip, the region bar and the dotted map exist; no
wrong-date story (Kerch, Nvidia, Knesset) sits in the mains; every
also-on one-liner fits its column in one line; and two builds are
byte-identical. Also writes a 300 px downscale for the legibility check
the judge applies. Exit 0 only when every cap passes.

Run: python3 verify_poster.py
"""
import hashlib
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PNG = os.path.join(HERE, "entry.png")
BUILDER = os.path.join(HERE, "build_poster.py")

failures = []


def check(name, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    with open(PNG, "rb") as fh:
        head = fh.read(8)
    check("PNG signature", head == b"\x89PNG\r\n\x1a\n",
          "first 8 bytes are the PNG magic")
    size = os.path.getsize(PNG)
    check("size at most 1 MiB", size <= 1048576, f"{size} bytes")
    img = Image.open(PNG)
    check("dimensions 1024x1024", img.size == (1024, 1024),
          f"got {img.size[0]}x{img.size[1]}")
    check("mode RGB", img.mode == "RGB", img.mode)

    sys.path.insert(0, HERE)
    import build_poster as bp

    check("13 mains in data", len(bp.MAINS) == 13, f"got {len(bp.MAINS)}")
    check("27 also-on items", len(bp.ALSO) == 27, f"got {len(bp.ALSO)}")
    check("40 stories total", len(bp.MAINS) + len(bp.ALSO) == 40)
    check("region bar sums to 40",
          sum(c for _r, c in bp.REGION_BAR) == 40,
          str(bp.REGION_BAR))
    check("6 numbers in strip", len(bp.NUMBERS) == 6)

    mains_src = str(bp.MAINS)
    for bad in ("KERCH", "NVIDIA", "KNESSET"):
        check(f"no {bad} in mains", bad not in mains_src)
    check("DATE CHECK names the excluded stories",
          "Kerch Bridge" in bp.DATE_CHECK and "Nvidia" in bp.DATE_CHECK
          and "Knesset" in bp.DATE_CHECK)

    with open(BUILDER, encoding="utf-8") as fh:
        src = fh.read()
    check("date named in builder", "Wednesday 18 November 2026" in src)
    check("DATE CHECK footer drawn", '"DATE CHECK"' in src)
    check("numbers strip drawn", "THE DAY IN NUMBERS" in src)
    check("region bar drawn", "REGION_BAR" in src)
    check("dotted map drawn", "draw_map(d, MX, map_y, 404, map_h)" in src)
    check("footer sources", "Sources: Reuters, AP, AFP, BBC" in src)

    # Every also-on one-liner must fit its column (276 px) at 11 pt,
    # number included — otherwise it would be truncated like v1.
    probe = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(probe)
    fnt_n = ImageFont.truetype(bp.SANS_B, 11)
    fnt_t = ImageFont.truetype(bp.SANS, 11)
    too_long = []
    for n, _region, text, _lon, _lat in bp.ALSO:
        w = d.textlength(str(n), font=fnt_n) + 5 + \
            d.textlength(text, font=fnt_t)
        if w > 276:
            too_long.append((n, round(w)))
    check("all also-on lines fit one line", not too_long, str(too_long))

    # Determinism: two builds must be byte-identical.
    subprocess.run([sys.executable, BUILDER], cwd=HERE, check=True,
                   capture_output=True)
    h1 = hashlib.sha256(open(PNG, "rb").read()).hexdigest()
    subprocess.run([sys.executable, BUILDER], cwd=HERE, check=True,
                   capture_output=True)
    h2 = hashlib.sha256(open(PNG, "rb").read()).hexdigest()
    check("two builds byte-identical", h1 == h2, h1[:12])

    small = img.resize((300, 300), Image.LANCZOS)
    thumb = "/tmp/ni18-v2-300px.png"
    small.save(thumb)
    print(f"[info] 300px legibility render written to {thumb}")

    if failures:
        print(f"{len(failures)} cap(s) failed")
        sys.exit(1)
    print("all caps pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
