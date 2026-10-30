#!/usr/bin/env python3
"""Build portable, script-free README artwork from the portfolio's public assets.

Run from any directory with: python scripts/build-assets.py
Install requirements in a virtual environment first. Font outlines keep the
portfolio's Geist typeface intact when GitHub loads each SVG as an image.
"""

from collections import defaultdict
from functools import lru_cache
from html import escape
from pathlib import Path
import math
import ssl
import urllib.request

import certifi
from PIL import Image, ImageOps
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
ASSETS = ROOT / "assets"
SOURCE = "https://raw.githubusercontent.com/jgil325/jgil325.github.io/main/assets/"
LOOKS = {
    "light": {"canvas": "#fafafc", "ink": "#17191d", "muted": "#60656f", "accent": "#3159d8", "line": "#dfe2e8"},
    "dark": {"canvas": "#15171b", "ink": "#f4f5f8", "muted": "#adb2be", "accent": "#8ca7ff", "line": "#343842"},
}


def download(relative):
    target = CACHE / relative
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(SOURCE + relative, context=context, timeout=30) as response:
            target.write_bytes(response.read())
    return target


@lru_cache(maxsize=2)
def font(weight):
    variable = TTFont(download("fonts/geist-latin.woff2"))
    return instantiateVariableFont(variable, {"wght": weight}, inplace=False)


def lettering(copy, x, y, size, color, weight=500, tracking=0, center=False):
    face = font(weight)
    scale = size / face["head"].unitsPerEm
    glyphs = face.getGlyphSet()
    mapping = face.getBestCmap()
    metrics = face["hmtx"].metrics
    width = sum(metrics[mapping[ord(char)]][0] * scale for char in copy) + tracking * (len(copy) - 1)
    cursor = x - width / 2 if center else x
    fragments = []
    for char in copy:
        name = mapping[ord(char)]
        pen = SVGPathPen(glyphs, ntos=lambda n: str(round(n, 2)))
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, y)))
        fragments.append(pen.getCommands())
        cursor += metrics[name][0] * scale + tracking
    return f'<path fill="{color}" aria-label="{escape(copy)}" d="{"".join(fragments)}"/>'


def smooth(a, b, value):
    t = min(1, max(0, (value - a) / (b - a)))
    return t * t * (3 - 2 * t)


def scene(width, height, theme, mobile):
    """Sample the site's mirrored hillside into a fixed vector dot field."""
    image = ImageOps.mirror(Image.open(download("scenes/hillside.jpg")).convert("RGB"))
    iw, ih = image.size
    crop_width = iw
    crop_height = iw * height / width
    if crop_height > ih:
        crop_height = ih
        crop_width = ih * width / height
    crop_width /= 1.04
    crop_height /= 1.04
    anchor = (0.50, 0.84) if mobile else (0.73, 0.81)
    x = min(iw - crop_width, max(0, 0.68 * iw - anchor[0] * crop_width))
    y = min(ih - crop_height, max(0, 0.55 * ih - anchor[1] * crop_height))
    pitch = 7 if mobile else 6
    cols, rows = math.ceil(width / pitch), math.ceil(height / pitch)
    sample = image.crop((x, y, x + crop_width, y + crop_height)).resize((cols, rows), Image.Resampling.BOX)
    # The site's ordered edge dissolve, retained as a vector pattern.
    bayer = [[0, 48, 12, 60, 3, 51, 15, 63], [32, 16, 44, 28, 35, 19, 47, 31], [8, 56, 4, 52, 11, 59, 7, 55], [40, 24, 36, 20, 43, 27, 39, 23], [2, 50, 14, 62, 1, 49, 13, 61], [34, 18, 46, 30, 33, 17, 45, 29], [10, 58, 6, 54, 9, 57, 5, 53], [42, 26, 38, 22, 41, 25, 37, 21]]
    groups = defaultdict(lambda: defaultdict(list))
    for row in range(rows):
        for col in range(cols):
            px, py = (col + .5) * pitch, (row + .5) * pitch
            keep = 1 - smooth(.80, 1, py / height)
            if keep <= bayer[row % 8][col % 8] / 64:
                continue
            rgb = [v / 255 for v in sample.getpixel((col, row))]
            if theme == "dark":
                rgb = [max(0, min(1, value * multiplier)) ** 1.15 for value, multiplier in zip(rgb, (.55, .66, .98))]
            lum = sum(value * factor for value, factor in zip(rgb, (.2126, .7152, .0722)))
            saturation = 1.3 if theme == "dark" else 1.35
            exposure = 1.05 if theme == "dark" else .97
            rgb = [max(0, min(1, (lum + (value - lum) * saturation) * exposure)) for value in rgb]
            color = "#" + "".join(f"{round(value * 31) * 255 // 31:02x}" for value in rgb)
            size = ((.25 + .55 * lum ** .9) if theme == "dark" else (.5 + .4 * (1 - lum) ** .9)) * pitch
            band = min(11, int(math.hypot(1 - px / width, py / height) / math.sqrt(2) * 12))
            if theme == "dark":
                radius = round(size * .56, 1)
                shape = f'M{px - radius:.1f} {py:.1f}a{radius} {radius} 0 1 0 {radius * 2:.1f} 0a{radius} {radius} 0 1 0 {-radius * 2:.1f} 0'
            else:
                size = round(size, 1)
                shape = f'M{px - size / 2:.1f} {py - size / 2:.1f}h{size}v{size}h{-size}z'
            groups[band][color].append(shape)
    return "".join(
        f'<g class="field wave-{band}">' + "".join(f'<path fill="{color}" d="{"".join(paths)}"/>' for color, paths in colors.items()) + "</g>"
        for band, colors in sorted(groups.items())
    )


