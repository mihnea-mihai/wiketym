
import re


class Template:

    INHERITED = {'inh', 'inherited', 'inh+'}
    BORROWED = {'bor', 'borrowed', 'bor+'}
    DERIVED = {'der', 'derived', 'der+'}
    AFFIX = {'af', 'affix', 'vrd', 'compound'}  # no compound and vrd
    SUFFIX = {'suf', 'suffix'}
    PREFIX = {'prefix'}
    MENTION = {'m', 'mention', 'back-form', 'm+'}  # no backform
    LINK = {'l', 'link'}
    COGNATE = {'cog'}
    COMPOUND = {'com'}
    DIRECTIONAL = INHERITED | BORROWED | DERIVED
    MULTIPLE = AFFIX | SUFFIX | PREFIX
    NONDIRECTIONAL = MENTION | LINK

    class Term:
        def __init__(self) -> None:
            self.lemma = ''
            self.lang_code = ''
            self.alt = ''
            self.t = ''
            self.tr = ''
            self.id = ''

        def __str__(self) -> str:
            show = self.alt if self.alt else self.lemma
            return f'{show} ({self.lang_code}) "{self.t}"'

        def __repr__(self) -> str:
            return self.__str__()

    def __init__(self, text: str) -> None:
        def parse_pos_params():

            def parse_fixed(lang_code, lemma=None, alt=None, t=None):
                self.terms = [self.Term()]
                self.terms[0].lang_code = lang_code
                self.terms[0].lemma = lemma
                self.terms[0].alt = alt
                self.terms[0].t = t

            def parse_var(lang_code, *args):
                for arg in args:
                    t = self.Term()
                    t.lemma = arg
                    t.lang_code = lang_code
                    self.terms.append(t)

            if self.type in self.INHERITED | self.BORROWED | self.DERIVED:
                parse_fixed(*self.parts[2:])
            elif self.type in self.MENTION | self.LINK | self.COGNATE:
                parse_fixed(*self.parts[1:])
            elif (self.type in self.AFFIX | self.SUFFIX
                    | self.PREFIX | self.COMPOUND):
                parse_var(*self.parts[1:])

        def parse_key_params():
            kwparams = {'alt': 'alt', 't': 't', 'gloss': 't',
                        'tr': 'tr', 'id': 'id'}
            for part in self.key_parts:
                key, val = part.split('=', 1)
                for template_key, param_key in kwparams.items():
                    if key.startswith(template_key) and self.terms:
                        if key == template_key:
                            setattr(self.terms[0], param_key, val)
                            break
                        elif re.match(template_key + r'\d+', key):
                            term_i = int(key[len(template_key):]) - 1
                            setattr(self.terms[term_i], param_key, val)
                            break

        self.parts = text.replace('\n', '').split('|')
        self.key_parts = [part for part in self.parts if '=' in part]
        self.parts = [part for part in self.parts if '=' not in part]
        self.type = self.parts[0]
        self.terms: list[Template.Term] = []
        parse_pos_params()
        parse_key_params()

    @staticmethod
    def extract_all_raw(text: str) -> list[str]:
        matches = re.findall(
            r'''\{\{
                (
                    (?:
                        [^{}]*
                        |
                        \{\{[^{}]*\}\}
                    )*
                )
                \}\}''',
            text,
            flags=re.VERBOSE)
        if matches:
            return matches
        return []

    def __repr__(self) -> str:
        return str(self.parts)
