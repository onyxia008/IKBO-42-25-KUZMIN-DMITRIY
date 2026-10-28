#!/bin/sh
# Тестирование основных команд (этап 4) на глубокой VFS.
cd "$(dirname "$0")/.." || exit 1
./run.sh --vfs examples/vfs/deep.xml --script examples/scripts/stage4.txt
