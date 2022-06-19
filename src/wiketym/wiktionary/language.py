"""
Interface to a language in Wiktionary.
"""
import json
from functools import cache

import requests
from bs4 import BeautifulSoup

from ..helpers import load_json


class Language:
    """
    Mapping between language codes and the corresponding language
    name or metadata in Wiktionary.
    """

    lang_data = load_json("src/wiketym/data/langs.json")

    @cache
    def __new__(cls, code):
        return object.__new__(cls)

    def __init__(self, code) -> None:
        lang_obj = self.lang_data[code]
        self.name = lang_obj["name"]
        """Friendly name of the language."""
        self.page_name = lang_obj["page_name"]
        """Name of the language in page context.
        (e.g. `Latin` as opposed to `Vulgar Latin`)."""
        self.diacr = lang_obj["diacr"]
        """Whether or not diacritics should be stripped."""
        self.pro = lang_obj["pro"]
        """Whether or not this is a reconstruction language."""
        self.code = code
        """Language code."""

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Language({self.code})"

    @staticmethod
    def build():
        """Generate the json of languages from Wiktionary pages."""
        url = "https://en.wiktionary.org/wiki"
        langs = {}

        res = requests.get(f"{url}/Wiktionary:List_of_languages").text
        soup = BeautifulSoup(res, features="html.parser")
        trows = soup.select("table tbody tr")
        for tr in trows:
            tds = tr.select("td")
            if tds:
                code = tds[0].select_one("code").text
                name = tds[1].select_one("a").text
                diacr = tds[6].text.strip() == "Yes"
                langs[code] = {
                    "name": name,
                    "diacr": diacr,
                    "page_name": name,
                    "pro": False,
                }

        res = requests.get(f"{url}/Wiktionary:List_of_languages/special").text
        soup = BeautifulSoup(res, features="html.parser")
        table = soup.select_one("table")
        trows = table.select("tbody>tr")
        for tr in trows:
            tds = tr.select("td")
            if tds:
                code = tds[0].select_one("code").text
                name = tds[1].select_one("a").text
                diacr = tds[6].text.strip() == "Yes"
                langs[code] = {
                    "name": name,
                    "diacr": diacr,
                    "page_name": name,
                    "pro": True,
                }
        table = soup.select("table")[-1]
        trows = table.select("tbody>tr")
        for tr in trows:
            tds = tr.select("td")
            if tds:
                codes = tds[0].select("code")
                name = tds[1].select_one("a").text
                page_name = tds[3].select_one("a").text
                copy_code = None
                for subcode, sublang in langs.items():
                    if sublang["page_name"] == page_name:
                        copy_code = subcode
                        break
                print(name, page_name, copy_code)
                for code in codes:
                    if copy_code:
                        langs[code.text] = {
                            "name": name,
                            "diacr": langs[copy_code]["diacr"],
                            "page_name": page_name,
                            "pro": langs[copy_code]["pro"],
                        }
                    else:
                        langs[code.text] = {
                            "name": name,
                            "diacr": False,
                            "page_name": page_name,
                            "pro": False,
                        }

        res = requests.get(f"{url}/Wiktionary:List_of_families").text
        soup = BeautifulSoup(res, features="html.parser")
        trows = soup.select("table>tbody>tr")
        for tr in trows:
            tds = tr.select("td")
            if tds:
                code = tds[0].select_one("code").text
                name = tds[1].select_one("a").text
                page_name = name
                langs[code] = {
                    "name": name,
                    "diacr": None,
                    "page_name": page_name,
                    "pro": None,
                }

        with open("src/wiketym/data/langs.json", "w", encoding="utf-8") as file:
            json.dump(langs, file)
