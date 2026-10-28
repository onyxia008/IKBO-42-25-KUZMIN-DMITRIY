"""Тесты команд, работающих с VFS: ls, cd, cal, echo, whoami."""

import datetime
import getpass
import io
import os
import unittest

from emulator import cal
from emulator.shell import Shell
from emulator.vfs import load_vfs

DEEP_VFS = os.path.join(
    os.path.dirname(__file__), "..", "examples", "vfs", "deep.xml",
)


class CommandTestCase(unittest.TestCase):
    """Базовый класс: интерпретатор с глубокой VFS."""

    def setUp(self):
        """Создать интерпретатор с VFS deep.xml."""
        self.shell = Shell(vfs=load_vfs(DEEP_VFS), out=io.StringIO())

    def run_ok(self, line):
        """Выполнить строку, ожидая успех, и вернуть вывод."""
        self.shell.out = io.StringIO()
        self.assertTrue(self.shell.execute(line), self.shell.out.getvalue())
        return self.shell.out.getvalue()

    def run_fail(self, line):
        """Выполнить строку, ожидая ошибку, и вернуть вывод."""
        self.shell.out = io.StringIO()
        self.assertFalse(self.shell.execute(line))
        return self.shell.out.getvalue()


class LsTest(CommandTestCase):
    """Проверки команды ls."""

    def test_root(self):
        """ls без аргументов выводит корень."""
        self.assertEqual(self.run_ok("ls"), "bin  etc  home  tmp\n")

    def test_quoted_path_with_spaces(self):
        """Путь с пробелами передаётся в кавычках."""
        output = self.run_ok('ls "home/user/my documents"')
        self.assertEqual(output, "report.txt\n")

    def test_names_with_spaces_are_quoted(self):
        """Имена с пробелами выводятся в кавычках."""
        self.assertIn("'my documents'", self.run_ok("ls /home/user"))

    def test_long_format(self):
        """ls -l выводит тип, размер и имя."""
        output = self.run_ok("ls -l /etc")
        self.assertRegex(output, r"drwxr-xr-x +0 .* app")
        self.assertRegex(output, r"-rw-r--r-- +8 .* hostname")

    def test_file_argument(self):
        """Для файла выводится его имя."""
        self.assertEqual(self.run_ok("ls /etc/hostname"), "hostname\n")

    def test_empty_dir(self):
        """Пустой каталог — пустой вывод."""
        self.assertEqual(self.run_ok("ls /tmp"), "")

    def test_several_paths(self):
        """Несколько путей выводятся с заголовками."""
        output = self.run_ok("ls /bin /etc/app")
        self.assertEqual(output, "/bin:\ntool\n/etc/app:\napp.conf\n")

    def test_missing_path(self):
        """Несуществующий путь — ошибка."""
        self.assertIn("нет такого", self.run_fail("ls /nope"))

    def test_bad_option(self):
        """Неизвестный ключ — ошибка."""
        self.assertIn("неверный ключ", self.run_fail("ls -z"))


class CdTest(CommandTestCase):
    """Проверки команды cd."""

    def test_absolute_and_prompt(self):
        """cd меняет каталог, приглашение показывает путь."""
        self.run_ok("cd /home/user")
        self.assertEqual(self.shell.prompt(), "deep:/home/user$ ")

    def test_relative_and_parent(self):
        """Относительные пути и .. работают."""
        self.run_ok("cd home")
        self.run_ok("cd user/../user/projects")
        self.assertEqual(self.shell.cwd, ["home", "user", "projects"])

    def test_no_args_goes_to_root(self):
        """cd без аргументов переходит в корень."""
        self.run_ok("cd /etc/app")
        self.run_ok("cd")
        self.assertEqual(self.shell.cwd, [])

    def test_ls_after_cd(self):
        """ls после cd выводит новый текущий каталог."""
        self.run_ok("cd /etc")
        self.assertEqual(self.run_ok("ls"), "app  hostname\n")

    def test_cd_to_file(self):
        """cd в файл — ошибка, каталог не меняется."""
        self.assertIn("не является каталогом",
                      self.run_fail("cd /etc/hostname"))
        self.assertEqual(self.shell.cwd, [])

    def test_cd_missing(self):
        """cd в несуществующий каталог — ошибка."""
        self.assertIn("нет такого", self.run_fail("cd /nope"))


class CalTest(CommandTestCase):
    """Проверки команды cal."""

    def test_current_month(self):
        """cal без аргументов выводит текущий месяц."""
        today = datetime.date.today()
        title = f"{cal.MONTH_NAMES[today.month]} {today.year}"
        self.assertIn(title, self.run_ok("cal"))

    def test_month_year(self):
        """cal месяц год: неделя начинается с понедельника."""
        output = self.run_ok("cal 10 2026")
        self.assertIn("Октябрь 2026", output)
        self.assertIn("Пн Вт Ср Чт Пт Сб Вс", output)
        self.assertIn(" 1  2  3  4", output)

    def test_year(self):
        """cal год выводит все 12 месяцев."""
        output = self.run_ok("cal 2026")
        for name in cal.MONTH_NAMES[1:]:
            self.assertIn(name, output)

    def test_errors(self):
        """Неверные аргументы cal — ошибки."""
        self.assertIn("от 1 до 12", self.run_fail("cal 13 2026"))
        self.assertIn("числом", self.run_fail("cal abc"))
        self.assertIn("от 1 до 9999", self.run_fail("cal 0"))
        self.assertIn("слишком много", self.run_fail("cal 1 2 3"))


class EchoWhoamiTest(CommandTestCase):
    """Проверки команд echo и whoami."""

    def test_echo(self):
        """echo выводит аргументы через пробел."""
        self.assertEqual(self.run_ok("echo 'a  b' c"), "a  b c\n")

    def test_echo_empty(self):
        """echo без аргументов выводит пустую строку."""
        self.assertEqual(self.run_ok("echo"), "\n")

    def test_whoami(self):
        """whoami выводит имя пользователя ОС."""
        self.assertEqual(self.run_ok("whoami"), getpass.getuser() + "\n")

    def test_whoami_args(self):
        """whoami с аргументами — ошибка."""
        self.assertIn("не принимает", self.run_fail("whoami root"))


if __name__ == "__main__":
    unittest.main()
