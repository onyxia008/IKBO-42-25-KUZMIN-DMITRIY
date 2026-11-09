#!/bin/sh
# Этап 4: обратные зависимости на разных случаях тестового репозитория.
cd "$(dirname "$0")/.." || exit 1
for config in examples/configs/reverse_*.json; do
    echo "--- $config"
    python3 -m src.main "$config"
    echo "код возврата: $?"
done
