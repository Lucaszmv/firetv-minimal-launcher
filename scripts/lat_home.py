#!/usr/bin/env python
"""3 presses HOME consecutivos; mede latencia de foco -> painel em cada."""
import time, re
from common_adb import connect, run
from dev import DEV
S = connect(DEV)
def adb(*a, timeout=60):
    return run(*a, serial=S, timeout=timeout).strip()
def focus():
    m = re.search(r"mCurrentFocus=Window\{\S+ u0 (\S+)\}", adb("shell", "dumpsys window | grep mCurrentFocus"))
    return m.group(1) if m else "??"

lat = []
for n in range(1, 4):
    adb("shell", "input keyevent KEYCODE_HOME")
    t0 = time.time()
    # 1a amostra: espera 0.3s (flash minimo) e comeca a olhar
    time.sleep(0.3)
    seen_launcher, done = False, None
    while time.time()-t0 < 5:
        f = focus()
        if 'tv.launcher' in f:
            seen_launcher = True
        elif 'freemytv' in f:
            done = time.time()-t0
            break
        time.sleep(0.05)
    lat.append((n, seen_launcher, round(done, 2) if done else None))
    print(f"press {n}: volta pro painel em {done}s (launcher visto: {seen_launcher})")
    time.sleep(1)

print("LATENCIAS:", [(d) for _, _, d in lat])
