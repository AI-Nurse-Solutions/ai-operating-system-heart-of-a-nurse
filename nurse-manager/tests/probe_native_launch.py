"""Bounded CI diagnostics: synthetic homes, no URLs or raw process output."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import re

binary = str(Path(sys.argv[1]).resolve())
for cwd_kind in ("repository", "empty"):
    for stdin_kind in ("pipe", "closed", "files", "inherited-env"):
        with tempfile.TemporaryDirectory(prefix="nm-native-probe-") as tmp:
            env = dict(os.environ)
            if stdin_kind != "inherited-env":
                env.pop("PYTHONPATH", None)
                env.pop("PYTHONHOME", None)
            out_file = tempfile.TemporaryFile()
            err_file = tempfile.TemporaryFile()
            process = subprocess.Popen(
                [binary, "--self-test"], env=env,
                cwd=tmp if cwd_kind == "empty" else None,
                stdin=subprocess.PIPE if stdin_kind == "pipe" else subprocess.DEVNULL,
                stdout=out_file if stdin_kind == "files" else subprocess.PIPE,
                stderr=err_file if stdin_kind == "files" else subprocess.PIPE,
            )
            timed_out = False
            try:
                # communicate closes PIPE stdin as well; both cases have EOF.
                out, err = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                timed_out = True
                if cwd_kind == "repository" and stdin_kind == "pipe" and sys.platform == "darwin":
                    sample = subprocess.run(["sample", str(process.pid), "1", "1"],
                                            capture_output=True, text=True, timeout=10)
                    # Native symbol names only, no arguments, paths or memory contents.
                    frames = re.findall(r"\b(?:pyi_[A-Za-z0-9_]+|Py[A-Za-z0-9_]+|[A-Za-z0-9_]*(?:wait|read|write|dlopen|mach_msg|dispatch)[A-Za-z0-9_]*)\b", sample.stdout)
                    print(json.dumps({"native_frames": sorted(set(frames))[:80]}), flush=True)
                process.kill()
                out, err = process.communicate()
            if stdin_kind == "files":
                out_file.seek(0); err_file.seek(0)
                out, err = out_file.read(), err_file.read()
            out_file.close(); err_file.close()
            print(json.dumps({"cwd": cwd_kind, "stdin": stdin_kind,
                              "timed_out": timed_out, "exit": process.returncode,
                              "stdout_bytes": len(out), "stderr_bytes": len(err),
                              "self_test_pass_count": out.count(b"PASS ")}), flush=True)
