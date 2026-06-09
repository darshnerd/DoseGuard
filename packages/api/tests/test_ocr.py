from app.services import ocr
from app.services.ocr import extract_words


def test_extract_words_filters_low_confidence(monkeypatch):
    fake_pages = [
        {
            "rec_texts": ["Warfarin", "mg", "Aspirin tablet", "ok"],
            "rec_scores": [0.95, 0.97, 0.88, 0.30],
        }
    ]
    monkeypatch.setattr(ocr, "_downscale", lambda image: image)
    monkeypatch.setattr(ocr._ocr, "predict", lambda image: fake_pages)

    words = extract_words(None)
    names = [text for text, _ in words]

    assert "Warfarin" in names
    assert "Aspirin" in names
    assert "tablet" in names
    assert "mg" not in names
    assert "ok" not in names
    