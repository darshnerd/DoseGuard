from app.services.ocr import extract_words
from app.services.preprocess import preprocess
from app.services.rxnorm import RxNormClient


async def detect_drugs(image):
    processed = preprocess(image)
    words = extract_words(processed)

    client = RxNormClient()
    detected = []
    seen = set()
    for text, _ in words:
        resolved = await client.resolve_exact(text)
        if resolved.matched and resolved.ingredient_name:
            key = resolved.ingredient_name.lower()
            if key not in seen:
                seen.add(key)
                detected.append(resolved)
    return detected
    