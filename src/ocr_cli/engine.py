from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from .types import OCRBlock, OCRResult

MODEL_ROOT = Path.home() / ".ocr-cli" / "models"


@dataclass(frozen=True)
class ProfileConfig:
    ocr_version: str
    model_type: str
    lang_type: str


PROFILE_MAP: dict[str, ProfileConfig] = {
    "fast": ProfileConfig("PP-OCRv4", "mobile", "ch"),
    "default": ProfileConfig("PP-OCRv5", "mobile", "ch"),
    "doc": ProfileConfig("PP-OCRv5", "mobile", "ch_doc"),
    "accurate": ProfileConfig("PP-OCRv5", "server", "ch"),
}


class OCREngine:
    def __init__(self, profile: str = "default", debug: bool = False) -> None:
        if profile not in PROFILE_MAP:
            raise ValueError(f"不支持的 profile: {profile}")
        self.profile = profile
        self.debug = debug
        self._ocr: Any | None = None

    def load(self) -> None:
        if self._ocr is not None:
            return
        try:
            from rapidocr import RapidOCR
        except Exception as exc:
            raise RuntimeError("rapidocr 未安装，请执行: pip install -e '.[ocr]'") from exc
        p = PROFILE_MAP[self.profile]
        self._ocr = RapidOCR(
            model_root_dir=str(MODEL_ROOT),
            det_use_cuda=False,
            rec_use_cuda=False,
            cls_use_cuda=False,
            text_det_model_type=p.model_type,
            text_det_ocr_version=p.ocr_version,
            text_rec_model_type=p.model_type,
            text_rec_lang_type=p.lang_type,
            text_rec_ocr_version=p.ocr_version,
        )

    def run(
        self,
        image_path: Path,
        *,
        max_side_len: int = 2000,
        min_side_len: int = 30,
        width_height_ratio: float = 8,
        min_height: int = 30,
        markdown: bool = False,
    ) -> OCRResult:
        if max_side_len <= 0 or min_side_len <= 0 or min_height <= 0:
            return OCRResult(status="failed", text="", blocks=[], error="预处理参数必须为正数")
        if not image_path.exists() or not image_path.is_file():
            return OCRResult(status="failed", text="", blocks=[], error=f"文件不存在: {image_path}")
        try:
            Image.open(image_path).verify()
        except Exception as exc:
            return OCRResult(status="failed", text="", blocks=[], error=f"不是有效图片: {exc}")
        self.load()
        kwargs: dict[str, Any] = {
            "max_side_len": max_side_len,
            "min_side_len": min_side_len,
            "width_height_ratio": width_height_ratio,
            "min_height": min_height,
        }
        if markdown:
            kwargs["return_word_box"] = True
            kwargs["return_single_char_box"] = True

        result = self._ocr(str(image_path), **kwargs)
        if hasattr(result, "to_markdown"):
            md = result.to_markdown() if markdown else ""
            lines = getattr(result, "txts", None) or []
            text = "\n".join(lines)
            rec_res = getattr(result, "rec_res", []) or []
            boxes = getattr(result, "boxes", []) or []
            blocks = [
                OCRBlock(text=r[0], box=boxes[i] if i < len(boxes) else [], confidence=float(r[1]))
                for i, r in enumerate(rec_res)
            ]
            return OCRResult(status="success", text=text, blocks=blocks, markdown=md)

        raw, _ = result
        if not raw:
            return OCRResult(status="success", text="", blocks=[], markdown="")
        blocks: list[OCRBlock] = []
        lines: list[str] = []
        for item in raw:
            box, text, conf = item
            blocks.append(OCRBlock(text=text, box=box, confidence=float(conf)))
            lines.append(text)
        return OCRResult(status="success", text="\n".join(lines), blocks=blocks)
