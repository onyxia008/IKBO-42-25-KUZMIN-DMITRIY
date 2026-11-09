"""Получение зависимостей пакетов из реестра npm."""

import http.client
import json
import re
import urllib.request

TIMEOUT_SECONDS = 20
EXACT_VERSION = re.compile(r"\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?")


class RegistryError(Exception):
    """Ошибка при получении данных из реестра npm."""


def pick_version(requirement):
    """Выбрать версию для запроса к реестру.

    Реестр отдаёт пакет только по точной версии или метке latest, а у
    зависимостей записаны требования вида ~1.3.8. Поэтому берётся
    точная версия, записанная в требовании, а если её нет (например,
    «*»), — последняя версия.

    :param requirement: требование к версии из поля dependencies.
    :return: точная версия или "latest".
    """
    match = EXACT_VERSION.search(requirement)
    return match.group() if match else "latest"


def fetch_dependencies(repository, name, version):
    """Вернуть прямые зависимости пакета нужной версии.

    :param repository: URL реестра npm.
    :param name: имя пакета.
    :param version: точная версия или требование к версии.
    :return: словарь {имя зависимости: требование к версии}.
    :raises RegistryError: данные получить не удалось.
    """
    base = repository.rstrip("/")
    url = f"{base}/{name}/{pick_version(version)}"
    manifest = _fetch_json(url)
    if not isinstance(manifest, dict):
        raise RegistryError(f"{url}: ответ не описывает пакет")
    return manifest.get("dependencies", {})


def _fetch_json(url):
    """Загрузить и разобрать JSON-документ по URL."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except (OSError, http.client.HTTPException, ValueError) as error:
        raise RegistryError(f"{url}: {error}") from error
