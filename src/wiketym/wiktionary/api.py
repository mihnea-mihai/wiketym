import json
from functools import cache

import requests

from ..helpers import load_json


@cache
def get_page(title: str) -> dict:
    return API._get_page(title)


class API:
    """
    Interface for using the Wiktionary API.
    """

    _cache: dict[str:dict] = load_json("src/wiketym/data/cache.json")
    url: str = "https://en.wiktionary.org/w/api.php"

    @classmethod
    def _get_page(cls, title: str) -> dict[str, dict]:
        """
        Return API response either from cache or from actual API call.
        """
        try:
            response = cls._cache[title]
        except KeyError:
            params = {
                "action": "parse",
                "format": "json",
                "page": title,
                "prop": "sections|wikitext",
            }
            response: dict = requests.get(cls.url, params).json()
            cls._cache[title] = response

        return response.get("parse", {})
