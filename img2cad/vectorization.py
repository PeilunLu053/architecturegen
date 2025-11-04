"""Convert processed bitmaps into lightweight vector primitives."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Sequence, Tuple

BinaryImage = Sequence[Sequence[int]]


@dataclass(slots=True)
class VectorizerConfig:
    """Configuration parameters that tune the vectorization behaviour."""

    min_component_size: int = 8
    simplify: bool = True
    close_shapes: bool = True


@dataclass(slots=True)
class VectorShape:
    """Vector representation of a raster component."""

    points: Tuple[Tuple[float, float], ...]
    closed: bool = True
    layer: str = "0"


class Vectorizer:
    """Extract vector primitives from normalized images."""

    def vectorize(self, image: BinaryImage, config: VectorizerConfig) -> List[VectorShape]:
        height = len(image)
        width = len(image[0]) if height else 0
        visited = [[False for _ in range(width)] for _ in range(height)]
        shapes: List[VectorShape] = []
        for y in range(height):
            for x in range(width):
                if image[y][x] and not visited[y][x]:
                    component = self._flood_fill(image, visited, (y, x))
                    if len(component) >= config.min_component_size:
                        shapes.append(self._component_to_shape(component, config))
        return shapes

    def _flood_fill(
        self, image: BinaryImage, visited: List[List[bool]], start: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """Return the coordinates belonging to the connected component at ``start``."""

        queue: deque[Tuple[int, int]] = deque([start])
        component: List[Tuple[int, int]] = []
        height = len(image)
        width = len(image[0]) if height else 0
        while queue:
            y, x = queue.popleft()
            if visited[y][x]:
                continue
            visited[y][x] = True
            if not image[y][x]:
                continue
            component.append((y, x))
            for ny, nx in self._neighbors(y, x, height, width):
                if not visited[ny][nx]:
                    queue.append((ny, nx))
        return component

    def _neighbors(
        self, y: int, x: int, height: int, width: int
    ) -> Iterator[Tuple[int, int]]:
        if y > 0:
            yield y - 1, x
        if y < height - 1:
            yield y + 1, x
        if x > 0:
            yield y, x - 1
        if x < width - 1:
            yield y, x + 1

    def _component_to_shape(
        self, component: Iterable[Tuple[int, int]], config: VectorizerConfig
    ) -> VectorShape:
        ys, xs = zip(*component)
        min_y, max_y = min(ys), max(ys)
        min_x, max_x = min(xs), max(xs)
        bbox: Tuple[Tuple[float, float], ...] = (
            (float(min_x), float(min_y)),
            (float(max_x + 1), float(min_y)),
            (float(max_x + 1), float(max_y + 1)),
            (float(min_x), float(max_y + 1)),
        )
        if config.simplify:
            bbox = self._simplify_rectangle(bbox)
        return VectorShape(points=bbox, closed=config.close_shapes)

    def _simplify_rectangle(
        self, points: Tuple[Tuple[float, float], ...]
    ) -> Tuple[Tuple[float, float], ...]:
        """Remove redundant points in the rectangle definition."""

        if len(points) <= 4:
            return points
        unique: List[Tuple[float, float]] = []
        for point in points:
            if not unique or unique[-1] != point:
                unique.append(point)
        if unique and unique[0] == unique[-1]:
            unique.pop()
        return tuple(unique)
