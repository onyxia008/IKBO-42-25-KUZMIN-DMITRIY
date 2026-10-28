"""Встроенные команды эмулятора."""

from dataclasses import dataclass

from emulator.errors import CommandError

MAX_CD_ARGS = 1
MAX_EXIT_ARGS = 1


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
    """Заглушка ls: вывести имя команды и аргументы."""
    _print_stub(shell, "ls", args)


def cmd_cd(shell, args):
    """Заглушка cd: проверить число аргументов и вывести их."""
    if len(args) > MAX_CD_ARGS:
        raise CommandError("cd: слишком много аргументов")
    _print_stub(shell, "cd", args)


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


def _parse_exit_code(text):
    """Преобразовать аргумент exit в целое число."""
    try:
        return int(text)
    except ValueError:
        raise CommandError(
            f"exit: {text}: требуется числовой аргумент"
        ) from None


def _print_stub(shell, name, args):
    """Вывести имя команды-заглушки и её аргументы."""
    shell.write(f"{name}: аргументы {args}")


COMMANDS = {
    "ls": Command(cmd_ls, "ls [путь]", "вывести содержимое каталога"),
    "cd": Command(cmd_cd, "cd [путь]", "сменить текущий каталог"),
    "exit": Command(cmd_exit, "exit [код]", "завершить работу эмулятора"),
    "vfs-info": Command(
        cmd_vfs_info, "vfs-info", "служебная: сведения о загруженной VFS",
    ),
}
