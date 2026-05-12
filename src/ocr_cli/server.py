from __future__ import annotations

import base64
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from .engine import OCREngine


class OCRBase64Req(BaseModel):
    image_base64: str
    output: str = "text"
    max_side_len: int = 2000
    min_side_len: int = 30
    width_height_ratio: float = 8
    min_height: int = 30
    long_image: bool = False


def _render_response(res, output: str):
    if output == "json":
        return res.to_dict()
    if output == "markdown":
        return {"status": res.status, "markdown": res.markdown, "error": res.error}
    return {"status": res.status, "text": res.text, "error": res.error}


def create_app(engine: OCREngine) -> FastAPI:
    app = FastAPI(title="ocr-cli")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ocr/upload")
    async def ocr_upload(
        file: UploadFile = File(...),
        output: str = "text",
        max_side_len: int = 2000,
        min_side_len: int = 30,
        width_height_ratio: float = 8,
        min_height: int = 30,
        long_image: bool = False,
    ):
        if long_image:
            if max_side_len == 2000:
                max_side_len = 4000
            if width_height_ratio == 8:
                width_height_ratio = -1
        with NamedTemporaryFile(suffix=Path(file.filename or "upload.png").suffix, delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = Path(tmp.name)
        res = engine.run(tmp_path, max_side_len=max_side_len, min_side_len=min_side_len, width_height_ratio=width_height_ratio, min_height=min_height, markdown=(output == "markdown"))
        tmp_path.unlink(missing_ok=True)
        return _render_response(res, output)

    @app.post("/ocr/base64")
    def ocr_base64(payload: OCRBase64Req):
        try:
            raw = base64.b64decode(payload.image_base64)
        except Exception as exc:
            return {"status": "failed", "text": "", "blocks": [], "markdown": "", "error": f"base64 解码失败: {exc}"}
        if payload.long_image:
            if payload.max_side_len == 2000:
                payload.max_side_len = 4000
            if payload.width_height_ratio == 8:
                payload.width_height_ratio = -1
        with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(raw)
            tmp_path = Path(tmp.name)
        res = engine.run(tmp_path, max_side_len=payload.max_side_len, min_side_len=payload.min_side_len, width_height_ratio=payload.width_height_ratio, min_height=payload.min_height, markdown=(payload.output == "markdown"))
        tmp_path.unlink(missing_ok=True)
        return _render_response(res, payload.output)

    return app
