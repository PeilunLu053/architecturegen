"""Configuration objects for the image to DWG conversion pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class ConversionSettings:
    """Fine tune how raster images are converted to CAD drawings."""

    dpi: int = 300
    blur_kernel_size: int = 5
    canny_threshold1: int = 100
    canny_threshold2: int = 200
    contour_simplify_epsilon: float = 2.0
    min_contour_points: int = 8
    dxf_version: str = "R2018"
    line_weight_mm: float = 0.25
    layer_name: str = "VECTOR_OUTLINES"
    oda_converter_path: Optional[Path] = None
    cleanup_intermediate_files: bool = True
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if self.blur_kernel_size % 2 == 0:
            raise ValueError("blur_kernel_size must be an odd number so OpenCV can build the kernel.")
        if self.canny_threshold1 >= self.canny_threshold2:
            raise ValueError("canny_threshold1 must be lower than canny_threshold2.")
        if self.contour_simplify_epsilon < 0:
            raise ValueError("contour_simplify_epsilon must be non-negative.")
        if self.min_contour_points < 3:
            raise ValueError("min_contour_points must be at least 3 to define a polygon.")
        if self.line_weight_mm <= 0:
            raise ValueError("line_weight_mm must be positive.")
        if self.oda_converter_path and not self.oda_converter_path.exists():
            raise FileNotFoundError(
                f"Provided ODAFileConverter path '{self.oda_converter_path}' does not exist."
            )
