# Image to DWG Converter

This project provides a reusable Python module and command line interface that converts raster
images (PNG, JPG, TIFF, …) into CAD drawings. The pipeline combines image pre-processing, contour
vectorisation, and CAD export capabilities. DWG export is supported through the
[`ODAFileConverter`](https://www.opendesign.com/guestfiles/oda_file_converter) utility when
available, while DXF export works out of the box using [`ezdxf`](https://github.com/mozman/ezdxf).

## Features

- Configurable image preparation (denoising, DPI normalisation, binary thresholding).
- Contour extraction with OpenCV to approximate vector outlines.
- DXF generation via `ezdxf` with configurable layers and line weights.
- Optional DWG conversion by shelling out to `ODAFileConverter`.
- Python API (`ConversionPipeline`) and CLI (`img-to-dwg`).

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[cli]
```

The optional `rich` dependency enables richer CLI output. Install it via the `cli` extra as shown
above.

## CLI Usage

```bash
img-to-dwg input.png --output-dir cad --dpi 300 --canny-low 80 --canny-high 160 \
  --simplify-epsilon 1.5 --oda-converter /path/to/ODAFileConverter
```

If `--oda-converter` is omitted, the pipeline still emits a DXF file. When provided, the tool expects
the path to either the `ODAFileConverter` executable or its installation directory. Intermediate DXF
files are removed after a successful DWG export unless `--keep-intermediate` is supplied.

## Python API

```python
from pathlib import Path
from img_to_dwg import ConversionPipeline, ConversionSettings

settings = ConversionSettings(dpi=400, canny_threshold1=75, canny_threshold2=150)
pipeline = ConversionPipeline(settings)
result = pipeline.run(Path("input.png"), Path("cad-output"))

print("DXF:", result.dxf_path)
print("DWG:", result.dwg_path)
```

The `ConversionSettings` class exposes numerous knobs to tailor preprocessing, vectorisation, and
CAD export. Refer to `img_to_dwg/config.py` for the full list of options.

## Limitations

- Raster-to-vector conversion is best suited for images with clear contours (e.g., scanned line
  drawings). Complex photographs will likely produce noisy results.
- Native DWG writing is not available in pure Python; an external `ODAFileConverter` installation is
  required to convert the generated DXF into DWG.
- The project does not currently apply machine learning or OCR techniques to improve vectorisation.
