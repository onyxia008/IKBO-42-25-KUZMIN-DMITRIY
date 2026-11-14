"""Тесты точки входа приложения."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from src.main import main
from src.visual import VisualError

REAL = {
    "package": "express",
    "repository": "https://registry.npmjs.org",
    "test_mode": False,
    "version": "4.18.2",
    "ascii_tree": False,
    "filter": "",
}

DEPENDENCIES = {
    "https://registry.npmjs.org/express/4.18.2": {
        "accepts": "~1.3.8",
        "qs": "6.11.0",
    },
    "https://registry.npmjs.org/accepts/1.3.8": {"negotiator": "0.6.3"},
    "https://registry.npmjs.org/qs/6.11.0": {},
    "https://registry.npmjs.org/negotiator/0.6.3": {},
}

DIAMOND = "A: B C\nB: D\nC: D\nD:\n"


def fake_urlopen(url, **_):
    """Ответить как реестр npm: манифест версии пакета по URL."""
    base, version = url.rsplit("/", 1)
    manifest = {
        "name": base.rsplit("/", 1)[1],
        "version": version,
        "dependencies": DEPENDENCIES[url],
    }
    return io.BytesIO(json.dumps(manifest).encode("utf-8"))


class MainTest(unittest.TestCase):
    """Поведение приложения при запуске."""

    def run(self, result=None):
        """Перед каждой проверкой выполнить prepare (аналог setUp)."""
        self.prepare()
        return super().run(result)

    def prepare(self):
        """Подготовить папку, заменить сеть и рисование картинки."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name
        patcher = mock.patch("urllib.request.urlopen", side_effect=fake_urlopen)
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "src.main.show_image",
            side_effect=lambda text, name: f"graph-{name}.svg",
        )
        self.show_image = patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, name, text):
        """Записать текст во временный файл и вернуть путь к нему."""
        path = os.path.join(self.folder, name)
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def config(self, **changes):
        """Записать конфигурацию с изменёнными параметрами."""
        return self.write("config.json", json.dumps({**REAL, **changes}))

    def graph_config(self, graph, package="A", **changes):
        """Записать граф тестового репозитория и конфигурацию к нему."""
        return self.config(
            test_mode=True,
            package=package,
            repository=self.write("graph.txt", graph),
            **changes,
        )

    @staticmethod
    def run_main(args):
        """Запустить приложение и вернуть код возврата и вывод."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_prints_graph_from_registry(self):
        """Граф строится по реестру с учётом транзитивных зависимостей."""
        code, out, _ = self.run_main([self.config()])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "Граф зависимостей express@4.18.2 (пакетов: 4)",
            '"express"',
            '"express" -> "accepts"',
            '"express" -> "qs"',
            '"accepts" -> "negotiator"',
            "Картинка графа: graph-express.svg",
        ])

    def test_test_mode_reads_graph_file_without_network(self):
        """В тестовом режиме граф берётся из файла, сеть не нужна."""
        path = self.graph_config("A: B C\nB: C\nC: A\n")
        code, out, _ = self.run_main([path])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "Граф зависимостей A (пакетов: 3)",
            '"A"',
            '"A" -> "B"',
            '"A" -> "C"',
            '"B" -> "C"',
            '"C" -> "A"',
            "Картинка графа: graph-A.svg",
        ])
        self.urlopen.assert_not_called()

    def test_filter_from_config_removes_packages(self):
        """Подстрока filter из конфигурации убирает пакеты из графа."""
        path = self.graph_config("A: B C\nB: C\n", filter="B")
        _, out, _ = self.run_main([path])
        self.assertEqual(out.splitlines(), [
            "Граф зависимостей A (пакетов: 2)",
            '"A"',
            '"A" -> "C"',
            "Картинка графа: graph-A.svg",
        ])

    def test_ascii_tree_is_printed_when_enabled(self):
        """При ascii_tree: true после описания D2 выводится дерево."""
        path = self.graph_config("A: B C\nB: D\n", ascii_tree=True)
        _, out, _ = self.run_main([path])
        self.assertEqual(out.splitlines()[-5:], [
            "A",
            "├── B",
            "│   └── D",
            "└── C",
            "Картинка графа: graph-A.svg",
        ])

    def test_image_is_drawn_from_d2_description(self):
        """Картинка рисуется по тому же описанию D2, что выведено."""
        self.run_main([self.graph_config("A: B\n")])
        self.show_image.assert_called_once_with('"A"\n"A" -> "B"\n', "A")

    def test_missing_d2_is_reported(self):
        """Без программы d2 описание выведено, но код возврата 1."""
        self.show_image.side_effect = VisualError("программа d2 не найдена")
        code, out, err = self.run_main([self.graph_config("A: B\n")])
        self.assertEqual(code, 1)
        self.assertIn('"A" -> "B"', out)
        self.assertIn("d2 не найдена", err)

    def test_unknown_test_package_is_error(self):
        """Пакета нет в тестовом репозитории — код 1 и сообщение."""
        code, out, err = self.run_main([self.graph_config("A: B\n", "Z")])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("'Z'", err)

    def test_registry_failure_reports_error(self):
        """Ошибка реестра даёт код 1 и сообщение в stderr."""
        self.urlopen.side_effect = TimeoutError("timed out")
        code, out, err = self.run_main([self.config()])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_invalid_config_reports_error(self):
        """При ошибке код возврата 1, сообщение в stderr, stdout пуст."""
        code, out, err = self.run_main([self.write("config.json", "{}")])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_without_arguments_reads_default_file(self):
        """Без аргументов читается файл конфигурации по умолчанию."""
        with mock.patch("src.main.DEFAULT_CONFIG", self.config()):
            code, out, _ = self.run_main([])
        self.assertEqual(code, 0)
        self.assertIn('"express" -> "accepts"', out)

    def test_reverse_mode_lists_dependents(self):
        """reverse: пакеты, которые зависят от заданного пакета."""
        code, out, _ = self.run_main([
            self.graph_config(DIAMOND, "D", reverse=True)
        ])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "Обратные зависимости D (пакетов: 3)",
            "D <- B, C",
            "B <- A",
            "C <- A",
            "A <- (никто не зависит)",
        ])

    def test_reverse_mode_stops_on_cycle(self):
        """Цикл виден в выводе, но не зацикливает обход."""
        path = self.graph_config("A: B\nB: C\nC: A\n", reverse=True)
        _, out, _ = self.run_main([path])
        self.assertEqual(out.splitlines(), [
            "Обратные зависимости A (пакетов: 2)",
            "A <- C",
            "C <- B",
            "B <- A",
        ])

    def test_reverse_of_package_nobody_needs(self):
        """От пакета на вершине графа никто не зависит."""
        _, out, _ = self.run_main([
            self.graph_config(DIAMOND, "A", reverse=True)
        ])
        self.assertEqual(out.splitlines(), [
            "Обратные зависимости A (пакетов: 0)",
            "A <- (никто не зависит)",
        ])

    def test_reverse_mode_applies_filter(self):
        """Фильтр убирает пакеты и из обратных зависимостей."""
        _, out, _ = self.run_main([
            self.graph_config(DIAMOND, "D", reverse=True, filter="B")
        ])
        self.assertEqual(out.splitlines(), [
            "Обратные зависимости D (пакетов: 2)",
            "D <- C",
            "C <- A",
            "A <- (никто не зависит)",
        ])

    def test_reverse_of_package_only_mentioned_as_dependency(self):
        """Пакет без своей строки, но нужный другим, тоже ищется."""
        _, out, _ = self.run_main([
            self.graph_config("A: B\n", "B", reverse=True)
        ])
        self.assertEqual(out.splitlines(), [
            "Обратные зависимости B (пакетов: 1)",
            "B <- A",
            "A <- (никто не зависит)",
        ])

    def test_reverse_unknown_package_is_error(self):
        """Пакета нет в тестовом репозитории — код 1 и сообщение."""
        code, out, err = self.run_main([
            self.graph_config(DIAMOND, "Z", reverse=True)
        ])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("'Z'", err)


if __name__ == "__main__":
    unittest.main()
