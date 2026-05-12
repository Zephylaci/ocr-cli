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


def create_app(engine: OCREngine) -> FastAPI:
    app = FastAPI(title="ocr-cli")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ocr/upload")
    async def ocr_upload(file: UploadFile = File(...), output: str = "text"):
        with NamedTemporaryFile(suffix=Path(file.filename or "upload.png").suffix, delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = Path(tmp.name)
        res = engine.run(tmp_path)
        tmp_path.unlink(missing_ok=True)
        return res.to_dict() if output == "json" else {"status": res.status, "text": res.text, "error": res.error}

    @app.post("/ocr/base64")
    def ocr_base64(payload: OCRBase64Req):
        try:
            raw = base64.b64decode(payload.image_base64)
        except Exception as exc:
            return {"status": "failed", "text": "", "blocks": [], "error": f"base64 解码失败: {exc}"}
        with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(raw)
            tmp_path = Path(tmp.name)
        res = engine.run(tmp_path)
        tmp_path.unlink(missing_ok=True)
        return res.to_dict() if payload.output == "json" else {"status": res.status, "text": res.text, "error": res.error}

    return app
