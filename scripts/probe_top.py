#!/usr/bin/env python
import time, re
from common_adb import connect, run
from dev import DEV
S = connect(DEV)
def adb(*a, timeout=60):
    return run(*a, serial=S, timeout=timeout)
def focus():
    o = adb("shell", "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'")
    return re.findall(r"m(?:CurrentFocus|FocusedApp)=([^\s}]+)", o)
print("connect:", adb("connect", DEV).strip())
print("baseline:", focus())
t0 = time.time()
adb("shell", "input keyevent KEYCODE_HOME")
last = None
while time.time()-t0 < 8:
    f = focus()
    if f != last:
        print(f"[{time.time()-t0:6.2f}s] {f}")
        last = f
        if any('freemytv' in s for s in f):
            print("TOTAL:", round(time.time()-t0, 2), "s")
            break
    time.sleep(0.08)
