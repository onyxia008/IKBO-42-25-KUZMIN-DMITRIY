"""Тесты параметров командной строки и стартового скрипта."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from emulator.config import Config, debug_lines, parse_args
from emulator.errors import ScriptError
from emulator.shell import Shell
from emulator.vfs import Vfs


class ConfigTest(unittest.TestCase):
    """Проверки разбора параметров."""

    def test_no_args(self):
        """Без параметров оба пути не заданы."""
        self.assertEqual(parse_args([]), Config(None, None))

    def test_all_args(self):
        """Оба параметра разбираются."""
        config = parse_args(["--vfs", "a.xml", "--script", "s.txt"])
        self.assertEqual(config, Config("a.xml", "s.txt"))

    def test_unknown_arg(self):
        """Неизвестный параметр завершает программу с ошибкой."""
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parse_args(["--bad"])

    def test_debug_lines(self):
        """Отладочный вывод содержит все параметры."""
        text = "\n".join(debug_lines(Config("a.xml", None)))
        self.assertIn("vfs    = a.xml", text)
        self.assertIn("script = <не задан>", text)


class ScriptTest(unittest.TestCase):
    """Проверки выполнения стартового скрипта."""

    def run_script(self, text):
        """Записать скрипт во временный файл и выполнить его."""
        shell = Shell(vfs=Vfs("t"), out=io.StringIO())
        with tempfile.NamedTemporaryFile(
                "w", suffix=".txt", delete=False, encoding="utf-8") as file:
            file.write(text)
        try:
            errors = shell.run_script(file.name)
        finally:
            os.unlink(file.name)
        return shell, errors

    def test_echo_input_and_output(self):
        """Скрипт показывает и ввод, и вывод."""
        shell, errors = self.run_script("echo a\n")
        self.assertEqual(errors, 0)
        self.assertIn("t:/$ echo a\na\n",
                      shell.out.getvalue())

    def test_errors_are_skipped(self):
        """Ошибочные строки пропускаются, выполнение продолжается."""
        shell, errors = self.run_script("bad\ncd a b\necho ok\n")
        self.assertEqual(errors, 2)
        self.assertIn("строка 1 скрипта пропущена", shell.out.getvalue())
        self.assertIn("ok", shell.out.getvalue())

    def test_comments_and_blank_lines(self):
        """Комментарии и пустые строки не выполняются."""
        shell, errors = self.run_script("# comment\n\n")
        self.assertEqual((errors, shell.out.getvalue()), (0, ""))

    def test_exit_stops_script(self):
        """После exit оставшиеся строки не выполняются."""
        shell, _ = self.run_script("exit 1\necho never\n")
        self.assertNotIn("never", shell.out.getvalue())
        self.assertEqual(shell.exit_code, 1)

    def test_missing_script(self):
        """Отсутствующий скрипт приводит к ScriptError."""
        shell = Shell(out=io.StringIO())
        with self.assertRaises(ScriptError):
            shell.run_script("/no/such/script.txt")


if __name__ == "__main__":
    unittest.main()
