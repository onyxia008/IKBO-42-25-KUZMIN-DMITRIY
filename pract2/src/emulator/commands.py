"""Встроенные команды эмулятора."""

import getpass
import time
from dataclasses import dataclass

from emulator import cal
from emulator.errors import CommandError, VfsError
from emulator.vfs import HOME_DIR

MAX_CD_ARGS = 1
MAX_EXIT_ARGS = 1
MAX_HELP_ARGS = 1
MAX_CAL_ARGS = 2
CAL_YEAR_ONLY_ARGS = 1
SINGLE_TARGET = 1
LONG_FLAG = "-l"
OPTION_PREFIX = "-"
TIME_FORMAT = "%Y-%m-%d %H:%M"
DIR_MODE = "drwxr-xr-x"
FILE_MODE = "-rw-r--r--"
SIZE_WIDTH = 8
SPACE = " "
USAGE_WIDTH = 24


@dataclass(frozen=True)
class Command:
    """Описание встроенной команды.

    :param handler: функция ``handler(shell, args)``.
    :param usage: синтаксис вызова.
    :param description: краткое описание.
    """

    handler: object
    usage: str
    description: str


def cmd_ls(shell, args):
    """Вывести содержимое каталогов: ``ls [-l] [путь ...]``.

    Без пути выводится текущий каталог. Для файла выводится его имя.
    Ошибки по отдельным путям собираются и сообщаются в конце.
    """
    long_format, paths = _parse_ls_args(args)
    targets = paths or [""]
    errors = []
    for path in targets:
        try:
            node = shell.vfs.lookup(path, shell.cwd)[1]
        except VfsError as error:
            errors.append(f"ls: {error}")
            continue
        if len(targets) > SINGLE_TARGET and node.is_dir:
            shell.write(f"{path}:")
        _list_node(shell, node, long_format)
    if errors:
        raise CommandError("\n".join(errors))


def cmd_cd(shell, args):
    """Сменить текущий каталог: ``cd [путь]`` (без пути — в корень)."""
    if len(args) > MAX_CD_ARGS:
        raise CommandError("cd: слишком много аргументов")
    path = args[0] if args else HOME_DIR
    try:
        parts, node = shell.vfs.lookup(path, shell.cwd)
    except VfsError as error:
        raise CommandError(f"cd: {error}") from None
    if not node.is_dir:
        raise CommandError(f"cd: {path}: не является каталогом")
    shell.cwd = parts


def cmd_cal(shell, args):
    """Вывести календарь: ``cal``, ``cal год``, ``cal месяц год``."""
    if len(args) > MAX_CAL_ARGS:
        raise CommandError("cal: слишком много аргументов")
    if not args:
        text = cal.current_month_text()
    elif len(args) == CAL_YEAR_ONLY_ARGS:
        text = cal.year_text(cal.parse_year(args[0]))
    else:
        month = cal.parse_month(args[0])
        text = cal.month_text(cal.parse_year(args[1]), month)
    shell.write(text)


def cmd_echo(shell, args):
    """Вывести аргументы через пробел."""
    shell.write(" ".join(args))


def cmd_whoami(shell, args):
    """Вывести имя текущего пользователя ОС."""
    if args:
        raise CommandError("whoami: команда не принимает аргументов")
    try:
        shell.write(getpass.getuser())
    except (OSError, KeyError):
        raise CommandError("whoami: не удалось определить имя") from None


def cmd_touch(shell, args):
    """Создать пустые файлы или обновить время изменения.

    Синтаксис ``touch файл [файл ...]``. Изменения — только в памяти.
    Ошибки по отдельным путям собираются и сообщаются в конце.
    """
    if not args:
        raise CommandError("touch: пропущен операнд, задающий файл")
    errors = []
    for path in args:
        try:
            shell.vfs.touch(path, shell.cwd)
        except VfsError as error:
            errors.append(f"touch: {error}")
    if errors:
        raise CommandError("\n".join(errors))


