#!/usr/bin/env python3
"""Build portable, script-free README artwork from the portfolio's public assets.

Run from any directory with: python scripts/build-assets.py
Install requirements in a virtual environment first. Font outlines keep the
portfolio's Geist typeface intact when GitHub loads each SVG as an image.
"""

from functools import lru_cache
from html import escape
from pathlib import Path
import argparse
import base64
import io
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
LOCAL_ASSETS = None
SOURCE = "https://raw.githubusercontent.com/jgil325/jgil325.github.io/main/assets/"
# Order, subjects, mirroring, contrast, and timing from the portfolio's
# src/templates.mjs and src/scene.js. Only the decorative background rotates.
SCENES = [
    {"key": "hillside", "subject": (.68, .55), "flip": True},
    {"key": "open-skies", "subject": (.75, .50), "contrast": .9},
    {"key": "golden-hour", "subject": (.60, .45), "flip": True},
    {"key": "snowy-crossing", "subject": (.85, .82)},
    {"key": "arcane-city", "subject": (.52, .45), "contrast": .8},
    {"key": "sunlit-study", "subject": (.55, .55), "contrast": .85},
    {"key": "sleepy-cats", "subject": (.72, .40)},
]
DWELL_SECONDS = 8
RIPPLE_SECONDS = 1.9
RIPPLE_BANDS = 12
BAYER = [[0, 48, 12, 60, 3, 51, 15, 63], [32, 16, 44, 28, 35, 19, 47, 31], [8, 56, 4, 52, 11, 59, 7, 55], [40, 24, 36, 20, 43, 27, 39, 23], [2, 50, 14, 62, 1, 49, 13, 61], [34, 18, 46, 30, 33, 17, 45, 29], [10, 58, 6, 54, 9, 57, 5, 53], [42, 26, 38, 22, 41, 25, 37, 21]]
LOOKS = {
    "light": {"canvas": "#fafafc", "ink": "#17191d", "muted": "#60656f", "accent": "#3159d8", "line": "#dfe2e8"},
    "dark": {"canvas": "#15171b", "ink": "#f4f5f8", "muted": "#adb2be", "accent": "#8ca7ff", "line": "#343842"},
}


def download(relative):
    if LOCAL_ASSETS is not None and (LOCAL_ASSETS / relative).is_file():
        return LOCAL_ASSETS / relative
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


def scene_texture(width, height, theme, mobile, config, anchor=None):
    """Embed one color sample per dot; SVG supplies the crisp vector dot mask.

    The scene textures stay small while the vector mask stays sharp at any
    display density. No artwork is fetched when a visitor loads the banner.
    """
    image = Image.open(download(f"scenes/{config['key']}.jpg")).convert("RGB")
    if config.get("flip"):
        image = ImageOps.mirror(image)
    iw, ih = image.size
    crop_width = iw
    crop_height = iw * height / width
    if crop_height > ih:
        crop_height = ih
        crop_width = ih * width / height
    crop_width /= 1.04
    crop_height /= 1.04
    if anchor is None:
        anchor = (0.50, 0.84) if mobile else (0.73, 0.81)
    subject_x, subject_y = config["subject"]
    x = min(iw - crop_width, max(0, subject_x * iw - anchor[0] * crop_width))
    y = min(ih - crop_height, max(0, subject_y * ih - anchor[1] * crop_height))
    pitch = 7 if mobile else 6
    cols, rows = math.ceil(width / pitch), math.ceil(height / pitch)
    sample = image.crop((x, y, x + crop_width, y + crop_height)).resize((cols, rows), Image.Resampling.BOX)
    texture = Image.new("RGB", (cols, rows))
    pixels = []
    for row in range(rows):
        for col in range(cols):
            rgb = [v / 255 for v in sample.getpixel((col, row))]
            contrast = config.get("contrast", 1)
            rgb = [.62 + (value - .62) * contrast for value in rgb]
            if theme == "dark":
                rgb = [max(0, min(1, value * multiplier)) ** 1.15 for value, multiplier in zip(rgb, (.55, .66, .98))]
            lum = sum(value * factor for value, factor in zip(rgb, (.2126, .7152, .0722)))
            saturation = 1.3 if theme == "dark" else 1.35
            exposure = 1.05 if theme == "dark" else .97
            rgb = [max(0, min(1, (lum + (value - lum) * saturation) * exposure)) for value in rgb]
            pixels.append(tuple(round(value * 255) for value in rgb))
    texture.putdata(pixels)
    encoded = io.BytesIO()
    texture.save(encoded, "WEBP", lossless=True, method=6)
    return "data:image/webp;base64," + base64.b64encode(encoded.getvalue()).decode("ascii")


