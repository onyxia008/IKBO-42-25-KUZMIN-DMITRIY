#!/bin/sh
# Запуск: ./run.sh [файл_конфигурации]
cd "$(dirname "$0")" && exec python3 -m src.main "$@"
