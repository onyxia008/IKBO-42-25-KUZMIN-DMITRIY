"""Форматирование календаря для команды cal."""

import calendar
import datetime

from emulator.errors import CommandError

MIN_MONTH = 1
MAX_MONTH = 12
MIN_YEAR = 1
MAX_YEAR = 9999

MONTH_NAMES = (
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
)
WEEKDAY_NAMES = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


class RuCalendar(calendar.TextCalendar):
    """Текстовый календарь с русскими названиями, неделя с понедельника."""

    def __init__(self):
        """Создать календарь с первым днём недели — понедельником."""
        super().__init__(firstweekday=calendar.MONDAY)

    def formatweekday(self, day, width):
        """Вернуть название дня недели, выровненное по ширине."""
        return WEEKDAY_NAMES[day][:width].center(width)

    def formatmonthname(self, theyear, themonth, width, withyear=True):
        """Вернуть заголовок месяца, выровненный по центру."""
        title = MONTH_NAMES[themonth]
        if withyear:
            title = f"{title} {theyear}"
        return title.center(width)


def month_text(year, month):
    """Календарь на месяц ``month`` года ``year``."""
    return RuCalendar().formatmonth(year, month).rstrip("\n")


def year_text(year):
    """Календарь на весь год ``year``."""
    return RuCalendar().formatyear(year).rstrip("\n")


def current_month_text(today=None):
    """Календарь на текущий месяц."""
    today = today or datetime.date.today()
    return month_text(today.year, today.month)


def parse_month(text):
    """Разобрать номер месяца (1–12)."""
    return _parse_in_range(text, MIN_MONTH, MAX_MONTH, "месяц")


def parse_year(text):
    """Разобрать год (1–9999)."""
    return _parse_in_range(text, MIN_YEAR, MAX_YEAR, "год")


def _parse_in_range(text, low, high, what):
    """Преобразовать строку в целое из диапазона [low, high]."""
    try:
        value = int(text)
    except ValueError:
        raise CommandError(f"cal: {text}: {what} должен быть числом") from None
    if not low <= value <= high:
        raise CommandError(
            f"cal: {value}: {what} должен быть от {low} до {high}"
        )
    return value
