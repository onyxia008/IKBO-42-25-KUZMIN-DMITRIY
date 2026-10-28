"""Ядро эмулятора: цикл REPL и выполнение команд."""

import sys

from emulator.commands import COMMANDS
from emulator.errors import CommandError, ShellError
from emulator.parser import tokenize

DEFAULT_VFS_NAME = "vfs"


class Shell:
    """Интерпретатор команд эмулятора.

    :param vfs_name: имя VFS, отображаемое в приглашении.
    :param out: поток вывода.
    """

    def __init__(self, vfs_name=DEFAULT_VFS_NAME, out=None):
        """Создать интерпретатор."""
        self.vfs_name = vfs_name
        self.out = out if out is not None else sys.stdout
        self.running = True
        self.exit_code = 0

    def prompt(self):
        """Сформировать приглашение к вводу с именем VFS."""
        return f"{self.vfs_name}:/$ "

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

    def _dispatch(self, name, args):
        """Найти команду по имени и выполнить её."""
        command = COMMANDS.get(name)
        if command is None:
            raise CommandError(f"{name}: команда не найдена")
        command.handler(self, args)
