// Entry program for news-image-20261118.
//
// The poster (entry.png, drawn by build_poster.py) sits next to this file.
// This program copies it to the output directory the grader reads:
// /output/entry.png inside the grading container, or $MAKEFUN_OUTPUT_DIR
// when set (handy for a local run: MAKEFUN_OUTPUT_DIR=out node main.ts).
// The file must stay a PNG or JPEG of at most 1 MiB and 1024x1024 px.

import { copyFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });
copyFileSync(new URL('./entry.png', import.meta.url), join(outDir, 'entry.png'));
