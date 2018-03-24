# -*- coding: utf-8 -*-
"""Custom Completers for better cli selections."""
import datetime

from fuzzyfinder import fuzzyfinder
from prompt_toolkit.completion import Completer, Completion


class FuzzyCompleter(Completer):
    """Fuzzy Completer Alpha Sorted."""

    def __init__(self, words):
        """Initialize."""
        self.words = words

    def get_completions(self, document, complete_event):
        """Use fuzzyfinder for completions."""
        word_before_cursor = document.text_before_cursor
        words = fuzzyfinder(word_before_cursor, self.words)
        for x in words:
            yield Completion(x, -len(word_before_cursor))


class DateFuzzyCompleter(Completer):
    """Fuzzy Completer For Dates."""

    def get_completions(self, document, complete_event):
        """Use fuzzyfinder for date completions.

        The fuzzyfind auto sorts by alpha so this is to show dates relative to
        the current date instead of by day of week.
        """
        base = datetime.datetime.today()
        date_format = '%a, %Y-%m-%d'
        date_list = [(base - datetime.timedelta(days=x)).strftime(date_format)
                     for x in range(0, 30)]
        word_before_cursor = document.text_before_cursor
        words = fuzzyfinder(word_before_cursor, date_list)

        def sort_by_date(date_str: str):
            return datetime.datetime.strptime(date_str, date_format)

        # Re-sort by date rather than day name
        words = sorted(words, key=sort_by_date, reverse=True)
        for x in words:
            yield Completion(x, -len(word_before_cursor))


class WeekFuzzyCompleter(Completer):
    """Fuzzy Completer For Weeks."""

    def get_completions(self, document, complete_event):
        """Use fuzzyfinder for week completions."""
        def datetime_to_week_str(dt: datetime.datetime):
            """Convert a datetime to weekstring.

            datetime.datetime(2018, 2, 26, 0, 0) => '2018-02-26 to 2018-03-04'
            """
            if dt.weekday() != 0:
                monday_dt = dt - datetime.timedelta(days=dt.weekday())
            else:
                monday_dt = dt
            sunday_dt = monday_dt + datetime.timedelta(days=6)
            return '{} to {}'.format(
                monday_dt.strftime('%Y-%m-%d'), sunday_dt.strftime('%Y-%m-%d'))

        base = datetime.datetime.today()
        week_list = [datetime_to_week_str(base - datetime.timedelta(weeks=x))
                     for x in range(0, 5)]
        word_before_cursor = document.text_before_cursor
        words = fuzzyfinder(word_before_cursor, week_list)
        words = sorted(words, reverse=True)
        for x in words:
            yield Completion(x, -len(word_before_cursor))
