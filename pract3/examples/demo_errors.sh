#!/bin/sh
# Показывает обработку ошибок: запускает приложение с неверными
# конфигурациями. Файла no_such_file.json специально не существует.
cd "$(dirname "$0")/.." || exit 1
for config in examples/errors/*.json examples/errors/no_such_file.json; do
    echo "--- $config"
    python3 -m src.main "$config"
    echo "код возврата: $?"
done
