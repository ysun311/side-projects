#!/usr/bin/env bash

set -euo pipefail

BUNDLED_PNPM="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/pnpm"

if command -v pnpm >/dev/null 2>&1; then
  PNPM="$(command -v pnpm)"
elif [[ -x "$BUNDLED_PNPM" ]]; then
  PNPM="$BUNDLED_PNPM"
else
  echo "pnpm was not found. Install Node.js and enable pnpm with: corepack enable pnpm" >&2
  exit 1
fi

echo "Building a browser-stable local preview..."
"$PNPM" build
echo "Starting Codex Personalizer..."
exec "$PNPM" exec next start --hostname 0.0.0.0
