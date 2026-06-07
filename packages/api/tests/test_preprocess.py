import numpy as np

from app.services.preprocess import preprocess


def test_preprocess_returns_grayscale():
    image = np.full((120, 400, 3), 255, dtype=np.uint8)
    result = preprocess(image)
    assert result.ndim == 2
    assert result.dtype == np.uint8
    