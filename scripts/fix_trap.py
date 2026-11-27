#!/usr/bin/env python3
"""Build + install + rebind + valida o Home Trap do Free My TV (uma unica execucao)."""
import glob, hashlib, os, re, shutil, subprocess, time

from common_adb import connect, run
from dev import DEV

S = connect(DEV)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FTV = os.path.join(ROOT, "free-my-tv")
APK = os.path.join(FTV, "FreeMyTV.apk")
BASH = shutil.which("bash") or "bash"


def sh(*a, timeout=300):
    return run(*a, serial=S, timeout=timeout).strip()


def shell(cmd, cwd=None, timeout=600):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd,
                       timeout=timeout, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip()


def apksigner():
    """apksigner do build-tools mais recente do SDK (sem caminho cravado)."""
    sdk = os.environ.get("ANDROID_HOME") or os.path.join(os.environ.get("LOCALAPPDATA", ""), "android-sdk")
    found = sorted(glob.glob(os.path.join(sdk, "build-tools", "*", "apksigner*")))
    return found[-1] if found else ""

def focus():
    d = sh("shell", "dumpsys", "activity", "a")
    m = re.search(r"mFocusedApp=ActivityRecord\{[^ ]+ u0 ([^ ]+)", d)
    return m.group(1) if m else "?"

def build():
    print("=== BUILD ===")
    env = dict(os.environ)
    env.setdefault("ANDROID_HOME", os.path.join(os.environ.get("LOCALAPPDATA", ""), "android-sdk"))
    if not env.get("JAVA_HOME"):
        print("defina JAVA_HOME (o build.sh usa o javac do JDK)"); return False
    b = subprocess.run([BASH, "build.sh"], cwd=FTV, capture_output=True, text=True,
                       env=env, timeout=600, encoding="utf-8", errors="replace")
    bout = b.stdout + b.stderr
    err = [l for l in bout.splitlines() if re.search(r"error|BUILD FAILED", l, re.I)]
    print("build err:", err[:5] or "nenhum")
    if not os.path.exists(APK):
        print("APK NAO GERADO"); print(bout[-800:]); return False
    signer = apksigner()
    v = shell(f'"{signer}" verify "{APK}"', timeout=120) if signer else "apksigner nao encontrado"
    print("apksigner:", "SIGN_OK" if "verified" in v.lower() or not v else v[:200])
    return True
def install():
    print("=== INSTALL ===")
    local_sha = hashlib.sha256(open(APK, "rb").read()).hexdigest()
    print("install:", sh("install", "-r", APK)[-80:]); time.sleep(4)
    ap = sh("shell", "dumpsys", "package", "io.freemytv")
    m = re.search(r"codePath=(\S+)", ap)
    dev_sha = sh("shell", "sha256sum", m.group(1) + "/base.apk").split()[0] if m else "?"
    print("sha local :", local_sha[:24]); print("sha device:", dev_sha[:24])
    print("SHA OK" if dev_sha == local_sha else "!!! SHA DIFERE")
def rebind_service():
    # Estado morto: Fire OS pode registrar crash do :keys e virar accessibility_enabled=0
    # mesmo com o servico listado. Rebind com retry: toggle off -> on -> checar -> repetir.
    for tent in range(3):
        sh("shell", "settings", "put", "secure", "enabled_accessibility_services", ""); time.sleep(1)
        sh("shell", "settings", "put", "secure", "enabled_accessibility_services", "io.freemytv/io.freemytv.RemoteKeyService")
        sh("shell", "settings", "put", "secure", "accessibility_enabled", "1"); time.sleep(2)
        bound = sh("shell", "dumpsys accessibility | grep -i 'Bound services'")
        acc = sh("shell", "settings", "get", "secure", "accessibility_enabled").strip()
        if acc == "1" and ("Service[label=Free My TV" in bound or "RemoteKeyService" in bound):
            print(f"=== REBIND ok (tent {tent + 1}): acc_enabled=1, servico bound ===")
            return
        print(f"=== REBIND falho (tent {tent + 1}): acc={acc}, bound={bound[:80]}")
    print("=== AVISO: servico de acessibilidade nao subiu apos 3 tentativas ===")
def restore_home():
    # install -r perde o papel de HOME padrao: restaura pro painel (senao o Fire OS
    # comeca pelo launcher da Amazon a cada tecla Home — flash de segundos).
    print("set-home:", sh("shell", "cmd", "package", "set-home-activity", "io.freemytv/io.freemytv.HomeActivity").strip())
    # pm clear acima derruba o grant: devolve o self-heal do guard (WRITE_SECURE_SETTINGS).
    print("wr-secure:", sh("shell", "pm", "grant", "io.freemytv", "android.permission.WRITE_SECURE_SETTINGS").strip() or "ok")
    print("standby:", sh("shell", "am", "set-inactive", "io.freemytv", "false").strip() or "ok")
    print("doze:", sh("shell", "cmd", "deviceidle", "whitelist", "+io.freemytv").strip() or "ok")
    print("acc:", sh("shell", "settings", "get", "secure", "enabled_accessibility_services"))
    print("trap:", sh("shell", "settings", "get", "global", "fmtv_trap"))
def rebind():
    print("=== REBIND ===")
    sh("shell", "pm", "clear", "io.freemytv"); time.sleep(2)
    sh("shell", "settings", "put", "secure", "enabled_accessibility_services", ""); time.sleep(1)
    sh("shell", "settings", "put", "secure", "enabled_accessibility_services", "io.freemytv/io.freemytv.RemoteKeyService")
    sh("shell", "settings", "put", "global", "fmtv_trap", "1")
    rebind_service(); restore_home()
def validate():
    print("=== VALIDA ===")
    sh("shell", "am", "start", "-n", "io.freemytv/.HomeActivity"); time.sleep(12)
    print("foco apos start:", focus())
    # simula tecla Home do controle
    sh("shell", "input", "keyevent", "3"); time.sleep(6)
    print("foco apos HOME :", focus())
    # abre Ajustes da TV (MainSettingsActivity) e ve se permanece
    sh("shell", "am", "start", "-n", "com.amazon.tv.launcher/.ui.MainSettingsActivity"); time.sleep(6)
    print("foco em ajustes:", focus())
    sh("shell", "input", "keyevent", "3"); time.sleep(6)
    print("foco final HOME:", focus())
    print("=== FIM ===")
def main():
    if build():
        install(); rebind(); validate()

if __name__ == "__main__":
    main()
