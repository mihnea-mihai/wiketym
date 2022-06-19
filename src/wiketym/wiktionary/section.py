from __future__ import annotations

from functools import cached_property
from typing import Iterator

import src.wiketym.wiktionary as wkt
from cacheable_iter import iter_cache

from ..helpers import filter, get


class Section:
    """
    Interface for the section of a specific page.
    """

    def __init__(
        self,
        page: wkt.Page = wkt.Page("DUMMY"),
        toclevel: int = 0,
        line: str = "",
        number: str = "",
        index: str = "0",
        byteoffset: int = 0,
        **_,
    ) -> None:
        self.page = page
        """The `Page` this `Section` belongs to."""

        self.line: str = line
        """The title of the section."""

        self.toclevel: int = toclevel
        """Nesting level under the page."""

        self.number: str = number
        """Full nesting levels (ex.: 2.3.4)"""

        self.byteoffset: int = byteoffset
        """String offset in the page wikitext."""

        self.index: int = int(index)
        """Index of the section within the page."""

    @iter_cache
    def __iter__(self) -> Iterator[Section]:
        return filter(
            self.page.sections,
            number=lambda c: c.startswith(self.number + "."),
        )

    def __getitem__(self, line) -> Section:
        return self.get(line=line)

    def __repr__(self) -> str:
        return f"Page({self.page.title}).Section({self.number},{self.line})"

    def __bool__(self) -> bool:
        return self.wikitext != ""

    def get(self, **kwargs):
        return get(self, **kwargs, __default=Section())

    @cached_property
    def wikitext(self):
        next_section: Section = get(
            self.page.sections,
            index=lambda x: x > self.index,
            toclevel=lambda x: x == self.toclevel,
        )
        return self.page.wikitext[
            self.byteoffset : getattr(next_section, "byteoffset", None)
        ]

    @cached_property
    def strict_wikitext(self):
        next_section: Section = get(
            self.page.sections,
            index=lambda x: x > self.index,
        )
        return self.page.wikitext[
            self.byteoffset : getattr(next_section, "byteoffset", None)
        ]
