"""Baseline do device antes da update OTA (pacotes, acessibilidade, trap, build)."""
import json, sys

from common_adb import connect, run
from dev import DEV

S = connect(DEV)

def r(*a, timeout=120):
    return run(*a, serial=S, timeout=timeout).strip()

def baseline() -> dict:
    props = {}
    for p in ('ro.build.version.incremental', 'ro.build.display.id', 'ro.build.version.fireos',
              'ro.build.date', 'ro.build.mktg.fireos'):
        props[p] = r('shell', 'getprop', p)
    return {
        'build': props,
        'trap': {
            'fmtv_trap': r('shell', 'settings', 'get', 'global', 'fmtv_trap'),
            'acc_services': r('shell', 'settings', 'get', 'secure', 'enabled_accessibility_services'),
            'acc_enabled': r('shell', 'settings', 'get', 'secure', 'accessibility_enabled'),
        },
        'disabled_packages': [l.replace('package:', '') for l in r('shell', 'pm', 'list', 'packages', '-d').splitlines() if l],
    }

def main() -> None:
    b = baseline()
    with open('fmtv_ota_baseline.json', 'w', encoding='utf-8') as f:
        json.dump(b, f, indent=1, ensure_ascii=False)
    with open('pm_list_before.txt', 'w', encoding='utf-8') as f:
        f.write(r('shell', 'pm', 'list', 'packages'))
    print('build:', b['build']['ro.build.version.incremental'], b['build']['ro.build.display.id'])
    print('trap:', b['trap']['fmtv_trap'], '| acc:', b['trap']['acc_services'][:40] if b['trap']['acc_services'] else 'VAZIO')
    print('disabled:', len(b['disabled_packages']))
    print('baseline OK')

if __name__ == '__main__':
    main()
