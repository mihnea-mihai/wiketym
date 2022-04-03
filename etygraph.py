"""Provides support for building etymology trees."""
from functools import cache
import networkx as nx
from word import Word
import textwrap
from wiktionary.template import Template, TemplateType

class EtyGraph(nx.DiGraph):
    """Graph of etymological relationships between words."""
    def __init__(self, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data, **attr)
        self.all_words: set[Word] = set()

    @cache
    def add_word(self, w: Word):
        label = f'<<FONT POINT-SIZE="10">{w.lang.name}</FONT>>'
        if w.lemma:
            lemma_label = f'<BR ALIGN="CENTER"/><B>{w.lemma}</B>'
            label = label[:-1] + lemma_label + label[-1]
        if w.meaning and w.lang_code != 'en':
            meaning_column = "<BR />".join(textwrap.wrap(w.meaning, 30))
            meaning_label = f'<BR ALIGN="CENTER"/>' \
                            f'<FONT POINT-SIZE="10"><I>' \
                            f'{meaning_column}</I></FONT>'
            label = label[:-1] + meaning_label + label[-1]
        if w.section:
            super().add_node(w, label=label)
        else:
            super().add_node(w, label=label, fontcolor='gray50', 
                             color='gray50', style='dashed')
    
    def connect(self, from_word: Word, to_word: Word, link_type: str):
        MAPPING = {
            'inherited_from': {'color': 'green'},
            'borrowed_from': {'color': 'red'},
            'derived_from': {'color': 'purple'},
            'redirects_to': {'arrowhead': 'none'},
            'inflection_of': {'arrowhead': 'none'},
            'mentioned': {'arrowhead': 'none'},
            'linked': {'arrowhead': 'none'},
            'internally_from': {'color': 'blue'}
        }
        if link_type in MAPPING:
            super().add_edge(from_word, to_word, **MAPPING[link_type])
        else:
            super().add_edge(from_word, to_word)
        if not nx.algorithms.is_directed_acyclic_graph(self):
            self.remove_edge(from_word, to_word)

    def build(self, word_set: set[Word], level=0):
        print(word_set)
        if not word_set:
            return
        self.all_words.update(word_set)
        next_set = set()
        for word in word_set:
            self.add_word(word)
            if level == 0:
                self.add_node(word, shape='box', fontcolor='red',
                            color='red', style='bold')
            word.parse_templates(TemplateType.DIRECTIONAL
                                 | TemplateType.MULTIPLE)
            if not word.has_valid_ascendants():
                word.parse_templates(TemplateType.NONDIRECTIONAL)
            for link_type, words_list in word.links.items():
                for org_w in words_list:
                    self.add_word(org_w)
                    self.connect(org_w, word, link_type)
                next_set.update(word for word in words_list
                                 if word not in self.all_words)
        self.build(next_set, level+1)

    def reduce(self):
        reduced = EtyGraph(nx.algorithms.transitive_reduction(self))
        reduced.add_nodes_from(self.nodes(data=True))
        reduced.add_edges_from(
            (u, v, self.edges[u, v]) for u, v in reduced.edges)
        return reduced


    def render(self, path):
        nx.nx_pydot.to_pydot(self).write_pdf(path)
if __name__ == '__main__':
    G = EtyGraph()
    G.build({Word.get('water', 'en')})
    reduced = G.reduce()
    reduced.render('outputs/test.pdf')
    # G.connect(Word.get('cat', 'en'), Word.get('pix', 'ro'), None)

    # G.render('outputs/test.pdf')

    # ZBURA SENS VOLO