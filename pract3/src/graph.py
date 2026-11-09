"""Построение графа зависимостей обходом в ширину (BFS) без рекурсии."""

from collections import deque


def build_graph(root, version, fetch, exclude):
    """Построить граф зависимостей пакета с учётом транзитивности.

    Очередь queue хранит пакеты, которые ещё нужно разобрать, а
    множество seen — пакеты, которые уже попали в очередь. Поэтому
    каждый пакет запрашивается один раз, и циклы не зацикливают обход.

    :param root: имя анализируемого пакета.
    :param version: версия анализируемого пакета.
    :param fetch: функция (имя, версия) -> {зависимость: требование}.
    :param exclude: подстрока; пакеты с ней в имени не учитываются.
    :return: словарь {пакет: [его зависимости]} в порядке обхода.
    """
    graph = {}
    queue = deque([(root, version)])
    seen = {root}
    while queue:
        name, wanted = queue.popleft()
        dependencies = {
            dependency: requirement
            for dependency, requirement in fetch(name, wanted).items()
            if not (exclude and exclude in dependency)
        }
        graph[name] = list(dependencies)
        for dependency, requirement in dependencies.items():
            if dependency not in seen:
                seen.add(dependency)
                queue.append((dependency, requirement))
    return graph


def invert(graph):
    """Перевернуть рёбра графа: для пакета — кто от него зависит.

    :param graph: словарь {пакет: [его зависимости]}.
    :return: словарь {пакет: [пакеты, которые от него зависят]}.
    """
    reverse = {name: [] for name in graph}
    for name, dependencies in graph.items():
        for dependency in dependencies:
            reverse.setdefault(dependency, []).append(name)
    return reverse
