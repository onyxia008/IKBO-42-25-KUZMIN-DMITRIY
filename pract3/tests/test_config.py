"""Тесты чтения и проверки конфигурации."""

import glob
import json
import os
import tempfile
import unittest

from src.config import ConfigError, load_config, validate

GOOD = {
    "package": "express",
    "repository": "https://registry.npmjs.org",
    "test_mode": False,
    "version": "4.18.2",
    "ascii_tree": True,
    "filter": "test",
}

BAD_VALUES = [
    ("package", 5),
    ("package", ""),
    ("package", "Bad Name"),
    ("repository", 5),
    ("repository", ""),
    ("repository", "registry.npmjs.org"),
    ("test_mode", "yes"),
    ("test_mode", 1),
    ("version", 4),
    ("version", ""),
    ("version", "1.2"),
    ("version", "^1.2.3"),
    ("version", "latest"),
    ("ascii_tree", "yes"),
    ("ascii_tree", 1),
    ("filter", 5),
    ("filter", None),
]


class ValidateTest(unittest.TestCase):
    """Проверка значений параметров."""

    def test_accepts_correct_values(self):
        """Верная конфигурация возвращается, reverse по умолчанию false."""
        self.assertEqual(validate(GOOD), {**GOOD, "reverse": False})

    def test_reverse_must_be_boolean(self):
        """Необязательный параметр reverse — true или false."""
        with self.assertRaisesRegex(ConfigError, "^reverse:"):
            validate({**GOOD, "reverse": "yes"})

    def test_reverse_needs_test_mode(self):
        """Обратные зависимости ищутся только в тестовом репозитории."""
        with self.assertRaisesRegex(ConfigError, "^reverse:"):
            validate({**GOOD, "reverse": True})

    def test_accepts_scoped_package(self):
        """Имя вида @scope/name допустимо для npm."""
        config = validate({**GOOD, "package": "@babel/core"})
        self.assertEqual(config["package"], "@babel/core")

    def test_accepts_prerelease_version(self):
        """Версия с предрелизной меткой допустима."""
        config = validate({**GOOD, "version": "1.0.0-beta.1"})
        self.assertEqual(config["version"], "1.0.0-beta.1")

    def test_bad_value_is_reported_by_parameter_name(self):
        """Ошибка называет параметр с неверным значением."""
        for key, value in BAD_VALUES:
            with self.subTest(key=key, value=value):
                with self.assertRaisesRegex(ConfigError, f"^{key}:"):
                    validate({**GOOD, key: value})

    def test_missing_parameter_is_reported_by_name(self):
        """Ошибка называет отсутствующий параметр."""
        for key in GOOD:
            with self.subTest(key=key):
                data = {k: v for k, v in GOOD.items() if k != key}
                with self.assertRaisesRegex(ConfigError, f"^{key}:"):
                    validate(data)


class TestRepositoryModeTest(unittest.TestCase):
    """Проверка параметров в режиме тестового репозитория."""

    def setUp(self):
        """Подготовить верные параметры режима тестирования."""
        self.data = {
            **GOOD,
            "test_mode": True,
            "package": "A",
            "repository": __file__,
        }

    def test_accepts_existing_file_and_uppercase_name(self):
        """Существующий файл и имя из больших букв допустимы."""
        self.assertEqual(validate(self.data), {**self.data, "reverse": False})

    def test_accepts_reverse_mode(self):
        """В тестовом режиме можно включить обратные зависимости."""
        self.assertIs(validate({**self.data, "reverse": True})["reverse"], True)

    def test_rejects_missing_file(self):
        """Путь к несуществующему файлу отклоняется."""
        self.data["repository"] = "no/such/file.txt"
        with self.assertRaisesRegex(ConfigError, "^repository:"):
            validate(self.data)

    def test_rejects_lowercase_name(self):
        """Имя не из больших латинских букв отклоняется."""
        self.data["package"] = "express"
        with self.assertRaisesRegex(ConfigError, "^package:"):
            validate(self.data)


class LoadConfigTest(unittest.TestCase):
    """Чтение файла конфигурации."""

    def setUp(self):
        """Подготовить путь к временному файлу."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, "config.json")

    def write(self, text):
        """Записать текст во временный файл конфигурации."""
        with open(self.path, "w", encoding="utf-8") as file:
            file.write(text)

    def test_reads_parameters_from_file(self):
        """Параметры читаются из JSON-файла."""
        self.write(json.dumps(GOOD))
        self.assertEqual(load_config(self.path), {**GOOD, "reverse": False})

    def test_missing_file_is_config_error(self):
        """Отсутствие файла — ошибка конфигурации."""
        with self.assertRaises(ConfigError):
            load_config(self.path)

    def test_broken_json_is_config_error(self):
        """Некорректный JSON — ошибка конфигурации."""
        self.write("{")
        with self.assertRaises(ConfigError):
            load_config(self.path)

    def test_root_must_be_object(self):
        """Корень JSON-документа должен быть объектом."""
        self.write("[1, 2]")
        with self.assertRaises(ConfigError):
            load_config(self.path)

    def test_every_demo_example_is_rejected(self):
        """Каждый файл из examples/errors вызывает ошибку."""
        paths = glob.glob("examples/errors/*.json")
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path):
                with self.assertRaises(ConfigError):
                    load_config(path)


if __name__ == "__main__":
    unittest.main()
