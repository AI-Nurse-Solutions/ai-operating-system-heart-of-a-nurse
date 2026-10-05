// Test launcher shared by source and packaged journeys. A packaged target
// runs from an empty directory without Python source paths in its environment.
import { spawn } from 'node:child_process';
import { mkdirSync, lstatSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
// Windowed bundles can suppress stdout. Reuse the app's existing owner-only
// instance record, and authenticate its local status before accepting it.
async function instanceAddress(home) {
  try {
    const path = join(home, 'app.lock.json');
    const stat = lstatSync(path);
    if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 4096) return null;
    if (process.platform !== 'win32' && (stat.mode & 0o077)) return null;
    const record = JSON.parse(readFileSync(path, 'utf8'));
    if (!Number.isInteger(record.port) || record.port < 1 || record.port > 65535
        || typeof record.token !== 'string' || !/^[A-Za-z0-9_-]{20,128}$/.test(record.token)) return null;
    const base = `http://127.0.0.1:${record.port}`;
    const response = await fetch(`${base}/app/status`, {
      headers: { authorization: `Bearer ${record.token}` }, signal: AbortSignal.timeout(500),
    });
    if (!response.ok || (await response.json()).app !== 'nurse-ai-os') return null;
    return `${base}/#token=${record.token}`;
  } catch { return null; }
}
export function launchApp(home) {
  mkdirSync(home, { recursive: true });
  const binary = process.env.NURSE_AI_OS_BIN;
  const env = { ...process.env };
  if (binary) { delete env.PYTHONPATH; delete env.PYTHONHOME; }
  else env.PYTHONPATH = fileURLToPath(new URL('../src', import.meta.url));
  const args = ['--no-browser', '--print-url', '--idle-timeout', '120', '--home', home];
  const child = binary ? spawn(binary, args, { env, cwd: home }) : spawn('python3', ['-m', 'nurse_manager.app', ...args], { env, cwd: home });
  const exited = new Promise(resolve => child.on('exit', resolve));
  // Consume errors without echoing workspace text or launch credentials.
  let stderrBytes = 0;
  let stderrKind = 'none';
  child.stderr.on('data', chunk => {
    stderrBytes += chunk.length;
    // Classify only known runtime failures; never echo the error payload.
    for (const kind of ['ModuleNotFoundError', 'ImportError', 'FileNotFoundError', 'PermissionError', 'Traceback']) {
      if (chunk.toString().includes(kind)) { stderrKind = kind; break; }
    }
  });
  const ready = new Promise((resolve, reject) => {
    let settled = false; let output = ''; let polling = false;
    let poll;
    const clear = () => { clearTimeout(timer); clearInterval(poll); };
    const publish = url => { if (!settled) { settled = true; clear(); resolve(url); } };
    const fail = message => {
      if (settled) return;
      settled = true; clear(); child.kill(); reject(new Error(message));
    };
    const timer = setTimeout(() => {
      let lock = 'absent';
      try { const stat = lstatSync(join(home, 'app.lock.json')); lock = `present,mode=${(stat.mode & 0o777).toString(8)}`; } catch {}
      fail(`App did not publish a launch address within 20 seconds (record=${lock}; stdoutBytes=${output.length}; stderrBytes=${stderrBytes}; runtimeError=${stderrKind}).`);
    }, 20000);
    poll = setInterval(async () => {
      if (settled || polling) return;
      polling = true;
      const address = await instanceAddress(home);
      polling = false;
      if (address) publish(address);
    }, 100);
    child.on('error', () => fail('App executable could not be launched.'));
    child.on('exit', code => fail(`App exited before startup (code ${code}).`));
    child.stdout.on('data', chunk => {
      if (settled) return;
      output += chunk;
      if (output.length > 4096) { fail('App startup output exceeded its limit.'); return; }
      if (!output.includes('\n')) return;
      const url = output.split('\n')[0].trim();
      if (!/^http:\/\/127\.0\.0\.1:[0-9]+\/#token=[A-Za-z0-9_-]{20,}$/.test(url)) { fail('App did not publish a local launch address.'); return; }
      publish(url);
    });
  });
  return { child, ready, exited };
}
