#!/usr/bin/env bash
# Compatibility entry point. The hardened installer lives in the versioned skill payload.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT_DIR/ultimate-dev/scripts/install.sh" "$@"
