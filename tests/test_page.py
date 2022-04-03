from wiktionary import Page

class TestPage:
    def test_unique(self):
        assert Page('cat') is not Page('cat')
        assert Page.get('cat') is Page.get('cat')
    
    def test_wikitext(self):
        assert '[[cow]]' in Page('vită').wikitext
    
    def test_lang_section(self):
        assert Page('vită').get_lang_section('Romanian').line == 'Romanian'
    
    def test_sections(self):
        assert Page('vită').sections[1].line == 'Etymology'
    
    def test_subsections(self):
        lang_section = Page('vită').get_lang_section('Romanian')
        assert len(lang_section.get_subsection('Noun').subsections) == 3
    
    def test_invalid(self):
        asd = Page('asd')
        assert asd.parsed == {}
        assert asd.wikitext == ''
        assert asd.get_lang_section('qwerty') == None