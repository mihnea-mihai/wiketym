from wiktionary.page import Page, Section
from wiktionary.template import Template
from wiktionary.language import Language

class TestPage:
    def test_init(self):
        p = Page('cat')
        assert p.title == 'cat'
        assert 'Felidae' in p.wikitext
        assert len(p.sections) > 80

    def test_invalid_init(self):
        p = Page('tteesstt')
        assert p.title == 'tteesstt'
        assert p.wikitext == ''
        assert p.sections == []

    def test_get_unique(self):
        assert Page('cat') is not Page('cat')
        assert Page.get('cat') is Page.get('cat')

    def test_sections(self):
        assert Page('cat').sections[0].level == 2

    def test_cache(self):
        Page('cat')
        len_before = len(Page._cache)
        Page('cat')
        assert len_before == len(Page._cache)

    def test_get_main_section(self):
        p = Page('cat')
        assert p.get_lang_section('English')
        assert p.get_lang_section('French') is None

    def test_repr(self):
        assert repr(Page('cat') == "Page(cat)")

class TestSection:
    def test_init(self):
        s = Page.get('cat').get_lang_section('English')
        assert s.page == Page.get('cat')
        assert s.line == 'English'
        assert s.level == 2
        assert s.number == '1'

    def test_invalid_init(self):
        s = Page.get('cat').get_lang_section('Engrish')
        assert s is None

    def test_subsections(self):
        assert (Page.get('cat')
                    .get_lang_section('English')
                    .get_subsection('Synonyms').level == 5
        )

    def test_templates(self):
        assert (Page.get('vâsc')
                    .get_lang_section('Romanian')
                    .get_subsection('Etymology').templates[0].parts[1]
                    == 'ro')

class TestTemplate:


    def test_extract_all_raw(self):
        text = '{{content}} and {{before{{inner}}after}}'
        assert Template.extract_all_raw(text)[1] == 'before{{inner}}after'
        assert Template.extract_all_raw('normal text') == []
    
    def test_fixed_params(self):
        t = Template('inh|ro|lat|canis|CANIS|dog|id=dogid|tr=cnis')
        assert t.terms[0].lemma == 'canis'
        assert t.terms[0].lang_code == 'lat'
        assert t.terms[0].alt == 'CANIS'
        assert t.terms[0].t == 'dog'
        assert t.terms[0].tr == 'cnis'
        assert t.terms[0].id == 'dogid'

        t = Template('inh|ro|lat|id=dogid|canis|CANIS|tr=cnis|dog')
        assert t.terms[0].lemma == 'canis'
        assert t.terms[0].lang_code == 'lat'
        assert t.terms[0].alt == 'CANIS'
        assert t.terms[0].t == 'dog'
        assert t.terms[0].tr == 'cnis'
        assert t.terms[0].id == 'dogid'

        t = Template('inh|ro|lat|canis|t=dog|alt=CANIS')
        assert t.terms[0].lemma == 'canis'
        assert t.terms[0].lang_code == 'lat'
        assert t.terms[0].alt == 'CANIS'
        assert t.terms[0].t == 'dog'

    def test_var_params(self):
        t = Template('af|ro|cat|usa|t2=suffix|gloss1=kitten|t3=tt|test')
        assert t.terms[0].lemma == 'cat'
        assert t.terms[0].lang_code == 'ro'
        assert t.terms[0].t == 'kitten'
        assert t.terms[1].lemma == 'usa'
        assert t.terms[1].lang_code == 'ro'
        assert t.terms[1].t == 'suffix'
        assert t.terms[2].lemma == 'test'
        assert t.terms[2].lang_code == 'ro'
        assert t.terms[2].t == 'tt'
    
class TestLanguage:
    def test_get_unique(self):
        assert Language.get('ro') is Language.get('ro')
        assert Language('ro') is not Language('ro')
    
    def test_init(self):
        ro = Language('ro')
        assert ro.name == 'Romanian'
        assert ro.page_name == 'Romanian'
        assert ro.diacr == False
        assert ro.pro == False
        assert ro.code == 'ro'
        la = Language('la')
        assert la.name == 'Latin'
        assert la.page_name == 'Latin'
        assert la.diacr == True
        assert la.pro == False
        pie = Language('ine-pro')
        assert pie.name == 'Proto-Indo-European'
        assert pie.page_name == 'Proto-Indo-European'
        assert pie.diacr == False
        assert pie.pro == True
        vl = Language('VL.')
        assert vl.name == 'Vulgar Latin'
        assert vl.page_name == 'Latin'
        assert vl.diacr == True
        assert vl.pro == False