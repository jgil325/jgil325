# Profile artwork

This profile follows [Jacob Gil’s portfolio](https://jgil325.github.io): Geist type, blue accents, a halftone hillside, light and dark palettes, and the same project descriptions and previews.

## Rebuild

```sh
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/build-assets.py
```

The builder fetches public source assets from `jgil325/jgil325.github.io` into an ignored `.cache/` directory. Generated artwork is checked in, so the profile needs no build service or third-party image endpoint. Rebuild after changing the banner or portfolio source artwork. Text in the SVG is outlined so Geist remains consistent in GitHub’s image context. Accessible image descriptions are provided in `README.md` and in the SVG title and description.

To read assets directly from a local portfolio checkout, append `--portfolio /path/to/jgil325.github.io` to the build command.

The four hero SVGs cover narrow and wide screens in light and dark mode. They rotate through the website’s seven scenes in order: hillside, open skies, golden hour, snowy crossing, arcane city, sunlit study, and sleepy cats. Each holds for eight seconds, followed by a 1.9-second ripple spreading from the top right. The heading stays fixed. Twelve concentric SVG clips stagger a short crossfade across the picture, approximating the website’s dot-by-dot WebGL transition within GitHub’s image context.

Each scene is sampled once per dot and embedded as a small lossless WebP texture. A shared vector mask supplies crisp circular or square dots and an ordered dissolve at the bottom. This keeps the complete seven-scene cycle smaller than repeating every vector dot seven times. Typography, dot masks, and transition clips remain vector shapes. `prefers-reduced-motion: reduce` disables rotation and displays only the first hillside scene. No JavaScript, external fonts, embedded HTML, or network requests run inside the SVGs.

## Credits

- Geist is by Vercel and basement.studio, licensed under the SIL Open Font License 1.1. The license is included in [`assets/OFL.txt`](assets/OFL.txt).
- The backgrounds use the same Mushoku Tensei artwork and anime screenshots as the portfolio: [Roxy & Rudeus, hillside](https://wallhaven.cc/w/gpeoyl), [Eris, open skies](https://wallhaven.cc/w/v936d8), [Sylphie, golden hour](https://wallhaven.cc/w/g76xe3), [snowy mountain crossing](https://wallhaven.cc/w/jxvl8p), [Roxy, arcane city](https://wallhaven.cc/w/x6vlw3) ([artist](https://www.pixiv.net/artworks/123786185)), [sunlit study](https://wallhaven.cc/w/j3ym5y) ([artist](https://www.pixiv.net/en/artworks/88777467)), and [sleepy cats](https://wallhaven.cc/w/6dzz36). Artwork belongs to its creators and rights holders. Original provenance is recorded in the [portfolio repository](https://github.com/jgil325/jgil325.github.io#credits-and-image-provenance).
- Product previews are the portfolio’s existing compositions from actual project screens. Broadcast previews are the RF Cloud renderer with sample hand and player data, credited to RF Labs. They are not captures of a live broadcast.
- OiStir and Vanilla Chat are team projects. Weekly Slopmeter is adapted from [JeanMeijer/slopmeter](https://github.com/JeanMeijer/slopmeter) (MIT); the portfolio’s usage example is illustrative.
