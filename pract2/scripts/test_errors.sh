#!/bin/sh
# Тестирование ошибок при разборе параметров и исполнении скрипта.
cd "$(dirname "$0")/.." || exit 1

echo "=== 1. Стартовый скрипт не существует ==="
./run.sh --vfs examples/vfs/deep.xml --script no_such_script.txt
echo "код возврата: $?"

echo "=== 2. Скрипт с ошибочными строками (они пропускаются) ==="
./run.sh --vfs examples/vfs/deep.xml \
    --script examples/scripts/stage2.txt </dev/null
echo "код возврата: $?"

echo "=== 3. Неизвестный параметр ==="
./run.sh --unknown
echo "код возврата: $?"

echo "=== 4. Параметр без значения ==="
./run.sh --vfs examples/vfs/deep.xml --script
echo "код возврата: $?"
