from app.services.ocr import extract_words


def test_extract_words_filters_low_confidence(monkeypatch):
    fake = {
        "text": ["Warfarin", "mg", "", "Aspirin"],
        "conf": ["95", "40", "-1", "88"],
    }
    monkeypatch.setattr(
        "app.services.ocr.pytesseract.image_to_data",
        lambda *args, **kwargs: fake,
    )
    words = extract_words(None)
    names = [text for text, _ in words]
    assert "Warfarin" in names
    assert "Aspirin" in names
    assert "mg" not in names
    assert "" not in names
    