from .helpers import load_json, dump_json
from .word import Word
from .etygraph import EtyGraph
from .wiktionary.api import API
from werkzeug.utils import secure_filename


class Query:
    ALL_LINKS = load_json("src/wiketym/data/link_types.json").keys()

    def __init__(
        self,
        start_words: set[Word] = [],
        allowed_links: set[str] = ALL_LINKS,
        max_level: int = 10,
        allow_invalid: bool = False,
        max_count: int = 10,
        reduce: bool = True,
        max_count_weak: int = 2,
        ignore_affixes: bool = True,
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

        future_words = start_words
        level = 0  # will be incremented
        while (current_words := future_words) and ((level := level + 1) <= max_level):
            future_words = set()
            for current_word in current_words:
                related_count = 0
                for link_type, related_words in current_word.links.items():
                    if related_count >= max_count:
                        break
                    if link_type in {"mentioned", "linked"} and related_count:
                        break
                    for related_word in related_words:
                        if current_word.lang.pro and not related_word.lang.pro:
                            continue
                        if ignore_affixes:
                            wk = current_word.entry.wikitext
                            if "==Suffix==" in wk or "==Prefix==" in wk:
                                break
                        if related_count >= max_count or (
                            link_type in {"mentioned", "linked"}
                            and related_count >= max_count_weak
                        ):
                            break
                        if allow_invalid or related_word:
                            related_count += 1
                            if related_word not in self.handled_words | future_words:
                                print(
                                    "added",
                                    related_word,
                                    "to",
                                    current_word,
                                    related_count,
                                )
                                future_words.add(related_word)
                                self.G.add(related_word)
                            self.G.link(related_word, current_word, link_type)
                self.handled_words.add(current_word)

        # self.G.add_node("Legend", image="../outputs/test.svg", shape="none", label="")
        if reduce:
            self.G.reduce().render(self.filename)
        else:
            self.G.render(self.filename)
        dump_json("src/wiketym/data/cache.json", API._cache)

    @property
    def filename(self):
        return (
            secure_filename(
                "-".join(f"{word.lemma}_{word.lang.code}" for word in self.start_words)
            )
            or "file.pdf"
        )
