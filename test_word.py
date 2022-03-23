from word import Word


class TestWord:
    def test_strip_dict(self):
        assert Word.strip_dict['ē'] == 'e'
        assert Word.strip_dict['ᾱ́'] == 'ά'

    def test_strip(self):
        assert Word.strip('veniō') == 'venio'

    def test_get_page(self):
        assert Word('mēnsa', 'la').page.title == 'mensa'
        assert Word('*watar', 'gmw-pro').page.title == \
            'Reconstruction:Proto-West Germanic/watar'
        assert Word('*linguāticum', 'VL.').page.title == \
            'Reconstruction:Latin/linguaticum'

    def test_init(self):
        assert Word('*ārdere', 'VL.').page.title == \
            'Reconstruction:Latin/ardere'
        assert Word('capus', 'VL.').section.line == 'Latin'
        assert Word('cat', 'en').id == 'cat_en'

    def test_get_etymology(self):
        assert Word('capus', 'VL.').etymology.line == 'Etymology 1'

    # cap PIE kaput(-) redirect
