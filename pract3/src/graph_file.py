"""Тестовый репозиторий: файл описания графа пакетов.

Каждая строка описывает пакет и его прямые зависимости: «A: B C».
Имена пакетов — большие латинские буквы. Пустые строки и строки,
начинающиеся с #, пропускаются.
"""

import re

NAME = re.compile(r"[A-Z]+")


class GraphFileError(Exception):
    """Ошибка в тестовом репозитории."""


def load_graph_file(path):
    """Прочитать файл тестового репозитория.

    :param path: путь к файлу описания графа.
    :return: словарь {пакет: [его зависимости]}.
    :raises GraphFileError: файл не прочитан или записан неверно.
    """
    try:
        with open(path, encoding="utf-8") as file:
            lines = file.read().splitlines()
    except OSError as error:
        raise GraphFileError(f"файл не прочитан: {error}") from error
    graph = {}
    for number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, dependencies = _parse_line(line, number)
        if name in graph:
            raise GraphFileError(
                f"строка {number}: пакет '{name}' уже описан"
            )
        graph[name] = dependencies
    return graph


def _parse_line(line, number):
    """Разобрать строку «A: B C» в имя пакета и список зависимостей."""
    name, colon, rest = line.partition(":")
    if not colon:
        raise GraphFileError(
            f"строка {number}: нужен формат «ПАКЕТ: ЗАВИСИМОСТИ»"
        )
    names = [name.strip()] + rest.split()
    for item in names:
        if not NAME.fullmatch(item):
            raise GraphFileError(
                f"строка {number}: имя '{item}' — нужны большие "
                "латинские буквы"
            )
    return names[0], names[1:]
