"""Тесты точки входа приложения."""

import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from src.main import main

CONFIG = """{
    "package": "express",
    "repository": "https://registry.npmjs.org",
    "test_mode": false,
    "version": "4.18.2",
    "ascii_tree": true,
    "filter": "test"
}"""

MANIFEST = b"""{
    "name": "express",
    "version": "4.18.2",
    "dependencies": {"accepts": "~1.3.8", "qs": "6.11.0"}
}"""


class MainTest(unittest.TestCase):
    """Поведение приложения при запуске."""

    def setUp(self):
        """Подготовить временный файл и заменить обращение к сети."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, "config.json")
        patcher = mock.patch(
            "urllib.request.urlopen",
            side_effect=lambda *_, **__: io.BytesIO(MANIFEST),
        )
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, text):
        """Записать текст во временный файл конфигурации."""
        with open(self.path, "w", encoding="utf-8") as file:
            file.write(text)

    @staticmethod
    def run_main(args):
        """Запустить приложение и вернуть код возврата и вывод."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_prints_direct_dependencies(self):
        """Выводятся все прямые зависимости заданной версии."""
        self.write(CONFIG)
        code, out, _ = self.run_main([self.path])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "Прямые зависимости express@4.18.2: 2",
            "accepts: ~1.3.8",
            "qs: 6.11.0",
        ])

    def test_registry_failure_reports_error(self):
        """Ошибка реестра даёт код 1 и сообщение в stderr."""
        self.write(CONFIG)
        self.urlopen.side_effect = TimeoutError("timed out")
        code, out, err = self.run_main([self.path])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_invalid_config_reports_error(self):
        """При ошибке код возврата 1, сообщение в stderr, stdout пуст."""
        self.write("{}")
        code, out, err = self.run_main([self.path])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_without_arguments_reads_default_file(self):
        """Без аргументов читается файл конфигурации по умолчанию."""
        self.write(CONFIG)
        with mock.patch("src.main.DEFAULT_CONFIG", self.path):
            code, out, _ = self.run_main([])
        self.assertEqual(code, 0)
        self.assertIn("accepts: ~1.3.8", out)


if __name__ == "__main__":
    unittest.main()
