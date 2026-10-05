"""Bounded CI diagnostics: synthetic homes, no URLs or raw process output."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

binary = str(Path(sys.argv[1]).resolve())
for cwd_kind in ("repository", "empty"):
    for stdin_kind in ("pipe", "closed"):
        with tempfile.TemporaryDirectory(prefix="nm-native-probe-") as tmp:
            env = dict(os.environ)
            env.pop("PYTHONPATH", None)
            env.pop("PYTHONHOME", None)
            process = subprocess.Popen(
                [binary, "--self-test"], env=env,
                cwd=tmp if cwd_kind == "empty" else None,
                stdin=subprocess.PIPE if stdin_kind == "pipe" else subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            timed_out = False
            try:
                # communicate closes PIPE stdin as well; both cases have EOF.
                out, err = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                out, err = process.communicate()
            print(json.dumps({"cwd": cwd_kind, "stdin": stdin_kind,
                              "timed_out": timed_out, "exit": process.returncode,
                              "stdout_bytes": len(out), "stderr_bytes": len(err),
                              "self_test_pass_count": out.count(b"PASS ")}), flush=True)
