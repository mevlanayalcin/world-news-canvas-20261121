// World News Canvas: Saturday 21 November 2026.
// The front page is pre-rendered by tools/render.py (deterministic, no network) and stored as
// entry.png beside this file: JPEG bytes, 1024 x 1024. This program only checks those bytes and
// writes them unchanged to $MAKEFUN_OUTPUT_DIR (default /output), so every run is identical.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const source = new URL('./entry.png', import.meta.url);
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const bytes = readFileSync(source);

const isJpeg = bytes[0] === 0xff && bytes[1] === 0xd8 && bytes.at(-2) === 0xff && bytes.at(-1) === 0xd9;
const isPng = bytes.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]));
if (!isJpeg && !isPng) throw new Error('entry.png is neither a whole JPEG nor a PNG');
if (bytes.length > 1048576) throw new Error(`entry.png is ${bytes.length} bytes, over 1 MiB`);

mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'entry.png'), bytes);
