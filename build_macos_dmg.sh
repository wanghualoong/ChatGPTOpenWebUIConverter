#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-build.txt

rm -rf build dist

.venv/bin/pyinstaller --noconfirm --windowed --name "ChatGPTOpenWebUIConverter" gui_app.py

APP_PATH="dist/ChatGPTOpenWebUIConverter.app"
DMG_PATH="dist/ChatGPTOpenWebUIConverter.dmg"

hdiutil create -volname "ChatGPTOpenWebUIConverter" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"

echo "[done] DMG created: $DMG_PATH"
