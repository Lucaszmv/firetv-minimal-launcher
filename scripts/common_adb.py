"""Ponto unico do adb: caminho, serial, timeout e encoding.

Antes cada script repetia o caminho do adb (metade com C:\\Users\\... cravado) e
chamava subprocess sem timeout/encoding. Importe daqui em vez de copiar.
"""
import os
import shutil
import subprocess

PKG = "io.freemytv"
HOME = PKG + "/.HomeActivity"
SERVICE = PKG + "/" + PKG + ".RemoteKeyService"
PORT = 5555


def _find_adb():
    """SDK primeiro (um `adb` de outra suíte no PATH pode ser outro protocolo), PATH depois."""
    for base in (os.environ.get("ANDROID_HOME"), os.environ.get("LOCALAPPDATA", "") and
                 os.path.join(os.environ["LOCALAPPDATA"], "android-sdk")):
        if not base:
            continue
        path = os.path.join(base, "platform-tools", "adb.exe" if os.name == "nt" else "adb")
        if os.path.isfile(path):
            return path
    return shutil.which("adb") or "adb"


ADB = _find_adb()


def serial(ip):
    """'192.168.1.50' ou '192.168.1.50:5555' -> serial do adb."""
    return ip if ":" in ip else "%s:%d" % (ip, PORT)


def run(*args, serial=None, timeout=60):
    """Roda o adb e devolve stdout+stderr; nunca quebra por encoding ou timeout."""
    cmd = [ADB] + (["-s", serial] if serial else []) + [str(a) for a in args]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return p.stdout + p.stderr
    except FileNotFoundError:
        raise SystemExit("adb nao encontrado em " + ADB)
    except subprocess.TimeoutExpired:
        return ""


def connect(ip, tries=5):
    """Conecta no device e devolve o serial pronto para `-s`."""
    addr = serial(ip)
    for _ in range(tries):
        if "connected" in run("connect", addr, timeout=30).lower():
            break
    return addr


def device(ip, *args, timeout=60):
    return run(*args, serial=connect(ip), timeout=timeout)
