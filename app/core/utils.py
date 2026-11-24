import re

_APOSTROPHES = "'`ʻʼ’‘"

# O'zbek va rus kirill harflari -> lotin (slug uchun)
_CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "",
    "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ў": "o", "қ": "q", "ғ": "g", "ҳ": "h",
}


def slugify(text: str) -> str:
    text = text.lower()
    for ch in _APOSTROPHES:
        text = text.replace(ch, "")
    text = "".join(_CYRILLIC.get(ch, ch) for ch in text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def like_pattern(q: str) -> str:
    """ILIKE uchun: foydalanuvchi kiritgan % va _ oddiy belgi sifatida qidiriladi.
    Ishlatish: column.ilike(like_pattern(q), escape="\\")"""
    q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{q}%"
