"""Тесты получения прямых зависимостей из реестра npm."""

import http.client
import io
import json
import unittest
import urllib.error
from unittest import mock

from src.npm import RegistryError, get_direct_dependencies

CONFIG = {
    "package": "express",
    "repository": "https://registry.npmjs.org",
    "test_mode": False,
    "version": "4.18.2",
    "ascii_tree": False,
    "filter": "",
}

MANIFEST = {
    "name": "express",
    "version": "4.18.2",
    "dependencies": {"accepts": "~1.3.8", "qs": "6.11.0"},
    "devDependencies": {"mocha": "^10.0.0"},
}

FAILURES = [
    urllib.error.HTTPError("url", 404, "Not Found", {}, None),
    urllib.error.URLError("нет сети"),
    TimeoutError("timed out"),
    http.client.InvalidURL("неверный адрес"),
]


def response(document):
    """Сформировать ответ реестра с JSON-документом."""
    return io.BytesIO(json.dumps(document).encode("utf-8"))


class DirectDependenciesTest(unittest.TestCase):
    """Запрос к реестру и разбор ответа."""

    def setUp(self):
        """Заменить обращение к сети."""
        patcher = mock.patch("urllib.request.urlopen")
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)

    def test_returns_only_runtime_dependencies(self):
        """Возвращается поле dependencies, без devDependencies."""
        self.urlopen.return_value = response(MANIFEST)
        self.assertEqual(
            get_direct_dependencies(CONFIG),
            {"accepts": "~1.3.8", "qs": "6.11.0"},
        )

    def test_requests_given_version_from_given_repository(self):
        """URL строится из адреса реестра, имени и версии."""
        self.urlopen.return_value = response(MANIFEST)
        config = {**CONFIG, "repository": "https://mirror.example/npm/"}
        get_direct_dependencies(config)
        self.assertEqual(
            self.urlopen.call_args.args[0],
            "https://mirror.example/npm/express/4.18.2",
        )

    def test_requests_scoped_package(self):
        """Имя со scope подставляется в URL как есть."""
        self.urlopen.return_value = response(MANIFEST)
        config = {**CONFIG, "package": "@babel/core", "version": "7.22.0"}
        get_direct_dependencies(config)
        self.assertEqual(
            self.urlopen.call_args.args[0],
            "https://registry.npmjs.org/@babel/core/7.22.0",
        )

    def test_package_without_dependencies(self):
        """Пакет без поля dependencies не имеет зависимостей."""
        self.urlopen.return_value = response({"name": "lodash"})
        self.assertEqual(get_direct_dependencies(CONFIG), {})

    def test_request_failures_become_registry_error(self):
        """Ошибки сети и HTTP превращаются в RegistryError."""
        for failure in FAILURES:
            with self.subTest(failure=failure):
                self.urlopen.side_effect = failure
                with self.assertRaises(RegistryError):
                    get_direct_dependencies(CONFIG)

    def test_invalid_json_is_registry_error(self):
        """Ответ не в формате JSON — ошибка реестра."""
        self.urlopen.return_value = io.BytesIO(b"<html></html>")
        with self.assertRaises(RegistryError):
            get_direct_dependencies(CONFIG)

    def test_response_must_be_object(self):
        """Ответ, не являющийся объектом, — ошибка реестра."""
        self.urlopen.return_value = response(["express"])
        with self.assertRaises(RegistryError):
            get_direct_dependencies(CONFIG)

    def test_test_mode_does_not_use_network(self):
        """Режим тестового репозитория пока даёт ошибку без запроса."""
        with self.assertRaises(RegistryError):
            get_direct_dependencies({**CONFIG, "test_mode": True})
        self.urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
