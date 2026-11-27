import time
from common_adb import connect, run
from dev import DEV
S = connect(DEV)
r = lambda *a, timeout=60: run(*a, serial=S, timeout=timeout)
sh = r("shell", "settings", "put", "secure", "enabled_accessibility_services", "")
r("shell", "settings", "put", "secure", "enabled_accessibility_services", "io.freemytv/io.freemytv.RemoteKeyService")
r("shell", "settings", "put", "secure", "accessibility_enabled", "1")
r("shell", "am", "start", "-a", "android.settings.SETTINGS")
time.sleep(3)
r("shell", "input", "keyevent", "3")
time.sleep(3)
r("shell", "input", "keyevent", "3")
time.sleep(3)
print("LOG:", r("shell", "logcat", "-d", "-s", "FreeMyTV")[-1200:])
o = r("shell", "dumpsys", "activity", "a")
print("FOCUS:", o[o.find("mFocusedApp"):o.find("mFocusedApp") + 110])
