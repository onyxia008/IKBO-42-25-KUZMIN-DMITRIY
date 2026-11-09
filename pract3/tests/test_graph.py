"""Тесты построения графа зависимостей обходом в ширину."""

import unittest

from src.graph import build_graph, invert


def fetch_from(repository, calls=None):
    """Вернуть функцию получения зависимостей из словаря-репозитория.

    :param repository: словарь {пакет: [зависимости]}.
    :param calls: список, в который записываются запрошенные пакеты.
    """
    def fetch(name, version):
        """Вернуть зависимости пакета с пустыми требованиями к версии."""
        if calls is not None:
            calls.append(name)
        return dict.fromkeys(repository.get(name, []), "")
    return fetch


DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}


class BuildGraphTest(unittest.TestCase):
    """Обход графа: транзитивность, порядок, циклы, фильтр."""

    def test_collects_transitive_dependencies(self):
        """В граф попадают зависимости зависимостей."""
        graph = build_graph("A", "1.0.0", fetch_from(DIAMOND), "")
        self.assertEqual(
            graph, {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        )

    def test_visits_packages_level_by_level(self):
        """Обход в ширину: сначала все пакеты уровня, потом следующий."""
        repository = {"A": ["B", "C"], "B": ["D"], "C": ["E"]}
        graph = build_graph("A", "1.0.0", fetch_from(repository), "")
        self.assertEqual(list(graph), ["A", "B", "C", "D", "E"])

    def test_shared_dependency_is_requested_once(self):
        """Пакет, нужный двум другим, запрашивается один раз."""
        calls = []
        build_graph("A", "1.0.0", fetch_from(DIAMOND, calls), "")
        self.assertEqual(calls, ["A", "B", "C", "D"])

    def test_cycle_keeps_edges_and_stops(self):
        """Цикл A -> B -> C -> A не зацикливает обход, ребро остаётся."""
        calls = []
        repository = {"A": ["B"], "B": ["C"], "C": ["A"]}
        graph = build_graph("A", "1.0.0", fetch_from(repository, calls), "")
        self.assertEqual(graph, {"A": ["B"], "B": ["C"], "C": ["A"]})
        self.assertEqual(calls, ["A", "B", "C"])

    def test_package_depending_on_itself(self):
        """Зависимость пакета от самого себя не зацикливает обход."""
        graph = build_graph("A", "1.0.0", fetch_from({"A": ["A"]}), "")
        self.assertEqual(graph, {"A": ["A"]})

    def test_filter_skips_packages_and_their_branches(self):
        """Пакеты с подстрокой в имени и то, что нужно только им, пропадают."""
        repository = {"A": ["B", "XC"], "B": ["XD"], "XC": ["E"]}
        graph = build_graph("A", "1.0.0", fetch_from(repository), "X")
        self.assertEqual(graph, {"A": ["B"], "B": []})

    def test_empty_filter_skips_nothing(self):
        """Пустая подстрока фильтра не отбрасывает ни одного пакета."""
        graph = build_graph("A", "1.0.0", fetch_from(DIAMOND), "")
        self.assertEqual(set(graph), {"A", "B", "C", "D"})

    def test_versions_come_from_parent_requirements(self):
        """Корень запрашивается с версией из настроек, остальные — с
        требованием, записанным у родителя."""
        requests = []

        def fetch(name, version):
            """Записать запрос и вернуть зависимости с требованиями."""
            requests.append((name, version))
            return {"B": "^2.0.0"} if name == "A" else {}

        build_graph("A", "1.0.0", fetch, "")
        self.assertEqual(requests, [("A", "1.0.0"), ("B", "^2.0.0")])

    def test_long_chain_does_not_hit_recursion_limit(self):
        """Цепочка из 3000 пакетов строится: обход идёт без рекурсии."""
        names = [f"P{i}" for i in range(3000)]
        repository = {a: [b] for a, b in zip(names, names[1:])}
        graph = build_graph("P0", "1.0.0", fetch_from(repository), "")
        self.assertEqual(len(graph), 3000)


class InvertTest(unittest.TestCase):
    """Переворот рёбер графа для обратных зависимостей."""

    def test_lists_who_depends_on_each_package(self):
        """Для каждого пакета — пакеты, которые от него зависят."""
        self.assertEqual(
            invert({"A": ["B", "C"], "B": ["C"], "C": []}),
            {"A": [], "B": ["A"], "C": ["A", "B"]},
        )

    def test_package_only_mentioned_as_dependency(self):
        """Пакет без своей записи тоже попадает в перевёрнутый граф."""
        self.assertEqual(invert({"A": ["B"]}), {"A": [], "B": ["A"]})


if __name__ == "__main__":
    unittest.main()
