from .helpers import load_json, dump_json
from .word import Word
from .etygraph import EtyGraph
from .wiktionary.api import API


class Query:
    ALL_LINKS = load_json("src/wiketym/data/link_types.json").keys()

    def __init__(
        self,
        start_words: set[Word] = [],
        allowed_links: set[str] = ALL_LINKS,
        max_level: int = 5,
        allow_invalid: bool = False,
        max_count: int = 2,
    ) -> None:
        self.start_words: str[Word] = start_words
        """Words for the current query."""
        self.allowed_links: set[str] = allowed_links
        """Allowed links to be considered."""
        self.max_level = max_level
        """Maximum distance from source words to consider."""
        self.G = EtyGraph()
        """Graph resulted from the query."""
        self.handled_words: str[Word] = set()

        for word in start_words:
            word.level = 0
            self.G.add(word)

        next_future_words = start_words
        level = 0  # will be incremented
        while (future_words := next_future_words) and (level := level + 1 <= max_level):
            next_future_words = set()
            for word in future_words:
                related_count = 0
                for link_type, related_words in word.links.items():
                    if related_count >= max_count:
                        break
                    if link_type in self.allowed_links:
                        for related_word in related_words:
                            if related_count >= max_count:
                                break
                            if allow_invalid or related_word:
                                if related_word not in self.handled_words:
                                    related_count += 1
                                    next_future_words.add(related_word)
                                    self.G.add(related_word)
                                self.G.link(related_word, word, link_type)
                self.handled_words.add(word)

        self.G.reduce().render(f"test")
        dump_json("src/wiketym/data/cache.json", API._cache)
