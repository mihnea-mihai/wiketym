from src.wiketym.wiktionary import Page, Section, Language


class TestPage:
    def test_duplicates(self):
        assert Page("test") == Page("test")

    def test_valid(self):
        p = Page("ghiozdan")
        assert p
        assert "==Romanian==" in p.wikitext
        assert len(p.sections) > 1
        assert len([section for section in p]) == 1
        assert p[Language("ro")]
        assert p["ro"]

    def test_invalid(self):
        p = Page("invalid entry asd")
        assert not p
        assert p.wikitext == ""
        assert len(p.sections) == 0
        assert len([section for section in p]) == 0
        assert p[Language("ro")].wikitext == ""

    def test_sections(self):
        assert Page("vită").sections[1].line == "Etymology"

    def test_subsections(self):
        lang_section = Page("vită")["ro"]
        assert len([s for s in lang_section["Noun"]]) == 3