def banner(theme, mobile):
    width, height = (640, 580) if mobile else (1000, 480)
    palette = LOOKS[theme]
    suffix = "mobile-" if mobile else ""
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Jacob Gil — Good ideas. Real products.</title>
<desc id="desc">Product Lead at RF Labs. A gently rippling dot-field hillside, matching jgil325.github.io. Animation stops for reduced motion.</desc>
<defs>
  <clipPath id="frame"><rect width="{width}" height="{height}" rx="20"/></clipPath>
  <radialGradient id="quiet" cx="50%" cy="38%" r="62%"><stop stop-color="{palette['canvas']}" stop-opacity=".97"/><stop offset=".52" stop-color="{palette['canvas']}" stop-opacity=".88"/><stop offset="1" stop-color="{palette['canvas']}" stop-opacity="0"/></radialGradient>
  <linearGradient id="top" x2="0" y2="1"><stop stop-color="{palette['canvas']}" stop-opacity=".7"/><stop offset="1" stop-color="{palette['canvas']}" stop-opacity="0"/></linearGradient>
</defs>
<style>
  .field {{ animation: ripple 12s ease-in-out infinite; }}
  @keyframes ripple {{ 0%, 60%, 83%, 100% {{ opacity: 1; }} 70% {{ opacity: .30; }} }}
  {''.join(f'.wave-{i} {{ animation-delay: {-5 + i * .16:.2f}s; }}' for i in range(12))}
  @media (prefers-reduced-motion: reduce) {{ .field {{ animation: none; }} }}
</style>
<g clip-path="url(#frame)"><rect width="{width}" height="{height}" fill="{palette['canvas']}"/>
{scene(width, height, theme, mobile)}
<rect width="{width}" height="{height}" fill="url(#quiet)"/>
<rect width="{width}" height="100" fill="url(#top)"/>
''']
    if mobile:
        parts.append(lettering("jacob gil.", 320, 58, 32, palette["accent"], 600, -1.9, True))
        pill_x, pill_y, pill_w, pill_h = 117, 87, 406, 42
        parts.append(f'<rect x="{pill_x}" y="{pill_y}" width="{pill_w}" height="{pill_h}" rx="21" fill="{palette["canvas"]}" stroke="{palette["line"]}"/>')
        parts.append(f'<rect x="123" y="93" width="64" height="30" rx="15" fill="{palette["accent"]}"/>')
        parts.append(lettering("Now", 155, 115, 20, palette["canvas"], center=True))
        parts.append(lettering("Product Lead at RF Labs", 199, 115, 21, palette["ink"]))
        parts.append(lettering("Good ideas.", 320, 231, 83, palette["ink"], tracking=-5.1, center=True))
        parts.append(lettering("Real products.", 320, 315, 83, palette["accent"], tracking=-5.1, center=True))
    else:
        parts.append(lettering("jacob gil.", 38, 59, 27, palette["accent"], 600, -1.6))
        parts.append(f'<rect x="695" y="30" width="267" height="34" rx="17" fill="{palette["canvas"]}" stroke="{palette["line"]}"/>')
        parts.append(f'<rect x="700" y="35" width="46" height="24" rx="12" fill="{palette["accent"]}"/>')
        parts.append(lettering("Now", 723, 52, 13, palette["canvas"], center=True))
        parts.append(lettering("Product Lead at RF Labs", 755, 52, 14, palette["ink"]))
        parts.append(lettering("Good ideas.", 500, 190, 96, palette["ink"], tracking=-6.2, center=True))
        parts.append(lettering("Real products.", 500, 284, 96, palette["accent"], tracking=-6.2, center=True))
        parts.append(lettering("Product thinking. Interface craft. Systems underneath.", 500, 330, 19, palette["ink"], center=True))
    parts.append("</g></svg>\n")
    destination = ASSETS / f"hero-{suffix}{theme}.svg"
    destination.write_text("".join(parts))
    print(f"Built {destination.relative_to(ROOT)} ({destination.stat().st_size:,} bytes)")


def project_previews():
    for key, source, size in [
        ("ofc-mobile", "ofc-desktop", (1000, 680)),
        ("taiwanese-study", "taiwanese-desktop", (1000, 680)),
        ("broadcast-graphics", "broadcast-desktop", (1600, 549)),
    ]:
        source_image = Image.open(download(f"source/{source}.png")).convert("RGBA")
        canvas = Image.new("RGBA", source_image.size, LOOKS["light"]["canvas"])
        original = Image.alpha_composite(canvas, source_image).convert("RGB")
        # Contain instead of crop: every original product composition stays visible.
        fitted = ImageOps.contain(original, size, Image.Resampling.LANCZOS)
        background = Image.new("RGB", size, original.getpixel((0, 0)))
        background.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
        background.save(ASSETS / f"{key}.webp", "WEBP", quality=93, method=6)


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    for theme in LOOKS:
        for mobile in (False, True):
            banner(theme, mobile)
    project_previews()
    (ASSETS / "OFL.txt").write_bytes(download("fonts/OFL.txt").read_bytes())
