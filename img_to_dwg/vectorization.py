"""Convert binary images into vector polylines."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import cv2
import numpy as np

from .config import ConversionSettings


@dataclass(slots=True)
class Polyline:
    """Simple wrapper for vector coordinates in image space."""

    points: np.ndarray

    def as_tuples(self) -> List[tuple[float, float]]:
        return [(float(x), float(y)) for x, y in self.points]


class VectorizationError(RuntimeError):
    """Raised when we fail to generate vector geometry from the raster image."""


def detect_edges(image: np.ndarray, settings: ConversionSettings) -> np.ndarray:
    return cv2.Canny(image, settings.canny_threshold1, settings.canny_threshold2)


def contours_to_polylines(contours: Iterable[np.ndarray], settings: ConversionSettings) -> list[Polyline]:
    polylines: list[Polyline] = []
    for contour in contours:
        if len(contour) < settings.min_contour_points:
            continue
        epsilon = settings.contour_simplify_epsilon
        simplified = cv2.approxPolyDP(contour, epsilon, closed=True)
        points = simplified.reshape(-1, 2)
        polylines.append(Polyline(points=points))
    return polylines


def extract_polylines(image: np.ndarray, settings: ConversionSettings) -> list[Polyline]:
    edges = detect_edges(image, settings)
    contours, _hierarchy = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise VectorizationError("No contours were detected in the raster image.")
    return contours_to_polylines(contours, settings)
