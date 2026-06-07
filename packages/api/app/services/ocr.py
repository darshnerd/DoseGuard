import pytesseract

MIN_CONFIDENCE = 60


def extract_words(image):
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    words = []
    for text, conf in zip(data["text"], data["conf"], strict=False):
        text = text.strip()
        try:
            confidence = float(conf)
        except (TypeError, ValueError):
            confidence = -1.0
        if text and confidence >= MIN_CONFIDENCE:
            words.append((text, confidence))
    return words
