import cv2
from paddleocr import PaddleOCR

MIN_CONFIDENCE = 0.6
MAX_SIDE = 1600

# Loaded once. 3.x API: no show_log / use_angle_cls.
# Mobile models + mkldnn off: the PP-OCRv5 *server* models segfault on some CPUs.
_ocr = PaddleOCR(
    lang="en",
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    enable_mkldnn=False,
)
