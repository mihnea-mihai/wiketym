import doctest
from tkinter.ttk import Style
import wiktionary
import json
import graphviz
from pprint import pprint
import re
import textwrap


MEANING_POS = ['Noun', 'Verb', 'Adjective', 'Preposition']

class Word:
    """
    >>> w = Word.get('natural', 'en')
    >>> w.etymology.wikitext
    >>> for t in w.etymology.templates:
    ...     t.type, t.gloss
    
    >>> w.make_edge_mentions(w.etymology.templates[6])
    >>> w._words
    
    """
    with open('langs.json') as file:
        langs: "dict[str, str]" = json.load(file)

    _words: "dict[str, Word]" = {}
    g = graphviz.Digraph('Etymology Tree', filename='etym', format='svg')
    _indent = 0

    @classmethod
    def get(cls, lemma: str, lang_code: str) -> "Word":
        if lang_code in ['LL.', 'ML.', 'VL.']:
            lang_code = 'la'
        lemma = cls.strip(lemma, lang_code)
        id = lemma + '_' + lang_code
        if id not in cls._words:
            # Create and add to stack if not already
            cls._words[id] = Word(lemma, lang_code)
            # Add ascendants recursively only after adding to stack
            cls._words[id].add_ascendants()
        # Return from stack anyway
        return cls._words[id]
    
    @classmethod
    def strip(cls, lemma, lang_code):
        if cls.langs[lang_code] in ['Latin', 'Old High German',
                                     'Ancient Greek', 'Old English']:
            return (
                lemma
                    .replace('ā', 'a')
                    .replace('ē', 'e')
                    .replace('ī', 'i')
                    .replace('ō', 'o')
                    .replace('ū', 'u')
                    .replace('î', 'i')
                    .replace('ᾱ́', 'ά')
                    .replace('ċ', 'c')
            )
        return lemma


    def __init__(self, lemma: str, lang_code):
        self.indent = Word._indent
        self.gloss = None
        self.id = lemma + '_' + lang_code
        self.lemma = lemma
        self.lang_code = lang_code
        try:
            self.lang = self.langs[self.lang_code] # ok to throw error
        except KeyError:
            raise KeyError(f'Language code {self.lang_code} not found!')
        print('\t' * Word._indent, self)
        self.page = self._get_page()
        self.section = self.page.get_main_section(self.lang)
        self.meaning = self.get_meaning()
        self.add_node()
        self.etymology = self._get_etymology()
        # self.add_ascendants() NO WAY, added in get
        # self.ascendants = self._get_ascendants()
        # self.descendants = []
        # if self.section and not self.meaning:
        #     raise ValueError(f"could not find meaning of word {self}")
    
    def get_meaning(self):
        if self.section:
            for s in self.section.subsections:
                if s.line in MEANING_POS:
                    return s

    def extract_gloss(self):
        if self.meaning and not self.gloss:
            s = re.search(r'#.*?\[\[(?P<gloss>.*?)\]\]', self.meaning.wikitext)
            if s:
                self.gloss = s['gloss']

    def add_node(self):
        lemma = self.lemma if self.lemma else ' '
        label = (f'<<FONT POINT-SIZE="10">{self.lang}</FONT>'
                f'<BR ALIGN="CENTER"/>'
                f'<B>{lemma}</B>>')
        if self.gloss:
            wraped = textwrap.wrap(self.gloss, 30)
            label = label[:-1] \
                + f'<BR ALIGN="CENTER"/>' \
                + f'<FONT POINT-SIZE="10"><I>{"<BR />".join(wraped)}</I></FONT>' \
                + '>'
        if self.indent==0:
            Word.g.node(
                self.id, 
                label,
                shape='box',
                fontcolor='red',
                color='red',
                style='bold'
            )
        if self.section:
            Word.g.node(
                self.id, 
                label
            )
        else:
            Word.g.node(
                self.id, 
                label,
                fontcolor='grey',
                color='grey',
                style='dashed'
            )

    def __getattr__(self, __name: str):
            if __name not in self.__dict__:
                return None
            return self.__dict__[__name]

    def __str__(self):
        return f'{self.lemma} ({self.lang})'
    
    def __repr__(self) -> str:
        return f'Word({self.lemma}, {self.lang_code})'
        
    def _get_etymology(self):
        if self.section:
            for subsection in self.section.subsections:
                if subsection.line.startswith('Etymology'):
                    return subsection

    def add_ascendants(self):

        Word._indent += 1
        self.num_tried = 0
        self.num_valid = 0
        if self.etymology:
            # for t in [temp for temp in self.etymology.templates
            #             if temp.type in temp.INHERITED|temp.BORROWED
            #                             |temp.AFFIX|temp.SUFFIX]:
            #     if self.num_tried < 3 and self.num_valid < 1:
            #         self.make_edge(t)
            # for t in [temp for temp in self.etymology.templates
            #             if temp.type in temp.DERIVED]:
            #     if self.num_tried < 3 and self.num_valid < 1:
            #         self.make_edge_der(t)
            # for t in [temp for temp in self.etymology.templates
            #             if temp.type in temp.MENTION|temp.LINK|temp.COGNATE]:
            #     if self.num_tried < 3 and self.num_valid < 1:
            #         self.make_edge_mentions(t)
            #         self.make_edge_cognate(t)

            for t in [temp for temp in self.etymology.templates
                if temp.type in temp.INHERITED|temp.BORROWED
                                        |temp.AFFIX|temp.SUFFIX]:
                if self.num_tried < 3 and self.num_valid < 1:
                    self.make_edge(t)
            for t in [temp for temp in self.etymology.templates
                        if temp.type in temp.DERIVED]:
                if self.num_tried < 3 and self.num_valid < 1:
                    self.make_edge_der(t)
            for t in [temp for temp in self.etymology.templates
                        if temp.type in temp.MENTION|temp.LINK|temp.COGNATE]:
                if self.num_tried < 3 and self.num_valid < 1:
                    self.make_edge_mentions(t)
                    self.make_edge_cognate(t)
        Word._indent -= 1

    def _get_page(self) -> "wiktionary.Page":
        """
        >>> Word('mēnsa', 'la').page.title
        'mensa'
        >>> Word('*watar', 'gmw-pro').page.title
        'Reconstruction:Proto-West Germanic/watar'
        >>> Word('*linguāticum', 'VL.').page.title
        'Reconstruction:Latin/linguaticum'
        """
        page_title = self.lemma
        if self.lang in ['Latin', 'Old High German', 'Ancient Greek',
                            'Old English', 'Russian']:
            page_title = (
                self.lemma
                    .replace('ā', 'a')
                    .replace('ē', 'e')
                    .replace('ī', 'i')
                    .replace('ō', 'o')
                    .replace('ū', 'u')
                    .replace('î', 'i')
                    .replace('ᾱ́', 'ά')
                    .replace('ċ', 'c')
                    .replace('о́', 'о')
                    .replace('а́', 'а')
                    .replace('ġ', 'g')
            )
        page_title = page_title.replace('*', f'Reconstruction:{self.lang}/')

        return wiktionary.Page.get(page_title)
    
    def make_edge(self, t: "wiktionary.Template"):
        if t:
            self.num_tried += 1
            if t.type in t.INHERITED:
                if t.term_from:
                    w = Word.get(t.term_from, t.lang_from)
                    if t.gloss and not w.gloss:
                        w.gloss = t.gloss
                        w.add_node()
                    Word.g.edge(w.id, self.id, color='green')
                    if w.etymology and w.etymology.wikitext != '':
                        self.num_valid += 1
                    if not w.etymology or w.etymology.wikitext == '':
                        if w.meaning:
                            m = re.search(
                                r'{{inflection of\|\w*\|(?P<true>.*?)\|',
                                w.meaning.wikitext
                            )
                            if m:
                                w2 = Word.get(m['true'], t.lang_from)
                                Word.g.edge(w2.id, w.id, color='blue')
            elif t.type in t.BORROWED:
                if t.term_from:
                    w = Word.get(t.term_from, t.lang_from)
                    if t.gloss and not w.gloss:
                        w.gloss = t.gloss
                        w.add_node()
                    Word.g.edge(w.id, self.id, color='red')
                    if w.etymology and w.etymology.wikitext != '':
                        self.num_valid += 1
                    if not w.etymology or w.etymology.wikitext == '':
                        if w.meaning:
                            m = re.search(
                                r'{{inflection of\|\w*\|(?P<true>.*?)\|',
                                w.meaning.wikitext
                            )
                            if m:
                                w2 = Word.get(m['true'], t.lang_from)
                                Word.g.edge(w2.id, w.id, color='blue')
            elif t.type in t.AFFIX | t.SUFFIX:
                w1 = Word.get(t.term1, t.lang)
                if t.gloss1 and not w1.gloss:
                    w1.gloss = t.gloss1
                    w1.add_node()
                w2 = None
                if t.term2:
                    w2 = Word.get(t.term2, t.lang)
                    if t.gloss2 and not w2.gloss:
                        w2.gloss = t.gloss2
                        w2.add_node()
                    if w2.lemma:
                        if w2.lemma[0] not in ['*', '-'] and not w2.section:
                            w2 = Word.get('-'+t.term2, t.lang)
                    if t.term3:
                        w3 = Word.get(t.term3, t.lang)
                        Word.g.edge(w3.id, self.id, color='blue')
                    Word.g.edge(w2.id, self.id, color='blue')
                Word.g.edge(w1.id, self.id, color='blue')
                if w2:
                    if w1.etymology or w2.etymology:
                        self.num_valid += 1
    
    def make_edge_mentions(self, t: "wiktionary.Template"):
        if t:
            self.num_tried += 1
            if (t.type in t.MENTION
                    or t.type in t.LINK):
                w = Word.get(t.term, t.lang)
                if t.gloss and not w.gloss:
                    w.gloss = t.gloss
                    w.add_node()
                Word.g.edge(w.id, self.id, color='grey', arrowhead='none',
                            style='dashed')
                if w.etymology and w.etymology.wikitext != '':
                    self.num_valid += 1
                if not w.etymology or w.etymology.wikitext == '':
                    if w.meaning:
                        m = re.search(
                            r'{{inflection of\|\w*\|(?P<true>.*?)\|',
                            w.meaning.wikitext
                        )
                        if m:
                            w2 = Word.get(m['true'], t.lang)
                            Word.g.edge(w2.id, w.id, color='blue')

    def make_edge_der(self, t: "wiktionary.Template"):
        if t:
            self.num_tried += 1
            if t.type in t.DERIVED:
                if t.term_from:
                    w = Word.get(t.term_from, t.lang_from)
                    Word.g.edge(w.id, self.id)
                    if t.gloss and not w.gloss:
                        w.gloss = t.gloss
                        w.add_node()
                    if w.etymology and w.etymology.wikitext != '':
                        self.num_valid += 1
                    if not w.etymology or w.etymology.wikitext == '':
                        if w.meaning:
                            m = re.search(
                                r'{{inflection of\|\w*\|(?P<true>.*?)\|',
                                w.meaning.wikitext
                            )
                            if m:
                                w2 = Word.get(m['true'], t.lang_from)
                                Word.g.edge(w2.id, w.id, color='blue')

    def make_edge_cognate(self, template):
        if template:
            self.num_tried += 1
            if template.type in template.COGNATE:
                w = Word.get(template.term, template.lang)
                Word.g.edge(w.id, self.id, color='orange', arrowhead='none',
                            style='dashed')
                if w.section:
                    self.num_valid += 1
    
    def update_label(self):
        pass



