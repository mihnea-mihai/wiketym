from __future__ import annotations

import re

from ..helpers import load_json


class Term:
    """
    Representation for terms referenced in templates.
    """

    def __init__(self, lang_code, lemma="", alt="", t="", *_, **__) -> None:
        self.lemma = lemma
        "Lemma of the term"
        self.lang_code = lang_code
        "Wiktionary language code"
        self.alt = alt
        "Alternative form to be displayed"
        self.t = t
        "Translation of the term"
        self.tr = ""
        "Transliteration of the term"
        self.id = ""
        "Meaning ID of the term"

        if re.match(r"\{\{.*\}\}", lemma):  # if lemma is a template
            self.lemma = Template(lemma).terms[0].lemma

    def __repr__(self) -> str:
        show = self.alt if self.alt else self.lemma
        return f'{show} ({self.lang_code}) "{self.t}"'


class Template:
    class Type:
        INHERITED = {"inh", "inherited", "inh+"}
        BORROWED = {"bor", "borrowed", "bor+", "lbor"}
        DERIVED = {"der", "derived", "der+"}
        ROOT = {"root"}
        AFFIX = {"af", "affix", "vrd", "compound"}  # no compound and vrd
        SUFFIX = {"suf", "suffix"}
        PREFIX = {"prefix"}
        MENTION = {"m", "mention", "back-form", "m+"}  # no backform
        LINK = {"l", "link"}
        COGNATE = {"cog"}
        COMPOUND = {"com"}
        W = {"w"}
        DIRECTIONAL = INHERITED | BORROWED | DERIVED | ROOT
        MULTIPLE = AFFIX | SUFFIX | PREFIX
        NONDIRECTIONAL = MENTION | LINK
        ALL = DIRECTIONAL | MULTIPLE | NONDIRECTIONAL

    TO_LINK_MAPPING = load_json("src/wiketym/data/template_to_link.json")

    def __init__(self, text: str) -> None:
        self.text = text
        """Raw text content of the template."""
        spl = self._split_text()
        self.type = spl[0]
        """Template type."""
        self.params = spl[1:]
        """Parameters of the template."""
        self.terms = self._parse_params()
        """Terms contained in this Template instance."""

    def _split_text(self) -> list[str]:
        """
        Sanitise the input string for processing by:
        - cropping initial `{{` and final `}}`
        - removing newlines
        - escaping `|` inside nested templates

        Return the resulted string split by `|`
        after reverting the escaping.

        Returns a tuple of the template type and the list of parameters.
        """
        text = self.text[2:-2]  # crop {{ }}
        text = text.replace("\n", "")  # remove newlines
        for tmpl in re.findall(r"\{\{.*?\}\}", text):
            text = text.replace(tmpl, tmpl.replace("|", "~!~"))
        return [e.replace("~!~", "|") for e in text.split("|")]

    def _parse_params(self) -> list[Term]:
        pos_params = [param for param in self.params if "=" not in param]
        key_params = [param for param in self.params if "=" in param]
        terms = []

        if self.type in Template.Type.NONDIRECTIONAL:
            terms = [Term(*pos_params)]
        elif self.type in Template.Type.DIRECTIONAL:
            terms = [Term(*pos_params[1:])]
        elif self.type in Template.Type.MULTIPLE:
            for lemma in pos_params[1:]:  # exclude language
                terms.append(Term(pos_params[0], lemma))
        elif self.type in Template.Type.W:
            terms = [Term(None, pos_params[0])]

        key_mappings = {"alt": "alt", "gloss": "t", "t": "t", "tr": "tr", "id": "id"}
        for key_param in key_params:
            match = re.match(
                r"""
                (?P<name>\D+) # name without index
                (?P<term_i>\d*) # index
                =
                (?P<value>.*)
                """,
                key_param,
                flags=re.VERBOSE,
            )
            name = match["name"]
            term_i = int(i) - 1 if (i := match["term_i"]) else 0
            if name in key_mappings and terms:
                setattr(terms[term_i], key_mappings[name], match["value"])

        return terms

    @staticmethod
    def parse_all(text: str) -> list[Template]:
        matches = re.findall(
            r"""
            \{\{
            (?: # repeat this but do not capture (instead capture all)
            [^{}]* # usual content without nested brackets
            | # or
            \{\{[^{}]*\}\} # nested template
            )+
            \}\}
            """,
            text,
            flags=re.VERBOSE,
        )
        return [Template(match) for match in matches] if matches else []

    def __repr__(self) -> str:
        return f"{self.type} {self.params}"
