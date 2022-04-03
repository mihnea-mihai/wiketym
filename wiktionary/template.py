"""
Offers support for handling Wiktionary templates.
"""
from __future__ import annotations
import re

class Term:
    """
    Representation for terms referenced in templates.
    """
    def __init__(self, lang_code, lemma='', alt='', t='') -> None:
        self.lemma = lemma
        "Lemma of the term"
        self.lang_code = lang_code
        "Wiktionary language code"
        self.alt = alt
        "Alternative form to be displayed"
        self.t = t
        "Translation of the term"
        self.tr = ''
        "Transliteration of the term"
        self.id = ''
        "Meaning ID of the term"

        if re.match(r'\{\{.*\}\}', lemma):  # if lemma is a template
            self.lemma = Template(lemma).terms[0].lemma


    def __repr__(self) -> str:
        show = self.alt if self.alt else self.lemma
        return f'{show} ({self.lang_code}) "{self.t}"'

class TemplateType():
    """
    Static sets of template type names mappings and combinations.
    """
    INHERITED = {'inh', 'inherited', 'inh+'}
    BORROWED = {'bor', 'borrowed', 'bor+'}
    DERIVED = {'der', 'derived', 'der+'}
    ROOT = {'root'}
    AFFIX = {'af', 'affix', 'vrd', 'compound'}  # no compound and vrd
    SUFFIX = {'suf', 'suffix'}
    PREFIX = {'prefix'}
    MENTION = {'m', 'mention', 'back-form', 'm+'}  # no backform
    LINK = {'l', 'link'}
    COGNATE = {'cog'}
    COMPOUND = {'com'}
    W = {'w'}
    DIRECTIONAL = INHERITED | BORROWED | DERIVED | ROOT
    MULTIPLE = AFFIX | SUFFIX | PREFIX
    NONDIRECTIONAL = MENTION | LINK


class Template:
    """Interface for a Wiktionary template."""

    types = TemplateType()
    """List of possible template types."""

    def __init__(self, text: str) -> None:
        """
        Parse the input string as a Wiktionary template.
        """

        self.terms: list[Term] = []
        """List of terms (`Term` objects) referenced in the
        parsed template."""
        self.params: list[str] = []
        """List of parameters (as strings) of the template.
        Positional parameters are prepended by their position."""
        self.type: str = ''
        """Template type, as string."""

        raw = self._split_raw(text)
        self.type = raw[0]
        self.params = raw[1:]
        self.terms = self._parse_params()


    def _split_raw(self, text: str) -> str:
        """
        Sanitise the input string for processing by:
        - cropping initial `{{` and final `}}`
        - removing newlines
        - escaping `|` inside nested templates

        Return the resulted string split by `|`
        after reverting the escaping.
        """
        text = text[2:-2]
        text = text.replace('\n', '')
        for tmpl in re.findall(r'\{\{.*?\}\}', text):
            text = text.replace(tmpl, tmpl.replace('|', '~!~'))
        return [e.replace('~!~', '|') for e in text.split('|')]

    def _parse_params(self) -> list[Term]:
        """
        Map information from the template's parameters to the
        list of terms.
        """
        pos_params = [param for param in self.params if '=' not in param]
        key_params = [param for param in self.params if '=' in param]
        terms = []

        if self.type in self.types.NONDIRECTIONAL:
            terms = [Term(*pos_params)]
        elif self.type in self.types.DIRECTIONAL:
            terms = [Term(*pos_params[1:])]
        elif self.type in self.types.MULTIPLE:
            if self.type in self.types.SUFFIX:
                lang_code, root, suffix = pos_params
                terms.append(Term(lang_code, root))
                suffix = ('-'+suffix).replace('-*', '*-') \
                                     .replace('--', '-')
                terms.append(Term(lang_code, suffix))
            else:
                for lemma in pos_params[1:]:  # exclude language
                    terms.append(Term(pos_params[0], lemma))
        elif self.type in self.types.W:
            terms = [Term(None, pos_params[0])]
        
        key_mappings = {'alt': 'alt', 'gloss': 't', 't': 't',
                        'tr': 'tr', 'id': 'id'}
        for key_param in key_params:
            match = re.match(r'''
                (?P<name>\D+) # name without index
                (?P<term_i>\d*) # index
                =
                (?P<value>.*)
            ''', key_param, flags=re.VERBOSE)
            name = match['name']
            term_i = int(match['term_i']) - 1 if match['term_i'] else 0
            value = match['value']
            if name in key_mappings and terms:
                setattr(terms[term_i], key_mappings[name], value)
        
        return terms


    @staticmethod
    def parse_all(text: str) -> list[Template]:
        matches = re.findall(r'''
            \{\{
            (?: # repeat this but do not capture (instead capture all)
            [^{}]* # usual content without nested brackets
            | # or
            \{\{[^{}]*\}\} # nested template
            )+
            \}\}
            ''', text, flags=re.VERBOSE)
        return [Template(match) for match in matches] if matches else []

    def __repr__(self) -> str:
        return str(self.params)

