#!/bin/sh
# Тестирование загрузки различных вариантов VFS.
cd "$(dirname "$0")/.." || exit 1
VFS=examples/vfs

for name in minimal multi deep; do
    echo "=== VFS: $name.xml ==="
    printf 'vfs-info\nexit\n' | ./run.sh --vfs "$VFS/$name.xml"
done

echo "=== Ошибка: файл не найден ==="
./run.sh --vfs "$VFS/no_such.xml"
echo "код возврата: $?"

for name in broken wrong_root bad_base64 duplicate; do
    echo "=== Ошибка: invalid/$name.xml ==="
    ./run.sh --vfs "$VFS/invalid/$name.xml"
    echo "код возврата: $?"
done

echo "=== Стартовый скрипт этапа 3 ==="
./run.sh --vfs "$VFS/deep.xml" --script examples/scripts/stage3.txt
