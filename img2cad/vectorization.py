"""Convert processed bitmaps into lightweight vector primitives."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from math import hypot
from typing import Iterable, Iterator, List, Sequence, Tuple

BinaryImage = Sequence[Sequence[int]]


@dataclass(slots=True)
class VectorizerConfig:
    """Configuration parameters that tune the vectorization behaviour."""

    min_component_size: int = 8
    simplify: bool = True
    close_shapes: bool = True
    simplify_tolerance: float = 0.5


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
        points = list(component)
        if len(points) == 1:
            y, x = points[0]
            polygon = [
                (float(x), float(y)),
                (float(x + 1), float(y)),
                (float(x + 1), float(y + 1)),
                (float(x), float(y + 1)),
            ]
        else:
            polygon = self._trace_perimeter(points)
        if config.simplify and len(polygon) > 3:
            polygon = self._rdp(polygon, config.simplify_tolerance)
        if config.close_shapes and polygon and polygon[0] != polygon[-1]:
            polygon = [*polygon, polygon[0]]
        return VectorShape(points=tuple((float(x), float(y)) for x, y in polygon), closed=config.close_shapes)

    def _trace_perimeter(self, component: Sequence[Tuple[int, int]]) -> List[Tuple[float, float]]:
        """Construct an ordered list of vertices describing the component outline."""

        edges: set[Tuple[Tuple[int, int], Tuple[int, int]]] = set()
        for y, x in component:
            corners = [
                ((x, y), (x + 1, y)),
                ((x + 1, y), (x + 1, y + 1)),
                ((x + 1, y + 1), (x, y + 1)),
                ((x, y + 1), (x, y)),
            ]
            for start, end in corners:
                key = tuple(sorted((start, end)))
                if key in edges:
                    edges.remove(key)
                else:
                    edges.add(key)

        if not edges:
            return []

        adjacency: dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)
        for start, end in edges:
            adjacency[start].append(end)
            adjacency[end].append(start)

        for value in adjacency.values():
            value.sort()

        start_vertex = min(adjacency)
        path: List[Tuple[int, int]] = [start_vertex]
        current = start_vertex
        previous: Tuple[int, int] | None = None

        while True:
            neighbours = adjacency[current]
            if not neighbours:
                break
            next_vertex = None
            for candidate in neighbours:
                if candidate != previous:
                    next_vertex = candidate
                    break
            if next_vertex is None:
                next_vertex = neighbours[0]
            adjacency[current].remove(next_vertex)
            adjacency[next_vertex].remove(current)
            if next_vertex == start_vertex:
                path.append(next_vertex)
                break
            path.append(next_vertex)
            previous, current = current, next_vertex
            if len(path) > len(edges) + 2:
                # Prevent pathological loops by falling back to bounding box.
                return self._fallback_bbox(component)

        deduped: List[Tuple[float, float]] = []
        for x, y in path:
            point = (float(x), float(y))
            if not deduped or deduped[-1] != point:
                deduped.append(point)
        if deduped and deduped[0] == deduped[-1]:
            deduped.pop()
        if len(deduped) < 3:
            return self._fallback_bbox(component)
        return deduped

    def _fallback_bbox(self, component: Sequence[Tuple[int, int]]) -> List[Tuple[float, float]]:
        ys, xs = zip(*component)
        min_y, max_y = min(ys), max(ys)
        min_x, max_x = min(xs), max(xs)
        return [
            (float(min_x), float(min_y)),
            (float(max_x + 1), float(min_y)),
            (float(max_x + 1), float(max_y + 1)),
            (float(min_x), float(max_y + 1)),
        ]

    def _rdp(self, points: List[Tuple[float, float]], epsilon: float) -> List[Tuple[float, float]]:
        if len(points) < 3:
            return points
        start = points[0]
        end = points[-1]
        max_distance = -1.0
        index = -1
        for i in range(1, len(points) - 1):
            distance = self._distance_to_segment(points[i], start, end)
            if distance > max_distance:
                max_distance = distance
                index = i
        if max_distance > epsilon and index != -1:
            left = self._rdp(points[: index + 1], epsilon)
            right = self._rdp(points[index:], epsilon)
            return left[:-1] + right
        return [start, end]

    def _distance_to_segment(
        self, point: Tuple[float, float], start: Tuple[float, float], end: Tuple[float, float]
    ) -> float:
        if start == end:
            return hypot(point[0] - start[0], point[1] - start[1])
        x1, y1 = start
        x2, y2 = end
        x0, y0 = point
        dx = x2 - x1
        dy = y2 - y1
        t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return hypot(x0 - proj_x, y0 - proj_y)
