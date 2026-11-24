import re

_APOSTROPHES = "'`ʻʼ’‘"


def slugify(text: str) -> str:
    text = text.lower()
    for ch in _APOSTROPHES:
        text = text.replace(ch, "")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")