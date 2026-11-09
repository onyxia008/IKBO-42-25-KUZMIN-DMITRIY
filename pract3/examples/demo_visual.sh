#!/bin/sh
# Этап 5: визуализация зависимостей трёх пакетов из реестра npm.
# Каждая картинка открывается на экране; Enter — следующий пакет.
cd "$(dirname "$0")/.." || exit 1
for config in examples/configs/npm_*.json; do
    echo "--- $config"
    python3 -m src.main "$config"
    echo "код возврата: $?"
    printf "Enter — дальше: "
    read -r _
done
