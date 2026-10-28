"""Тесты парсера командной строки."""

import unittest

from emulator.errors import ParseError
from emulator.parser import tokenize


class TokenizeTest(unittest.TestCase):
    """Проверки функции tokenize."""

    def test_simple_words(self):
        """Аргументы разделяются пробелами и табуляцией."""
        self.assertEqual(tokenize("ls  -l\t/home"), ["ls", "-l", "/home"])

    def test_empty_line(self):
        """Пустая строка даёт пустой список."""
        self.assertEqual(tokenize("   "), [])

    def test_double_quotes(self):
        """Двойные кавычки объединяют слова в один аргумент."""
        self.assertEqual(tokenize('cd "my docs"'), ["cd", "my docs"])

    def test_single_quotes(self):
        """Внутри одинарных кавычек всё берётся буквально."""
        self.assertEqual(tokenize(r"echo 'a \" b'"), ["echo", r'a \" b'])

    def test_glued_quotes(self):
        """Кавычки внутри слова склеиваются с соседними символами."""
        self.assertEqual(tokenize('a"b c"\'d\''), ["ab cd"])

    def test_empty_quoted_argument(self):
        """Пустые кавычки дают пустой аргумент."""
        self.assertEqual(tokenize('echo "" x'), ["echo", "", "x"])

    def test_escape_outside_quotes(self):
        """Обратная косая черта экранирует пробел."""
        self.assertEqual(tokenize(r"cd my\ dir"), ["cd", "my dir"])

    def test_escape_in_double_quotes(self):
        """В двойных кавычках экранируются только \" и \\."""
        self.assertEqual(tokenize(r'"a\"b\n"'), [r'a"b\n'])

    def test_unclosed_quote(self):
        """Незакрытая кавычка приводит к ошибке."""
        with self.assertRaises(ParseError):
            tokenize('echo "hello')

    def test_trailing_escape(self):
        """Обратная косая черта в конце строки приводит к ошибке."""
        with self.assertRaises(ParseError):
            tokenize("echo \\")


if __name__ == "__main__":
    unittest.main()
