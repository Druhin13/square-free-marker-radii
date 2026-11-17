#!/usr/bin/env bash
# Build upstream MIT-licensed DRAT-trim at one immutable source revision.
# Never modifies source proof certificates or the internal research branch.
set -euo pipefail

REV="effa1dcce85c878236f8313133dff1a2b766cd7c"
URL="https://github.com/marijnheule/drat-trim.git"
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
DEST="$ROOT/.build/drat-trim"

if [[ -e "$DEST" || -L "$DEST" ]]; then
  echo "Refusing to overwrite existing checker directory: $DEST" >&2
  exit 1
fi
command -v git >/dev/null || { echo "git required" >&2; exit 1; }
command -v cc >/dev/null || { echo "C compiler required" >&2; exit 1; }

mkdir -p -- "$DEST"
git clone --quiet --no-checkout "$URL" "$DEST/source"
git -C "$DEST/source" checkout --quiet --detach "$REV"

ACTUAL="$(git -C "$DEST/source" rev-parse HEAD)"
if [[ "$ACTUAL" != "$REV" ]]; then
  echo "Upstream revision mismatch: $ACTUAL" >&2
  exit 1
fi

if [[ ! -f "$DEST/source/LICENSE" || ! -f "$DEST/source/drat-trim.c" ]]; then
  echo "Upstream license or C source missing" >&2
  exit 1
fi

cc -O2 -o "$DEST/drat-trim" "$DEST/source/drat-trim.c"
if [[ ! -x "$DEST/drat-trim" ]]; then
  echo "Compiled checker is not executable" >&2
  exit 1
fi

echo "SOURCE-PINNED DRAT CHECKER BUILT"
echo "Upstream: $URL"
echo "Commit: $REV"
echo "License: upstream LICENSE (MIT)"
echo "Binary: $DEST/drat-trim"
echo "NOTE: external source checkout and binary are local build files only."
