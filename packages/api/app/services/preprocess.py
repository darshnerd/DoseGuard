import cv2

MAX_SIDE = 2000


def _downscale(image):
    height, width = image.shape[:2]
    longest = max(height, width)
    if longest <= MAX_SIDE:
        return image
    scale = MAX_SIDE / longest
    size = (int(width * scale), int(height * scale))
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)


def preprocess(image):
    resized = _downscale(image)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    return cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )
    