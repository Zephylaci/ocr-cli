# ocr-cli v2

## 简介
`ocr-cli` 是一个面向 AI Agent 与自动化脚本的本地优先 OCR 命令行/HTTP 工具，支持文本、结构化 JSON 与 markdown 输出。

## 安装
```bash
pip install -e .
pip install -e '.[ocr]'
```

## 初始化
```bash
ocr-cli setup --check
ocr-cli setup
ocr-cli setup --debug
```

- `setup --check`：仅检查依赖、版本和模型目录权限。
- `setup`：预下载默认 `default` 档位模型并执行自检。
- `setup --debug`：开启 RapidOCR 调试日志。

## 模型档位 `--profile`

| 档位 | Det | Rec | OCR 版本 | 适用场景 |
|---|---|---|---|---|
| `fast` | mobile | `LangRec.CH` + mobile | PP-OCRv4 | 更快启动与吞吐 |
| `default` | mobile | `LangRec.CH` + mobile | PP-OCRv5 | 通用默认 |
| `doc` | mobile | `LangRec.CH_DOC` + mobile | PP-OCRv5 | 文档/票据排版更友好 |
| `accurate` | mobile | `LangRec.CH` + server | PP-OCRv5 | 更高精度 |

示例：
```bash
ocr-cli run demo.jpg --profile fast
ocr-cli run demo.jpg --profile default
ocr-cli run demo.jpg --profile doc
ocr-cli run demo.jpg --profile accurate
```

首次切换到某个 profile 会自动下载对应模型。`serve` 模式下 profile 在启动时锁定，不能按请求动态切换。

## 直接识别 `run`

```bash
ocr-cli run demo.jpg
ocr-cli run demo.jpg --output json
ocr-cli run demo.jpg --output markdown
```

| 参数 | 含义 | 默认 |
|---|---|---|
| `--output` | 输出格式 `text / json / markdown` | `text` |
| `--profile` | 模型档位 `fast / default / doc / accurate` | `default` |
| `--max-side-len` | 最大边长上限，超过等比缩放 | `2000` |
| `--min-side-len` | 最小边长下限，低于等比放大 | `30` |
| `--width-height-ratio` | 宽高比阈值，超过跳过检测；`-1` 禁用 | `8` |
| `--min-height` | 高度阈值，低于跳过检测 | `30` |
| `--long-image` | 长图快捷开关 | `off` |
| `--debug` | 打开 RapidOCR 详细日志 | `off` |

## 长图 / 非标准图

- 横向单行长条（票号、收据条码下一行字）：
  ```bash
  ocr-cli run receipt_line.jpg
  ```
- 横向多行长条（横屏多行评论、横向截屏）：
  ```bash
  ocr-cli run wide_multiline.jpg --width-height-ratio -1
  ```
- 纵向超长截图（手机长截图、网页全屏）：
  ```bash
  ocr-cli run long_screenshot.jpg --long-image
  ```
  当高宽比 > 10 时，建议叠加 `--max-side-len 4000~6000`。

已知限制：当前不内建超长图自动切片；极端纵长图（高宽比 > 10）建议先在外层预处理分片后再调用。

## 预处理参数详解

- `--max-side-len`（默认 `2000`）：控制最长边缩放上限。增大可提升超大图细节，但会显著增加内存占用；通常不建议超过 `4000`。
- `--width-height-ratio`（默认 `8`）：会改变识别行为的关键开关。默认适配多数场景；横向多行长图请设 `-1` 关闭阈值。
- `--min-side-len`（默认 `30`）：短边过小才需要调高，一般无需修改。
- `--min-height`（默认 `30`）：过滤过矮文本区域，绝大多数情况下保持默认即可。

## HTTP 服务 `serve`

启动：
```bash
ocr-cli serve --host 0.0.0.0 --port 8000 --profile default
```

健康检查：
```bash
curl http://127.0.0.1:8000/health
```

上传文件识别（multipart）：
```bash
curl 'http://127.0.0.1:8000/ocr/upload?output=json' -F 'file=@demo.jpg'
```

base64 识别（JSON）：
```bash
curl -X POST http://127.0.0.1:8000/ocr/base64 -H 'content-type: application/json' -d '{"image_base64":"<BASE64>","output":"markdown"}'
```

说明：profile 在服务启动时锁定；当前阶段 HTTP 接口不做鉴权。

## 输出约定

- `text`：仅识别文本。
- `json`：返回 `status / text / blocks(text/box/confidence 列表) / error / markdown`。
- `markdown`：返回 markdown 字符串。

## 退出码

- `0`：成功
- `2`：环境/依赖问题
- `3`：setup 自检失败
- 其他非零：一般运行失败

## 清理与卸载

```bash
ocr-cli cleanup --purge-models
ocr-cli cleanup --keep-models
pip uninstall -y ocr-cli rapidocr onnxruntime
```

## 已知限制

- 仅支持 CPU（不支持 GPU/NPU/MPS）
- 中英之外语种未启用
- 不内建超长图自动切片
- HTTP serve 当前阶段不做鉴权
