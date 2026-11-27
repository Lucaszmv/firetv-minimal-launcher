#!/usr/bin/env python
"""Rebind RemoteKeyService e cronometra o retorno do painel apos HOME, com logs de debug."""
import time, re
from common_adb import connect, run
from dev import DEV
S = connect(DEV)
PY = Q = None

def adb(*a, timeout=60):
    return run(*a, serial=S, timeout=timeout).strip()

def focus():
    m = re.search(r"mCurrentFocus=Window\{\S+ u0 (\S+)\}", adb("shell", "dumpsys window | grep mCurrentFocus"))
    return m.group(1) if m else "??"

adb("logcat", "-c")
# rebind
adb("shell", "settings put secure enabled_accessibility_services ''")
time.sleep(1.0)
adb("shell", "settings put secure enabled_accessibility_services io.freemytv/io.freemytv.RemoteKeyService")
adb("shell", "settings put global fmtv_trap 1")
time.sleep(0.5)
adb("shell", "settings put secure accessibility_enabled 1")
time.sleep(2.5)
print("focus pre-HOME:", focus())

t0 = time.time()
adb("shell", "input keyevent KEYCODE_HOME")
last = None
first_freetv = None
while time.time()-t0 < 8:
    f = focus()
    if f != last:
        print(f"[{time.time()-t0:5.2f}s] {f}")
        last = f
        if 'freemytv' in f and first_freetv is None:
            first_freetv = time.time()-t0
            print("LATENCIA FOCUS:", round(first_freetv, 2), "s")
            break
    time.sleep(0.05)

logs = adb("logcat", "-d", "-v", "time", "*:I")
for l in logs.splitlines():
    if 'FreeMyTV' in l or 'freemytv' in l.lower():
        print("DBG:", l)