if __name__ == '__main__':
    # Word.get('computer', 'en')

    # Word.get('Lucifer', 'en')
    # Word.get('Lucian', 'en')

    # Word.get('graphic', 'en')
    # Word.get('carve', 'en')

    # Word.get('gyno-', 'en')
    # Word.get('queen', 'en')
    # Word.get('banshee', 'en')

    # Word.get('pământ', 'ro')

    # Word.get('undă', 'ro')
    # Word.get('water', 'en')
    # Word.get('winter', 'en')
    # Word.get('whiskey', 'en')
    # Word.get('hydro-', 'en')
    # Word.get('clepsidră', 'ro')

    # Word.get('heart', 'en')
    # Word.get('core', 'en')
    # Word.get('crede', 'ro')
    # Word.get('cord', 'ro')

    # Word.get('wise', 'en')
    # Word.get('wissen', 'de')
    # Word.get('wit', 'en')
    # Word.get('envy', 'en')
    # Word.get('history', 'en')

    # Word.get('verb', 'en')
    # Word.get('word', 'en')

    # Word.get('skirt', 'en')
    # Word.get('shirt', 'en')
    # Word.get('short', 'en')
    # Word.get('șorț', 'ro')
    # Word.get('scurt', 'ro')

    # Word.get('fior', 'ro')
    # Word.get('febră', 'ro')

    # Word.get('drac', 'ro')
    # Word.get('dragon', 'ro')

    # Word.get('dezmierda', 'ro')


    Word.get('afară', 'ro')

    Word.g = Word.g.unflatten(stagger=2)
    Word.g.view()
