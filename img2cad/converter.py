"""High-level interface for converting raster images into CAD drawings."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Protocol, Sequence

from .image_processing import ImageProcessor, ProcessingConfig
from .vectorization import VectorShape, Vectorizer, VectorizerConfig


class Exporter(Protocol):
    """Protocol that exporters must fulfil."""

    def export(self, shapes: Iterable[VectorShape], output_path: Path | str) -> None:
        """Persist the supplied shapes to ``output_path``."""


@dataclass(slots=True)
class ConversionConfig:
    """Composite configuration holding the relevant sub-settings."""

    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    vectorizer: VectorizerConfig = field(default_factory=VectorizerConfig)


class ImageToCadConverter:
    """Facade orchestrating the processing, vectorization and export stages."""

    def __init__(
        self,
        *,
        processor: ImageProcessor | None = None,
        vectorizer: Vectorizer | None = None,
        exporter: Exporter | None = None,
        config: ConversionConfig | None = None,
    ) -> None:
        self.processor = processor or ImageProcessor()
        self.vectorizer = vectorizer or Vectorizer()
        if exporter is None:
            from .exporters.dxf import DxfExporter

            exporter = DxfExporter()
        self.exporter = exporter
        self.config = config or ConversionConfig()

    def convert(self, image_path: Path | str, output_path: Path | str) -> None:
        """Convert ``image_path`` into a CAD drawing at ``output_path``."""

        normalized_image = self.processor.load(image_path, self.config.processing)
        shapes = self.vectorizer.vectorize(normalized_image, self.config.vectorizer)
        self.exporter.export(shapes, output_path)

    def convert_from_array(
        self, image_array: Sequence[Sequence[int]] | Sequence[Sequence[Sequence[int]]], output_path: Path | str
    ) -> None:
        """Variant of :meth:`convert` that accepts an already loaded image."""

        normalized_image = self.processor.normalize(image_array, self.config.processing)
        shapes = self.vectorizer.vectorize(normalized_image, self.config.vectorizer)
        self.exporter.export(shapes, output_path)
