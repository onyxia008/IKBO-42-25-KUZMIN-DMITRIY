"""Точка входа: ``python -m emulator``."""

import sys

from emulator.config import debug_lines, parse_args, vfs_name_from_path
from emulator.errors import ScriptError
from emulator.shell import DEFAULT_VFS_NAME, Shell

EXIT_SCRIPT_ERROR = 2


def main(argv=None):
    """Запустить эмулятор и вернуть код завершения."""
    config = parse_args(argv)
    for line in debug_lines(config):
        print(line)
    name = vfs_name_from_path(config.vfs_path, DEFAULT_VFS_NAME)
    shell = Shell(vfs_name=name)
    if config.script_path:
        try:
            errors = shell.run_script(config.script_path)
        except ScriptError as error:
            shell.report_error(error)
            return EXIT_SCRIPT_ERROR
        shell.write(f"[script] выполнен, ошибок: {errors}")
    if shell.running:
        shell.run_repl(input if sys.stdin.isatty() else _echo_input)
    return shell.exit_code


def _echo_input(prompt):
    """Прочитать строку из канала и повторить её, имитируя ввод."""
    line = input(prompt)
    print(line)
    return line


if __name__ == "__main__":
    sys.exit(main())
