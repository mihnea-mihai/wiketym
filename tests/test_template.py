from wiktionary import Template

class TestTemplate:

    def test_main(self):
        term = Template('{{inh|en|enm|water}}').terms[0]
        assert term.lemma == 'water'
        assert term.lang_code == 'enm'

    def test_empty_pos_param(self):
        term = Template('{{inh|en|ine-pro|*wódr̥||water}}').terms[0]
        assert term.lemma == '*wódr̥'
        assert term.lang_code == 'ine-pro'
        assert term.t == 'water'

    def test_only_language(self):
        tpl = Template('{{der|en|afa}}')

    def test_type(self):
        assert Template('{{inh|en|enm|water}}').type == 'inh'
        assert Template('{{der|en|afa}}').type == 'der'
    
    def test_multiple(self):
        tpl = Template('{{affix|la|ex-|pōnō|gloss2=place, put}}')
        assert tpl.terms[0].lemma == 'ex-'
        assert tpl.terms[0].lang_code == 'la'
        assert tpl.terms[1].lemma == 'pōnō'
        assert tpl.terms[1].lang_code == 'la'
        assert tpl.terms[1].t == 'place, put'
    
    def test_nested_templates(self):
        term = Template('{{bor|ro|fr|{{w|Société Bic|Bic}}}}').terms[0]
        assert term.lang_code == 'fr'
        assert term.lemma == 'Société Bic'

    def test_parse_all(self):
        text = """Borrowed from {{bor|ro|en|pick}}
        or {{bor|ro|fr|{{w|Société Bic|Bic}}|pos=a brand of ballpoint pen}}."""
        tpl_list = Template.parse_all(text)
        assert tpl_list[0].terms[0].lemma == 'pick'
        assert tpl_list[1].terms[0].lemma == 'Société Bic'
    
    def test_case_vita(self):
        tpl = Template('{{inh|ro|la|vīta||life}}')
        term = tpl.terms[0]
        assert tpl.type == 'inh'
        assert term.lemma == 'vīta'
        assert term.lang_code == 'la'
        assert term.t == 'life'
        tpl = Template('{{inh|ro|itc-pro|*gʷītā}}')
        term = tpl.terms[0]
        assert tpl.type == 'inh'
        assert term.lemma == '*gʷītā'
        assert term.lang_code == 'itc-pro'
        tpl = Template('{{root|la|ine-pro|*gʷeyh₃-}}')
        term = tpl.terms[0]
        assert tpl.type == 'root'
        assert term.lemma == '*gʷeyh₃-'
        assert term.lang_code == 'ine-pro'

