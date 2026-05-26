#!/usr/bin/env bash
# Regenerate assets/demo/demo.gif
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v vhs &>/dev/null; then
  vhs demo.tape
  mv -f assets/demo/demo-vhs.gif assets/demo/demo.gif 2>/dev/null || true
  echo "✓ Generated with VHS"
else
  python3 -m pip install -q pillow 2>/dev/null || pip3 install -q pillow
  python3 scripts/make_demo_gif.py
fi
