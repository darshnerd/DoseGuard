import asyncio
import re
from difflib import SequenceMatcher

from sqlmodel import select

from app.models import DrugAlias, DrugConcept
from app.normalize import normalize
from app.services.ocr import extract_words
from app.services.rxnorm import RxNormClient

# packaging / dosage-form / salt-modifier words that are never the active salt
STOPWORDS = {
    "tablet", "tablets", "capsule", "capsules", "syrup", "suspension", "injection",
    "drops", "cream", "gel", "oral", "film", "coated", "dispersible", "chewable",
    "extended", "sustained", "modified", "prolonged", "release", "form",
    "ip", "bp", "usp", "each", "contains", "composition", "excipients",
    "mg", "ml", "mcg", "gm", "gms", "color", "colour",
}

SIMILARITY_THRESHOLD = 0.8
CONNECTORS = {"and", "with", "plus", "n"}
# connectors glued INSIDE a token, e.g. OCR's "aspirinandclopidogrel"
_INFIX = re.compile(r"and|with|plus|[+&/]", re.I)
# cap RxNorm fallback calls so a noisy label can't trigger dozens of requests
MAX_RXNORM_FALLBACK = 12

_semaphore = asyncio.Semaphore(8)


def _expand(token):
    """'aspirinandclopidogrel' -> ['aspirin', 'clopidogrel']; [] when not a real split."""
    parts = [p for p in _INFIX.split(token) if len(p) >= 4]
    return parts if len(parts) > 1 else []


def _candidates(tokens):
    segments, cur = [], []
    for t in tokens:
        w = t.lower()
        if w in CONNECTORS:
            if cur:
                segments.append(cur)
                cur = []
            continue
        if w in STOPWORDS or len(w) < 3:
            continue
        cur.append(w)
    if cur:
        segments.append(cur)

    phrases = set()
    for seg in segments:
        n = len(seg)
        for size in (3, 2, 1):
            for i in range(n - size + 1):
                phrases.add(" ".join(seg[i : i + size]))
        for w in seg:
            for part in _expand(w):
                phrases.add(part)
    return phrases


def _local_lookup(session, n):
    """Canonical ingredient for a normalized phrase from the local DB, or None."""
    ing = session.exec(
        select(DrugConcept.normalized_name).where(DrugConcept.normalized_name == n)
    ).first()
    if ing:
        return ing
    return session.exec(
        select(DrugAlias.concept_normalized).where(DrugAlias.alias_normalized == n)
    ).first()


async def _rxnorm_lookup(client, phrase):
    async with _semaphore:
        resolved = await client.resolve(phrase)
    if not resolved.matched or not resolved.name or not resolved.ingredient_names:
        return []
    score = SequenceMatcher(None, phrase, resolved.name.lower()).ratio()
    if score < SIMILARITY_THRESHOLD:
        return []
    return resolved.ingredient_names


async def detect_drugs(session, image):
    tokens = [t for t, _ in extract_words(image)]
    phrases = _candidates(tokens)

    found, seen = [], set()
    unresolved_singles = set()

    # 1) Local DB first (instant, offline) — for every candidate phrase.
    for phrase in phrases:
        n = normalize(phrase)
        if len(n) < 3:
            continue
        ing = _local_lookup(session, n)
        if ing:
            if ing not in seen:
                seen.add(ing)
                found.append(ing)
        elif " " not in n:  # only SINGLE words fall back to RxNorm
            unresolved_singles.add(n)

    # 2) RxNorm fallback — only single-word phrases the DB didn't know.
    fallback = list(unresolved_singles)[:MAX_RXNORM_FALLBACK]
    if fallback:
        client = RxNormClient()
        results = await asyncio.gather(*[_rxnorm_lookup(client, p) for p in fallback])
        for names in results:
            for name in names:
                ingredient = name.lower()
                if ingredient and ingredient not in seen:
                    seen.add(ingredient)
                    found.append(ingredient)

    return found
