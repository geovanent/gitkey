# Brand guide

## Colors

| Name | Hex | Usage |
|------|-----|--------|
| Slate 900 | `#0F172A` | Backgrounds |
| Slate 800 | `#1E293B` | Panels |
| Cyan | `#22D3EE` | Commands, accents |
| Indigo | `#6366F1` | Gradients |
| Mint | `#00D4AA` | Success, highlights |
| Slate 400 | `#94A3B8` | Secondary text |

## Assets

| File | Use |
|------|-----|
| `assets/brand/logo.svg` | Icon, favicon base |
| `assets/brand/banner.svg` | README header |
| `assets/demo/demo.gif` | README demo animation |

## Regenerate demo GIF

**Option A — Python (no extra tools beyond Pillow):**

```sh
pip install pillow
python3 scripts/make_demo_gif.py
```

**Option B — VHS (real terminal recording):**

```sh
brew install vhs
vhs demo.tape
```
