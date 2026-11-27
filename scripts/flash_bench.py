#!/usr/bin/env python3
"""Bench do flash da launcher na tecla Home (Fire TV; IP via dev.py).

Por press: sai do painel, aperta Home e mede no logcat o intervalo entre o
START da launcher da Amazon e o START do painel (re-firm). Tambem mede a
cobertura (foco final) e conta cold starts do painel.

Uso:
  python scripts/flash_bench.py --presses 12
  python scripts/flash_bench.py --presses 12 --json docs/flash_after.json
"""
import argparse
import json
import re
import time

from common_adb import connect, run
from dev import DEV

S = connect(DEV)
LEAVE = "io.freemytv/.SettingsActivity"   # app qualquer para sair do painel antes do press


def adb(*args, timeout=25):
    return run(*args, serial=S, timeout=timeout)


def ts_ms(line):
    m = re.match(r"(?:\d\d-\d\d\s+)?(\d\d):(\d\d):(\d\d)\.(\d+)", line)
    if not m:
        return None
    h, mi, s, frac = m.groups()
    return (int(h) * 3600 + int(mi) * 60 + int(s)) * 1000 + int(frac.ljust(3, "0")[:3])


def focus():
    out = adb("shell", "dumpsys window | grep mCurrentFocus")
    m = re.search(r"u0 (\S+)}", out)
    return m.group(1) if m else "?"


def rearm_delta(log):
    """START launcher -> primeiro START do painel depois dele (ms)."""
    t_lau = t_pan = None
    for line in log.splitlines():
        t = ts_ms(line)
        if t is None or "START u0" not in line:
            continue
        if "com.amazon.tv.launcher/.ui.Home" in line and t_lau is None:
            t_lau = t
        elif "io.freemytv/.HomeActivity" in line and t_lau is not None:
            t_pan = t
            break
    if t_lau is None or t_pan is None:
        return None
    return (t_pan - t_lau) % 60000


def pct(values, q):
    v = sorted(values)
    return v[min(len(v) - 1, int(round(q * (len(v) - 1))))]


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--presses", type=int, default=12)
    ap.add_argument("--gap", type=float, default=1.5, help="intervalo entre presses (s)")
    ap.add_argument("--leave", default=LEAVE, help="activity aberta antes de cada press")
    ap.add_argument("--json", default="")
    return ap.parse_args()


def press_once(i, args):
    adb("shell", "am", "start", "-n", args.leave)
    time.sleep(1.2)
    adb("logcat", "-c")
    adb("shell", "input", "keyevent", "KEYCODE_HOME")
    time.sleep(1.6)
    f = focus()
    ok = "io.freemytv" in f
    log = adb("shell", "logcat", "-d", "-v", "time")
    d = rearm_delta(log)
    frio = "Displayed io.freemytv/io.freemytv.HomeActivity" in log
    print(f"[{i + 1:2d}] rearm={'-' if d is None else str(d) + 'ms':>7}  foco={'PAINEL' if ok else 'LAUNCHER':8s} {f}")
    time.sleep(max(0.0, args.gap - 1.6))
    return ok, d, frio


def summarize(presses, deltas, cobertos, frios):
    return {
        "presses": presses,
        "cobertura": f"{cobertos}/{presses}",
        "cold_starts_painel": frios,
        "rearm_ms": {
            "n": len(deltas),
            "p50": pct(deltas, 0.50) if deltas else None,
            "p90": pct(deltas, 0.90) if deltas else None,
            "p95": pct(deltas, 0.95) if deltas else None,
            "max": max(deltas) if deltas else None,
        },
    }


def main():
    args = parse_args()
    deltas, cobertos, frios = [], 0, 0
    for i in range(args.presses):
        ok, d, frio = press_once(i, args)
        cobertos += ok
        frios += frio
        if d is not None:
            deltas.append(d)
    res = summarize(args.presses, deltas, cobertos, frios)
    print("\n== RESUMO ==")
    print(json.dumps(res, indent=2))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2)
        print("salvo em", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
