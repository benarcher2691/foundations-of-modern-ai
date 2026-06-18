#!/usr/bin/env bash
# Build script for the "Foundations of Modern AI" study series.
# Converts every .md file in this directory to a standalone, self-contained .html
# (CSS embedded, no external dependencies — each .html opens correctly on its own).
#
# Usage:
#   ./build.sh            # rebuild all .md files
#   ./build.sh FILE.md    # rebuild just one file
set -euo pipefail

cd "$(dirname "$0")"

build_one() {
  local md="$1"
  local html="${md%.md}.html"
  pandoc "$md" \
    --from gfm \
    --to html5 \
    --standalone \
    --embed-resources \
    --css=style.css \
    --metadata title="${md%.md}" \
    --output "$html"
  echo "  ✓ $md → $html"
}

if [ "$#" -ge 1 ]; then
  build_one "$1"
else
  echo "Building all .md files…"
  for md in *.md; do
    [ -e "$md" ] || continue
    build_one "$md"
  done
fi
echo "Done."
