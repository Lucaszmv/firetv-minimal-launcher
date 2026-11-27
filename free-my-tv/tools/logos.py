#!/usr/bin/env python3
"""Logos do dock para apps que so trazem banner 16:9 com fundo claro.

Le o APK ja instalado no device (adb pull) e grava app/assets/logos/<key>.png: o
lockup do app sem o fundo, com o wordmark em branco, no mesmo espirito dos logos
que o dock ja usa (Spotify, KICK, Twitch).

Uso:
  python free-my-tv/tools/logos.py --apks <dir com <package>.apk>
  python free-my-tv/tools/logos.py --check
"""
import argparse
import io
import os
import sys
import zipfile

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "app", "assets", "logos")
MAX_W = 512

# key -> (pacote, entrada no APK, monocromatico, cor da marca no SHELF, tirar selo verde)
APPS = {
    "unitv": ("com.integration.unitvsiptv", "res/wN.png", False, "E01B24", False),
    "stv": ("com.stv.vod", "res/5h.png", False, "E6007E", False),
    "tizentube": ("io.gh.reisxd.tizentube.cobalt",
                  "res/drawable-xxxhdpi-v4/app_banner", True, "0E7BB5", True),
}


def load(apks, pkg, entry):
    path = os.path.join(apks, pkg + ".apk")
    with zipfile.ZipFile(path) as z:
        return Image.open(io.BytesIO(z.read(entry))).convert("RGBA")


def smooth_profile(profile, window):
    r = window // 2
    padded = np.pad(profile, ((r, r), (0, 0)), mode="edge")
    k = np.ones(window) / window
    return np.stack([np.convolve(padded[:, i], k, "valid") for i in range(profile.shape[1])], axis=1)


def background_model(rgb):
    """Fundo em cada ponto: as quatro bordas interpoladas (degrade incluso), como no bannerLogo do app."""
    h, w, _ = rgb.shape
    band = max(1, round(h * 0.03))
    left = smooth_profile(rgb[:, :band].mean(axis=1), 25)
    right = smooth_profile(rgb[:, w - band:].mean(axis=1), 25)
    top = smooth_profile(rgb[:band].mean(axis=0), 41)
    bottom = smooth_profile(rgb[h - band:].mean(axis=0), 41)
    p00, p10, p01, p11 = top[0], top[-1], bottom[0], bottom[-1]
    u = (np.arange(w) / max(1, w - 1))[None, :, None]
    v = (np.arange(h) / max(1, h - 1))[:, None, None]
    return ((1 - v) * top[None] + v * bottom[None] + (1 - u) * left[:, None] + u * right[:, None]
            - ((1 - u) * (1 - v) * p00 + u * (1 - v) * p10 + (1 - u) * v * p01 + u * v * p11))


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def cut_background(img):
    """Se o APK ja entrega o recorte, usa o alpha dele; senao tira o fundo pela cor."""
    px = np.asarray(img, dtype=np.float64)
    rgb = px[:, :, :3] / 255.0
    src = px[:, :, 3] / 255.0
    if src.min() < 0.98:
        return rgb, (src * 255).round().astype(np.uint8)
    bg = background_model(rgb)
    dist = np.sqrt(((rgb - bg) ** 2).mean(axis=2))
    a = smoothstep(0.07, 0.22, dist)
    safe = np.maximum(a, 1e-6)[:, :, None]
    out = np.clip((rgb - (1 - a)[:, :, None] * bg) / safe, 0, 1)
    alpha = (a * 255).round().astype(np.uint8)
    return out, alpha


def drop_badge(rgb, alpha):
    """Tira o selo verde 'android tv' do banner do TizenTube (some junto o texto branco de dentro)."""
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    green = (alpha > 0) & (g > 0.55) & (g > r + 0.15) & (g > b + 0.10)
    ys, xs = np.nonzero(green)
    if len(xs) == 0:
        return alpha
    y0, y1 = max(0, ys.min() - 2), min(alpha.shape[0] - 1, ys.max() + 2)
    x0, x1 = max(0, xs.min() - 2), min(alpha.shape[1] - 1, xs.max() + 2)
    alpha[y0:y1 + 1, x0:x1 + 1] = 0
    return alpha


def split_icon(rgb, alpha):
    """Primeira coluna vazia depois do icone: a esquerda fica colorida, a direita e texto."""
    h, w = alpha.shape
    empty = alpha.max(axis=0) == 0
    start = max(2, int(w * 0.15))
    run = 0
    for x in range(start, w):
        if empty[x]:
            run += 1
            if run >= max(3, int(w * 0.04)):
                return x - run + 1
        else:
            run = 0
    return 0


def to_white(rgb, mask):
    rgb[mask] = 1.0


def luminance(rgb):
    return 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]


def saturation(rgb):
    hi = rgb.max(axis=2)
    lo = rgb.min(axis=2)
    return np.where(hi <= 0, 0.0, (hi - lo) / np.maximum(hi, 1e-6))


def trim(rgb, alpha):
    ys, xs = np.nonzero(alpha > 10)
    if len(xs) == 0:
        return None
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    return rgb[y0:y1 + 1, x0:x1 + 1], alpha[y0:y1 + 1, x0:x1 + 1]


def build(key, apks):
    pkg, entry, mono, _, badge = APPS[key]
    img = load(apks, pkg, entry)
    rgb, alpha = cut_background(img)
    if badge:
        alpha = drop_badge(rgb, alpha)
    if mono:
        to_white(rgb, alpha > 0)
    else:
        split = split_icon(rgb, alpha)
        if split:
            text = np.zeros(alpha.shape, dtype=bool)
            text[:, split:] = True
            dark = (luminance(rgb) < 0.5) & (saturation(rgb) < 0.35) & text
            to_white(rgb, dark)
    cropped = trim(rgb, alpha)
    if cropped is None:
        raise SystemExit("sem tinta em " + key)
    rgb, alpha = cropped
    out = np.dstack([(rgb * 255).round().astype(np.uint8), alpha])
    im = Image.fromarray(out)
    pad = max(2, round(max(im.size) * 0.02))
    if im.width > MAX_W - 2 * pad:
        h = max(1, round(im.height * (MAX_W - 2 * pad) / im.width))
        im = im.resize((MAX_W - 2 * pad, h), Image.LANCZOS)
    canvas = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    canvas.paste(im, (pad, pad), im)
    os.makedirs(OUT, exist_ok=True)
    canvas.save(os.path.join(OUT, key + ".png"))
    return canvas


def check():
    ok = True
    for key in APPS:
        path = os.path.join(OUT, key + ".png")
        if not os.path.exists(path):
            print("faltando:", path)
            ok = False
            continue
        im = Image.open(path)
        alpha = im.getchannel("A").getextrema()
        good = im.mode == "RGBA" and alpha[0] < 255 and im.width <= MAX_W
        print("%-10s %s %s alpha=%s" % (key, im.size, im.mode, alpha))
        ok = ok and good
    print("=== OK ===" if ok else "=== FALHOU ===")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apks", default=os.environ.get("FMT_APKS", ""))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        sys.exit(check())
    if not a.apks:
        sys.exit("--apks <dir> (ou FMT_APKS) com <package>.apk")
    for key in APPS:
        im = build(key, a.apks)
        print("%-10s %s %s" % (key, im.size, APPS[key][3]))
    sys.exit(check())


if __name__ == "__main__":
    main()
