from __future__ import annotations

import re
import unicodedata
from functools import cache, cached_property

from .helpers import load_json
from .wiktionary import Language, Page, Section, Template


class Word:
    @cache
    def __new__(cls, lemma, lang_code):
        return object.__new__(cls)

    def __init__(self, lemma: str, lang_code: str) -> None:

        self.lemma: str = lemma
        """Dictionary lookup form of the word."""

        self.lang: Language = Language(lang_code)
        """Object holding metadata for the language of the word."""

        self.page: Page = Page(self.page_title)
        """Wiktionary Page of this word."""

        self.entry: Section = self.page[self.lang]
        """Wikipedia Page Section corresponding to this word."""

        self.templates: list[Template] = Template.parse_all(
            self.entry.get(line=lambda x: x.startswith("Etymology")).strict_wikitext
        )
        """List of all parsed templates in the Etymology section wikitext."""

        self.level = None
        """Distance from this word to one of the original words in the query."""
        # self.links: dict[str, list[Word]] = load_json(
        #     "src/wiketym/data/link_types.json"
        # )
        # """Dictionary of link types to this word."""

        # self._ensure_redirect()

        # self._populate_links(Template.Type.ALL)

    @property
    def page_title(self):
        """
        Infer the title of the Wiktionary page providing information
        about this lemma and language code by:
        - stripping accents when necessary according to the language
        - applying the page naming conventions for reconstrcuted lemmas
        """
        title = self.lemma
        # Strip accents according to language
        if self.lang.diacr:
            nkfd_form = unicodedata.normalize("NFKD", title)
            if not self.lang.code == "grc":
                title = "".join(c for c in nkfd_form if not unicodedata.combining(c))
            else:  # Special case for Greek incomplete stripping
                title = "".join(
                    c
                    for c in nkfd_form
                    if not unicodedata.name(c) == "COMBINING MACRON"
                )
                # Normalise back to ensure equality
                title = unicodedata.normalize("NFKC", title)
        self.lemma = title
        # Change page title for reconstructed lemmas
        title = title.replace("*", f"Reconstruction:{self.lang.page_name}/")

        return title

    @cached_property
    def links(self) -> dict[str, list[Word]]:
        links: dict[str, list[Word]] = load_json("src/wiketym/data/link_types.json")

        for tpl in self.templates:
            if tpl.type in Template.TO_LINK_MAPPING:
                for term in tpl.terms:
                    links[Template.TO_LINK_MAPPING[tpl.type]].append(
                        Word(term.lemma, term.lang_code)
                    )

        if match := re.match(r"#REDIRECT \[\[(.+)\]\]", self.page.wikitext):
            lemma = match[1]
            if "/" in lemma:
                lemma = "*" + lemma.split("/", maxsplit=1)[1]
            links["redirects_to"] = [Word(lemma, self.lang.code)]

        return links

    NODE_STYLES = load_json("src/wiketym/data/styles.json")["nodes"]

    @property
    def node(self):
        text = []
        text.append(f'<font point-size="10">{self.lang.name}</font>')
        if self.lemma:
            text.append(f"<b>{self.lemma}</b>")

        node = {}
        node["label"] = "<" + "<br/>".join(text) + ">"

        if not self:
            node |= self.NODE_STYLES["invalid"]

        if self.level == 0:
            node |= self.NODE_STYLES["start"]

        return node

    def __bool__(self) -> bool:
        return bool(self.entry)

    def __repr__(self) -> str:
        return f"{self.lemma} ({self.lang.name})"
