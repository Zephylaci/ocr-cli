# ocr-cli v2

## 安装
```bash
pip install -e .
pip install -e '.[ocr]'
```

## setup
```bash
ocr-cli setup --check
ocr-cli setup
```

## run
```bash
ocr-cli run demo.jpg
ocr-cli run demo.jpg --output json
ocr-cli run bill.png --profile doc --output markdown
ocr-cli run long_chat.png --long-image
ocr-cli run banner.png --width-height-ratio -1
```

参数：
- `--profile`: `fast|default|doc|accurate`（默认 `default`）
- `--output`: `text|json|markdown`（默认 `text`）
- 预处理：`--max-side-len` `--min-side-len` `--width-height-ratio` `--min-height`
- `--long-image`: 等价于 `max_side_len=4000` + `width_height_ratio=-1`（可被显式参数覆盖）

## serve
```bash
ocr-cli serve --host 0.0.0.0 --port 8000 --profile default
curl 'http://127.0.0.1:8000/ocr/upload?output=markdown&long_image=true' -F 'file=@demo.jpg'
curl -X POST http://127.0.0.1:8000/ocr/base64 -H 'content-type: application/json' -d '{"image_base64":"<BASE64>","output":"markdown"}'
```

## cleanup
```bash
ocr-cli cleanup --purge-models
pip uninstall -y ocr-cli rapidocr onnxruntime
```
