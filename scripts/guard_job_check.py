#!/usr/bin/env python3
"""Backstop do Home Trap: confere o job periodico 2001 e prova que ele cura o servico pelo processo principal."""
import os
import re
import shutil
import subprocess
import sys
import time

from common_adb import connect, run
from dev import DEV as D

S = connect(D)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FTV = os.path.join(ROOT, "free-my-tv")
APK = os.path.join(FTV, "FreeMyTV.apk")
BASH = shutil.which("bash") or "bash"
PKG, JOB = "io.freemytv", "2001"
SERVICE = "io.freemytv/io.freemytv.RemoteKeyService"


def sh(*a, t=60):
    return run(*a, serial=S, timeout=t).strip()


def build():
    env = dict(os.environ)
    env.setdefault("ANDROID_HOME", os.path.join(os.environ.get("LOCALAPPDATA", ""), "android-sdk"))
    if not env.get("JAVA_HOME"):
        sys.exit("defina JAVA_HOME (o build.sh usa o javac do JDK)")
    p = subprocess.run([BASH, "build.sh"], cwd=FTV, env=env, capture_output=True, text=True,
                       timeout=900, encoding="utf-8", errors="replace")
    print((p.stdout + p.stderr)[-1200:])
    if p.returncode != 0:
        sys.exit("build falhou")


def first_install():
    m = re.search(r"firstInstallTime=(.+)", sh("shell", "dumpsys package " + PKG, t=90))
    return m.group(1).strip() if m else "?"


def install(before):
    out = sh("install", "-r", APK, t=300)
    print(out[-300:])
    if "Success" not in out:
        sys.exit("install falhou")
    after = first_install()
    print("firstInstallTime:", before, "->", after)
    if before != "?" and before != after:
        sys.exit("reinstalacao detectada (dados perdidos)")


def job_block():
    lines = sh("shell", "dumpsys jobscheduler", t=90).splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if "JOB #" in ln and "/" + JOB + ":" in ln and PKG + "/.ModeJob" in ln), None)
    if start is None:
        return ""
    end = next((i for i in range(start + 1, len(lines)) if "JOB #" in lines[i]), len(lines))
    return "\n".join(lines[start:end])


def check_job():
    block = job_block()
    print("--- job " + JOB + " ---\n" + (block or "(nao encontrado)"))
    periodic = "PERIODIC" in block and ("interval=+15m" in block or "900000" in block)
    persisted = "PERSISTED" in block or any(
        "persisted" in ln.lower() and "true" in ln.lower() for ln in block.splitlines())
    ok = bool(block) and periodic and persisted
    print("periodico (15m) e persistido:", ok)
    return ok


def drop_service():
    print("drop:", repr(sh("shell", "settings", "delete", "secure", "enabled_accessibility_services")))


def main_pid(seconds=15):
    for _ in range(seconds):
        out = sh("shell", "pidof", PKG).strip()
        if out:
            return out.split()[0]
        time.sleep(1)
    return ""


def rebound_line(main):
    log = sh("shell", "logcat", "-d", "-v", "threadtime", "-s", "FreeMyTV")
    for ln in log.splitlines():
        parts = ln.split()
        if "rebound" in ln and len(parts) > 2 and parts[2] == main:
            return ln
    return ""


def heal_by_job(n, seconds=12):
    drop_service()
    sh("shell", "logcat", "-c")
    pid = ""
    for _ in range(seconds * 4):
        out = sh("shell", "cmd", "jobscheduler", "run", "-f", PKG, JOB)
        if "Running job" not in out:
            print("run recusado:", out)
        pid = pid or main_pid(3)
        line = rebound_line(pid) if pid else ""
        if line and SERVICE in sh("shell", "settings", "get", "secure", "enabled_accessibility_services"):
            print("tentativa %d: job curou pelo processo principal (pid %s)" % (n, pid))
            print(line)
            return line
        if SERVICE in sh("shell", "settings", "get", "secure", "enabled_accessibility_services"):
            print("tentativa %d: o guard de 5 s curou antes do job" % n)
            return ""
        time.sleep(0.25)
    print("tentativa %d: o job nao curou em %ss" % (n, seconds))
    return ""


def run_attempts(n=4):
    return any(heal_by_job(i) for i in range(1, n + 1))


def main():
    if "--install" in sys.argv:
        build()
        before = first_install()
        install(before)
        time.sleep(8)
    ok = check_job()
    if ok:
        ok = run_attempts()
    sh("shell", "am", "start", "-n", PKG + "/.HomeActivity")
    print("=== OK ===" if ok else "=== FALHOU ===")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
