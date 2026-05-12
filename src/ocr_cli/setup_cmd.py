from __future__ import annotations

import importlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from .engine import OCREngine

MODEL_DIR = Path.home() / ".ocr-cli" / "models"


@dataclass
class CheckItem:
    name: str
    ok: bool
    reason: str = ""


def _print_check_result(checks: list[CheckItem]) -> None:
    for c in checks:
        marker = "✓" if c.ok else "✗"
        msg = f"[{marker}] {c.name}"
        if c.reason:
            msg += f" - {c.reason}"
        print(msg)


def run_setup(check_only: bool, debug: bool) -> int:
    checks: list[CheckItem] = []
    for mod in ["PIL", "typer", "fastapi"]:
        try:
            importlib.import_module(mod)
            checks.append(CheckItem(mod, True))
        except Exception as exc:
            checks.append(CheckItem(mod, False, str(exc)))

    try:
        importlib.import_module("rapidocr_onnxruntime")
        checks.append(CheckItem("rapidocr_onnxruntime", True))
    except Exception as exc:
        checks.append(CheckItem("rapidocr_onnxruntime", False, f"未安装: {exc}"))

    _print_check_result(checks)
    print(f"[i] 模型目录: {MODEL_DIR}")
    print(f"[i] 模型目录存在: {'是' if MODEL_DIR.exists() else '否'}")

    if check_only:
        ready = all(c.ok for c in checks)
        print("[READY]" if ready else "[FAIL]")
        return 0 if ready else 2

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[✓] 模型目录已就绪: {MODEL_DIR}")

    if not all(c.ok for c in checks):
        print("[FAIL]")
        return 2

    sample = MODEL_DIR / "selftest.png"
    from PIL import Image

    Image.new("RGB", (32, 32), "white").save(sample)
    try:
        engine = OCREngine(debug=debug)
        ret = engine.run(sample)
        if ret.status != "success":
            print("[✗] 验证失败:", json.dumps(ret.to_dict(), ensure_ascii=False))
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
    print("[i] 清理说明: Python 依赖需要通过 pip 卸载，本命令仅清理本地模型与缓存。")
    print("[i] 建议卸载命令: pip uninstall -y ocr-cli rapidocr-onnxruntime")

    if purge_models:
        if MODEL_DIR.exists():
            shutil.rmtree(MODEL_DIR)
            print(f"[✓] 已删除模型目录: {MODEL_DIR}")
        else:
            print(f"[i] 模型目录不存在，无需删除: {MODEL_DIR}")

    home_dir = Path.home() / ".ocr-cli"
    if home_dir.exists() and not any(home_dir.iterdir()):
        home_dir.rmdir()
        print(f"[✓] 已删除空目录: {home_dir}")

    print("[READY]")
    return 0
