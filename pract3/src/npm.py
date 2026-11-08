"""Получение прямых зависимостей пакета из реестра npm."""

import http.client
import json
import urllib.request

TIMEOUT_SECONDS = 20


class RegistryError(Exception):
    """Ошибка при получении данных из реестра npm."""


def get_direct_dependencies(config):
    """Вернуть прямые зависимости заданной версии пакета.

    :param config: проверенные параметры конфигурации.
    :return: словарь {имя зависимости: требуемая версия}.
    :raises RegistryError: данные получить не удалось.
    """
    if config["test_mode"]:
        raise RegistryError("тестовый репозиторий появится на этапе 3")
    base = config["repository"].rstrip("/")
    url = f"{base}/{config['package']}/{config['version']}"
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
