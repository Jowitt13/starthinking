# StartThinking Desktop

本地 AI 复习软件：导入资料，使用 Unlimited-OCR 识别 PDF/图片，再用本地 Qwen3.5-4B 生成题目、闪卡和复习队列。

## 当前可运行版本

当前主入口是 Python 桌面版，不需要下载前端依赖：

```powershell
desktop_python\run_startthinking.bat
```

如果系统提示没有 Python，可以安装 Python 3.11+，或者继续使用 Codex 自带 Python 路径运行：

```powershell
C:\Users\hangi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe desktop_python\startthinking.py
```

## 架构

- 桌面壳：Python Tkinter（当前可运行主版本）
- 可选桌面壳：Electron（源码已保留，安装依赖后可继续升级）
- OCR：调用本机 `baidu/Unlimited-OCR` 的 `infer.py`
- 本地大模型：Ollama，默认 `qwen3.5:4b`
- 数据保存：`data/startthinking.json`，资料和生成结果不上传云端

## 准备本地模型

安装 Ollama 后拉取默认模型：

```powershell
ollama pull qwen3.5:4b
```

Ollama 默认服务地址是：

```text
http://127.0.0.1:11434
```

## 准备 Unlimited-OCR

项目地址：

```text
https://github.com/baidu/Unlimited-OCR
```

按官方 README 安装依赖和模型后，在 StartThinking 的“设置”里填写：

- Python：例如 `python` 或你的虚拟环境 Python 路径
- Unlimited-OCR infer.py：例如 `C:\AI\Unlimited-OCR\infer.py`
- OCR 并发：个人电脑建议先用 `1` 或 `2`

PDF 和图片导入时，软件会调用：

```text
python infer.py --pdf <file> --output_dir <temp> --concurrency <n> --image_mode <mode>
```

图片会先放入临时目录，然后用 `--image_dir` 调用。

## Electron 可选版本

```powershell
npm install
npm start
```

如果 PowerShell 拦截 `npm.ps1`，用：

```powershell
npm.cmd install
npm.cmd start
```

## 当前能力

- 直接读取 TXT / MD / CSV / JSON。
- PDF / PNG / JPG / JPEG / WEBP 通过 Unlimited-OCR 识别。
- 调用 Ollama `qwen3.5:4b` 生成单选题、填空题、简答题和闪卡。
- Ollama 或 Unlimited-OCR 不可用时，文本资料会回退到本地启发式生成。
- 按“忘记 / 模糊 / 记住 / 熟练”调整下次复习时间。
- 可导出本地 JSON 备份。

## 模型选择

默认使用 `qwen3.5:4b`，原因：

- 体积约 3.4GB，个人电脑更容易跑起来。
- 256K 上下文，适合长资料总结和出题。
- 中文、多语言、视觉能力都比普通小模型更适合学习资料处理。
