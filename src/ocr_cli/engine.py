from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from .types import OCRBlock, OCRResult

MODEL_ROOT = Path.home() / ".ocr-cli" / "models"


@dataclass(frozen=True)
class ProfileConfig:
    det_model_type: str
    rec_model_type: str
    ocr_version: str


PROFILE_MAP: dict[str, ProfileConfig] = {
    "fast": ProfileConfig("mobile", "mobile", "PP-OCRv4"),
    "default": ProfileConfig("mobile", "mobile", "PP-OCRv5"),
    "accurate": ProfileConfig("mobile", "server", "PP-OCRv5"),
}


class OCREngine:
    def __init__(self, profile: str = "default", debug: bool = False) -> None:
        if profile not in PROFILE_MAP:
            valid = ", ".join(sorted(PROFILE_MAP))
            raise ValueError(f"不支持的 profile: {profile}（可选: {valid}）")
        self.profile = profile
        self.debug = debug
        self._ocr: Any | None = None
        self._params_key: tuple[Any, ...] | None = None

    def _build_params(
        self,
        *,
        max_side_len: int,
        min_side_len: int,
        width_height_ratio: float,
        min_height: int,
        debug: bool,
    ) -> dict[str, Any]:
        from rapidocr import EngineType, LangCls, LangDet, LangRec, ModelType, OCRVersion

        p = PROFILE_MAP[self.profile]
        return {
            "Global.model_root_dir": str(MODEL_ROOT),
            "Global.max_side_len": max_side_len,
            "Global.min_side_len": min_side_len,
            "Global.width_height_ratio": width_height_ratio,
            "Global.min_height": min_height,
            "Global.log_level": "debug" if debug else "critical",
            "Det.engine_type": EngineType.ONNXRUNTIME,
            "Det.lang_type": LangDet.CH,
            "Det.model_type": ModelType.MOBILE if p.det_model_type == "mobile" else ModelType.SERVER,
            "Det.ocr_version": OCRVersion.PPOCRV4 if p.ocr_version == "PP-OCRv4" else OCRVersion.PPOCRV5,
            "Cls.engine_type": EngineType.ONNXRUNTIME,
            "Cls.lang_type": LangCls.CH,
            "Rec.engine_type": EngineType.ONNXRUNTIME,
            "Rec.lang_type": LangRec.CH,
            "Rec.model_type": ModelType.MOBILE if p.rec_model_type == "mobile" else ModelType.SERVER,
            "Rec.ocr_version": OCRVersion.PPOCRV4 if p.ocr_version == "PP-OCRv4" else OCRVersion.PPOCRV5,
        }

    def _ensure_loaded(self, params_key: tuple[Any, ...], params: dict[str, Any]) -> None:
        if self._ocr is not None and self._params_key == params_key:
            return
        try:
            from rapidocr import RapidOCR
        except Exception as exc:
            raise RuntimeError("rapidocr 未安装，请执行: pip install -e '.[ocr]'") from exc
        self._ocr = RapidOCR(params=params)
        self._params_key = params_key

    def load(self) -> None:
        params_key = (self.profile, 2000, 30, 8.0, 30, self.debug)
        params = self._build_params(
            max_side_len=2000,
            min_side_len=30,
            width_height_ratio=8,
            min_height=30,
            debug=self.debug,
        )
        self._ensure_loaded(params_key, params)

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

        params_key = (self.profile, max_side_len, min_side_len, float(width_height_ratio), min_height, self.debug)
        params = self._build_params(
            max_side_len=max_side_len,
            min_side_len=min_side_len,
            width_height_ratio=width_height_ratio,
            min_height=min_height,
            debug=self.debug,
        )
        self._ensure_loaded(params_key, params)

        result = self._ocr(
            str(image_path),
            return_word_box=markdown,
            return_single_char_box=markdown,
        )

        def _as_list(value: Any) -> list[Any]:
            if value is None:
                return []
            tolist = getattr(value, "tolist", None)
            return tolist() if callable(tolist) else list(value)

        txts = _as_list(getattr(result, "txts", None))
        scores = _as_list(getattr(result, "scores", None))
        boxes = _as_list(getattr(result, "boxes", None))
        text = "\n".join(str(x) for x in txts)
        blocks: list[OCRBlock] = []
        for i, txt in enumerate(txts):
            raw_box = boxes[i] if i < len(boxes) else []
            box = raw_box.tolist() if hasattr(raw_box, "tolist") else raw_box
            confidence = float(scores[i]) if i < len(scores) else 0.0
            blocks.append(OCRBlock(text=str(txt), box=box, confidence=confidence))

        md = result.to_markdown() if markdown and hasattr(result, "to_markdown") else ""
        return OCRResult(status="success", text=text, blocks=blocks, markdown=md)
