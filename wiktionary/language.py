from bs4 import BeautifulSoup
import json
from functools import cache
import requests


class Language:
    with open('langs.json') as file:
        _langs: dict = json.load(file)

    def __init__(self, code) -> None:
        self.name = self._langs[code]['name']
        self.page_name = self._langs[code]['page_name']
        self.diacr = self._langs[code]['diacr']
        self.pro = self._langs[code]['pro']
        self.code = code

    def __str__(self) -> str:
        return self.name

    @cache
    @staticmethod
    def get(code):
        return Language(code)

    @staticmethod
    def build():
        url = 'https://en.wiktionary.org/wiki'
        langs = {}

        res = requests.get(f'{url}/Wiktionary:List_of_languages').text
        soup = BeautifulSoup(res, features='html.parser')
        trows = soup.select('table tbody tr')
        for tr in trows:
            tds = tr.select('td')
            if tds:
                code = tds[0].select_one('code').text
                name = tds[1].select_one('a').text
                diacr = tds[6].text.strip() == 'Yes'
                langs[code] = {'name': name, 'diacr': diacr,
                               'page_name': name, 'pro': False}

        res = requests.get(f'{url}/Wiktionary:List_of_languages/special').text
        soup = BeautifulSoup(res, features='html.parser')
        table = soup.select_one('table')
        trows = table.select('tbody>tr')
        for tr in trows:
            tds = tr.select('td')
            if tds:
                code = tds[0].select_one('code').text
                name = tds[1].select_one('a').text
                diacr = tds[6].text.strip() == 'Yes'
                langs[code] = {'name': name, 'diacr': diacr,
                               'page_name': name, 'pro': True}
        table = soup.select('table')[-1]
        trows = table.select('tbody>tr')
        for tr in trows:
            tds = tr.select('td')
            if tds:
                codes = tds[0].select('code')
                name = tds[1].select_one('a').text
                page_name = tds[3].select_one('a').text
                copy_code = None
                for subcode, sublang in langs.items():
                    if sublang['page_name'] == page_name:
                        copy_code = subcode
                        break
                print(name, page_name, copy_code)
                for code in codes:
                    if copy_code:
                        langs[code.text] = {
                            'name': name,
                            'diacr': langs[copy_code]['diacr'],
                            'page_name': page_name,
                            'pro': langs[copy_code]['pro']
                        }
                    else:
                        langs[code.text] = {'name': name, 'diacr': False,
                            'page_name': page_name, 'pro': False}

        res = requests.get(f'{url}/Wiktionary:List_of_families').text
        soup = BeautifulSoup(res, features='html.parser')
        trows = soup.select('table>tbody>tr')
        for tr in trows:
            tds = tr.select('td')
            if tds:
                code = tds[0].select_one('code').text
                name = tds[1].select_one('a').text
                page_name = name
                langs[code] = {'name': name, 'diacr': None,
                    'page_name': page_name, 'pro': None}

        with open('langs.json', 'w') as file:
            json.dump(langs, file)
