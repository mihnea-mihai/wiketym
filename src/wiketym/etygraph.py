"""Provides support for building etymology trees."""
from functools import cache

import graphviz
import networkx as nx

from .helpers import load_json

from .word import Word


class EtyGraph(nx.DiGraph):
    """Provides support for building etymology trees."""

    def __init__(self, incoming_graph_data=None, **attr):
        super().__init__(incoming_graph_data, **attr)

    EDGE_STYLES = load_json("src/wiketym/data/styles.json")["edges"]

    @cache
    def add(self, word: Word) -> None:
        super().add_node(word, **word.node)

    def refresh(self, word: Word) -> None:
        for attr_key, attr_value in word.node.items():
            self.nodes[word][attr_key] = attr_value

    def link(self, from_word: Word, to_word: Word, link_type: str) -> None:
        super().add_edge(from_word, to_word, **self.EDGE_STYLES[link_type])
        if not nx.algorithms.is_directed_acyclic_graph(self):
            self.remove_edge(from_word, to_word)

    def reduce(self):
        reduced = EtyGraph(nx.algorithms.transitive_reduction(self))
        reduced.add_nodes_from(self.nodes(data=True))
        reduced.add_edges_from((u, v, self.edges[u, v]) for u, v in reduced.edges)
        return reduced

    def render(self, filename):
        source = nx.nx_pydot.to_pydot(self).to_string()
        dot = graphviz.Source(source).unflatten(5)
        dot.render(f"outputs/{filename}")

    def merge(self):
        edges: list[tuple[Word, Word]] = []
        for _ in range(2):  # twice because of fringe case of nested edges to be deleted
            edges = [
                (u, v)
                for u, v, d in self.edges().data()
                if d.get("arrowhead") == "onormal"
            ]
            for u, v in edges:
                self.add_edges_from(
                    (u, succ, self.edges[v, succ]) for succ in self.successors(v)
                )

        for u, v in edges:
            # u.lang = v.lang
            # u.lemma = v.lemma
            if not v.meaning:
                v._template_meaning = u.meaning
            self.nodes[u]["label"] = v.node["label"]
            if v in self:
                self.remove_node(v)


if __name__ == "__main__":
    for link_type in EtyGraph.EDGE_STYLES:

        print(link_type)
