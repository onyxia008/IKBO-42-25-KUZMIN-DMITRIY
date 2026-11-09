"""Точка входа: граф зависимостей npm-пакета."""

import functools
import sys

from src.config import ConfigError, load_config
from src.graph import build_graph, invert
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
        repository = load_graph_file(config["repository"])
        fetch = _dict_fetch(repository, config["package"])
    else:
        fetch = functools.partial(fetch_dependencies, config["repository"])
    return build_graph(
        config["package"], config["version"], fetch, config["filter"]
    )


def load_reverse_graph(config):
    """Найти пакеты, которые зависят от заданного (обратные зависимости).

    Граф тестового репозитория переворачивается, и по нему тем же
    обходом в ширину ищутся все пакеты, которые зависят от заданного
    напрямую или через другие пакеты.

    :param config: проверенные параметры конфигурации.
    :return: словарь {пакет: [пакеты, которые от него зависят]}.
    :raises GraphFileError: ошибка в тестовом репозитории.
    """
    reverse = invert(load_graph_file(config["repository"]))
    fetch = _dict_fetch(reverse, config["package"])
    return build_graph(
        config["package"], config["version"], fetch, config["filter"]
    )


def _dict_fetch(repository, package):
    """Вернуть функцию получения зависимостей из словаря-репозитория.

    :raises GraphFileError: анализируемого пакета нет в репозитории.
    """
    if package not in repository:
        raise GraphFileError(
            f"пакет '{package}' не найден в тестовом репозитории"
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


def print_reverse(config, graph):
    """Вывести обратные зависимости: кто от кого зависит."""
    count = len(graph) - 1
    print(f"Обратные зависимости {config['package']} (пакетов: {count})")
    for name, dependents in graph.items():
        print(f"{name} <- {', '.join(dependents) or '(никто не зависит)'}")


def main(args):
    """Вывести граф зависимостей или обратные зависимости пакета.

    :param args: аргументы командной строки: [путь к конфигурации].
    :return: код возврата процесса.
    """
    path = args[0] if args else DEFAULT_CONFIG
    try:
        config = load_config(path)
        if config["reverse"]:
            print_reverse(config, load_reverse_graph(config))
        else:
            print_graph(config, load_graph(config))
    except ERRORS as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
