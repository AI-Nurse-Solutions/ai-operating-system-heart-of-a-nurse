"""Test-only readiness barrier; preserves the signed Mission Control source.

HTTP health readiness does not mean the asynchronous demo-vault collector has
committed its first index. Wait for the real first /api/memory result, bounded;
never seed notes, fabricate responses, skip assertions, or modify release bytes.
"""
from __future__ import annotations
import runpy
import sys
import time
from pathlib import Path


def with_demo_index_readiness(get, *, timeout=10.0):
    first_memory = True
    def checked(path, port):
        nonlocal first_memory
        result = get(path, port)
        if path != '/api/memory' or not first_memory:
            return result
        first_memory = False
        deadline = time.monotonic() + timeout
        while result[0] == 200 and len(result[1].get('notes', [])) < 4:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break  # Return actual failure data to the unchanged assertions.
            time.sleep(min(0.05, remaining))
            result = get(path, port)
        return result
    return checked


def main(mc):
    suite = runpy.run_path(str(Path(mc) / 'tests/self_test.py'),
                          run_name='mission_control_rehearsal_self_test')
    suite['main'].__globals__['get'] = with_demo_index_readiness(suite['get'])
    return suite['main']()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
