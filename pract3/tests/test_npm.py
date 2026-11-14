"""Тесты получения зависимостей пакета из реестра npm."""

import http.client
import io
import json
import unittest
import urllib.error
from unittest import mock

from src.npm import RegistryError, fetch_dependencies, pick_version

REGISTRY = "https://registry.npmjs.org"

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


class PickVersionTest(unittest.TestCase):
    """Выбор версии для запроса к реестру."""

    def test_takes_exact_version_written_in_requirement(self):
        """Из требования берётся записанная в нём точная версия."""
        cases = {
            "4.18.2": "4.18.2",
            "~1.3.8": "1.3.8",
            "^2.6.9": "2.6.9",
            ">= 2.1.2 < 3": "2.1.2",
            "1.0.0-beta.1": "1.0.0-beta.1",
        }
        for requirement, version in cases.items():
            with self.subTest(requirement=requirement):
                self.assertEqual(pick_version(requirement), version)

    def test_requirement_without_exact_version_means_latest(self):
        """Без точной версии в требовании запрашивается последняя."""
        for requirement in ("*", "", "1.x", "latest"):
            with self.subTest(requirement=requirement):
                self.assertEqual(pick_version(requirement), "latest")


class FetchDependenciesTest(unittest.TestCase):
    """Запрос к реестру и разбор ответа."""

    def run(self, result=None):
        """Перед каждой проверкой выполнить prepare (аналог setUp)."""
        self.prepare()
        return super().run(result)

    def prepare(self):
        """Заменить обращение к сети."""
        patcher = mock.patch("urllib.request.urlopen")
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)
        self.urlopen.return_value = response(MANIFEST)

    def requested_url(self):
        """Вернуть URL, который был запрошен у реестра."""
        return self.urlopen.call_args.args[0]

    def test_returns_only_runtime_dependencies(self):
        """Возвращается поле dependencies, без devDependencies."""
        self.assertEqual(
            fetch_dependencies(REGISTRY, "express", "4.18.2"),
            {"accepts": "~1.3.8", "qs": "6.11.0"},
        )

    def test_requests_given_version_from_given_repository(self):
        """URL строится из адреса реестра, имени и версии."""
        fetch_dependencies("https://mirror.example/npm/", "express", "4.18.2")
        self.assertEqual(
            self.requested_url(), "https://mirror.example/npm/express/4.18.2"
        )

    def test_requirement_is_turned_into_exact_version(self):
        """Требование ~1.3.8 превращается в запрос версии 1.3.8."""
        fetch_dependencies(REGISTRY, "accepts", "~1.3.8")
        self.assertEqual(
            self.requested_url(), "https://registry.npmjs.org/accepts/1.3.8"
        )

    def test_requests_scoped_package(self):
        """Имя со scope подставляется в URL как есть."""
        fetch_dependencies(REGISTRY, "@babel/core", "7.22.0")
        self.assertEqual(
            self.requested_url(),
            "https://registry.npmjs.org/@babel/core/7.22.0",
        )

    def test_package_without_dependencies(self):
        """Пакет без поля dependencies не имеет зависимостей."""
        self.urlopen.return_value = response({"name": "lodash"})
        self.assertEqual(fetch_dependencies(REGISTRY, "lodash", "4.17.21"), {})

    def test_request_failures_become_registry_error(self):
        """Ошибки сети и HTTP превращаются в RegistryError."""
        for failure in FAILURES:
            with self.subTest(failure=failure):
                self.urlopen.side_effect = failure
                with self.assertRaises(RegistryError):
                    fetch_dependencies(REGISTRY, "express", "4.18.2")

    def test_invalid_json_is_registry_error(self):
        """Ответ не в формате JSON — ошибка реестра."""
        self.urlopen.return_value = io.BytesIO(b"<html></html>")
        with self.assertRaises(RegistryError):
            fetch_dependencies(REGISTRY, "express", "4.18.2")

    def test_response_must_be_object(self):
        """Ответ, не являющийся объектом, — ошибка реестра."""
        self.urlopen.return_value = response("version not found: ~1.3.8")
        with self.assertRaises(RegistryError):
            fetch_dependencies(REGISTRY, "express", "4.18.2")


if __name__ == "__main__":
    unittest.main()
