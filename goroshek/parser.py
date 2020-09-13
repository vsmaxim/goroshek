import datetime
from typing import Iterable, NamedTuple, Optional

from natasha.grammars.date import Date, DAY, MONTH, MONTH_NAME, YEAR, YEAR_SHORT, YEAR_WORD
from natasha.grammars.name import NAME
from yargy import or_, Parser, rule

from goroshek.config import STUDENTS

DATE = or_(
    # TODO: Maybe this is not necessary, and will produce Type 2 errors
    rule(
        DAY,
        '.',
        MONTH,
    ),
    rule(
        DAY,
        '.',
        MONTH,
        '.',
        or_(
            YEAR,
            YEAR_SHORT
        ),
        YEAR_WORD.optional()
    ),
    rule(
        YEAR,
        YEAR_WORD
    ),
    rule(
        DAY,
        MONTH_NAME
    ),
    rule(
        MONTH_NAME,
        YEAR,
        YEAR_WORD.optional()
    ),
    rule(
        DAY,
        MONTH_NAME,
        YEAR,
        YEAR_WORD.optional()
    ),
).interpretation(
    Date
)


NAME_PARSER = Parser(NAME)
DATE_PARSER = Parser(DATE)


class Person(NamedTuple):
    first_name: str
    middle_name: str
    last_name: str

    @property
    def is_full(self):
        return self.first_name and self.last_name

    @property
    def student(self) -> Optional[dict]:
        for student in STUDENTS:
            fn_not_matched = self.first_name and student["first_name"] != self.first_name
            ln_not_matched = self.last_name and student["last_name"] != self.last_name
            mn_not_matched = self.middle_name and student["middle_name"] != self.middle_name

            if fn_not_matched or ln_not_matched or mn_not_matched:
                continue

            return student

    @property
    def telegram_handle(self) -> Optional[str]:
        return self.student and self.student.get("telegram") or None

    @property
    def chat_id(self) -> Optional[str]:
        return self.student and self.student.get("chat_id") or None

    def __str__(self) -> str:
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p.capitalize() for p in parts if p)


def parse_dates(text: str) -> Iterable[datetime.date]:
    """
    Parse dates from text and return datetime.date.
    If parsed date is less than today, then return this date in next year.

    :param text: text to parse from
    :return: iterator of dates in text
    """
    for match in DATE_PARSER.findall(text):
        date_fact = match.fact
        today = datetime.date.today()
        extracted_date = datetime.date(date_fact.year or today.year, date_fact.month, date_fact.day)

        if today > extracted_date:
            extracted_date.replace(year=extracted_date.year + 1)

        yield extracted_date


def parse_persons(text: str) -> Iterable[Person]:
    """
    Parse persons from text and return iterator.
    TODO: Add normalization of names (Гриша -> Григорий)

    :param text: text to parse from
    :return: iterator of persons in text
    """
    for match in NAME_PARSER.findall(text):
        name_fact = match.fact
        yield Person(name_fact.first, name_fact.middle, name_fact.last)
