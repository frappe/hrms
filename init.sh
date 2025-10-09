#!/bin/bash
set -euo pipefail

# Delegate to the actual init script kept under docker/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/docker/init.sh" "$@"