def dot_mask(width, height, theme, mobile, fade_top=0, fade_bottom=.2):
    pitch = 7 if mobile else 6
    cols, rows = math.ceil(width / pitch), math.ceil(height / pitch)
    first_full = math.ceil(height * fade_top / pitch)
    last_full = math.floor(height * (1 - fade_bottom) / pitch)
    edge = [f'M0 {first_full * pitch}h{width}v{(last_full - first_full) * pitch}H0z']
    for row in range(rows):
        if first_full <= row < last_full:
            continue
        position = (row + .5) * pitch / height
        keep_top = smooth(0, fade_top, position) if fade_top else 1
        keep_bottom = 1 - smooth(1 - fade_bottom, 1, position) if fade_bottom else 1
        keep = keep_top * keep_bottom
        for col in range(cols):
            if keep > BAYER[row % 8][col % 8] / 64:
                edge.append(f'M{col * pitch} {row * pitch}h{pitch}v{pitch}h{-pitch}z')
    if theme == "dark":
        dot = f'<circle cx="{pitch / 2}" cy="{pitch / 2}" r="{pitch * .29}" fill="white"/>'
    else:
        dot = f'<rect x="{pitch * .18}" y="{pitch * .18}" width="{pitch * .64}" height="{pitch * .64}" fill="white"/>'
    return f'''<pattern id="dots" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse">{dot}</pattern>
<clipPath id="edge-dissolve"><path d="{''.join(edge)}"/></clipPath>
<mask id="dot-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="{width}" height="{height}"><g clip-path="url(#edge-dissolve)"><rect width="{width}" height="{height}" fill="url(#dots)"/></g></mask>'''


def ripple_clips(width, height):
    clips = []
    diagonal = math.hypot(width, height)
    for band in range(RIPPLE_BANDS):
        inner = max(0, diagonal * band / RIPPLE_BANDS - .5)
        outer = diagonal * (band + 1) / RIPPLE_BANDS + .5
        def circle(radius):
            return f'M{width + radius:.2f} 0a{radius:.2f} {radius:.2f} 0 1 0 {-2 * radius:.2f} 0a{radius:.2f} {radius:.2f} 0 1 0 {2 * radius:.2f} 0z'
        path = circle(outer) + (circle(inner) if inner else "")
        clips.append(f'<clipPath id="band-{band}"><path clip-rule="evenodd" d="{path}"/></clipPath>')
    return "".join(clips)


def scene_rotation(scenes=SCENES):
    layers = []
    for band in range(RIPPLE_BANDS):
        layers.append(f'<g clip-path="url(#band-{band})">')
        for index, config in enumerate(scenes):
            delay = index * (DWELL_SECONDS + RIPPLE_SECONDS) - RIPPLE_SECONDS + band * (RIPPLE_SECONDS - .25) / (RIPPLE_BANDS - 1)
            layers.append(f'<use href="#scene-{config["key"]}" class="scene scene-{index}" style="animation-delay:{delay:.3f}s"/>')
        layers.append('</g>')
    return "".join(layers)


def banner(theme, mobile):
    width, height = (640, 580) if mobile else (1000, 480)
    palette = LOOKS[theme]
    suffix = "mobile-" if mobile else ""
    cycle = len(SCENES) * (DWELL_SECONDS + RIPPLE_SECONDS)
    fade_in = .25 / cycle * 100
    active = 100 / len(SCENES)
    textures = "".join(f'<image id="scene-{config["key"]}" width="{width}" height="{height}" preserveAspectRatio="none" style="image-rendering:pixelated" href="{scene_texture(width, height, theme, mobile, config)}"/>' for config in SCENES)
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Jacob Gil — Good ideas. Real products.</title>
<desc id="desc">Product Lead at RF Labs. Seven dot-field scenes rotate in the same order as jgil325.github.io, with an eight-second hold and a ripple from the top right. Reduced motion shows a still hillside.</desc>
<defs>
  <clipPath id="frame"><rect width="{width}" height="{height}" rx="20"/></clipPath>
  <radialGradient id="quiet" cx="50%" cy="38%" r="62%"><stop stop-color="{palette['canvas']}" stop-opacity=".97"/><stop offset=".52" stop-color="{palette['canvas']}" stop-opacity=".88"/><stop offset="1" stop-color="{palette['canvas']}" stop-opacity="0"/></radialGradient>
  <linearGradient id="top" x2="0" y2="1"><stop stop-color="{palette['canvas']}" stop-opacity=".7"/><stop offset="1" stop-color="{palette['canvas']}" stop-opacity="0"/></linearGradient>
  {ripple_clips(width, height)}
  {dot_mask(width, height, theme, mobile)}
  {textures}
