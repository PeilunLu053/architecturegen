"""Minimal FastAPI app exposing the conversion pipeline through a browser UI."""
from __future__ import annotations

import tempfile
from pathlib import Path

try:
    from fastapi import FastAPI, File, Form, UploadFile
    from fastapi.requests import Request
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
except ImportError as exc:  # pragma: no cover - exercised when optional deps missing
    raise RuntimeError(
        "FastAPI 未安装。请先运行 'pip install img2cad[web]' 或 'pip install fastapi' 再导入 webapp 模块。"
    ) from exc

from .converter import ConversionConfig, ImageToCadConverter
from .image_processing import ProcessingConfig
from .vectorization import VectorizerConfig

app = FastAPI(title="img2cad", description="Raster to CAD conversion toolkit")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "defaults": {
                "width": "",
                "height": "",
                "threshold": 128,
                "min_component_size": 8,
                "simplify_tolerance": 0.5,
                "maintain_aspect": True,
                "close_shapes": True,
            },
        },
    )


@app.post("/convert")
async def convert(
    request: Request,
    file: UploadFile = File(...),
    width: str = Form(""),
    height: str = Form(""),
    threshold: int = Form(128),
    min_component_size: int = Form(8),
    simplify_tolerance: float = Form(0.5),
    maintain_aspect: str | None = Form("true"),
    close_shapes: str | None = Form("true"),
) -> FileResponse | HTMLResponse:
    if not file.filename:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "请先选择需要转换的图片。",
            },
            status_code=400,
        )

    target_size = None
    try:
        if width and height:
            target_size = (int(width), int(height))
    except ValueError:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "宽度和高度必须是整数。",
            },
            status_code=400,
        )

    converter = ImageToCadConverter(
        config=ConversionConfig(
            processing=ProcessingConfig(
                target_size=target_size,
                maintain_aspect=maintain_aspect is not None,
                threshold=threshold,
            ),
            vectorizer=VectorizerConfig(
                min_component_size=min_component_size,
                simplify_tolerance=simplify_tolerance,
                close_shapes=close_shapes is not None,
            ),
        )
    )

    suffix = Path(file.filename).suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
        tmp_in.write(await file.read())
        tmp_in_path = Path(tmp_in.name)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_out:
        tmp_out_path = Path(tmp_out.name)

    try:
        converter.convert(tmp_in_path, tmp_out_path)
    finally:
        tmp_in_path.unlink(missing_ok=True)

    download_name = f"{Path(file.filename).stem or 'conversion'}.dxf"
    return FileResponse(tmp_out_path, filename=download_name, media_type="application/dxf")
