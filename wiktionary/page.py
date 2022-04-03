from __future__ import annotations
import json
from functools import cache, cached_property
# from wiktionary import Template
import requests
import re


class Page:
    """
    Interface to a Wiktionary Page.
    """

    def __init__(self, title: str) -> None:        
        self.title = title
        """Title of the page."""
        self.parsed = self._API_call()
        """API call result."""
        self.wikitext: str = self.parsed.get('wikitext', {}).get('*', '')
        """Full wikitext."""

    @cache
    @staticmethod
    def get(title: str):
        """
        Get a `Page` guaranteed to be unique within this run,
        otherwise create and initialise one.
        """
        return Page(title)

    @classmethod
    def _get_cache(cls):
        with open('data/cache.json', encoding='utf-8') as file:
            cls._cache = json.load(file)

    def _API_call(self) -> dict:
        """
        Return API response either from cache or from actual API call.
        """
        try:
            self._cache
        except AttributeError:
            self._get_cache()

        url = 'https://en.wiktionary.org/w/api.php'

        if self.title not in self._cache:  # Add to cache if missing
            params = {
                'action': 'parse',
                'format': 'json',
                'page': self.title,
                'prop': 'sections|wikitext'
            }
            self._cache[self.title] = requests.get(url, params).json()
            with open('data/cache.json', 'w', encoding='utf-8') as file:
                json.dump(self._cache, file, ensure_ascii=False)
        # Return from cache anyway
        return self._cache[self.title].get('parse', {})


    @cached_property
    def sections(self):
        """
        Cached list of `Section` objects for the current page.
        """
        return [
            Section(self, obj, wikitext)
            for obj, wikitext in zip(
                self.parsed.get('sections', []),
                re.split(r'={2,}.+?={2,}', self.wikitext)[1:]
            )
        ]

    def get_lang_section(self, lang_name: str) -> Section | None:
        """
        Fetch the specified language section of the page.
        If missing, return `None`.
        """
        for section in self.sections:
            if section.level == 2 and section.line == lang_name:
                return section


    def __repr__(self) -> str:
        """
        >>> Page.get('cat')
        Page(cat)
        """
        return f'Page({self.title})'



class Section:
    """
    Interface for the section of a specific page.
    """

    def __init__(self, page: Page, obj, wikitext: str) -> None:
        self.page = page
        """The `Page` this `Section` belongs to."""

        self.line: str = obj['line']
        """The title of the section."""

        self.level = int(obj['level'])
        """Nesting level under the page (starts at 2)."""

        self.number: str = obj['number']
        """Full nesting levels (ex.: 2.3.4)"""

        self.wikitext = wikitext.strip()
        """Full wikitext of the section (not including subsections)"""

    @cached_property
    def subsections(self) -> list[Section]:
        """
        List of sections under the current section.
        """
        return [
            section for section in self.page.sections
            if section.number.startswith(self.number+'.')
        ]

    # @cached_property
    # def templates(self) -> list[Template]:
    #     return [Template(text)
    #             for text in Template.extract_all_raw(self.wikitext)]

    def get_subsection(self, subsection_line):
        for subsection in self.subsections:
            if subsection.line == subsection_line:
                return subsection

    def __repr__(self) -> str:
        return f'Page({self.page.title}).Section({self.number},{self.line})'
