"""Точка входа: вывод прямых зависимостей npm-пакета."""

import sys

from src.config import ConfigError, load_config
from src.npm import RegistryError, get_direct_dependencies

DEFAULT_CONFIG = "config.json"


def main(args):
    """Вывести прямые зависимости пакета из конфигурации.

    :param args: аргументы командной строки: [путь к конфигурации].
    :return: код возврата процесса.
    """
    path = args[0] if args else DEFAULT_CONFIG
    try:
        config = load_config(path)
        dependencies = get_direct_dependencies(config)
    except (ConfigError, RegistryError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    print(
        f"Прямые зависимости {config['package']}@{config['version']}: "
        f"{len(dependencies)}"
    )
    for name, version in dependencies.items():
        print(f"{name}: {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
