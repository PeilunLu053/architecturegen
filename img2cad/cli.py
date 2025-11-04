"""Command line entry point."""
from __future__ import annotations

import argparse
from pathlib import Path

from .converter import ConversionConfig, ImageToCadConverter
from .exporters.dxf import DxfExporter
from .image_processing import ProcessingConfig
from .vectorization import VectorizerConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert raster images into CAD drawings")
    parser.add_argument("image", type=Path, help="Input raster image")
    parser.add_argument("output", type=Path, help="Output DWG/DXF file path")
    parser.add_argument("--width", type=int, help="Target width for resizing")
    parser.add_argument("--height", type=int, help="Target height for resizing")
    parser.add_argument(
        "--no-aspect",
        action="store_true",
        help="Disable aspect ratio preservation during resizing",
    )
    parser.add_argument("--threshold", type=int, default=128, help="Binarization threshold")
    parser.add_argument(
        "--min-component-size",
        type=int,
        default=8,
        help="Minimum number of pixels required to form a vector primitive",
    )
    parser.add_argument(
        "--open-shapes",
        action="store_true",
        help="Emit polylines without closing the last vertex",
    )
    parser.add_argument(
        "--no-simplify",
        action="store_true",
        help="Disable contour simplification for debugging purposes",
    )
    parser.add_argument(
        "--simplify-tolerance",
        type=float,
        default=0.5,
        help="Maximum deviation allowed when simplifying outlines",
    )
    parser.add_argument(
        "--layer",
        default="0",
        help="Layer name to use in the produced CAD file",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    target_size = None
    if args.width and args.height:
        target_size = (args.width, args.height)

    converter = ImageToCadConverter(
        exporter=DxfExporter(layer=args.layer),
        config=ConversionConfig(
            processing=ProcessingConfig(
                target_size=target_size,
                maintain_aspect=not args.no_aspect,
                threshold=args.threshold,
            ),
            vectorizer=VectorizerConfig(
                min_component_size=args.min_component_size,
                simplify=not args.no_simplify,
                close_shapes=not args.open_shapes,
                simplify_tolerance=args.simplify_tolerance,
            ),
        ),
    )
    converter.convert(args.image, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
