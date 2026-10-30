# Profile artwork

This profile follows [Jacob Gil’s portfolio](https://jgil325.github.io): Geist type, blue accents, a halftone hillside, light and dark palettes, and the same project descriptions and previews.

## Rebuild

```sh
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/build-assets.py
```

The builder fetches public source assets from `jgil325/jgil325.github.io` into an ignored `.cache/` directory. Generated artwork is checked in, so the profile needs no build service or third-party image endpoint. Rebuild after changing the banner or portfolio source artwork. Text in the SVG is outlined so Geist remains consistent in GitHub’s image context. Accessible image descriptions are provided in `README.md` and in the SVG title and description.

The four hero SVGs cover narrow and wide screens in light and dark mode. CSS opacity animation creates a slow ripple through the dot field. `prefers-reduced-motion: reduce` disables it and leaves a complete static illustration. No JavaScript, external fonts, embedded HTML, or network requests run inside the SVGs.

## Credits

- Geist is by Vercel and basement.studio, licensed under the SIL Open Font License 1.1. The license is included in [`assets/OFL.txt`](assets/OFL.txt).
- The halftone hillside uses the same Mushoku Tensei artwork as the portfolio: [Roxy & Rudeus, hillside](https://wallhaven.cc/w/gpeoyl). Artwork belongs to its creators and rights holders. Original provenance is recorded in the [portfolio repository](https://github.com/jgil325/jgil325.github.io#credits-and-image-provenance).
- Product previews are the portfolio’s existing compositions from actual project screens. Broadcast previews are the RF Cloud renderer with sample hand and player data, credited to RF Labs. They are not captures of a live broadcast.
- OiStir and Vanilla Chat are team projects. Weekly Slopmeter is adapted from [JeanMeijer/slopmeter](https://github.com/JeanMeijer/slopmeter) (MIT); the portfolio’s usage example is illustrative.
