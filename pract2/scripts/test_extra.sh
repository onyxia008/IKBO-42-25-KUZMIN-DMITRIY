#!/bin/sh
# Тестирование дополнительных команд (этап 5) и проверка, что
# файл VFS на диске не изменяется.
cd "$(dirname "$0")/.." || exit 1
VFS=examples/vfs/deep.xml
BEFORE=$(cksum < "$VFS")
./run.sh --vfs "$VFS" --script examples/scripts/stage5.txt
AFTER=$(cksum < "$VFS")
if [ "$BEFORE" = "$AFTER" ]; then
    echo "OK: файл $VFS не изменён"
else
    echo "ОШИБКА: файл $VFS изменён"
    exit 1
fi