def cmd_help(shell, args):
    """Вывести список команд или справку по одной команде."""
    if len(args) > MAX_HELP_ARGS:
        raise CommandError("help: слишком много аргументов")
    if not args:
        shell.write("Доступные команды:")
        for command in COMMANDS.values():
            shell.write(f"  {command.usage:<{USAGE_WIDTH}} "
                        f"{command.description}")
        return
    command = COMMANDS.get(args[0])
    if command is None:
        raise CommandError(f"help: нет справки по «{args[0]}»")
    shell.write(f"{command.usage}\n    {command.description}")


def cmd_exit(shell, args):
    """Завершить работу эмулятора с необязательным кодом возврата."""
    if len(args) > MAX_EXIT_ARGS:
        raise CommandError("exit: слишком много аргументов")
    code = _parse_exit_code(args[0]) if args else 0
    shell.stop(code)


def cmd_vfs_info(shell, args):
    """Служебная команда: вывести сведения о загруженной VFS."""
    if args:
        raise CommandError("vfs-info: команда не принимает аргументов")
    dirs, files = shell.vfs.count()
    shell.write(f"имя:      {shell.vfs.name}")
    shell.write(f"источник: {shell.vfs.source or '<в памяти>'}")
    shell.write(f"каталогов: {dirs}, файлов: {files}")


def _parse_ls_args(args):
    """Отделить ключи ls от путей. Поддерживается только ``-l``."""
    long_format = False
    paths = []
    for arg in args:
        if arg == LONG_FLAG:
            long_format = True
        elif arg.startswith(OPTION_PREFIX) and arg != OPTION_PREFIX:
            raise CommandError(f"ls: неверный ключ «{arg}»")
        else:
            paths.append(arg)
    return long_format, paths


def _list_node(shell, node, long_format):
    """Вывести каталог (его содержимое) или файл."""
    nodes = node.sorted_children() if node.is_dir else [node]
    if long_format:
        for item in nodes:
            shell.write(_long_line(item))
    elif nodes:
        shell.write("  ".join(_quote_name(item.name) for item in nodes))


def _long_line(node):
    """Строка подробного формата ls -l."""
    mode = DIR_MODE if node.is_dir else FILE_MODE
    size = 0 if node.is_dir else node.size
    stamp = time.strftime(TIME_FORMAT, time.localtime(node.mtime))
    return f"{mode} {size:>{SIZE_WIDTH}} {stamp} {_quote_name(node.name)}"


def _quote_name(name):
    """Взять имя с пробелами в кавычки, как это делает ls."""
    return f"'{name}'" if SPACE in name else name


def _parse_exit_code(text):
    """Преобразовать аргумент exit в целое число."""
    try:
        return int(text)
    except ValueError:
        raise CommandError(
            f"exit: {text}: требуется числовой аргумент"
        ) from None


COMMANDS = {
    "ls": Command(
        cmd_ls, "ls [-l] [путь ...]",
        "вывести содержимое каталога; -l — подробный формат",
    ),
    "cd": Command(
        cmd_cd, "cd [путь]",
        "сменить текущий каталог; без аргумента — корень VFS",
    ),
    "cal": Command(
        cmd_cal, "cal [[месяц] год]",
        "вывести календарь на текущий месяц, месяц или год",
    ),
    "echo": Command(cmd_echo, "echo [текст ...]", "вывести аргументы"),
    "whoami": Command(
        cmd_whoami, "whoami", "вывести имя текущего пользователя ОС",
    ),
    "touch": Command(
        cmd_touch, "touch файл [файл ...]",
        "создать пустой файл или обновить время изменения",
    ),
    "help": Command(
        cmd_help, "help [команда]",
        "список команд или справка по одной команде",
    ),
    "exit": Command(cmd_exit, "exit [код]", "завершить работу эмулятора"),
    "vfs-info": Command(
        cmd_vfs_info, "vfs-info", "служебная: сведения о загруженной VFS",
    ),
}
