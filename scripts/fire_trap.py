"""Home Trap (Fire TV): liga/desliga o servico de acessibilidade que sobrepoe o launcher Amazon."""
import argparse
import sys

from common_adb import SERVICE, device


def adb(ip, *args):
    """Rodar um comando adb no device e devolver stdout+stderr."""
    return device(ip, *args, timeout=120)


def trap(ip, on):
    """Liga/desliga o Home Trap: flag global fmtv_trap + servico de acessibilidade."""
    adb(ip, "shell", "settings", "put", "global", "fmtv_trap", "1" if on else "0")
    out = adb(ip, "shell", "settings", "get", "secure", "enabled_accessibility_services").strip()
    new = "" if out in ("null", "none") else out
    services = {x for x in new.split(":") if x and x != SERVICE} | ({SERVICE} if on else set())
    new = ":".join(sorted(services))
    adb(ip, "shell", "settings", "put", "secure", "enabled_accessibility_services", new)
    adb(ip, "shell", "settings", "put", "secure", "accessibility_enabled", "1" if on else "0")
    print("  Home Trap:", "ATIVO" if on else "desligado", "->", new)


def set_trap(ip, on):
    """Atalho usado pelo fire_install.py."""
    trap(ip, on)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Home Trap (Fire TV)")
    ap.add_argument("--ip", help="IP do Fire TV (padrao: descobre na LAN)")
    ap.add_argument("--trap", choices=["on", "off"], required=True, help="estado desejado")
    args = ap.parse_args(argv)
    ip = args.ip
    if not ip:
        from dev import IP as ip   # resolve pelo serial (scripts/dev.py)
    trap(ip, args.trap == "on")
    return 0


if __name__ == "__main__":
    sys.exit(main())
