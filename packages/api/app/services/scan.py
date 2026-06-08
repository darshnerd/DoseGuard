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


def _candidates(tokens):
    words = [t.lower() for t in tokens if t.lower() not in STOPWORDS and len(t) >= 3]
    phrases = []
    n = len(words)
    for size in (3, 2, 1):
        for i in range(n - size + 1):
            phrases.append((i, i + size, " ".join(words[i : i + size])))
    return phrases


async def detect_drugs(image):
    tokens = [t for t, _ in extract_words(image)]

    ingredients = []
    seen = set()

    def add(ingredient):
        ingredient = ingredient.lower()
        if ingredient and ingredient not in seen:
            seen.add(ingredient)
            ingredients.append(ingredient)

    client = RxNormClient()
    consumed = set()
    for start, end, phrase in _candidates(tokens):
        if any(idx in consumed for idx in range(start, end)):
            continue
        resolved = await client.resolve_exact(phrase)
        if resolved.matched and resolved.ingredient_name:
            add(resolved.ingredient_name)
            consumed.update(range(start, end))

    return ingredients
