"""Виртуальная файловая система (VFS), загружаемая из XML.

Формат файла::

    <vfs name="demo">
      <dir name="home">
        <file name="note.txt">текст</file>
        <file name="logo.bin" encoding="base64">iVBORw0KGgo=</file>
      </dir>
    </vfs>

Все данные хранятся только в памяти, исходный файл не изменяется.
"""

import base64
import binascii
import os
import time
import xml.etree.ElementTree as ElementTree

from emulator.errors import VfsError

ROOT_TAG = "vfs"
DIR_TAG = "dir"
FILE_TAG = "file"
ENCODING_TEXT = "text"
ENCODING_BASE64 = "base64"
ENCODINGS = (ENCODING_TEXT, ENCODING_BASE64)
SEPARATOR = "/"
CURRENT_DIR = "."
PARENT_DIR = ".."
HOME_DIR = "~"
FORBIDDEN_NAMES = ("", CURRENT_DIR, PARENT_DIR)


class VfsNode:
    """Узел VFS: файл или каталог."""

    is_dir = False

    def __init__(self, name):
        """Создать узел с именем ``name`` и текущим временем изменения."""
        self.name = name
        self.mtime = time.time()

    def touch(self):
        """Обновить время изменения узла."""
        self.mtime = time.time()


class VfsFile(VfsNode):
    """Файл VFS с двоичным содержимым."""

    def __init__(self, name, data=b""):
        """Создать файл с содержимым ``data``."""
        super().__init__(name)
        self.data = data

    @property
    def size(self):
        """Размер файла в байтах."""
        return len(self.data)


class VfsDir(VfsNode):
    """Каталог VFS."""

    is_dir = True

    def __init__(self, name):
        """Создать пустой каталог."""
        super().__init__(name)
        self.children = {}

    def add(self, node):
        """Добавить дочерний узел, запрещая повтор имён."""
        if node.name in self.children:
            raise VfsError(f"повторяющееся имя «{node.name}»")
        self.children[node.name] = node

    def sorted_children(self):
        """Вернуть дочерние узлы, отсортированные по имени."""
        return [self.children[key] for key in sorted(self.children)]


class Vfs:
    """Виртуальная файловая система с корневым каталогом.

    :param name: имя VFS (отображается в приглашении).
    :param root: корневой каталог.
    :param source: путь к исходному XML-файлу.
    """

    def __init__(self, name, root=None, source=None):
        """Создать VFS."""
        self.name = name
        self.root = root if root is not None else VfsDir(SEPARATOR)
        self.source = source

    def resolve(self, path, cwd):
        """Нормализовать путь относительно ``cwd``.

        :param path: абсолютный или относительный путь.
        :param cwd: текущий каталог как список имён.
        :return: список имён от корня.
        """
        parts = [] if _is_rooted(path) else list(cwd)
        for name in path.split(SEPARATOR):
            if name in ("", CURRENT_DIR, HOME_DIR):
                continue
            if name == PARENT_DIR:
                if parts:
                    parts.pop()
            else:
                parts.append(name)
        return parts

    def node_at(self, parts):
        """Найти узел по списку имён от корня.

        :raises VfsError: узел не найден или путь проходит через файл.
        """
        node = self.root
        for index, name in enumerate(parts):
            if not node.is_dir:
                shown = format_path(parts[:index])
                raise VfsError(f"{shown}: не является каталогом")
            node = node.children.get(name)
            if node is None:
                shown = format_path(parts[:index + 1])
                raise VfsError(f"{shown}: нет такого файла или каталога")
        return node

    def lookup(self, path, cwd):
        """Вернуть пару (нормализованный путь, узел) для ``path``."""
        parts = self.resolve(path, cwd)
        return parts, self.node_at(parts)

    def touch(self, path, cwd):
        """Создать пустой файл или обновить время изменения узла.

        Изменения выполняются только в памяти.

        :return: True, если файл был создан.
        :raises VfsError: родительский каталог не существует.
        """
        parts = self.resolve(path, cwd)
        if not parts:
            self.root.touch()
            return False
        parent = self.node_at(parts[:-1])
        if not parent.is_dir:
            shown = format_path(parts[:-1])
            raise VfsError(f"{shown}: не является каталогом")
        node = parent.children.get(parts[-1])
        if node is not None:
            node.touch()
            return False
        if path.endswith(SEPARATOR):
            raise VfsError(f"{path}: нет такого каталога")
        parent.add(VfsFile(parts[-1]))
        parent.touch()
        return True

    def count(self):
        """Подсчитать каталоги и файлы (без корня)."""
        dirs = files = 0
        stack = [self.root]
        while stack:
            for child in stack.pop().children.values():
                if child.is_dir:
                    dirs += 1
                    stack.append(child)
                else:
                    files += 1
        return dirs, files


def format_path(parts):
    """Преобразовать список имён в строку абсолютного пути."""
    return SEPARATOR + SEPARATOR.join(parts)


def load_vfs(path):
    """Загрузить VFS из XML-файла.

    :raises VfsError: файл не найден, неверный XML или структура VFS.
    """
    try:
        tree = ElementTree.parse(path)
    except FileNotFoundError:
        raise VfsError(f"файл VFS не найден: {path}") from None
    except OSError as error:
        raise VfsError(f"не удалось открыть VFS {path}: {error}") from None
    except ElementTree.ParseError as error:
        raise VfsError(f"неверный формат XML в {path}: {error}") from None
    try:
        return _build_vfs(tree.getroot(), path)
    except VfsError as error:
        raise VfsError(f"неверный формат VFS в {path}: {error}") from None


def _is_rooted(path):
    """Проверить, задан ли путь от корня (``/`` или ``~``)."""
    return path.startswith(SEPARATOR) or path.split(SEPARATOR)[0] == HOME_DIR


def _build_vfs(element, path):
    """Построить объект Vfs из корневого XML-элемента."""
    if element.tag != ROOT_TAG:
        raise VfsError(f"корневой элемент должен быть <{ROOT_TAG}>")
    default_name = os.path.splitext(os.path.basename(path))[0]
    vfs = Vfs(element.get("name") or default_name, source=path)
    _fill_dir(vfs.root, element)
    return vfs


def _fill_dir(directory, element):
    """Заполнить каталог дочерними узлами XML-элемента."""
    for child in element:
        if child.tag == DIR_TAG:
            node = VfsDir(_node_name(child))
            _fill_dir(node, child)
        elif child.tag == FILE_TAG:
            node = _parse_file(child)
        else:
            raise VfsError(f"неизвестный элемент <{child.tag}>")
        directory.add(node)


def _parse_file(element):
    """Создать файл VFS из элемента ``<file>``."""
    name = _node_name(element)
    if len(element):
        raise VfsError(f"файл «{name}» не может содержать элементы")
    encoding = element.get("encoding", ENCODING_TEXT)
    if encoding not in ENCODINGS:
        raise VfsError(f"файл «{name}»: неизвестная кодировка {encoding}")
    text = element.text or ""
    if encoding == ENCODING_TEXT:
        return VfsFile(name, text.encode("utf-8"))
    try:
        data = base64.b64decode("".join(text.split()), validate=True)
    except binascii.Error:
        raise VfsError(f"файл «{name}»: некорректные base64-данные") from None
    return VfsFile(name, data)


def _node_name(element):
    """Получить и проверить атрибут name элемента."""
    name = element.get("name")
    if name is None:
        raise VfsError(f"у элемента <{element.tag}> нет атрибута name")
    if name in FORBIDDEN_NAMES or SEPARATOR in name:
        raise VfsError(f"недопустимое имя «{name}»")
    return name
