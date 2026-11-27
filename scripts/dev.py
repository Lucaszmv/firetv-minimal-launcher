"""Resolve o Fire TV Stick na LAN (o DHCP muda o IP). Cacheia em .device_addr."""
import concurrent.futures as cf
import os
import re
import socket
import subprocess

from common_adb import ADB

SERIAL = os.environ.get("FMTV_SERIAL", "G4N2JN03446643N7")
PREFIX = "10.20.20."
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".device_addr")


def _adb(*args, timeout=6):
    try:
        out = subprocess.run([ADB, *args], capture_output=True, timeout=timeout)
        return out.stdout.decode(errors="ignore")
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _valid(addr):
    return _adb("-s", addr, "shell", "getprop ro.serialno").strip() == SERIAL


def _cached():
    try:
        with open(CACHE, encoding="utf-8") as f:
            addr = f.read().strip()
    except OSError:
        return None
    return addr if addr and _valid(addr) else None


def _connected():
    for line in _adb("devices").splitlines():
        if "\tdevice" in line and _valid(line.split("\t")[0]):
            return line.split("\t")[0]
    return None


def _mdns():
    for line in _adb("mdns", "services").splitlines():
        m = re.search(r"(\d+\.\d+\.\d+\.\d+):(\d+)", line)
        if m and "._adb" in line and _valid("%s:%s" % m.groups()):
            return "%s:%s" % m.groups()
    return None


def _probe(i):
    host = PREFIX + str(i)
    try:
        socket.create_connection((host, 5555), timeout=0.35).close()
    except OSError:
        return None
    addr = host + ":5555"
    _adb("connect", addr, timeout=8)
    return addr if _valid(addr) else None


def _scan():
    with cf.ThreadPoolExecutor(max_workers=64) as pool:
        for addr in pool.map(_probe, range(1, 255)):
            if addr:
                return addr
    return None


def resolve(force=False):
    addr = None if force else (_cached() or _connected() or _mdns())
    addr = addr or _scan()
    if not addr:
        raise SystemExit("Fire TV %s nao encontrado na rede %s0/24" % (SERIAL, PREFIX))
    _adb("connect", addr)
    with open(CACHE, "w", encoding="utf-8") as f:
        f.write(addr)
    return addr


DEV = resolve()
IP = DEV.split(":")[0]
