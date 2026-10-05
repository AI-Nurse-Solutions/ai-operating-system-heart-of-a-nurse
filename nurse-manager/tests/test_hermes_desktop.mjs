// Native developer smoke: actual Intel bundle, synthetic homes, no setup clicks.
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';
const upstream = resolve(process.argv[2]);
const binary = resolve(process.argv[3]);
const require = createRequire(join(upstream, 'apps/desktop/package.json'));
const { _electron } = require('playwright');
const home = mkdtempSync(join(tmpdir(), 'naio-hermes-smoke-'));
const hermesHome = join(home, 'hermes');
const userData = join(home, 'electron');
const profile = '(version 1) (allow default) (deny network*) (allow network-inbound (local ip "localhost:*")) (allow network-outbound (remote ip "localhost:*")) (allow network-bind (local ip "localhost:*"))';
const quote = s => `'${s.replaceAll("'", "'\\''")}'`;
const wrapper = join(home, 'launch');
writeFileSync(wrapper, `#!/bin/sh\nexec /usr/bin/sandbox-exec -p ${quote(profile)} ${quote(binary)} "$@"\n`, { mode: 0o700 });
const env = Object.fromEntries(['PATH', 'HOME', 'TMPDIR', 'LANG', 'LC_ALL'].filter(k => process.env[k]).map(k => [k, process.env[k]]));
Object.assign(env, { HERMES_HOME: hermesHome, HERMES_SHARED_AUTH_DIR: join(home, 'shared'),
  HERMES_DESKTOP_USER_DATA_DIR: userData, HERMES_DESKTOP_HERMES_ROOT: join(home, 'no-runtime'),
  HERMES_SKIP_INTRO: '1', HERMES_GUEST_ONBOARDING: '0' });
let app;
try {
  app = await _electron.launch({ executablePath: wrapper, cwd: home, env, timeout: 60000 });
  const identity = await app.evaluate(({ app }) => ({ packaged: app.isPackaged, arch: process.arch, version: app.getVersion(), userData: app.getPath('userData') }));
  assert.deepEqual(identity, { packaged: true, arch: 'x64', version: '0.17.6', userData });
  // A raw TCP probe to a reserved documentation address must be denied by
  // the kernel sandbox, not merely fail from a timeout or unavailable server.
  const deny = await app.evaluate(() => new Promise(resolve => {
    const socket = process.getBuiltinModule('net').connect({ host: '192.0.2.1', port: 8080 });
    const timer = setTimeout(() => { socket.destroy(); resolve('timeout'); }, 2000);
    socket.once('error', e => { clearTimeout(timer); resolve(e.code); });
    socket.once('connect', () => { clearTimeout(timer); socket.destroy(); resolve('connected'); });
  }));
  assert.ok(['EPERM', 'EACCES'].includes(deny), 'outbound traffic must be denied by the native sandbox');
  const page = await app.firstWindow({ timeout: 60000 });
  await page.getByText('Set up Hermes Desktop', { exact: true }).waitFor({ timeout: 60000 });
  await page.getByText('Connect to existing Hermes', { exact: true }).waitFor();
  await page.getByText('Install Hermes locally', { exact: true }).waitFor();
  const check = async () => {
    const state = await page.evaluate(() => window.hermesDesktop.getBootstrapState());
    assert.ok(state.setupChoice, 'installation must wait for the human setup choice');
    assert.equal(state.active, false);
    assert.equal(state.manifest, null);
    assert.deepEqual(state.stages, {});
    for (const name of ['hermes-agent', '.hermes-bootstrap-complete', '.env', 'config.yaml']) {
      assert.equal(existsSync(join(hermesHome, name)), false, `${name} must not be installed or provisioned`);
    }
  };
  await check();
  await new Promise(r => setTimeout(r, 5000));
  await check();
  console.log('Hermes Intel Desktop: actual packaged x64 app; native outbound deny; idle human setup gate; no runtime/provider provisioning.');
} finally {
  if (app) {
    const timeout = setTimeout(() => app.process().kill('SIGKILL'), 10000);
    try { await app.close(); } finally { clearTimeout(timeout); }
  }
  rmSync(home, { recursive: true, force: true });
}
