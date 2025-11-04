# img2cad

A modular toolkit for converting raster images (JPG, PNG, BMP, …) into CAD-friendly
linework that can be imported into DWG-based workflows. The conversion pipeline now
extracts actual contours for detected silhouettes and exports them as lightweight
polylines inside an ASCII DXF container, which can be opened by most CAD packages or
converted to DWG using standard tooling (ODA File Converter, Autodesk TrueView, etc.).

## Features

- Configurable preprocessing (resizing, binarisation thresholding)
- Contour-aware vectorisation with simplification controls
- Minimal DXF exporter suitable for DWG-compatible pipelines
- Python API, command line interface, and browser UI built with FastAPI

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

> **Note:** Install the optional `pillow` extra (``pip install .[pillow]``) to enable
> reading image files directly via the `ImageProcessor.load` method. The converter
> can always operate on in-memory pixel matrices through `convert_from_array`.

## Usage

### Command line

```bash
python -m img2cad.cli input.png output.dxf --width 1024 --height 768 --threshold 140
# Additional options:
#   --open-shapes   Keep polylines open (no final vertex repetition)
#   --simplify-tolerance  Maximum deviation allowed when simplifying outlines
#   --no-simplify         Export raw contours without simplification
```

### Python

```python
from img2cad import ImageToCadConverter

converter = ImageToCadConverter()
converter.convert("input.png", "output.dxf")
```

### Web 界面

```bash
pip install .[web,pillow]
uvicorn img2cad.webapp:app --reload
```

打开浏览器访问 <http://127.0.0.1:8000>，上传图片即可获取 DXF 下载。

## Testing

```bash
pytest
```

## Limitations

- The vectoriser currently produces single-loop polylines for each connected region.
  More advanced vectorisation (spline fitting, hatch detection, etc.) can be
  implemented by providing a custom `Vectorizer`.
- Direct DWG binary writing is out of scope; the exporter produces an ASCII DXF file
  that can be fed into DWG conversion utilities bundled with most CAD applications.
