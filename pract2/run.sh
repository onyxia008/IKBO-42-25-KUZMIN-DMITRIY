#!/bin/sh
# Запуск эмулятора: ./run.sh [--vfs FILE.xml] [--script FILE]
ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$ROOT/src" exec python3 -m emulator "$@"
