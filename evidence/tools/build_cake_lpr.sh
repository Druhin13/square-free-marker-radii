#!/usr/bin/env bash
# Source-pinned CakeML formally verified LRAT checker. Build outputs only.
set -euo pipefail
REV="033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2"
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
DEST="$ROOT/.build/cake_lpr"
if [[ -e "$DEST" || -L "$DEST" ]]; then
  echo "Refusing to overwrite CakeML checker build: $DEST" >&2
  exit 1
fi
command -v git >/dev/null && command -v gcc >/dev/null
mkdir -p -- "$DEST"
git clone --quiet --no-checkout \
  "https://github.com/tanyongkiam/cake_lpr.git" "$DEST/source"
git -C "$DEST/source" checkout --quiet --detach "$REV"
[[ "$(git -C "$DEST/source" rev-parse HEAD)" == "$REV" ]] || {
  echo "Wrong source-pinned CakeML checker revision" >&2; exit 1;
}
for file in LICENSE Makefile basis_ffi.c cake_lpr.S; do
  [[ -f "$DEST/source/$file" ]] || { echo "Missing upstream: $file" >&2; exit 1; }
done
# C11 is essential: upstream basis_ffi.c uses aligned_alloc().
# C99 yields an implicit-int declaration, truncates the pointer and crashes.
gcc -O2 -std=c11 -Werror=implicit-function-declaration -Werror=int-conversion "$DEST/source/basis_ffi.c" \
  "$DEST/source/cake_lpr.S" -o "$DEST/cake_lpr"
test -x "$DEST/cake_lpr"
echo "SOURCE-PINNED CAKEML VERIFIED LRAT CHECKER BUILT"
echo "Upstream CakeML checker revision: $REV"
echo "Upstream license: BSD-3-Clause"
echo "No source proof artifact modified"
