"""Text normalization so that Cyrillic / Latin / Uzbek spellings of the same name match.

"ҚОПУР БРОКЕР" МЧЖ  -> "qopur broker"
Go‘qe Prokat MChJ   -> "goqe prokat"
"""
import re

_CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
    "ъ": "", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ў": "o", "қ": "q", "ғ": "g", "ҳ": "h", "ә": "a", "ө": "o", "ү": "u", "ң": "ng", "і": "i",
}

# legal forms / noise words removed from company names
_STOP = {
    "mchj", "mchj.", "ooo", "aj", "xk", "ok", "yatt", "qk", "dk", "ap", "uk", "chk", "masuliyati",
    "cheklangan", "jamiyati", "aksiyadorlik", "jamiyat", "jamiyati", "xususiy", "korxona", "korxonasi",
    "mas", "uliyati", "llc", "jsc", "ltd", "ao", "zao", "oao", "stir", "inn",
}


def translit(s: str) -> str:
    s = s.lower()
    return "".join(_CYR.get(ch, ch) for ch in s)


def norm(s: str | None, drop_stop: bool = True) -> str:
    if not s:
        return ""
    s = translit(s)
    # apostrophes of all kinds: o‘ g‘ o' oʻ -> o g
    s = re.sub(r"[‘’ʻʼ`'´]", "", s)
    s = re.sub(r"[^0-9a-z]+", " ", s)
    words = s.split()
    if drop_stop:
        words = [w for w in words if w not in _STOP]
    return " ".join(words)


def loose(s: str) -> str:
    """Even looser key: unify letters Uzbeks commonly swap (x/h, q/k, ya/ia...)."""
    s = norm(s)
    for a, b in (("x", "h"), ("q", "k"), ("yo", "e"), ("ts", "s"), ("w", "v"), ("y", "i")):
        s = s.replace(a, b)
    return s
