// A configured package must fail if absent, never fall back to Python source.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { launchApp } from './app-launch.mjs';
const original = process.env.NURSE_AI_OS_BIN;
const work = mkdtempSync(join(tmpdir(), 'nm-launch-test-'));
try {
  process.env.NURSE_AI_OS_BIN = join(work, 'missing-app-executable');
  const app = launchApp(work);
  assert.equal(app.child.spawnfile, process.env.NURSE_AI_OS_BIN);
  assert.deepEqual(app.child.spawnargs.slice(1), ['--no-browser','--print-url','--idle-timeout','120','--home',work]);
  await assert.rejects(app.ready, /App executable could not be launched/);
  console.log('Packaged launcher: missing executable refuses; no source fallback.');
} finally {
  if (original === undefined) delete process.env.NURSE_AI_OS_BIN;
  else process.env.NURSE_AI_OS_BIN = original;
  rmSync(work,{recursive:true,force:true});
}
