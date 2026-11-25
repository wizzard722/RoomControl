"""Run every test_*.py in this folder; exit 1 when one fails.

Each test is a plain script on a bare Home Assistant instance: it prints
PASS / FAIL lines and ends with ALL PASS (or SOME FAILED). A test fails when
it prints FAIL, raises (Traceback) or exits with an error.

    python tests/run_all.py            # all
    python tests/run_all.py lux need   # only the tests whose name contains "lux" or "need"
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
TIMEOUT = 120  # s per test


def main(args: list[str]) -> int:
    tests = sorted(HERE.glob("test_*.py"))
    if args:
        tests = [t for t in tests if any(a in t.stem for a in args)]
    failed: list[tuple[str, str]] = []
    start = time.time()
    for test in tests:
        try:
            run = subprocess.run([sys.executable, str(test)], capture_output=True, text=True, timeout=TIMEOUT, cwd=HERE)
            out = run.stdout + run.stderr
            bad = run.returncode != 0 or "Traceback" in out or any(line.startswith("FAIL") for line in out.splitlines())
        except subprocess.TimeoutExpired:
            out, bad = f"timed out after {TIMEOUT} s", True
        print(f"{'FAIL' if bad else 'ok  '} {test.stem}", flush=True)
        if bad:
            lines = [line for line in out.splitlines() if line.startswith("FAIL") or "Error" in line or "Traceback" in line]
            failed.append((test.stem, "\n".join(lines[:5]) or out[-500:]))
    print(f"\n{len(tests) - len(failed)} of {len(tests)} passed in {time.time() - start:.0f} s")
    for name, why in failed:
        print(f"\n== {name}\n{why}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
