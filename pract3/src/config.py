"""Чтение и проверка конфигурации из JSON-файла."""

import json
import os
import re

NPM_NAME = re.compile(r"(@[a-z0-9~-][a-z0-9._~-]*/)?[a-z0-9~-][a-z0-9._~-]*")
TEST_NAME = re.compile(r"[A-Z]+")
VERSION = re.compile(r"\d+\.\d+\.\d+([-+][0-9A-Za-z.+-]+)?")
URL_PREFIXES = ("http://", "https://")
TYPE_NAMES = {str: "строка", bool: "true или false"}


class ConfigError(Exception):
    """Ошибка в файле конфигурации."""


def load_config(path):
    """Прочитать файл конфигурации и проверить параметры.

    :param path: путь к JSON-файлу.
    :return: словарь проверенных параметров.
    :raises ConfigError: файл не прочитан или параметр задан неверно.
    """
    return validate(_read_json(path))


def validate(data):
    """Проверить все параметры конфигурации.

    :param data: содержимое JSON-файла.
    :return: словарь проверенных параметров.
    :raises ConfigError: параметр отсутствует или задан неверно.
    """
    if not isinstance(data, dict):
        raise ConfigError("корень файла должен быть JSON-объектом")
    test_mode = _get(data, "test_mode", bool)
    return {
        "package": _check_package(data, test_mode),
        "repository": _check_repository(data, test_mode),
        "test_mode": test_mode,
        "version": _check_version(data),
        "ascii_tree": _get(data, "ascii_tree", bool),
        "filter": _get(data, "filter", str),
        "reverse": _check_reverse(data, test_mode),
    }


def _read_json(path):
    """Прочитать JSON-документ из файла."""
    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except OSError as error:
        raise ConfigError(f"файл не прочитан: {error}") from error
    except ValueError as error:
        raise ConfigError(f"{path}: неверный JSON: {error}") from error


def _get(data, key, kind):
    """Вернуть значение параметра, проверив наличие и тип."""
    if key not in data:
        raise ConfigError(f"{key}: параметр не задан")
    if not isinstance(data[key], kind):
        raise ConfigError(f"{key}: ожидается {TYPE_NAMES[kind]}")
    return data[key]


def _check_package(data, test_mode):
    """Проверить имя пакета: npm-имя или большие латинские буквы."""
    package = _get(data, "package", str)
    pattern = TEST_NAME if test_mode else NPM_NAME
    if not pattern.fullmatch(package):
        raise ConfigError(f"package: недопустимое имя '{package}'")
    return package


def _check_repository(data, test_mode):
    """Проверить URL реестра или путь к файлу тестового репозитория."""
    repository = _get(data, "repository", str)
    if test_mode and not os.path.isfile(repository):
        raise ConfigError(f"repository: файл '{repository}' не найден")
    if not test_mode and not repository.startswith(URL_PREFIXES):
        raise ConfigError(f"repository: '{repository}' — не http(s) URL")
    return repository


def _check_version(data):
    """Проверить, что задана точная версия вида 1.2.3."""
    version = _get(data, "version", str)
    if not VERSION.fullmatch(version):
        raise ConfigError(f"version: '{version}' — нужен формат 1.2.3")
    return version


def _check_reverse(data, test_mode):
    """Проверить необязательный режим обратных зависимостей.

    Найти всех, кто зависит от пакета, можно только в тестовом
    репозитории: перебрать все пакеты реестра npm нельзя.
    """
    if "reverse" not in data:
        return False
    reverse = _get(data, "reverse", bool)
    if reverse and not test_mode:
        raise ConfigError(
            "reverse: обратные зависимости ищутся только в тестовом "
            "репозитории (test_mode: true)"
        )
    return reverse
