# StartThinking

一个给个人使用的静态复习网站：导入资料、生成题目和闪卡、按间隔复习队列背诵知识点。

## 当前能力

- TXT / Markdown / CSV / JSON 文件可直接读取并生成题目。
- PDF / DOCX / PPTX 可记录文件名；正文建议复制到输入框生成。
- 根据资料自动生成单选题、填空题、简答题和闪卡。
- 所有学习集、复习进度、错题和设置保存在当前浏览器本地。
- 简化版间隔复习调度：按“忘记 / 模糊 / 记住 / 熟练”调整下次复习时间。
- 可导出本地 JSON 备份。

## 本地打开

直接打开 `index.html` 即可使用。也可以用任意静态服务器托管。

## GitHub Pages

这个项目无需构建步骤。推送到 GitHub 后，在仓库的 `Settings -> Pages` 中选择：

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/ (root)`

保存后等待 GitHub Pages 发布。

## 后续可扩展

- 接入 OpenAI / Gemini / Ollama 生成更高质量的题目。
- 使用 PDF.js / mammoth.js 增加浏览器端 PDF、DOCX 正文解析。
- 把 localStorage 升级为 IndexedDB，支持更大的资料库和附件索引。
