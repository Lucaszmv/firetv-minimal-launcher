#!/usr/bin/env python3
"""Free My TV — Fire TV Stick installer: modo radical, --trap on/off, --revert (rollback)."""
import argparse, json, os, sys
from common_adb import ADB, HOME, PKG, device
from fire_debloat import DEBLOAT

HERE = os.path.dirname(os.path.abspath(__file__))
APK = os.path.abspath(os.path.join(HERE, "..", "free-my-tv", "FreeMyTV.apk"))
BACK = os.path.join(HERE, "fmtv_backup.json")     # legado (primeiro device); o novo vai por IP
DEFAULT_IP = os.environ.get("FMTV_IP", "")


def back_path(ip):
    """Snapshot por device: instalar em outro Fire TV nao pode sobrescrever o backup do primeiro."""
    safe = ip.replace(":", "_").replace(".", "_").replace("/", "_")
    return os.path.join(HERE, "fmtv_backup_%s.json" % safe)

# Firewall: nunca tocar nesses (settings, webview, Prime Video core, remote, launcher Amazon)
PROTECT = {"com.amazon.tv.launcher", "com.amazon.tv.settings", "com.amazon.webview",
           "com.amazon.avod", "com.amazon.maya", "com.amazon.platform", "com.amazon.tv.remote", PKG}
def adb(ip, *args, timeout=60):
    return device(ip, *args, timeout=timeout)

def disabled(ip):
    out = adb(ip, "shell", "pm", "list", "packages", "-d")
    return {l.replace("package:", "").strip() for l in out.splitlines()}

def snap(ip):
    home = ""
    q = adb(ip, "shell", "cmd", "package", "query-activities", "--brief", "-a",
            "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
    for l in q.splitlines():
        if l.strip() and PKG not in l and "Resolver" not in l and "/" in l:
            home = l.strip().split()[0]
            break
    return {"screen": adb(ip, "shell", "settings", "get", "secure", "screensaver_components").strip(),
            "disabled": sorted(disabled(ip)), "home": home}

def dream(ip):
    """Espelho de HomeMode.DREAM: o Android 11 (API 30) exige o screensaver fora do processo :home."""
    sdk = adb(ip, "shell", "getprop", "ro.build.version.sdk").strip()
    return PKG + "/" + PKG + (".ScreensaverAlone" if sdk == "30" else ".Screensaver")

def apply_mode(ip, name):
    print(adb(ip, "shell", "cmd", "package", "set-home-activity", name))
    print(adb(ip, "shell", "settings", "put", "secure", "screensaver_components", dream(ip)))

def install(ip):
    print("[1/4] Instalando APK...")
    r = adb(ip, "install", "-r", "-d", APK, timeout=600); print(r.strip())
    if "Success" not in r:
        sys.exit(1)
    print("[2/4] Snapshot do estado original...")
    json.dump(snap(ip), open(back_path(ip), "w"), indent=1)
    print("      ->", os.path.basename(back_path(ip)))
    print("[3/4] Debloat Amazon...")
    debloat(ip)
    print("[4/4] Tornando launcher padrão...")
    apply_mode(ip, HOME)
    trap(ip, True)

def debloat(ip):
    on = {l.replace("package:", "").strip() for l in
          adb(ip, "shell", "pm", "list", "packages").splitlines()}
    for p in DEBLOAT:
        if p in PROTECT or p not in on:
            print("  skip", p, "(protegido/ausente)")
        else:
            print("  off ", p, adb(ip, "shell", "pm", "disable-user", p, "--user", "0").strip())

def trap(ip, on):
    """Delegado ao fire_trap.py (modulo do Home Trap)."""
    import fire_trap
    fire_trap.trap(ip, on)
    now = " ".join(l.strip() for l in adb(ip, "shell", "cmd", "package",
                   "query-activities", "--brief", "-c", "-a", "android.intent.action.HOME",
                   "-c", "android.intent.category.DEFAULT").splitlines())
    print("Home holder:", now)
    print("OK. Se o botao Home abrir a home da Amazon, rode: python fire_install.py --revert")

def revert(ip):
    path = back_path(ip) if os.path.isfile(back_path(ip)) else BACK
    if not os.path.isfile(path):
        sys.exit("Sem snapshot (%s): nada para reverter com certeza." % os.path.basename(back_path(ip)))
    b = json.load(open(path))
    print("[1/3] Reativando pacotes desativados...")
    for p in b["disabled"]:
        print("  on ", p, adb(ip, "shell", "pm", "enable", p).strip())
    print("[2/3] Restaurando screensaver %r..." % b["screen"])
    adb(ip, "shell", "settings", "put", "secure", "screensaver_components", b["screen"])
    print("[3/3] Restaurando home original...")
    trap(ip, False)
    home = b.get("home") or "com.amazon.tv.launcher/com.amazon.tv.launcher.MainActivity"
    if not b.get("home"):
        print(adb(ip, "shell", "pm", "enable", "com.amazon.tv.launcher").strip())
    print(adb(ip, "shell", "cmd", "package", "set-home-activity", home).strip())
    os.remove(BACK)
    print("Revert OK.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Instala o Free My TV no Fire TV Stick")
    ap.add_argument("--ip", default=DEFAULT_IP, help="IP do Fire TV (padrao: descobre na LAN)")
    ap.add_argument("--revert", action="store_true", help="restaura launcher, screensaver e pacotes")
    ap.add_argument("--trap", choices=["on", "off"], help="liga/desliga so o Home Trap")
    args = ap.parse_args()

    ip = args.ip
    if not ip:
        from dev import IP as ip  # resolve pelo serial (scripts/dev.py)
    if not os.path.isfile(ADB):
        sys.exit("adb nao encontrado em " + ADB)
    if args.trap:
        import fire_trap
        sys.exit(fire_trap.set_trap(ip, args.trap == "on") or 0)
    sys.exit(revert(ip) if args.revert else install(ip) or 0)
