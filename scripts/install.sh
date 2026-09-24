#!/usr/bin/env bash
# Interactive compatibility entry point. The copy-only installer lives in the versioned skill payload.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT_DIR/ultimate-dev/scripts/install.sh" "$@"
