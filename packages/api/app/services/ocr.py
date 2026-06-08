import cv2
from paddleocr import PaddleOCR

MIN_CONFIDENCE = 0.6
MAX_SIDE = 1600

# Loaded once. 3.x API: no show_log / use_angle_cls.
_ocr = PaddleOCR(
    lang="en",
    text_detection_model_name="PP-OCRv5_server_det",
    text_recognition_model_name="PP-OCRv5_server_rec",
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_textline_orientation=True,
)


def _downscale(image):
    height, width = image.shape[:2]
    longest = max(height, width)
    if longest <= MAX_SIDE:
        return image
    scale = MAX_SIDE / longest
    size = (int(width * scale), int(height * scale))
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)


def extract_words(image):
    result = _ocr.predict(_downscale(image))
    words = []
    for page in result:
        texts = page["rec_texts"]
        scores = page["rec_scores"]
        for text, confidence in zip(texts, scores, strict=False):
            if confidence < MIN_CONFIDENCE:
                continue
            for raw in text.split():
                token = "".join(ch for ch in raw if ch.isalpha())
                if len(token) >= 4:
                    words.append((token, confidence * 100))
    return words
