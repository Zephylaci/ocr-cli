from __future__ import annotations

import importlib
import os
import shutil
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from .engine import MODEL_ROOT, OCREngine


@dataclass
class CheckItem:
    name: str
    ok: bool
    reason: str = ""


def _parse_version_parts(raw_version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for seg in raw_version.split("."):
        digits = ""
        for ch in seg:
            if ch.isdigit():
                digits += ch
            else:
                break
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def run_setup(check_only: bool, debug: bool) -> int:
    checks: list[CheckItem] = []
    for mod in ["PIL", "typer", "fastapi", "onnxruntime"]:
        try:
            importlib.import_module(mod)
            checks.append(CheckItem(mod, True))
        except Exception as exc:
            checks.append(CheckItem(mod, False, str(exc)))

    try:
        rapidocr_ver = version("rapidocr")
        parsed = _parse_version_parts(rapidocr_ver)
        rapidocr_ok = parsed >= (3, 2)
        checks.append(CheckItem("rapidocr>=3.2.0", rapidocr_ok, "" if rapidocr_ok else f"当前版本: {rapidocr_ver}"))
    except PackageNotFoundError:
        checks.append(CheckItem("rapidocr>=3.2.0", False, "未安装 rapidocr"))
    except Exception as exc:
        checks.append(CheckItem("rapidocr>=3.2.0", False, str(exc)))

    for c in checks:
        print(f"[{'✓' if c.ok else '✗'}] {c.name}{(' - ' + c.reason) if c.reason else ''}")

    model_dir = MODEL_ROOT
    if not model_dir.exists():
        model_dir.mkdir(parents=True, exist_ok=True)
    writable = model_dir.exists() and model_dir.is_dir() and os.access(model_dir, os.W_OK)
    print(f"[{'✓' if writable else '✗'}] 模型目录可写: {model_dir}")

    if check_only:
        ready = all(c.ok for c in checks) and writable
        print("[READY]" if ready else "[FAIL]")
        return 0 if ready else 2

    if not all(c.ok for c in checks) or not writable:
        print("[FAIL]")
        return 2

    try:
        engine = OCREngine(profile="default", debug=debug)
        engine.load()
        sample = model_dir / "selftest.png"
        from PIL import Image

        Image.new("RGB", (32, 32), "white").save(sample)
        ret = engine.run(sample)
        if ret.status != "success":
            print(f"[✗] 验证失败: {ret.error}")
            print("[FAIL]")
            return 3
    except Exception as exc:
        print(f"[✗] 验证失败: {exc}")
        print("[FAIL]")
        return 3

    print("[✓] 验证通过")
    print("[READY]")
    return 0


def run_cleanup(purge_models: bool) -> int:
    print("[i] 建议卸载命令: pip uninstall -y ocr-cli rapidocr onnxruntime")
    if purge_models and MODEL_ROOT.exists():
        shutil.rmtree(MODEL_ROOT)
        print(f"[✓] 已删除模型目录: {MODEL_ROOT}")
    print("[READY]")
    return 0
