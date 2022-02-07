import json
import requests
import re
import doctest

class Page:
    """
    Interface to a Wiktionary Page.

    >>> p = Page.get('vâsc')
    >>> p.title
    'vâsc'
    >>> p.wikitext[:12]
    '==Romanian=='

    Use the `get` classmethod to avoid creating duplicate entries!
    >>> Page('cat') is not Page('cat')
    True
    >>> Page.get('cat') is Page.get('cat')
    True


    Access all sections in the `sections` attribute
    or get a specific language section by name.
    >>> [section.line for section in p.sections]
    ['Romanian', 'Alternative forms', 'Etymology', 'Noun', 'Declension', 'Related terms']
    >>> p.get_main_section('Romanian').line
    'Romanian'
    >>> p.get_main_section('Etymology') is None
    True

    Robust to invalid titles.
    >>> inv = Page('tteesstt')
    >>> inv.title
    'tteesstt'
    >>> inv.wikitext
    ''
    >>> inv.sections
    []

    """
    with open('cache.json', encoding='utf-8') as file:
        _cache = json.load(file)
    _url = 'https://en.wiktionary.org/w/api.php'
    _pages: "dict[str, Page]" = {}

    @classmethod
    def get(cls, title: str) -> "Page":
        """
        Gets a `Page` guaranteed to be unique within this run.

        If the `Page` entry already exists in `Page._pages`
        (so having been created before), it is returned from there.

        Otherwise it is created and initialised (so also added to the dict).
        >>> length = len(Page._pages)
        >>> p = Page.get('cat') # already exists
        >>> len(Page._pages) - length
        0
        >>> n = Page.get('new')
        >>> len(Page._pages) - length
        1
        """
        if title not in cls._pages:
            Page(title) # this also adds it to the dict

        return cls._pages[title]

    def __init__(self, title: str) -> None:
        Page._pages[title] = self # Add to runtime history
        self.title = title
        parsed = self._API_call()
        self.wikitext = parsed.get('wikitext', {}).get('*', '')
        self.isFound = (self.wikitext != '')
        self.sections = self.get_sections(parsed)
        self._map_subsections()

    def _API_call(self) -> dict:
        """
        Return API response either from cache or from actual API call.

        `Page._cache` is loaded at runtime.
        If query had been done before, return from cache.

        Otherwise send request, save to cache and dump it
        (persists between different runs).
        """
        new = False
        if self.title not in self._cache:
            params = {
                'action': 'parse',
                'format': 'json',
                'page': self.title,
                'prop': 'sections|wikitext',
                'redirects': 1
            }
            Page._cache[self.title] = requests.get(Page._url, params).json()
            with open('cache.json', 'w', encoding='utf-8') as file:
                json.dump(Page._cache, file, ensure_ascii=False)
            new = True
        return Page._cache[self.title].get('parse', {})
    
    def _map_subsections(self):
        """
        Map each `Section` to its subsections
        (including nested subsections and excluding itself).

        >>> p = Page.get('vâsc')
        >>> [s.number for s in p.sections]
        ['1', '1.1', '1.2', '1.3', '1.3.1', '1.3.2']
        >>> p.sections[3].number
        '1.3'
        >>> [ss.number for ss in p.sections[3].subsections]
        ['1.3.1', '1.3.2']
        """
        for section in self.sections:
            section.subsections = [
                subsection for subsection in self.sections
                if subsection.number.startswith(section.number+'.')
            ]
    
    def get_main_section(self, section_line: str) -> "Section|None":
        """
        Returns the top-level section of the `Page` by name.

        Subsections are not taken into consideration.

        Returns the `Section` with the requested name
        If the requested section is missing, return `None` instead.

        >>> p = Page.get('cat')
        >>> [s.line for s in p.sections][:5]
        ['English', 'Pronunciation', 'Etymology 1', 'Alternative forms', 'Noun']
        >>> p.get_main_section('English') == p.sections[0]
        True
        >>> p.get_main_section('Pronunciation') is None
        True
        """
        for section in self.sections:
            if section.level == 2 and section.line == section_line:
                return section

    def __repr__(self) -> str:
        """
        >>> Page.get('cat')
        Page(cat)
        """
        return f'Page({self.title})'

    def get_sections(self, parsed) -> "list[Page.Sections]":
        """
        >>> Page('tteesstt').sections == []
        True
        >>> Page('cat').sections[5]
        Page(cat).Section(Synonyms)
        """
        return [
            Page.Section(self, obj, wikitext)
            for obj, wikitext in zip(
                parsed.get('sections', []),
                re.split(r'={2,}.+?={2,}', self.wikitext)[1:]
            )
        ]

    class Section:
        """
        Interface for the `Section`s of Wiktionary `Page`s.
        [Example Vâsc Page](https://en.wiktionary.org/wiki/v%C3%A2sc)
        >>> s = Page.get('vâsc').sections[2]
        >>> s
        Page(vâsc).Section(Etymology)
        >>> s.page
        Page(vâsc)
        >>> s.line
        'Etymology'
        >>> s.wikitext # this does not include subsection wikitext
        'From {{inh|ro|la|viscum}}.'
        >>> s.level
        3
        >>> s.number
        '1.2'
        >>> s.templates
        [['inh', 'ro', 'la', 'viscum']]
        >>> s.subsections
        []
        >>> Page('vâsc').sections[3].subsections
        [Page(vâsc).Section(Declension), Page(vâsc).Section(Related terms)]
        """
        def __init__(self, page: "Page", obj, wikitext: str) -> None:
            self.page = page
            self.line: str = obj['line']
            self.level = int(obj['level'])
            self.number: str = obj['number']
            self.wikitext = wikitext.strip()
            self.templates = self._get_templates()
            # self.subsections is set by Page._map_subsections()
            # after all Sections had been created
            self.subsections: list[Page.Section] = []

        def __repr__(self) -> str:
            """
            >>> Page.get('vâsc').sections[2]
            Page(vâsc).Section(Etymology)
            """
            return f'Page({self.page.title}).Section({self.line})'
        
        def _get_templates(self):
            """
            Extract all templates from the section's `wikitext`.

            >>> s = Page.get('portocală').sections[1]
            >>> s.wikitext
            'Borrowed from {{bor|ro|el|πορτοκάλι}}, from {{der|ro|vec|portogallo }}.'
            >>> s.templates
            [['bor', 'ro', 'el', 'πορτοκάλι'], ['der', 'ro', 'vec', 'portogallo ']]
            """
            matches = re.findall(r'{{.*?}}', self.wikitext, flags=re.DOTALL)
            if not matches:
                matches = []
            return [Template(match) for match in matches]
        
        def get_subsection(self, subsection_line):
            """
            >>> Page.get('cat') \
                 .get_main_section('English') \
                 .get_subsection('Synonyms')
            Page(cat).Section(Synonyms)
            """
            for subsection in self.subsections:
                if subsection.line == subsection_line:
                    return subsection

