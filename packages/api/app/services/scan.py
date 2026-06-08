import asyncio
from difflib import SequenceMatcher

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
_semaphore = asyncio.Semaphore(8)

def _candidates(tokens):
    words = [t.lower() for t in tokens if t.lower() not in STOPWORDS and len(t) >= 3]
    phrases = set()
    n = len(words)
    for size in (3, 2, 1):
        for i in range(n - size + 1):
            phrases.add(" ".join(words[i : i + size]))
    return phrases

async def _match(client, phrase):
    async with _semaphore:
        resolved = await client.resolve(phrase)
    if not resolved.matched or not resolved.ingredient_name or not resolved.name:
        return None

    score = SequenceMatcher(None, phrase, resolved.name.lower()).ratio()
    if score < SIMILARITY_THRESHOLD:
        return None
    return resolved.ingredient_name.lower()

async def detect_drugs(image):
    tokens = [t for t, _ in extract_words(image)]
    candidates = _candidates(tokens)

    client = RxNormClient()
    results = await asyncio.gather(*[_match(client, p) for p in candidates])

    ingredients = []
    seen = set()
    for ingredient in results:
        if ingredient and ingredient not in seen:
            seen.add(ingredient)
            ingredients.append(ingredient)
    return ingredients
