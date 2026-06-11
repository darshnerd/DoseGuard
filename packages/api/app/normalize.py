import re

CANONICAL_ALIASES = {
    "paracetamol": "acetaminophen", "acetylsalicylic acid": "aspirin",
    "amoxycillin": "amoxicillin", "salbutamol": "albuterol",
    "levosalbutamol": "levalbuterol", "frusemide": "furosemide",
    "rifampicin": "rifampin", "cetrizine": "cetirizine",
}
_STRENGTH = re.compile(r"\(.*?\)|\d+\s*(mg|mcg|ml|g|iu|%)\b", re.I)
_NONALPHA = re.compile(r"[^a-z0-9 ]+")
_SPLIT = re.compile(r"\s*(?:\band\b|\bwith\b|\bplus\b|[+&/,])\s*", re.I)


def normalize(name: str) -> str:
    if not name:
        return ""
    s = _NONALPHA.sub(" ", _STRENGTH.sub(" ", name.casefold().strip()))
    s = " ".join(s.split())
    return CANONICAL_ALIASES.get(s, s)

def split_components(text: str) -> list[str]:
    if not text:
        return []
    return [p.strip() for p in _SPLIT.split(text) if p.strip()]
