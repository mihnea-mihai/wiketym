from src.wiketym.wiktionary import Page, Section, Language


class TestSection:
    def test_valid(self):
        s = Page("lup")["ro"]
        assert "Etymology" in [section.line for section in s]
        assert s["Noun"].line == "Noun"
        assert "From" in s["Etymology"].wikitext
        assert "====Declension====" in s["Noun"].wikitext


# There are no invalid Sections. All existing Section objects are valid.
# If an object is not found, it usually is None
