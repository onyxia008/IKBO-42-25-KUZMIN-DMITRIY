#!/bin/sh
# Этап 3: граф зависимостей на разных случаях тестового репозитория.
cd "$(dirname "$0")/.." || exit 1
for config in examples/configs/test_*.json; do
    echo "--- $config"
    python3 -m src.main "$config"
    echo "код возврата: $?"
done
