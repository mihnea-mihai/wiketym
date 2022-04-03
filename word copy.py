from __future__ import annotations
import json
import re
import textwrap
import networkx as nx

from wiktionary.language import Language
from wiktionary.page import Page
from wiktionary.template import Template


class Word:

    g = nx.DiGraph()
    _indent = 0
    _words: dict[str, Word] = {}

    @staticmethod
    def get(lemma: str, lang_code: str, gloss: str = None) -> Word:
        lemma = lemma or ''
        id = lemma + '_' + lang_code
        if id not in Word._words:
            # Create and add to stack if not already
            Word._words[id] = Word(lemma, lang_code, gloss=gloss)
            # Add ascendants recursively only after adding to stack
            Word._words[id].add_ascendants()
        # Return from stack anyway
        return Word._words[id]

    def __init__(self, lemma: str, lang: Language, focus=False,
                 alt=None, gloss=None):

        def _get_page() -> Page:

            page_title = self.lemma

            if self.lang.diacr:
                page_title = self.strip(page_title)

            page_title = page_title.replace(
                '*',
                f'Reconstruction:{self.lang.page_name}/'
            )

            return Page.get(page_title)

        if type(lang) == str:
            lang = Language(lang)
        self.indent = Word._indent
        self.id = lemma + '_' + lang.code
        self.gloss = gloss
        self.lemma = lemma
        self.alt = alt if alt else lemma
        self.focus = focus
        self.lang = lang
        self.page = _get_page()
        self.section = self.page.get_lang_section(self.lang.page_name)
        self.add_node()
        print(self)
        self.etymology = self._get_etymology()

    def __bool__(self) -> bool:
        return bool(self.section)

    def add_node(self):
        alt = self.alt if self.alt else ' '
        label = (f'<<FONT POINT-SIZE="10">{self.lang.name}</FONT>'
                 f'<BR ALIGN="CENTER"/>'
                 f'<B>{alt}</B>>')
        if self.gloss:
            wraped = textwrap.wrap(self.gloss, 30)
            label = label[:-1] + f'<BR ALIGN="CENTER"/>' \
                f'<FONT POINT-SIZE="10"><I>{"<BR />".join(wraped)}</I></FONT>>'
        if self.focus:
            Word.g.add_node(
                self.id,
                label=label,
                shape='box',
                fontcolor='red',
                color='red',
                style='bold'
            )
        elif self.section:
            Word.g.add_node(
                self.id,
                label=label
            )
        else:
            Word.g.add_node(
                self.id,
                label=label,
                fontcolor='gray50',
                color='gray50',
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
        def title_to_lemma(title: str):
            if '/' in title:
                return '*' + title.split('/', maxsplit=1)[1]
            return title

        m = re.match(r'#REDIRECT \[\[(?P<page>.+)\]\]', self.page.wikitext)
        if m:
            w = Word.get(title_to_lemma(m['page']), self.lang.code)
            print('redirected from', self, 'to', w)
            Word.g.add_edge(w.id, self.id, label='redirect')
        found = False
        if self.etymology:
            for t in self.etymology.templates:
                if t.type in t.DIRECTIONAL:
                    term = t.terms[0]
                    w = Word.get(term.lemma, term.lang_code, term.t)
                    self.g.add_edge(w.id, self.id, label=t.type)
                    if not nx.algorithms.is_directed_acyclic_graph(Word.g):
                        Word.g.remove_edge(w.id, self.id)
                    if w:
                        found = True
                if t.type in t.MULTIPLE:
                    root = Word.get(t.terms[0].lemma,
                                    t.terms[0].lang_code,
                                    t.terms[0].t)
                    root.gloss = t.terms[0].t
                    suf_lemma = t.terms[1].lemma
                    if '-' not in suf_lemma:
                        if suf_lemma.startswith('*'):
                            suf_lemma = '*-' + suf_lemma[1:]
                        else:
                            suf_lemma = '-' + suf_lemma
                    suf = Word.get(suf_lemma,
                                   t.terms[1].lang_code,
                                   t.terms[1].t)
                    suf.gloss = t.terms[1].t
                    Word.g.add_edge(root.id, self.id, label='root')
                    Word.g.add_edge(suf.id, self.id, label='suffix')
                    found = True
            if not found:
                for t in self.etymology.templates:
                    if (t.type in t.NONDIRECTIONAL):
                        w = Word.get(t.terms[0].lemma, t.terms[0].lang_code,
                                     t.terms[0].t)
                        self.g.add_edge(w.id, self.id, label=t.type)
                        if not nx.algorithms.is_directed_acyclic_graph(Word.g):
                            Word.g.remove_edge(w.id, self.id)
                            w.gloss = t.terms[0].t
                        elif w:
                            break

        # Word._indent += 1
        # self.num_tried = 0
        # self.num_valid = 0
        # if self.etymology:
        #     # for t in [temp for temp in self.etymology.templates
        #     #             if temp.type in temp.INHERITED|temp.BORROWED
        #     #                             |temp.AFFIX|temp.SUFFIX]:
        #     #     if self.num_tried < 3 and self.num_valid < 1:
        #     #         self.make_edge(t)
        #     # for t in [temp for temp in self.etymology.templates
        #     #             if temp.type in temp.DERIVED]:
        #     #     if self.num_tried < 3 and self.num_valid < 1:
        #     #         self.make_edge_der(t)
        #     # for t in [temp for temp in self.etymology.templates
#     #             if temp.type in temp.MENTION|temp.LINK|temp.COGNATE]:
        #     #     if self.num_tried < 3 and self.num_valid < 1:
        #     #         self.make_edge_mentions(t)
        #     #         self.make_edge_cognate(t)

        #     for t in [temp for temp in self.etymology.templates
        #               if temp.type in temp.INHERITED | temp.BORROWED
        #               | temp.AFFIX | temp.SUFFIX]:
        #         if self.num_tried < 3 and self.num_valid < 1:
        #             self.make_edge(t)
        #     for t in [temp for temp in self.etymology.templates
        #               if temp.type in temp.DERIVED]:
        #         if self.num_tried < 3 and self.num_valid < 1:
        #             self.make_edge_der(t)
        #     for t in [temp for temp in self.etymology.templates
#               if temp.type in temp.MENTION | temp.LINK | temp.COGNATE]:
        #         if self.num_tried < 3 and self.num_valid < 1:
        #             self.make_edge_mentions(t)
        #             self.make_edge_cognate(t)
        # Word._indent -= 1

    def make_edge(self, t: Template):
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

    def make_edge_mentions(self, t: Template):
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

    def make_edge_der(self, t: Template):
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
    Word.get('water', 'en')
    nx.nx_pydot.to_pydot(Word.g).write_pdf('tesssst.pdf')
    reduced: nx.DiGraph = nx.algorithms.transitive_reduction(Word.g)
    reduced.add_nodes_from(Word.g.nodes(data=True))
    reduced.add_edges_from(
        (u, v, Word.g.edges[u, v]) for u, v in reduced.edges
    )
    nx.nx_pydot.to_pydot(reduced).write_pdf('test.pdf')
