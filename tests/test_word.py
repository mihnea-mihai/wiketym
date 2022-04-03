from wiktionary import Template
from word import Word

class TestWord:
    def test_page_title(self):
        # Test stripped diacritics
        assert Word('vīta', 'la').page_title == 'vita'
        # Test partial strip
        assert Word('γενεᾱ́', 'grc').page_title == 'γενεά'
        # Test reconstructed lemma
        assert Word('*gʷītā', 'itc-pro').page_title \
            == 'Reconstruction:Proto-Italic/gʷītā'

    def test_section(self):
        assert Word('vīta', 'la').section.page.title == 'vita'
        assert Word('*exvolāre', 'VL.').section.line == 'Latin'
        assert '[[fly]]' \
            in Word('zbura', 'ro').section.get_subsection('Verb').wikitext
    
    def test_relationships(self):
        zbura = Word.get('zbura', 'ro')
        zbura.parse_templates(Template.types.INHERITED)
        assert Word.get('volare', 'la') \
            in zbura.links['inherited_from']
    
    def test_meaning(self):
        assert Word.get('voler', 'fr').meaning == 'to fly (through the air)'
        assert Word.get('volāre', 'la').meaning == ''
        assert Word.get('water', 'enm').meaning == 'water'
        assert Word.get('lupus', 'la').meaning == "wolf (''C. lupus'')"
    
    def test_redirect(self):

        w1 = Word.get('*wódr̥', 'ine-pro')
        w2 = Word.get('*wédōr', 'ine-pro').redirects_to[0]
        assert Word.get('*wódr̥', 'ine-pro') \
            in Word.get('*wédōr', 'ine-pro').redirects_to
    
    def test_inflections(self):
        assert Word.get('lūmen', 'la') \
            in Word.get('lūmina', 'la').links['inflection_of']
