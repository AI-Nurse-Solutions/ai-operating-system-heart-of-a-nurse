// Test launcher shared by source and packaged journeys. A packaged target
// runs from an empty directory without Python source paths in its environment.
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
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
  child.stderr.on('data', () => {});
  const ready = new Promise((resolve, reject) => {
    let settled = false; let output = '';
    const fail = message => {
      if (settled) return;
      settled = true; clearTimeout(timer); child.kill(); reject(new Error(message));
    };
    const timer = setTimeout(() => fail('App did not publish a launch address within 20 seconds.'), 20000);
    child.on('error', () => fail('App executable could not be launched.'));
    child.on('exit', code => fail(`App exited before startup (code ${code}).`));
    child.stdout.on('data', chunk => {
      if (settled) return;
      output += chunk;
      if (output.length > 4096) { fail('App startup output exceeded its limit.'); return; }
      if (!output.includes('\n')) return;
      const url = output.split('\n')[0].trim();
      if (!/^http:\/\/127\.0\.0\.1:[0-9]+\/#token=[A-Za-z0-9_-]{20,}$/.test(url)) { fail('App did not publish a local launch address.'); return; }
      settled = true; clearTimeout(timer); resolve(url);
    });
  });
  return { child, ready, exited };
}
