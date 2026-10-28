"""Тесты загрузки VFS из XML и навигации по путям."""

import os
import unittest

from emulator.errors import VfsError
from emulator.vfs import Vfs, format_path, load_vfs

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples", "vfs")


def example(*names):
    """Путь к файлу из каталога examples/vfs."""
    return os.path.join(EXAMPLES, *names)


class LoadTest(unittest.TestCase):
    """Проверки загрузки разных вариантов VFS."""

    def test_minimal(self):
        """Минимальная VFS: пустой корень."""
        vfs = load_vfs(example("minimal.xml"))
        self.assertEqual((vfs.name, vfs.count()), ("minimal", (0, 0)))

    def test_multi_with_base64(self):
        """Несколько файлов, двоичные данные декодируются из base64."""
        vfs = load_vfs(example("multi.xml"))
        logo = vfs.node_at(["logo.png"])
        self.assertTrue(logo.data.startswith(b"\x89PNG"))
        self.assertEqual(vfs.node_at(["empty.txt"]).size, 0)

    def test_deep(self):
        """Глубокая VFS: не менее трёх уровней вложенности."""
        vfs = load_vfs(example("deep.xml"))
        parts = "home/user/projects/emulator/src/main.py".split("/")
        self.assertFalse(vfs.node_at(parts).is_dir)

    def test_file_not_found(self):
        """Отсутствующий файл — VfsError."""
        with self.assertRaisesRegex(VfsError, "не найден"):
            load_vfs(example("no_such.xml"))

    def test_invalid_files(self):
        """Неверный XML и неверная структура — VfsError."""
        for name in ("broken", "wrong_root", "bad_base64", "duplicate"):
            with self.subTest(name=name), self.assertRaises(VfsError):
                load_vfs(example("invalid", f"{name}.xml"))


class PathTest(unittest.TestCase):
    """Проверки разрешения путей."""

    def setUp(self):
        """Загрузить глубокую VFS."""
        self.vfs = load_vfs(example("deep.xml"))

    def test_resolve_relative_and_parent(self):
        """Относительный путь с . и .. нормализуется."""
        parts = self.vfs.resolve("../etc/./app", ["home"])
        self.assertEqual(parts, ["etc", "app"])

    def test_resolve_above_root(self):
        """Переход выше корня остаётся в корне."""
        self.assertEqual(self.vfs.resolve("../../..", ["home"]), [])

    def test_resolve_home(self):
        """Символ ~ означает корень VFS."""
        self.assertEqual(self.vfs.resolve("~/etc", ["home"]), ["etc"])

    def test_missing_node(self):
        """Несуществующий путь — ошибка."""
        with self.assertRaisesRegex(VfsError, "нет такого"):
            self.vfs.node_at(["home", "nobody"])

    def test_path_through_file(self):
        """Путь через файл — ошибка «не является каталогом»."""
        with self.assertRaisesRegex(VfsError, "не является каталогом"):
            self.vfs.node_at(["etc", "hostname", "x"])

    def test_format_path(self):
        """Список имён превращается в абсолютный путь."""
        self.assertEqual(format_path([]), "/")
        self.assertEqual(format_path(["a", "b"]), "/a/b")

    def test_empty_vfs(self):
        """VFS по умолчанию пуста."""
        self.assertEqual(Vfs("x").count(), (0, 0))


if __name__ == "__main__":
    unittest.main()
