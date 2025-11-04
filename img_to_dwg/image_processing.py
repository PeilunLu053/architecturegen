"""Image loading and preprocessing helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np

from .config import ConversionSettings


class ImageProcessingError(RuntimeError):
    """Raised when a raster image cannot be processed."""


def load_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        raise ImageProcessingError(f"Unable to read image from '{path}'.")
    return image


def resize_to_dpi(image: np.ndarray, source_dpi: int, target_dpi: int) -> np.ndarray:
    if source_dpi == target_dpi:
        return image
    scale = target_dpi / float(source_dpi)
    height, width = image.shape[:2]
    new_size: Tuple[int, int] = (int(width * scale), int(height * scale))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)


def denoise_image(image: np.ndarray, settings: ConversionSettings) -> np.ndarray:
    return cv2.GaussianBlur(image, (settings.blur_kernel_size, settings.blur_kernel_size), 0)


def binarize_image(image: np.ndarray) -> np.ndarray:
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def prepare_image(path: Path, settings: ConversionSettings, source_dpi: int | None = None) -> np.ndarray:
    settings.validate()
    image = load_image(path)
    if source_dpi:
        image = resize_to_dpi(image, source_dpi, settings.dpi)
    image = denoise_image(image, settings)
    return binarize_image(image)
