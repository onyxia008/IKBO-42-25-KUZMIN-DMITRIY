"""Визуализация графа: описание на языке D2, картинка и ASCII-дерево."""

import shutil
import subprocess
import webbrowser
from pathlib import Path


class VisualError(Exception):
    """Ошибка при построении картинки графа."""


def to_d2(graph, root):
    """Описать граф на языке диаграмм D2.

    Корень — отдельная фигура (чтобы пакет без зависимостей тоже был
    на картинке), каждая зависимость — стрелка "пакет" -> "зависимость".
    Имена в кавычках, потому что в именах npm бывают символы @ и /.

    :param graph: словарь {пакет: [его зависимости]}.
    :param root: анализируемый пакет.
    :return: текст на языке D2.
    """
    lines = [f'"{root}"']
    for name, dependencies in graph.items():
        lines += [f'"{name}" -> "{dependency}"' for dependency in dependencies]
    return "\n".join(lines) + "\n"


def show_image(d2_text, name):
    """Сохранить описание D2, нарисовать по нему картинку и открыть её.

    Картинку рисует программа d2 (https://d2lang.com), а показывает
    программа, которая в системе открывает SVG-файлы (обычно браузер).

    :param d2_text: описание графа на языке D2.
    :param name: имя пакета для имён файлов graph-<имя>.d2 и .svg.
    :return: имя файла с картинкой.
    :raises VisualError: программа d2 не найдена или не сработала.
    """
    if shutil.which("d2") is None:
        raise VisualError(
            "программа d2 не найдена, установите её: https://d2lang.com"
        )
    stem = "graph-" + name.replace("/", "_")
    source, image = f"{stem}.d2", f"{stem}.svg"
    Path(source).write_text(d2_text, encoding="utf-8")
    try:
        subprocess.run(["d2", source, image], check=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        reason = error.stderr.decode(errors="replace").strip()
        raise VisualError(f"d2 не нарисовал картинку: {reason}") from error
    webbrowser.open(Path(image).resolve().as_uri())
    return image


def ascii_tree(graph, root):
    """Нарисовать зависимости в виде ASCII-дерева.

    Пакет, который уже показан выше, второй раз не раскрывается и
    помечается (*): так дерево конечное даже при циклах.

    :param graph: словарь {пакет: [его зависимости]}.
    :param root: пакет в корне дерева.
    :return: список строк дерева.
    """
    lines = [root]
    _add_branches(graph, root, "", {root}, lines)
    return lines


def _add_branches(graph, name, prefix, shown, lines):
    """Дописать в дерево ветки зависимостей пакета name."""
    dependencies = graph.get(name, [])
    for dependency in dependencies:
        last = dependency == dependencies[-1]
        branch, indent = ("└── ", "    ") if last else ("├── ", "│   ")
        if dependency in shown:
            lines.append(f"{prefix}{branch}{dependency} (*)")
            continue
        shown.add(dependency)
        lines.append(f"{prefix}{branch}{dependency}")
        _add_branches(graph, dependency, prefix + indent, shown, lines)
