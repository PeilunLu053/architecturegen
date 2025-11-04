"""Command line interface for the image to DWG converter."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

try:  # pragma: no cover - optional dependency
    from rich.console import Console
    from rich.table import Table
except ImportError:  # pragma: no cover - optional dependency
    Console = None  # type: ignore
    Table = None  # type: ignore

from .config import ConversionSettings
from .pipeline import ConversionPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Path to the raster image to convert")
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=Path("output"), help="Directory to write CAD files to"
    )
    parser.add_argument("--output-name", help="Base name for the generated files (defaults to image stem)")
    parser.add_argument("--source-dpi", type=int, help="DPI of the source image if known")
    parser.add_argument("--dpi", type=int, default=300, help="Target DPI for scaling")
    parser.add_argument("--blur-kernel", type=int, default=5, help="Gaussian blur kernel size (odd number)")
    parser.add_argument("--canny-low", type=int, default=100, help="Lower threshold for Canny edge detection")
    parser.add_argument("--canny-high", type=int, default=200, help="Upper threshold for Canny edge detection")
    parser.add_argument(
        "--simplify-epsilon", type=float, default=2.0, help="Simplification tolerance for vector polylines"
    )
    parser.add_argument(
        "--min-contour-points",
        type=int,
        default=8,
        help="Ignore contours with fewer points than this value",
    )
    parser.add_argument(
        "--oda-converter",
        type=Path,
        help="Path to ODAFileConverter executable or installation directory for DWG export",
    )
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Do not delete intermediate DXF files when DWG export succeeds",
    )
    return parser


def build_settings(args: argparse.Namespace) -> ConversionSettings:
    return ConversionSettings(
        dpi=args.dpi,
        blur_kernel_size=args.blur_kernel,
        canny_threshold1=args.canny_low,
        canny_threshold2=args.canny_high,
        contour_simplify_epsilon=args.simplify_epsilon,
        min_contour_points=args.min_contour_points,
        oda_converter_path=args.oda_converter,
        cleanup_intermediate_files=not args.keep_intermediate,
    )


def print_result(result) -> None:  # pragma: no cover - presentation logic
    if Console and Table:
        console = Console()
        table = Table(title="Image to CAD Conversion")
        table.add_column("Artifact")
        table.add_column("Path")
        table.add_row("DXF", str(result.dxf_path))
        table.add_row("DWG", str(result.dwg_path) if result.dwg_path else "<not generated>")
        console.print(table)
    else:
        print(f"DXF written to: {result.dxf_path}")
        if result.dwg_path:
            print(f"DWG written to: {result.dwg_path}")
        else:
            print("DWG generation skipped. Configure --oda-converter to enable DWG output.")


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = build_settings(args)
    pipeline = ConversionPipeline(settings)
    result = pipeline.run(args.image, args.output_dir, args.output_name, args.source_dpi)
    print_result(result)


if __name__ == "__main__":  # pragma: no cover
    main()
