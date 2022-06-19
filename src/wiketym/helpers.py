"""
Utilities.
"""

import json
from typing import Any, Iterable, Iterator, Type


def load_json(path: str) -> dict:
    """Convenience function to load a dict from a JSON file by path."""
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def get(
    collection: Iterable[Type], __default: Type | None = None, **kwargs
) -> Type | None:
    try:
        return list(_query(collection, one=True, **kwargs))[0]
    except IndexError:
        return __default


def filter(collection: Iterable | Iterator, **kwargs) -> Iterator | None:
    return _query(collection, one=False, **kwargs)


def _query(collection: Iterable | Iterator, one=True, **kwargs) -> Iterator:
    for element in collection:
        valid = True
        for attr_name, attr_test in kwargs.items():
            value = getattr(element, attr_name)
            if callable(attr_test):
                valid = attr_test(value)
            else:
                valid = attr_test == value
            if not valid:
                break
        if valid:
            yield element
            if one:
                return