class Template:

    INHERITED = {'inh', 'inherited', 'inh+'}
    BORROWED = {'bor', 'borrowed', 'bor+'}
    DERIVED = {'der', 'derived', 'der+'}
    AFFIX = {'af', 'affix', 'vrd', 'compound'}
    SUFFIX = {'suf', 'suffix', 'prefix'}
    MENTION = {'m', 'mention', 'back-form'}
    LINK = {'l', 'link'}
    COGNATE = {'cog'}

    def __init__(self, text) -> None:
        cleaned = re.sub(r'\{\{.*?\}\}', '', text[2:-2])
        self.parts: list[str] = cleaned.replace('\n','').split('|')
        self.type = self.parts[0]
        self.parse()

    def parse(self):
        self.extract_keyword_parameters()
        if (self.type in self.INHERITED | self.BORROWED | self.DERIVED):
            self.lang_into = self.parts[1]
            self.lang_from = self.parts[2]
            self.term_from = self.parts[3] if len(self.parts) > 3 else None
            if len(self.parts) > 4:
                self.alt = self.parts[4]
            if len(self.parts) > 5:
                self.gloss = self.parts[5]
        if (self.type in self.AFFIX | self.SUFFIX):
            self.lang = self.parts[1]
            self.term1 = self.parts[2]
            self.term2 = self.parts[3] if len(self.parts) > 3 else None
            self.term3 = self.parts[4] if len(self.parts) > 4 else None
        if (self.type in self.MENTION | self.LINK | self.COGNATE):
            self.lang = self.parts[1]
            self.term = self.parts[2] if len(self.parts) > 2 else None
            self.alt = self.parts[3] if len(self.parts) > 3 else None
            if len(self.parts) > 4:
                self.gloss = self.parts[4]
        

    def extract_keyword_parameters(self):
        """
        >>> t = Template('{{inh|t=t|en|tr=tr|ro|alt=alt|term|id=id}}')
        >>> t.parts
        ['inh', 'en', 'ro', 'term']
        >>> t.alt
        'alt'
        >>> t.tr
        'tr'
        >>> t.id
        'id'
        """
        self.alt = None
        self.gloss = None
        self.tr = None
        self.pos = None
        self.lit = None
        self.id = None
        self.gloss1 = None
        self.gloss2 = None
        remove = []
        for part in self.parts:
            if re.search(r'(4|alt)\d*=', part):
                self.alt = part.split('=',1)[1]
                remove.append(part)
            if re.search(r'(5|t|gloss)\d*=', part):
                if '1' in part:
                    self.gloss1 = part.split('=',1)[1]
                elif '2' in part:
                    self.gloss2 = part.split('=',1)[1]
                else:
                    self.gloss = part.split('=',1)[1]
                remove.append(part)
            if re.search(r'(tr)\d*=', part):
                self.tr = part.split('=',1)[1]
                remove.append(part)
            if re.search(r'(pos)\d*=', part):
                self.pos = part.split('=',1)[1]
                remove.append(part)
            if re.search(r'(lit)\d*=', part):
                self.lit = part.split('=',1)[1]
                remove.append(part)
            if re.search(r'(id)\d*=', part):
                self.id = part.split('=',1)[1]
                remove.append(part)
            if re.search(r'(q)\d*=', part):
                self.q = part.split('=',1)[1]
                remove.append(part)
        
        self.parts = [part for part in self.parts if part not in remove]

    def __repr__(self) -> str:
        return str(self.parts)

if __name__ == '__main__':
    doctest.testmod(verbose=0)