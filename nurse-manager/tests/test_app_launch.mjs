// A configured package must fail if absent, never fall back to Python source.
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync, mkdirSync } from 'node:fs';
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
  // Emulate a windowed bundle that serves authenticated status but emits no stdout.
  const fixture = join(work, 'windowed-fixture');
  const home = join(work, 'fixture-home'); mkdirSync(home);
  writeFileSync(fixture, `#!/usr/bin/env node
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const home = process.argv[process.argv.indexOf('--home') + 1];
const token = 'synthetic-windowed-launch-token';
const server = http.createServer((req,res) => {
  if (req.url !== '/app/status' || req.headers.authorization !== 'Bearer ' + token) { res.writeHead(401); res.end(); return; }
  res.setHeader('content-type','application/json'); res.end(JSON.stringify({app:'nurse-ai-os'}));
});
server.listen(0,'127.0.0.1', () => {
  const file = path.join(home,'app.lock.json');
  // A stale/wrong token must not be accepted before the current record appears.
  fs.writeFileSync(file,JSON.stringify({port:server.address().port,token:'synthetic-stale-launch-token'}),{mode:0o600});
  setTimeout(() => fs.writeFileSync(file,JSON.stringify({port:server.address().port,token}),{mode:0o600}),300);
});
process.on('SIGTERM', () => server.close(() => process.exit(0)));
`, {mode:0o700});
  process.env.NURSE_AI_OS_BIN = fixture;
  const windowed = launchApp(home);
  try {
    const url = new URL(await windowed.ready);
    assert.equal(url.hostname, '127.0.0.1');
    assert.equal(url.hash, '#token=synthetic-windowed-launch-token');
  } finally { windowed.child.kill(); await windowed.exited; }
  console.log('Packaged launcher: no source fallback; authenticated windowed startup without stdout.');
} finally {
  if (original === undefined) delete process.env.NURSE_AI_OS_BIN;
  else process.env.NURSE_AI_OS_BIN = original;
  rmSync(work,{recursive:true,force:true});
}
