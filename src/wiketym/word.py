from __future__ import annotations

import textwrap

import re
import unicodedata
from functools import cache, cached_property

from .helpers import get, load_json
from .wiktionary import Language, Page, Section, Template


class Word:
    MEANING_NAMES = {
        "Noun",
        "Verb",
        "Adjective",
        "Adverb",
        "Root",
        "Proper noun",
        "Suffix",
        "Prefix",
        "Root",
    }

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
        if self.redirects_to() or self.equivalent_to() or self.accents_stripped_from():
            self.entry.wikitext = " "

        self.meaning_wikitext: str = self.entry.get(
            line=self.is_meaning_section
        ).wikitext

        self._template_meaning = ''
        self.translit = ''

    def redirects_to(self) -> str | None:
        if match := re.match(r"#REDIRECT \[\[(.+)\]\]", self.page.wikitext):
            lemma = match[1]
            if "/" in lemma:
                lemma = "*" + lemma.split("/", maxsplit=1)[1]
            return lemma

    def equivalent_to(self) -> Word | None:
        if self.lang.name != self.lang.page_name:
            for lang_code, data in Language.lang_data.items():
                if data["name"] == self.lang.page_name:
                    return Word(self.lemma, lang_code)

    def accents_stripped_from(self) -> Word | None:
        if self.lang.diacr:
            if self.stripped_lemma != self.lemma:
                return Word(self.stripped_lemma, self.lang.code)

    @property
    def stripped_lemma(self):
        lemma = self.lemma
        nkfd_form = unicodedata.normalize("NFKD", lemma)
        if self.lang.page_name != "Ancient Greek":
            lemma = "".join(c for c in nkfd_form if not unicodedata.combining(c))
        else:  # Special case for Greek incomplete stripping
            lemma = "".join(
                c for c in nkfd_form if not unicodedata.name(c) == "COMBINING MACRON"
            )
        # Normalise back to ensure equality
        lemma = unicodedata.normalize("NFKC", lemma)
        return lemma

    @property
    def page_title(self):
        """
        Infer the title of the Wiktionary page providing information
        about this lemma and language code by:
        - stripping accents when necessary according to the language
        - applying the page naming conventions for reconstrcuted lemmas
        """
        # Change page title for reconstructed lemmas
        return self.lemma.replace("*", f"Reconstruction:{self.lang.page_name}/")

    def valid_ascendant(self, word: Word) -> bool:
        if "==Suffix==" in self.meaning_wikitext:
            if "==Suffix==" not in word.meaning_wikitext:
                return False
        return True

    @cached_property
    def links(self) -> dict[str, list[Word]]:
        links: dict[str, list[Word]] = load_json("src/wiketym/data/link_types.json")

        for tpl in self.templates:
            if tpl.type in Template.TO_LINK_MAPPING:
                for term in tpl.terms:
                    if self.valid_ascendant(w := Word(term.lemma, term.lang_code)):
                        w.translit = term.tr
                        w._template_meaning = term.t
                        links[Template.TO_LINK_MAPPING[tpl.type]].append(w)

        if lemma := self.redirects_to():
            links["redirects_to"] = [Word(lemma, self.lang.code)]
        if word := self.equivalent_to():
            links["redirects_to"] = [word]
        if word := self.accents_stripped_from():
            links["redirects_to"] = [word]

        if infl_match := re.search(
            r"""
            \{\{
                (alternative\ form\ of
                |
                inflection\ of
                |
                alt\ form)
                \|
                (?P<lang>[^|]*)
                \|
                (?P<lemma>[^|}]*)
                .*
            \}\}
            """,
            self.meaning_wikitext,
            flags=re.VERBOSE,
        ):
            links["inflection_of"] = [Word(infl_match["lemma"], self.lang.code)]

        return links

    NODE_STYLES = load_json("src/wiketym/data/styles.json")["nodes"]

    @property
    def node(self):
        text = []
        text.append(f'<font point-size="10">{self.lang.name}</font>')
        if self.lemma:
            text.append(f'<b><font point-size="16">{self.lemma}</font></b>')
        if self.translit:
            text.append(f'<b><font point-size="10">{self.translit}</font></b>')
        if self.meaning:
            text.append(
                f"""<font point-size="10"><i>{"<br/>".join(textwrap.wrap(self.meaning, 30))}</i></font>"""
            )


        node = {}
        node["label"] = "<" + "<br/>".join(text) + ">"

        node[
            "URL"
        ] = f'"https://en.wiktionary.org/wiki/{self.page_title}#{self.lang.page_name.replace(" ", "_")}"'

        node["margin"] = "0.05"

        if not self:
            node |= self.NODE_STYLES["invalid"]

        if self.level == 0:
            node |= self.NODE_STYLES["start"]

        node["shape"] = "none"

        return node

    def __bool__(self) -> bool:
        return bool(self.entry)

    def __repr__(self) -> str:
        return f"{self.lemma} ({self.lang.name})"

    @classmethod
    def is_meaning_section(cls, line: str) -> bool:
        for title in cls.MEANING_NAMES:
            if line.startswith(title):
                return True

    @property
    def meaning(self):
        if self.lang.code == "en":
            return ""
        if self._template_meaning:
            return self._template_meaning

        if match := re.search(r"\# (.*)", self.meaning_wikitext):
            meaning = match[1]
        else:
            meaning = ""
        meaning = re.sub(r"\{\{l\|\w+?\|([^|]+)\}\} ?", lambda m: m[1], meaning)
        meaning = re.sub(r"\{\{.+?\}\} ?", "", meaning)
        meaning = re.sub(r"<.+?> ?", "", meaning)
        meaning = meaning.replace(":", "")
        meaning = re.sub(r"\[\[.*?([^|]+?)\]\]", lambda m: m[1], meaning)
        return meaning
