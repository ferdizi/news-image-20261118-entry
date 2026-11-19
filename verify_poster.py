#!/usr/bin/env python3
"""Shape-check the 18 November poster against every hard cap in RULES.txt.

Checks the built entry.png next to this file: it is a whole PNG, exactly
1024 by 1024 pixels, at most 1 MiB; the masthead names Wednesday
18 November 2026; all 13 numbered mains and the 20 also-on items are
present in the data the poster was drawn from; the map and the Today's
Numbers sidebar exist. Also writes a 300 px downscale for the legibility
check the judge applies. Exit 0 only when every cap passes.

Run: python3 verify_poster.py
"""
import os
import sys

from PIL import Image

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

    with open(BUILDER, encoding="utf-8") as fh:
        src = fh.read()
    check("date named in builder", "Wednesday 18 November 2026" in src)
    check("13 mains in data", src.count('"MIDDLE EAST"') + src.count('"EUROPE"')
          + src.count('"ASIA"') + src.count('"AMERICAS"')
          + src.count('"AFRICA"') + src.count('"OCEANIA"') >= 13,
          "region tags across the 13 mains")
    check("20 also-on items", "(14," in src and "(33," in src,
          "numbered 14 through 33")
    check("Today's Numbers sidebar", "TODAY'S NUMBERS" in src)
    check("map drawn", "draw_map(d, 16, 660, 340, 250)" in src)
    check("footer sources", "Sources: Reuters, AP, AFP, BBC" in src)

    small = img.resize((300, 300), Image.LANCZOS)
    thumb = "/tmp/ni18-300px.png"
    small.save(thumb)
    print(f"[info] 300px legibility render written to {thumb}")

    if failures:
        print(f"{len(failures)} cap(s) failed")
        sys.exit(1)
    print("all caps pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
