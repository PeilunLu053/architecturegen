"""Image loading and preprocessing utilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


PixelRow = List[int]
BinaryImage = List[PixelRow]


@dataclass(slots=True)
class ProcessingConfig:
    """Configuration for the preprocessing stage."""

    target_size: tuple[int, int] | None = None
    maintain_aspect: bool = True
    threshold: int = 128


class ImageProcessor:
    """Load images and convert them into normalized binary matrices."""

    def load(self, path: Path | str, config: ProcessingConfig) -> BinaryImage:
        try:
            from PIL import Image  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised when PIL missing
            raise RuntimeError(
                "Pillow is required to load image files. Install it via 'pip install pillow'."
            ) from exc
        image = Image.open(path)
        pixels = list(image.getdata())
        width, height = image.size
        rows = [pixels[i * width : (i + 1) * width] for i in range(height)]
        return self.normalize(rows, config)

    def normalize(
        self,
        array: Sequence[Sequence[int]] | Sequence[Sequence[Sequence[int]]],
        config: ProcessingConfig,
    ) -> BinaryImage:
        grayscale = self._to_grayscale(array)
        if config.target_size is not None:
            grayscale = self._resize(grayscale, config)
        if self._is_binary(grayscale):
            return [[1 if value else 0 for value in row] for row in grayscale]
        return [[1 if value <= config.threshold else 0 for value in row] for row in grayscale]

    def _to_grayscale(
        self, array: Sequence[Sequence[int]] | Sequence[Sequence[Sequence[int]]]
    ) -> BinaryImage:
        grayscale: BinaryImage = []
        for row in array:
            grayscale_row: PixelRow = []
            for value in row:
                grayscale_row.append(self._luminance(value))
            grayscale.append(grayscale_row)
        return grayscale

    def _luminance(self, value: int | Sequence[int]) -> int:
        if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
            seq = list(value)
            if len(seq) >= 3:
                r, g, b = seq[:3]
                return int(0.299 * r + 0.587 * g + 0.114 * b)
            if seq:
                return int(seq[0])
        return int(value)

    def _is_binary(self, array: BinaryImage) -> bool:
        for row in array:
            for value in row:
                if value not in (0, 1):
                    return False
        return True

    def _resize(self, array: BinaryImage, config: ProcessingConfig) -> BinaryImage:
        target_w, target_h = config.target_size
        src_h = len(array)
        src_w = len(array[0]) if array else 0
        if src_w == 0 or src_h == 0:
            return [[0 for _ in range(target_w)] for _ in range(target_h)]

        if config.maintain_aspect:
            scale = min(target_w / src_w, target_h / src_h)
            new_w = max(1, int(src_w * scale))
            new_h = max(1, int(src_h * scale))
        else:
            new_w, new_h = target_w, target_h

        resized = [[0 for _ in range(new_w)] for _ in range(new_h)]
        for y in range(new_h):
            src_y = int(y * src_h / new_h)
            for x in range(new_w):
                src_x = int(x * src_w / new_w)
                resized[y][x] = array[src_y][src_x]

        if not config.maintain_aspect:
            return resized

        # Place resized content onto a white canvas of the desired size.
        canvas = [[0 for _ in range(target_w)] for _ in range(target_h)]
        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        for y in range(new_h):
            for x in range(new_w):
                canvas[offset_y + y][offset_x + x] = resized[y][x]
        return canvas
