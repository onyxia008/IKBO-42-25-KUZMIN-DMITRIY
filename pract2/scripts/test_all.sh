#!/bin/sh
# Запуск всех проверочных скриптов и модульных тестов.
cd "$(dirname "$0")/.." || exit 1
for script in test_params test_errors test_vfs test_commands test_extra; do
    echo "########## scripts/$script.sh ##########"
    sh "scripts/$script.sh"
done
echo "########## unittest ##########"
PYTHONPATH=src python3 -m unittest discover -s tests
