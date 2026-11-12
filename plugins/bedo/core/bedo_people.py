# -*- coding: utf-8 -*-
"""A person is found by any name she goes by, not only the two the
connections table holds (9 Oct 2026).

The stream's person field carries whatever was typed: the full name, the short
name, a first name, a full name the table has only as a first name. On 8 Oct
her parents showed under "no circle yet" because the stream wrote one form and
the table held two others. She has been through this many times, so a third
form must not break it again.

Each person's forms are their full name, short name and any aliases, exactly;
and, derived, the first word of each. A lookup tries the name exactly, then
derived, then the name's own first word. A derived form two people share
belongs to neither — a wrong circle is worse than none.
"""
import re

_LEAD = re.compile(r'^[^\w]+')
_ZW = re.compile('[​‌⁠﻿]')


def norm(name):
    n = _ZW.sub('', name or '')
    n = re.sub(r'\([^)]*\)', ' ', n)                 # "Ana (aunt)" → "Ana"
    return re.sub(r'\s+', ' ', _LEAD.sub('', n.strip())).strip().lower()


def split_aliases(v):
    if not v:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v if x]
    return [x for x in re.split(r'[,;\n]', str(v)) if x.strip()]


class Index:
    """people: iterable of (key, [names]). Lookup returns the key or None."""

    def __init__(self, people):
        exact, derived = {}, {}
        for key, names in people:
            for n in names:
                f = norm(n)
                if not f:
                    continue
                exact.setdefault(f, set()).add(key)
                first = f.split(' ')[0]
                if first != f:
                    derived.setdefault(first, set()).add(key)
        self.exact = {f: next(iter(k)) for f, k in exact.items() if len(k) == 1}
        self.derived = {f: next(iter(k)) for f, k in derived.items() if len(k) == 1 and f not in exact}

    def find(self, name):
        f = norm(name)
        if not f:
            return None
        if f in self.exact:
            return self.exact[f]
        if f in self.derived:
            return self.derived[f]
        first = f.split(' ')[0]
        return self.exact.get(first) or self.derived.get(first)

    def __len__(self):
        return len(set(self.exact.values()) | set(self.derived.values()))
