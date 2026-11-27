"""Firewall on-device: personalDNSfilter com blocklist de OTA da Amazon (tudo via adb)."""
import sys, urllib.request

from common_adb import connect, run
from dev import DEV

S = connect(DEV)
APK = 'https://f-droid.org/repo/dnsfilter.android_1506103.apk'
# Dominios de update de firmware da Amazon (TroyPoint/zer0byte 2025-2026, Fire OS)
OTA_HOSTS = ['softwareupdates.amazon.com', 'updates.amazon.com', 'prod.ota-cloudfront.net',
             'd1s31zyz7dcc2d.cloudfront.net', 'amzdigitaldownloads.edgesuite.net',
             'amzdigital-a.akamaihd.net', 'amx-ds.akamaized.net']
CONF = '/sdcard/Android/data/dnsfilter.android/files/PersonalDNSFilter'

def sh(*a, timeout=180):
    return run(*a, serial=S, timeout=timeout)

def install():
    apk = sys.argv[1] if len(sys.argv) > 1 else 'personalDNSfilter.apk'
    urllib.request.urlretrieve(APK, apk)
    print(sh('install', '-r', apk).strip()[-300:])

def push_blocklist():
    hosts = '\r\n'.join(OTA_HOSTS) + '\r\n'
    open('additionalHosts.txt', 'w', encoding='ascii').write(hosts)
    print('mkdir:', (sh('shell', 'mkdir', '-p', CONF).strip() or 'ok').strip())
    print('push:', sh('push', 'additionalHosts.txt', CONF + '/additionalHosts.txt').strip())
    print('ler de volta:')
    cat = sh('shell', 'cat', CONF + '/additionalHosts.txt')
    print(cat if cat.strip() else '(vazio/negado)')

def grant_and_start():
    print('appops:', sh('shell', 'appops', 'set', 'dnsfilter.android',
                        'ACTIVATE_VPN', 'allow').strip() or 'ok')

def verify():
    print('instalado:', 'dnsfilter.android' in sh('shell', 'pm', 'list', 'packages'))
    print('ping OTA:', sh('shell', 'ping', '-c', '1', '-W', '2', OTA_HOSTS[0]).strip()[:200])

if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if a in ('install', 'all'):
        install()
    if a in ('block', 'all'):
        push_blocklist()
    if a in ('start', 'all'):
        grant_and_start()
    if a in ('verify', 'all'):
        verify()
