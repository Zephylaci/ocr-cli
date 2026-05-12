# ocr-cli

本项目是一个**本地优先**的 OCR 工具，面向 Agent 调用场景，提供 CLI 与 HTTP 服务两种模式。

## 1. 安装

```bash
pip install -e .
pip install -e '.[ocr]'
```

## 2. 初始化环境

1) 仅检查（不修改环境）
```bash
ocr-cli setup --check
```

2) 完整初始化 + 自检
```bash
ocr-cli setup
```

## 3. 直接识别（run）

1) 纯文本输出（默认）
```bash
ocr-cli run ./demo.png
```

2) JSON 输出
```bash
ocr-cli run ./demo.png --output json
```

## 4. HTTP 服务（serve）

1) 启动服务
```bash
ocr-cli serve --host 0.0.0.0 --port 8000
```

2) 健康检查
```bash
curl http://127.0.0.1:8000/health
```

3) 上传文件识别
```bash
curl -F 'file=@./demo.png' 'http://127.0.0.1:8000/ocr/upload?output=json'
```

4) Base64 识别
```bash
curl -X POST http://127.0.0.1:8000/ocr/base64 \
  -H 'content-type: application/json' \
  -d '{"image_base64":"<BASE64>","output":"json"}'
```

## 5. 输出约定

- text 模式：仅输出识别文本。
- json 模式：`status` / `text` / `blocks` / `error` 字段稳定存在（失败时 `error` 非空）。

## 6. 退出码

- `0` 成功
- 非 `0` 失败

## 7. 清理与卸载

1) 清理本地模型目录（`~/.ocr-cli/models`）
```bash
ocr-cli cleanup --purge-models
```

2) 仅保留模型，不执行删除
```bash
ocr-cli cleanup --keep-models
```

3) 卸载 Python 依赖（手动执行）
```bash
pip uninstall -y ocr-cli rapidocr-onnxruntime
```
