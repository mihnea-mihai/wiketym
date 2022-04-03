from __future__ import annotations
import re
import unicodedata
from functools import cache, cached_property

from wiktionary import Language, Page, Section, Template


class Word:
    """
    Word object, with properties derived from Wiktionary.
    """

    def __init__(self, lemma: str, lang_code: str):
        self.lemma = lemma
        """Dictionary lookup form of the word."""
        self.lang_code = lang_code
        """Wiktionary language form of the word."""
        self.lang = Language(lang_code)
        """Object holding metadata for the language of the word."""
        self.page_title = self._get_page_title()
        """Title of the Wiktionary page where this word can be found."""
        self.links: dict[str, list[Word]] = {'inherited_from': [],
        'redirects_to': [],
        'etymologycal_root': [], 'mentions': [], 'borrowed_from': [],
        'derived_from': [], 'mentioned': [], 'linked': [],
        'internally_from': []}
        """Dictionary of link types to this word."""
        self.page = Page.get(self.page_title)
        """Wiktionary Page of this word."""
        self.section = self.page.get_lang_section(self.lang.page_name)
        """Section of the Wiktionary Page from where information
        about this word is extracted."""
        self.etymology = self._get_etymology_section()
        """Section of the Wiktionary Page where etymology info is found."""
        self.meaning_section = self._get_meaning_section()
        """Section of the Wiktionary Page where meaning info is found."""
        self.meaning = self._get_meaning()
        """Meaning of the term in English."""
        self.templates = self._get_templates()
        """List of all parsed templates in the section wikitext."""
        self.links['redirects_to'] = self.redirects_to
        print(self)

    def __repr__(self) -> str:
        return f'{self.lemma} ({self.lang.name})'

    def __eq__(self, __o: Word) -> bool:
        return self.lemma == __o.lemma and self.lang_code == __o.lang_code

    @cache
    @staticmethod
    def get(lemma: str, lang_code: str):
        """
        Get a `Word` guaranteed to be unique within this run,
        otherwise create and initialise one.
        """
        return Word(lemma, lang_code)

    def _get_page_title(self):
        """
        Infer the title of the Wiktionary page providing information
        about this lemma and language code by:
        - stripping accents when necessary according to the language
        - applying the page naming conventions for reconstrcuted lemmas
        """
        title = self.lemma
        # Strip accents according to language
        if self.lang.diacr:
            nkfd_form = unicodedata.normalize('NFKD', title)
            if not self.lang_code == 'grc':
                title = ''.join(c for c in nkfd_form 
                                if not unicodedata.combining(c))
            else:  # Special case for Greek incomplete stripping
                title = ''.join(c for c in nkfd_form 
                    if not unicodedata.name(c) == 'COMBINING MACRON')
                # Normalise back to ensure equality
                title = unicodedata.normalize('NFKC', title)
        self.lemma = title
        # Change page title for reconstructed lemmas
        title = title.replace('*',
            f'Reconstruction:{self.lang.page_name}/')

        return title

    def _get_etymology_section(self):
        if not self.section:
            return
        for subsection in self.section.subsections:
            if subsection.line.startswith('Etymology'):
                return subsection

    def _get_meaning_section(self):
        if not self.section:
            return
        MEANING_SECTIONS = {'Noun', 'Verb', 'Adjective', 'Adverb', 'Root',
        'Root 1'}
        for subsection in self.section.subsections:
            if subsection.line in MEANING_SECTIONS:
                return subsection
    
    def _get_meaning(self):
        if not self.meaning_section:
            return ''
        match = re.search(r'\# (.*)', self.meaning_section.wikitext)
        if not match:
            return ''
        meaning = match[1]
        infl = re.match(r'\{\{inflection of\|.+?\|(.+?)\|.*\}\}', meaning)
        if infl:
            self.links['inflection_of'] = [Word.get(infl[1], self.lang_code)]
            return ''
        meaning = re.sub(r'\{\{l\|\w+?\|([^|]+)\}\} ?',
                            lambda match: match[1], meaning)
        meaning = re.sub(r'\{\{.+?\}\} ?', '', meaning)
        meaning = re.sub(r'\[\[.*?([^|]+?)\]\]', 
                        lambda match: match[1], meaning)
        return meaning

    def has_valid_ascendants(self) -> bool:
        for words_list in self.links.values():
            for word in words_list:
                if word.section:
                    return True
        return False

    @cached_property
    def redirects_to(self):
        match = re.match(r'#REDIRECT \[\[(.+)\]\]', self.page.wikitext)
        if match:
            lemma = match[1]
            if '/' in lemma:
                lemma = '*' + lemma.split('/', maxsplit=1)[1]
            return [Word.get(lemma, self.lang_code)]
        return []

    def _get_templates(self):
        """
        Get the list of templates from the Etymology section.
        If Etymology section does not exist return empty list.
        """
        if self.etymology:
            return Template.parse_all(self.etymology.wikitext)
        return []

    def parse_templates(self, allowed: set[str]):
        MAPPING = {
            'inh': 'inherited_from',
            'bor': 'borrowed_from',
            'der': 'derived_from',
            'suf': 'internally_from', 'suffix': 'internally_from',
            'af': 'internally_from', 'affix': 'internally_from',
            'm': 'mentioned', 'm+': 'mentioned',
            'l': 'linked', 'l+': 'linked'
        }
        for tpl in self.templates:
            if tpl.type in MAPPING and tpl.type in allowed:
                for term in tpl.terms:
                    self.links[MAPPING[tpl.type]].append(
                        Word.get(term.lemma, term.lang_code)
                    )


if __name__ == '__main__':
    w = Word('happy', 'en')
    print(w.meaning)
    # print(w.meaning_section.wikitext)
