"""Utilities to persist vector data as CAD files."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import ezdxf

from .config import ConversionSettings
from .vectorization import Polyline


class CADExportError(RuntimeError):
    """Raised when CAD data could not be written."""


@dataclass(slots=True)
class CADExportResult:
    dxf_path: Path
    dwg_path: Optional[Path]


def create_dxf_document(settings: ConversionSettings) -> ezdxf.EzdxfDocument:
    doc = ezdxf.new(dxfversion=settings.dxf_version)
    doc.units = ezdxf.units.MM
    if settings.layer_name not in doc.layers:
        doc.layers.add(settings.layer_name)
    return doc


def add_polylines_to_doc(doc: ezdxf.EzdxfDocument, polylines: Iterable[Polyline], settings: ConversionSettings) -> None:
    msp = doc.modelspace()
    for polyline in polylines:
        tuples = polyline.as_tuples()
        if len(tuples) < 2:
            continue
        msp.add_lwpolyline(
            tuples,
            format="xy",
            dxfattribs={
                "layer": settings.layer_name,
                "lineweight": int(settings.line_weight_mm * 100),
            },
        )


def write_dxf(polylines: Iterable[Polyline], output_dir: Path, stem: str, settings: ConversionSettings) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = create_dxf_document(settings)
    add_polylines_to_doc(doc, polylines, settings)
    dxf_path = output_dir / f"{stem}.dxf"
    doc.saveas(dxf_path)
    return dxf_path


def convert_dxf_to_dwg(dxf_path: Path, settings: ConversionSettings) -> Path:
    if not settings.oda_converter_path:
        raise CADExportError("ODAFileConverter path is not configured; cannot produce DWG output.")

    converter = settings.oda_converter_path
    if converter.is_dir():
        executable = converter / "ODAFileConverter"
    else:
        executable = converter

    if not executable.exists():
        raise CADExportError(f"ODAFileConverter executable not found at '{executable}'.")

    dwg_output = dxf_path.with_suffix(".dwg")
    try:
        subprocess.run(
            [
                str(executable),
                str(dxf_path.parent),
                str(dxf_path.parent),
                dxf_path.suffix.strip("."),
                dwg_output.suffix.strip("."),
                "0",
                "1",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - external process
        raise CADExportError("ODAFileConverter failed to generate DWG output.") from exc

    if not dwg_output.exists():  # pragma: no cover - sanity check
        raise CADExportError("ODAFileConverter reported success but the DWG file is missing.")

    if settings.cleanup_intermediate_files:
        dxf_path.unlink(missing_ok=True)

    return dwg_output


def export_polylines_to_cad(
    polylines: Iterable[Polyline],
    output_dir: Path,
    output_name: str,
    settings: ConversionSettings,
) -> CADExportResult:
    dxf_path = write_dxf(polylines, output_dir, output_name, settings)
    try:
        dwg_path = convert_dxf_to_dwg(dxf_path, settings)
    except CADExportError:
        dwg_path = None
    return CADExportResult(dxf_path=dxf_path, dwg_path=dwg_path)
