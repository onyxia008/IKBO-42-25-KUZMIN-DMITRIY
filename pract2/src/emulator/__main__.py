"""Точка входа: ``python -m emulator``."""

import sys

from emulator.shell import Shell


def main():
    """Запустить эмулятор и вернуть код завершения."""
    shell = Shell()
    shell.run_repl()
    return shell.exit_code


if __name__ == "__main__":
    sys.exit(main())
