"""Ядро эмулятора: цикл REPL и выполнение команд."""

import sys

from emulator.commands import COMMANDS
from emulator.errors import CommandError, ScriptError, ShellError
from emulator.parser import tokenize
from emulator.vfs import Vfs, format_path

DEFAULT_VFS_NAME = "vfs"
COMMENT_MARK = "#"


class Shell:
    """Интерпретатор команд эмулятора.

    :param vfs: виртуальная файловая система (по умолчанию пустая).
    :param out: поток вывода.
    """

    def __init__(self, vfs=None, out=None):
        """Создать интерпретатор."""
        self.vfs = vfs if vfs is not None else Vfs(DEFAULT_VFS_NAME)
        self.cwd = []
        self.out = out if out is not None else sys.stdout
        self.running = True
        self.exit_code = 0

    def prompt(self):
        """Сформировать приглашение: имя VFS и текущий каталог."""
        return f"{self.vfs.name}:{format_path(self.cwd)}$ "

    def write(self, text):
        """Вывести строку в поток вывода."""
        print(text, file=self.out)

    def report_error(self, error):
        """Вывести сообщение об ошибке."""
        self.write(f"ошибка: {error}")

    def stop(self, code=0):
        """Остановить интерпретатор с кодом возврата ``code``."""
        self.running = False
        self.exit_code = code

    def execute(self, line):
        """Разобрать и выполнить одну строку.

        :return: True, если строка выполнена без ошибок.
        """
        try:
            args = tokenize(line)
            if args:
                self._dispatch(args[0], args[1:])
        except ShellError as error:
            self.report_error(error)
            return False
        return True

    def run_repl(self, read_line=input):
        """Запустить интерактивный цикл чтение-выполнение-вывод."""
        while self.running:
            try:
                line = read_line(self.prompt())
            except EOFError:
                self.write("")
                break
            except KeyboardInterrupt:
                self.write("^C")
                continue
            self.execute(line)

    def run_script(self, path):
        """Выполнить стартовый скрипт построчно.

        Каждая строка выводится вместе с приглашением, имитируя
        диалог с пользователем. Ошибочные строки пропускаются.

        :return: число строк, завершившихся ошибкой.
        :raises ScriptError: файл скрипта не удалось прочитать.
        """
        lines = _read_script(path)
        errors = 0
        for number, line in enumerate(lines, start=1):
            if not self.running:
                break
            if _is_skippable(line):
                continue
            self.write(self.prompt() + line)
            if not self.execute(line):
                errors += 1
                self.report_error(f"строка {number} скрипта пропущена")
        return errors

    def _dispatch(self, name, args):
        """Найти команду по имени и выполнить её."""
        command = COMMANDS.get(name)
        if command is None:
            raise CommandError(f"{name}: команда не найдена")
        command.handler(self, args)


def _read_script(path):
    """Прочитать строки скрипта из файла."""
    try:
        with open(path, encoding="utf-8") as file:
            return file.read().splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ScriptError(
            f"не удалось прочитать скрипт {path}: {error}"
        ) from None


def _is_skippable(line):
    """Проверить, является ли строка пустой или комментарием."""
    stripped = line.strip()
    return not stripped or stripped.startswith(COMMENT_MARK)
