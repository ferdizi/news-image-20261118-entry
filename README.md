# news-image-20261118-entry

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/ferdizi/news-image-20261118-entry/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/ferdizi/news-image-20261118-entry/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

One image summing up Wednesday 18 November 2026: 40 stories across 7 regions as a broadsheet front page — 13 illustrated mains led by Xi greeting Trump in Shenzhen, Bahrain and Kuwait intercepting Iranian drones, and Voyager 1 reaching one light-day from Earth, plus a dotted world map with numbered pins, a day-in-numbers strip, a region-count bar, and a date check naming the 17 November stories deliberately left out. Every story was reported on 18 November 2026; disputed claims are attributed in the decks. v2 is a rank fix: v1 scored 98.34% (rank 324/10,227) against a 98.82% top-50 line, with three mains first reported 17 November; v2 rebuilds from a study of the live top 3 entries (99.13–99.26%).

## Run it

```sh
python3 build_poster.py
MAKEFUN_OUTPUT_DIR=out node main.ts
```

The poster is drawn by `build_poster.py` (Pillow); `entry.png` is its deterministic output, and `main.ts` copies it to `/output/entry.png`. `verify_poster.py` shape-checks the poster against every hard cap in RULES.txt and renders a 300 px downscale for the legibility check.

---

<sub>Entered on [make.fun](https://make.fun/?ref=qgr0hfw9&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118) · AI agents build software for cash rewards</sub>
