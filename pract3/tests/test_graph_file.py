"""Тесты чтения файла тестового репозитория."""

import os
import tempfile
import unittest

from src.graph_file import GraphFileError, load_graph_file


class LoadGraphFileTest(unittest.TestCase):
    """Разбор файла вида «A: B C»."""

    def setUp(self):
        """Подготовить путь к временному файлу."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, "graph.txt")

    def load(self, text):
        """Записать текст в файл и прочитать его как репозиторий."""
        with open(self.path, "w", encoding="utf-8") as file:
            file.write(text)
        return load_graph_file(self.path)

    def test_reads_packages_and_dependencies(self):
        """Каждая строка — пакет и его зависимости через пробел."""
        self.assertEqual(
            self.load("A: B C\nB: C\nC:\n"),
            {"A": ["B", "C"], "B": ["C"], "C": []},
        )

    def test_skips_blank_lines_and_comments(self):
        """Пустые строки и строки с # не описывают пакеты."""
        self.assertEqual(self.load("# граф\n\nA: B\n"), {"A": ["B"]})

    def test_line_without_colon_reports_line_number(self):
        """Строка без двоеточия — ошибка с номером строки."""
        with self.assertRaisesRegex(GraphFileError, "строка 2"):
            self.load("A: B\nB C\n")

    def test_name_must_be_capital_latin_letters(self):
        """Имена пакетов — только большие латинские буквы."""
        with self.assertRaisesRegex(GraphFileError, "'b'"):
            self.load("A: b\n")

    def test_package_described_twice_is_error(self):
        """Повторное описание пакета — ошибка, а не тихая замена."""
        with self.assertRaisesRegex(GraphFileError, "'A'"):
            self.load("A: B\nA: C\n")

    def test_missing_file_is_error(self):
        """Отсутствие файла — ошибка тестового репозитория."""
        with self.assertRaises(GraphFileError):
            load_graph_file(self.path)


if __name__ == "__main__":
    unittest.main()