</defs>
<style>
  .scene {{ opacity: 0; animation: show-scene {cycle:.1f}s linear infinite; }}
  .scene-0 {{ opacity: 1; }}
  @keyframes show-scene {{ 0% {{ opacity: 0; }} {fade_in:.5f}%, {active:.5f}% {{ opacity: 1; }} {active + fade_in:.5f}%, 100% {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .scene {{ animation: none; opacity: 0; }} .scene-0 {{ opacity: 1; }} }}
</style>
<g clip-path="url(#frame)"><rect width="{width}" height="{height}" fill="{palette['canvas']}"/>
<g mask="url(#dot-mask)">{scene_rotation()}</g>
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
    destination = ASSETS / f"hero-cycle-{suffix}{theme}.svg"
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


def contact_banner(theme, mobile):
    width, height = (640, 580) if mobile else (1000, 460)
    palette = LOOKS[theme]
    suffix = "mobile-" if mobile else ""
    start = next(index for index, config in enumerate(SCENES) if config["key"] == "snowy-crossing")
    scenes = SCENES[start:] + SCENES[:start]
    anchor = (.5, .75) if mobile else (.72, .55)
    cycle = len(scenes) * (DWELL_SECONDS + RIPPLE_SECONDS)
    fade_in, active = .25 / cycle * 100, 100 / len(scenes)
    textures = "".join(f'<image id="scene-{config["key"]}" width="{width}" height="{height}" preserveAspectRatio="none" style="image-rendering:pixelated" href="{scene_texture(width, height, theme, mobile, config, anchor)}"/>' for config in scenes)
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Have something in mind? Get in touch with Jacob Gil.</title>
<desc id="desc">The portfolio's contact background, starting with the snowy crossing and rotating through seven dot-field scenes. Email jacobgil325@gmail.com. Reduced motion displays a still snowy scene.</desc>
<defs>
  <clipPath id="frame"><rect width="{width}" height="{height}" rx="20"/></clipPath>
  <linearGradient id="quiet" x1="0" y1="0" x2="1" y2="0"><stop stop-color="{palette['canvas']}" stop-opacity=".94"/><stop offset=".32" stop-color="{palette['canvas']}" stop-opacity=".80"/><stop offset=".72" stop-color="{palette['canvas']}" stop-opacity="0"/></linearGradient>
  {ripple_clips(width, height)}
  {dot_mask(width, height, theme, mobile, fade_top=.3, fade_bottom=.3)}
  {textures}
</defs>
<style>
  .scene {{ opacity: 0; animation: show-scene {cycle:.1f}s linear infinite; }}
  .scene-0 {{ opacity: 1; }}
  @keyframes show-scene {{ 0% {{ opacity: 0; }} {fade_in:.5f}%, {active:.5f}% {{ opacity: 1; }} {active + fade_in:.5f}%, 100% {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .scene {{ animation: none; opacity: 0; }} .scene-0 {{ opacity: 1; }} }}
</style>
<g clip-path="url(#frame)"><rect width="{width}" height="{height}" fill="{palette['canvas']}"/>
<g mask="url(#dot-mask)">{scene_rotation(scenes)}</g>
<rect width="{width}" height="{height}" fill="url(#quiet)"/>
''']
    if mobile:
        parts.append(f'<rect x="38" y="48" width="208" height="48" rx="24" fill="{palette["canvas"]}" stroke="{palette["line"]}"/><circle cx="63" cy="72" r="6" fill="{palette["accent"]}"/>')
        parts.append(lettering("Get in touch", 81, 80, 24, palette["ink"]))
        parts.append(lettering("Have something", 38, 205, 76, palette["ink"], tracking=-4.6))
        parts.append(lettering("in mind?", 38, 285, 76, palette["accent"], tracking=-4.6))
        parts.append(f'<rect x="38" y="333" width="484" height="72" rx="36" fill="{palette["ink"]}"/>')
        parts.append(lettering("jacobgil325@gmail.com", 64, 378, 27, palette["canvas"]))
        parts.append(f'<path d="M477 379l18-18m-15 0h15v15" fill="none" stroke="{palette["canvas"]}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    else:
        parts.append(f'<rect x="44" y="47" width="154" height="35" rx="17.5" fill="{palette["canvas"]}" stroke="{palette["line"]}"/><circle cx="62" cy="64.5" r="4" fill="{palette["accent"]}"/>')
        parts.append(lettering("Get in touch", 76, 70, 17, palette["ink"]))
        parts.append(lettering("Have something", 44, 190, 84, palette["ink"], tracking=-5.4))
        parts.append(lettering("in mind?", 44, 275, 84, palette["accent"], tracking=-5.4))
        parts.append(f'<rect x="44" y="319" width="341" height="54" rx="27" fill="{palette["ink"]}"/>')
        parts.append(lettering("jacobgil325@gmail.com", 65, 353, 19, palette["canvas"]))
        parts.append(f'<path d="M351 352l13-13m-11 0h11v11" fill="none" stroke="{palette["canvas"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
    parts.append('</g></svg>\n')
    destination = ASSETS / f"contact-cycle-{suffix}{theme}.svg"
    destination.write_text("".join(parts))
    print(f"Built {destination.relative_to(ROOT)} ({destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portfolio", type=Path, help="Use the source assets in a local portfolio checkout")
    args = parser.parse_args()
    if args.portfolio:
        LOCAL_ASSETS = args.portfolio.resolve() / "assets"
        if not LOCAL_ASSETS.is_dir():
            parser.error("The portfolio path must contain its assets directory")
    ASSETS.mkdir(parents=True, exist_ok=True)
    for theme in LOOKS:
        for mobile in (False, True):
            banner(theme, mobile)
            contact_banner(theme, mobile)
    project_previews()
    (ASSETS / "OFL.txt").write_bytes(download("fonts/OFL.txt").read_bytes())
