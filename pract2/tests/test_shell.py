"""Тесты интерпретатора: REPL, разбор и обработка ошибок."""

import io
import unittest

from emulator.shell import Shell
from emulator.vfs import Vfs


def make_shell():
    """Создать интерпретатор, пишущий в буфер."""
    return Shell(vfs=Vfs("test"), out=io.StringIO())


class ShellTest(unittest.TestCase):
    """Проверки REPL, заглушек и обработки ошибок."""

    def test_prompt_contains_vfs_name(self):
        """Приглашение содержит имя VFS."""
        self.assertIn("test", make_shell().prompt())

    def test_quoted_args_reach_command(self):
        """Аргумент в кавычках передаётся команде целиком."""
        shell = make_shell()
        self.assertTrue(shell.execute('echo "a  b" c'))
        self.assertEqual(shell.out.getvalue(), "a  b c\n")

    def test_cd_too_many_args(self):
        """cd с двумя аргументами — ошибка."""
        shell = make_shell()
        self.assertFalse(shell.execute("cd a b"))
        self.assertIn("слишком много аргументов", shell.out.getvalue())

    def test_unknown_command(self):
        """Неизвестная команда — ошибка."""
        shell = make_shell()
        self.assertFalse(shell.execute("foo"))
        self.assertIn("foo: команда не найдена", shell.out.getvalue())

    def test_parse_error_reported(self):
        """Ошибка разбора выводится как ошибка."""
        shell = make_shell()
        self.assertFalse(shell.execute('ls "abc'))
        self.assertIn("незакрытая кавычка", shell.out.getvalue())

    def test_exit_with_code(self):
        """exit останавливает интерпретатор с заданным кодом."""
        shell = make_shell()
        shell.execute("exit 3")
        self.assertFalse(shell.running)
        self.assertEqual(shell.exit_code, 3)

    def test_exit_bad_code(self):
        """exit с нечисловым аргументом — ошибка."""
        shell = make_shell()
        self.assertFalse(shell.execute("exit abc"))
        self.assertTrue(shell.running)

    def test_repl_stops_on_exit(self):
        """REPL читает строки до команды exit."""
        shell = make_shell()
        lines = iter(["echo 1", "exit", "echo never"])
        shell.run_repl(lambda prompt: next(lines))
        self.assertNotIn("never", shell.out.getvalue())

    def test_repl_stops_on_eof(self):
        """REPL завершается по концу ввода."""
        shell = make_shell()

        def read_line(prompt):
            """Имитировать конец ввода."""
            raise EOFError

        shell.run_repl(read_line)
        self.assertEqual(shell.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
