from src.wiketym.wiktionary import Language
import pytest


class TestLanguage:
    def test_names(self):
        Language("VL.").name != Language("VL.").page_name
        Language("ro").name == "Romanian"
        Language("ro").page_name == "Romanian"

    def test_missing(self):
        with pytest.raises(KeyError):
            Language("invalid code")
