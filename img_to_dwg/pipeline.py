"""Conversion pipeline tying image processing and CAD export together."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .cad_export import CADExportResult, export_polylines_to_cad
from .config import ConversionSettings
from .image_processing import ImageProcessingError, prepare_image
from .vectorization import Polyline, VectorizationError, extract_polylines


@dataclass(slots=True)
class ConversionResult:
    settings: ConversionSettings
    polylines: Iterable[Polyline]
    dxf_path: Path
    dwg_path: Optional[Path]


class ConversionPipeline:
    """High-level helper to convert raster imagery into DWG files."""

    def __init__(self, settings: ConversionSettings | None = None) -> None:
        self.settings = settings or ConversionSettings()

    def run(
        self,
        image_path: Path,
        output_dir: Path,
        output_name: Optional[str] = None,
        source_dpi: Optional[int] = None,
    ) -> ConversionResult:
        try:
            binary_image = prepare_image(image_path, self.settings, source_dpi)
            polylines = extract_polylines(binary_image, self.settings)
            output_name = output_name or image_path.stem
            cad_result: CADExportResult = export_polylines_to_cad(
                polylines, output_dir, output_name, self.settings
            )
        except (ImageProcessingError, VectorizationError) as exc:
            raise RuntimeError("Image to DWG conversion failed.") from exc

        return ConversionResult(
            settings=self.settings,
            polylines=polylines,
            dxf_path=cad_result.dxf_path,
            dwg_path=cad_result.dwg_path,
        )
