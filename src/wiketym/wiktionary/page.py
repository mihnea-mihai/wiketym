from __future__ import annotations

from functools import cache
from typing import Iterator

import src.wiketym.wiktionary as wkt
from cacheable_iter import iter_cache

from ..helpers import filter, get
from . import api
from .language import Language


class Page:
    """
    Interface to a Wiktionary Page.

    Get a `Page` guaranteed to be unique within this run,
    otherwise create and initialise one.
    """

    @cache  # this ensures no duplicates
    def __new__(cls, title):
        return object.__new__(cls)

    def __init__(self, title: str) -> None:
        self.title = title
        """Title of the page."""
        json = api.get_page(title)

        self.wikitext: str = json.get("wikitext", {}).get("*", "")
        """Full wikitext."""

        self.sections = [wkt.Section(self, **obj) for obj in json.get("sections", [])]
        """`Section` objects for the current page."""

    @iter_cache
    def __iter__(self) -> Iterator[wkt.Section]:
        return filter(self.sections, toclevel=1)

    def __getitem__(self, lang: Language | str) -> wkt.Section:
        if isinstance(lang, Language):
            return get(self, line=lang.name, __default=wkt.Section())
        else:
            return get(self, line=Language(lang).name, __default=wkt.Section())

    def __repr__(self) -> str:
        return f"Page({self.title})"

    def __bool__(self) -> bool:
        return self.wikitext != ""
