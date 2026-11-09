"""Точка входа: граф зависимостей npm-пакета."""

import functools
import sys

from src.config import ConfigError, load_config
from src.graph import build_graph
from src.graph_file import GraphFileError, load_graph_file
from src.npm import RegistryError, fetch_dependencies

DEFAULT_CONFIG = "config.json"
ERRORS = (ConfigError, GraphFileError, RegistryError)


def load_graph(config):
    """Построить граф зависимостей пакета из конфигурации.

    :param config: проверенные параметры конфигурации.
    :return: словарь {пакет: [его зависимости]}.
    :raises GraphFileError: ошибка в тестовом репозитории.
    :raises RegistryError: ошибка при обращении к реестру npm.
    """
    if config["test_mode"]:
        fetch = _test_fetch(config)
    else:
        fetch = functools.partial(fetch_dependencies, config["repository"])
    return build_graph(
        config["package"], config["version"], fetch, config["filter"]
    )


def _test_fetch(config):
    """Вернуть функцию получения зависимостей из тестового репозитория."""
    repository = load_graph_file(config["repository"])
    if config["package"] not in repository:
        raise GraphFileError(
            f"пакет '{config['package']}' не найден в тестовом репозитории"
        )

    def fetch(name, _version):
        """Вернуть зависимости пакета: версий в тестовом режиме нет."""
        return dict.fromkeys(repository.get(name, []), "")

    return fetch


def print_graph(config, graph):
    """Вывести граф: заголовок и зависимости каждого пакета."""
    title = config["package"]
    if not config["test_mode"]:
        title += f"@{config['version']}"
    print(f"Граф зависимостей {title} (пакетов: {len(graph)})")
    for name, dependencies in graph.items():
        print(f"{name} -> {', '.join(dependencies) or '(нет зависимостей)'}")


def main(args):
    """Вывести граф зависимостей пакета из конфигурации.

    :param args: аргументы командной строки: [путь к конфигурации].
    :return: код возврата процесса.
    """
    path = args[0] if args else DEFAULT_CONFIG
    try:
        config = load_config(path)
        graph = load_graph(config)
    except ERRORS as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    print_graph(config, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
