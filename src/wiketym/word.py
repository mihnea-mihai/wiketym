from __future__ import annotations

import re
import textwrap
import unicodedata
from functools import cache, cached_property


from .helpers import get, load_json, nlp
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

        self.meaning_section: Section = self.entry.get(line=self.is_meaning_section)

        self.etymology_section: Section = self.entry.get(
            line=lambda x: x.startswith("Etymology")
        )

        # self.templates: list[Template] = Template.parse_all(
        #     self.entry.get(line=lambda x: x.startswith("Etymology")).strict_wikitext
        # )
        # """List of all parsed templates in the Etymology section wikitext."""

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

        # self.meaning_wikitext: str = self.entry.get(
        #     line=self.is_meaning_section
        # ).wikitext

        self._template_meaning = ""
        self._reference_meaning = ""
        self.translit = ""

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
                c
                for c in nkfd_form
                if unicodedata.name(c) not in {"COMBINING MACRON", "COMBINING BREVE"}
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

    @property
    def meaning_wikitext(self):
        return self.meaning_section.wikitext

    def valid_ascendant(self, word: Word) -> bool:
        if "==Suffix==" in self.meaning_wikitext:
            if "==Suffix==" not in word.meaning_wikitext:
                return False
        return True

    @cached_property
    def links(self) -> dict[str, list[Word]]:
        links: dict[str, list[Word]] = load_json("src/wiketym/data/link_types.json")

        for tpl in Template.parse_all(self.etymology_section.strict_wikitext):
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
        if word := self.inflection_of():
            links["inflection_of"] = [word]

        return links

    NODE_STYLES = load_json("src/wiketym/data/styles.json")["nodes"]

    def inflection_of(self):
        if infl_match := re.search(
            r"""
            \{\{
                (alternative\ form\ of
                |
                inflection\ of
                |
                alt\ form
                |
                alternative\ spelling\ of)
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
            return Word(infl_match["lemma"], self.lang.code)

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

    @staticmethod
    def extract_meaning(wikitext):
        if not (match := re.search(r"\# (.*)", wikitext)):
            return
        meaning = match[1]
        meaning = re.sub(r"\{\{l\|\w+?\|([^|]+)\}\} ?", lambda m: m[1], meaning)
        meaning = re.sub(r"\{\{.+?\}\} ?", "", meaning)
        meaning = re.sub(r"<.+?> ?", "", meaning)
        meaning = meaning.replace(":", "")
        meaning = re.sub(r"\[\[.*?([^|]+?)\]\]", lambda m: m[1], meaning)
        return meaning

    @property
    def meaning(self):
        if self.lang.code == "en":
            return ""
        if self._template_meaning:
            return self._template_meaning

        return self.extract_meaning(self.meaning_wikitext)

    def all_meanings(self) -> list[Section]:
        return [
            meaning_section
            for meaning_section in self.entry.filter(line=self.is_meaning_section)
        ]

    def disambiguate(self, reference: Word):
        print("inferring", self, "from", reference)
        if len(self.all_meanings()) < 2:
            print("Nothing to choose from")
            if (
                self.redirects_to()
                or self.equivalent_to()
                or self.accents_stripped_from()
                or self.inflection_of()
            ):
                self._reference_meaning = (
                    reference.meaning or reference._reference_meaning
                )
            return
        ref = None
        print(self._template_meaning, reference.meaning, reference._reference_meaning)
        if self._template_meaning:
            print("has meaning from template")
            ref = nlp(self._template_meaning)
        elif reference.meaning:
            print("take meaning from previous word")
            ref = nlp(reference.meaning)
        elif reference._reference_meaning:
            print("take meaning from passed prev word")
            ref = nlp(reference._reference_meaning)
        if not ref:
            return
        sims = {
            meaning_section: ref.similarity(nlp(meaning_section.strict_wikitext))
            for meaning_section in self.all_meanings()
        }
        correct_meaning_section = sorted(sims, key=lambda x: sims[x], reverse=True)[0]
        # print(self, reference)
        if correct_meaning_section != self.meaning_section:
            self.meaning_section = correct_meaning_section
            self.etymology_section = self.entry.get(
                number=".".join(
                    c for c in correct_meaning_section.number.split(".")[:-1]
                )
            )
            print(self.meaning_section)
            print(self.etymology_section)
