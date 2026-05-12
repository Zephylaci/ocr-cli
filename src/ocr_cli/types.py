from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class OCRBlock:
    text: str
    box: list[list[float]]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OCRResult:
    status: str
    text: str
    blocks: list[OCRBlock]
    error: str | None = None
    markdown: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "text": self.text,
            "blocks": [b.to_dict() for b in self.blocks],
            "error": self.error,
            "markdown": self.markdown,
        }
