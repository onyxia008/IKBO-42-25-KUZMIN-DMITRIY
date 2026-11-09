"""Тесты визуализации: язык D2, ASCII-дерево и картинка графа."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.visual import VisualError, ascii_tree, show_image, to_d2

DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}


class ToD2Test(unittest.TestCase):
    """Текстовое описание графа на языке D2."""

    def test_each_dependency_is_an_arrow(self):
        """Корень — отдельная фигура, каждая зависимость — стрелка."""
        self.assertEqual(
            to_d2({"A": ["B", "C"], "B": ["C"], "C": []}, "A"),
            '"A"\n"A" -> "B"\n"A" -> "C"\n"B" -> "C"\n',
        )

    def test_package_without_dependencies_is_drawn(self):
        """Пакет без зависимостей всё равно есть на картинке."""
        self.assertEqual(to_d2({"A": []}, "A"), '"A"\n')

    def test_scoped_names_are_quoted(self):
        """Символы @ и / в имени не ломают описание D2."""
        self.assertEqual(
            to_d2({"@babel/core": ["debug"], "debug": []}, "@babel/core"),
            '"@babel/core"\n"@babel/core" -> "debug"\n',
        )


class AsciiTreeTest(unittest.TestCase):
    """Вывод зависимостей в виде ASCII-дерева."""

    def test_draws_branches(self):
        """Ветки рисуются символами ├──, └── и │."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}
        self.assertEqual(
            ascii_tree(graph, "A"), ["A", "├── B", "│   └── D", "└── C"]
        )

    def test_repeated_package_is_not_expanded_again(self):
        """Пакет, уже показанный выше, помечается (*)."""
        self.assertEqual(ascii_tree(DIAMOND, "A"), [
            "A",
            "├── B",
            "│   └── D",
            "└── C",
            "    └── D (*)",
        ])

    def test_cycle_does_not_loop(self):
        """Цикл A -> B -> A даёт конечное дерево."""
        self.assertEqual(
            ascii_tree({"A": ["B"], "B": ["A"]}, "A"),
            ["A", "└── B", "    └── A (*)"],
        )


class ShowImageTest(unittest.TestCase):
    """Картинка: файл D2, запуск программы d2, открытие SVG."""

    def setUp(self):
        """Работать во временной папке и не открывать окна."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(folder.name)
        patcher = mock.patch("webbrowser.open")
        self.open = patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch("subprocess.run")
    @mock.patch("shutil.which", return_value="/usr/local/bin/d2")
    def test_draws_svg_with_d2_and_opens_it(self, _which, run):
        """Описание сохраняется, d2 рисует SVG, картинка открывается."""
        image = show_image('"A" -> "B"\n', "A")
        self.assertEqual(image, "graph-A.svg")
        self.assertEqual(Path("graph-A.d2").read_text(), '"A" -> "B"\n')
        self.assertEqual(
            run.call_args.args[0], ["d2", "graph-A.d2", "graph-A.svg"]
        )
        image_uri = Path("graph-A.svg").resolve().as_uri()
        self.open.assert_called_once_with(image_uri)

    @mock.patch("subprocess.run")
    @mock.patch("shutil.which", return_value="/usr/local/bin/d2")
    def test_scoped_name_gives_valid_file_name(self, _which, _run):
        """Косая черта в имени пакета не попадает в имя файла."""
        self.assertEqual(show_image('"x"\n', "@babel/core"),
                         "graph-@babel_core.svg")

    @mock.patch("shutil.which", return_value=None)
    def test_missing_d2_is_error(self, _which):
        """Без программы d2 — понятная ошибка, окно не открывается."""
        with self.assertRaisesRegex(VisualError, "d2"):
            show_image('"A"\n', "A")
        self.open.assert_not_called()

    @mock.patch("shutil.which", return_value="/usr/local/bin/d2")
    def test_d2_failure_is_error(self, _which):
        """Если d2 не смог нарисовать картинку — ошибка с причиной."""
        failure = subprocess.CalledProcessError(
            1, ["d2"], stderr=b"err: syntax error"
        )
        with mock.patch("subprocess.run", side_effect=failure):
            with self.assertRaisesRegex(VisualError, "syntax error"):
                show_image('"A" ->\n', "A")
        self.open.assert_not_called()

    @unittest.skipUnless(shutil.which("d2"), "программа d2 не установлена")
    def test_real_d2_draws_svg(self):
        """Настоящая программа d2 рисует SVG-файл."""
        show_image('"A" -> "B"\n', "A")
        self.assertIn("<svg", Path("graph-A.svg").read_text())


if __name__ == "__main__":
    unittest.main()
