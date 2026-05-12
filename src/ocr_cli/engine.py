from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from .types import OCRBlock, OCRResult


class OCREngine:
    def __init__(self, debug: bool = False) -> None:
        self.debug = debug
        self._ocr: Any | None = None

    def load(self) -> None:
        if self._ocr is not None:
            return
        try:
            from rapidocr_onnxruntime import RapidOCR
        except Exception as exc:
            raise RuntimeError(
                "rapidocr-onnxruntime 未安装，请执行: pip install 'ocr-cli[ocr]'"
            ) from exc
        self._ocr = RapidOCR()

    def run(self, image_path: Path) -> OCRResult:
        if not image_path.exists() or not image_path.is_file():
            return OCRResult(status="failed", text="", blocks=[], error=f"文件不存在: {image_path}")
        try:
            Image.open(image_path).verify()
        except Exception as exc:
            return OCRResult(status="failed", text="", blocks=[], error=f"不是有效图片: {exc}")
        self.load()
        result, _ = self._ocr(str(image_path))
        if not result:
            return OCRResult(status="success", text="", blocks=[])
        blocks: list[OCRBlock] = []
        lines: list[str] = []
        for item in result:
            box, text, conf = item
            blocks.append(OCRBlock(text=text, box=box, confidence=float(conf)))
            lines.append(text)
        return OCRResult(status="success", text="\n".join(lines), blocks=blocks)
