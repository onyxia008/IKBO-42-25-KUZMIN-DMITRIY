#!/bin/sh
# Тестирование всех параметров командной строки эмулятора.
cd "$(dirname "$0")/.." || exit 1

echo "=== 1. Без параметров (интерактивный режим, ввод из канала) ==="
printf 'ls\nexit\n' | ./run.sh

echo "=== 2. Только --vfs ==="
printf 'exit\n' | ./run.sh --vfs examples/vfs/deep.xml

echo "=== 3. Только --script ==="
./run.sh --script examples/scripts/stage2.txt </dev/null

echo "=== 4. --vfs и --script ==="
./run.sh --vfs examples/vfs/deep.xml \
    --script examples/scripts/stage2.txt </dev/null

echo "=== 5. Справка --help ==="
./run.sh --help
