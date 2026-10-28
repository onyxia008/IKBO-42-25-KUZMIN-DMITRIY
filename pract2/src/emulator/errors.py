"""Исключения эмулятора."""


class ShellError(Exception):
    """Базовая ошибка эмулятора."""


class ParseError(ShellError):
    """Ошибка разбора командной строки."""


class CommandError(ShellError):
    """Ошибка выполнения команды."""


class ScriptError(ShellError):
    """Ошибка открытия стартового скрипта."""
