"""Парсер командной строки с поддержкой кавычек."""

from emulator.errors import ParseError

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
QUOTES = (SINGLE_QUOTE, DOUBLE_QUOTE)
ESCAPE = "\\"
ESCAPABLE_IN_DOUBLE = (DOUBLE_QUOTE, ESCAPE)


def tokenize(line):
    """Разбить строку на аргументы по правилам UNIX-оболочки.

    Пробелы разделяют аргументы. Внутри одинарных кавычек все
    символы берутся буквально. Внутри двойных кавычек обратная
    косая черта экранирует только ``"`` и ``\\``. Вне кавычек
    обратная косая черта экранирует любой символ.

    :param line: исходная строка.
    :return: список аргументов.
    :raises ParseError: незакрытая кавычка или ``\\`` в конце строки.
    """
    return _Tokenizer(line).run()


class _Tokenizer:
    """Конечный автомат посимвольного разбора строки."""

    def __init__(self, line):
        """Подготовить автомат к разбору строки ``line``."""
        self._chars = iter(line)
        self._tokens = []
        self._current = []
        self._quote = None
        self._in_token = False

    def run(self):
        """Выполнить разбор и вернуть список аргументов."""
        for char in self._chars:
            if self._quote:
                self._feed_quoted(char)
            else:
                self._feed_plain(char)
        if self._quote:
            raise ParseError(f"незакрытая кавычка {self._quote}")
        self._flush()
        return self._tokens

    def _feed_quoted(self, char):
        """Обработать символ внутри кавычек."""
        if char == self._quote:
            self._quote = None
        elif char == ESCAPE and self._quote == DOUBLE_QUOTE:
            self._current.append(self._escaped_in_double())
        else:
            self._current.append(char)

    def _feed_plain(self, char):
        """Обработать символ вне кавычек."""
        if char.isspace():
            self._flush()
            return
        self._in_token = True
        if char in QUOTES:
            self._quote = char
        elif char == ESCAPE:
            self._current.append(self._next_char())
        else:
            self._current.append(char)

    def _escaped_in_double(self):
        """Вернуть результат экранирования внутри двойных кавычек."""
        char = self._next_char()
        if char in ESCAPABLE_IN_DOUBLE:
            return char
        return ESCAPE + char

    def _next_char(self):
        """Прочитать символ после ``\\``."""
        try:
            return next(self._chars)
        except StopIteration:
            raise ParseError("строка оканчивается символом '\\'") from None

    def _flush(self):
        """Завершить текущий аргумент, если он начат."""
        if self._in_token:
            self._tokens.append("".join(self._current))
        self._current = []
        self._in_token = False
