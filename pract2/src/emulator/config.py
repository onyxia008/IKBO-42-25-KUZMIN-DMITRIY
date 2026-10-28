"""Разбор параметров командной строки эмулятора."""

import argparse
from dataclasses import dataclass

DEBUG_PREFIX = "[debug]"
NOT_SET = "<не задан>"


@dataclass(frozen=True)
class Config:
    """Параметры запуска эмулятора.

    :param vfs_path: путь к физическому расположению VFS.
    :param script_path: путь к стартовому скрипту.
    """

    vfs_path: str | None = None
    script_path: str | None = None


def parse_args(argv=None):
    """Разобрать аргументы командной строки и вернуть Config."""
    parser = argparse.ArgumentParser(
        prog="emulator",
        description="Эмулятор командной оболочки UNIX-подобной ОС.",
    )
    parser.add_argument(
        "--vfs", dest="vfs_path", metavar="PATH",
        help="путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--script", dest="script_path", metavar="PATH",
        help="путь к стартовому скрипту",
    )
    namespace = parser.parse_args(argv)
    return Config(namespace.vfs_path, namespace.script_path)


def debug_lines(config):
    """Сформировать строки отладочного вывода параметров."""
    return [
        f"{DEBUG_PREFIX} Параметры запуска:",
        f"{DEBUG_PREFIX}   vfs    = {_show(config.vfs_path)}",
        f"{DEBUG_PREFIX}   script = {_show(config.script_path)}",
    ]


def _show(value):
    """Показать значение параметра или пометку «не задан»."""
    return value if value else NOT_SET
