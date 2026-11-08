"""Точка входа: вывод параметров конфигурации."""

import sys

from src.config import ConfigError, load_config

DEFAULT_CONFIG = "config.json"


def main(args):
    """Прочитать конфигурацию и вывести её параметры.

    :param args: аргументы командной строки: [путь к конфигурации].
    :return: код возврата процесса.
    """
    path = args[0] if args else DEFAULT_CONFIG
    try:
        config = load_config(path)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    for key, value in config.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
