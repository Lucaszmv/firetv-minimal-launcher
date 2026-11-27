"""NetGuard no Fire Stick: block por app dos 3 pacotes OTA (automação adb, sem digitar texto)."""
import re, subprocess, sys, time, urllib.request

from common_adb import connect, run
from dev import DEV

S = connect(DEV)
PKG = 'eu.faircode.netguard'
APK = 'https://github.com/M66B/NetGuard/releases/download/2.337/NetGuard-v2.337-release.apk'
OTA_PKGS = ['com.amazon.device.software.ota', 'com.amazon.device.software.ota.override',
            'com.amazon.tv.forcedotaupdater.v2']

def sh(*a, timeout=180):
    return run(*a, serial=S, timeout=timeout)

def local(*a, cwd=None):
    p = subprocess.run(*a, capture_output=True, text=True, shell=True)
    return p.stdout + p.stderr

def install():
    urllib.request.urlretrieve(APK, 'NetGuard.apk')
    print('instalando:', sh('install', '-r', 'NetGuard.apk').strip()[-200:])
    rid = sh('uninstall', 'dnsfilter.android').strip()
    print('rollback pDNSF:', rid or '(ja ausente)')

def grant_vpn():
    # appops ACTIVATE_VPN dispensa o dialogo de consentimento do VpnService
    print('appops:', sh('shell', 'appops', 'set', PKG, 'ACTIVATE_VPN', 'allow').strip() or 'ok')
    sh('shell', 'am', 'start', '-n', PKG + '/.ui.settings.SettingsMain')
    time.sleep(6)

def connectivity():
    d = sh('shell', 'dumpsys', 'connectivity')
    return 'eu.darken.netguard' in d or 'netguard' in d.lower()

def dump_xml():
    sh('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
    return re.sub(r'\n\s*', '', sh('shell', 'cat', '/sdcard/ui.xml'))

if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if a in ('install', 'all'):
        install()
    if a in ('start', 'all'):
        grant_vpn()
        print('VPN ativa:', connectivity())
    if a in ('check', 'all'):
        for p in OTA_PKGS:
            d = sh('shell', 'pm', 'list', 'packages')
            print(p, 'presente:', ('package:' + p) in d)
    if a == 'ping':
        print(sh('shell', 'ping', '-c', '1', '-W', '2', 'softwareupdates.amazon.com')[:300])
