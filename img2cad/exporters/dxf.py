"""Lightweight DXF exporter used as the default DWG-compatible output."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..vectorization import VectorShape


class DxfExporter:
    """Write vector shapes to a minimal ASCII DXF file."""

    def __init__(self, *, layer: str = "0") -> None:
        self.layer = layer

    def export(self, shapes: Iterable[VectorShape], output_path: Path | str) -> None:
        path = Path(output_path)
        content = self._assemble(list(shapes))
        path.write_text(content)

    def _assemble(self, shapes: list[VectorShape]) -> str:
        header = [
            "0",
            "SECTION",
            "2",
            "HEADER",
            "0",
            "ENDSEC",
            "0",
            "SECTION",
            "2",
            "TABLES",
            "0",
            "ENDSEC",
            "0",
            "SECTION",
            "2",
            "BLOCKS",
            "0",
            "ENDSEC",
            "0",
            "SECTION",
            "2",
            "ENTITIES",
        ]
        entities = []
        for shape in shapes:
            entities.extend(self._write_polyline(shape))
        footer = [
            "0",
            "ENDSEC",
            "0",
            "EOF",
        ]
        return "\n".join(header + entities + footer)

    def _write_polyline(self, shape: VectorShape) -> list[str]:
        points = list(shape.points)
        if shape.closed and points and points[0] != points[-1]:
            points.append(points[0])
        data = [
            "0",
            "LWPOLYLINE",
            "8",
            shape.layer or self.layer,
            "90",
            str(len(points)),
            "70",
            "1" if shape.closed else "0",
        ]
        for x, y in points:
            data.extend(["10", f"{x:.6f}", "20", f"{y:.6f}"])
        return data
