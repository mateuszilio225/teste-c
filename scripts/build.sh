#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p dist/vendor
cp index.html styles.css app.js icon.svg dist/
cp vendor/peerjs.min.js vendor/LICENSE-peerjs.txt dist/vendor/
node --check dist/app.js
