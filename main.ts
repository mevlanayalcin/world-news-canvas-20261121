// Full Saturday edition. The press image is immutable; the runtime does not fetch or re-encode it.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const source = new URL('./entry.png', import.meta.url);
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const bytes = readFileSync(source);

if (!bytes.subarray(0, 16).equals(Buffer.from('89504e470d0a1a0a0000000d49484452', 'hex')) ||
    !bytes.subarray(-12).equals(Buffer.from('0000000049454e44ae426082', 'hex'))) {
  throw new Error('entry.png is missing its PNG header or end marker');
}
if (bytes.readUInt32BE(16) !== 1024 || bytes.readUInt32BE(20) !== 1024) {
  throw new Error('expected a 1024 x 1024 press image');
}
if (bytes.length > 1048576) throw new Error(`entry.png is ${bytes.length} bytes, over 1 MiB`);

mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'entry.png'), bytes);
