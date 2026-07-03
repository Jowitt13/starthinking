const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const fs = require("fs/promises");
const path = require("path");
const os = require("os");
const { spawn } = require("child_process");

const ROOT = path.join(__dirname, "..");

function createWindow() {
  const win = new BrowserWindow({
    width: 1380,
    height: 880,
    minWidth: 1040,
    minHeight: 720,
    title: "StartThinking",
    backgroundColor: "#f6f8fb",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  win.loadFile(path.join(ROOT, "index.html"));
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

ipcMain.handle("materials:choose-files", async () => {
  const result = await dialog.showOpenDialog({
    title: "选择复习资料",
    properties: ["openFile", "multiSelections"],
    filters: [
      {
        name: "学习资料",
        extensions: ["pdf", "png", "jpg", "jpeg", "webp", "txt", "md", "csv", "json", "docx", "pptx"],
      },
      { name: "所有文件", extensions: ["*"] },
    ],
  });

  if (result.canceled) return [];
  return Promise.all(result.filePaths.map(fileInfo));
});

ipcMain.handle("materials:extract-files", async (_event, payload) => {
  const files = payload?.files || [];
  const settings = payload?.settings || {};
  const docs = [];

  for (const file of files) {
    docs.push(await extractFile(file.path, settings));
  }

  return docs;
});

ipcMain.handle("ai:generate-study-set", async (_event, payload) => {
  const settings = payload?.settings || {};
  const text = String(payload?.text || "").trim();
  const title = String(payload?.title || "新学习集").trim();

  if (!text) throw new Error("没有可生成的文本。");
  if ((settings.llmProvider || "ollama") !== "ollama") {
    throw new Error("当前桌面版只内置 Ollama 本地模型适配。");
  }

  return generateWithOllama({
    text,
    title,
    endpoint: settings.ollamaUrl || "http://127.0.0.1:11434",
    model: settings.ollamaModel || "qwen3.5:4b",
    count: Number(settings.generationCount || 12),
  });
});

ipcMain.handle("services:check", async (_event, payload) => {
  const settings = payload?.settings || {};
  const ollamaUrl = settings.ollamaUrl || "http://127.0.0.1:11434";
  const ocrScript = settings.unlimitedOcrScript || "";
  const pythonPath = settings.pythonPath || "python";

  const [ollama, unlimitedOcr] = await Promise.all([
    checkOllama(ollamaUrl),
    checkUnlimitedOcr({ pythonPath, scriptPath: ocrScript }),
  ]);

  return { ollama, unlimitedOcr };
});

ipcMain.handle("shell:open-external", async (_event, url) => {
  await shell.openExternal(url);
});

async function fileInfo(filePath) {
  const stat = await fs.stat(filePath);
  const ext = path.extname(filePath).toLowerCase().replace(".", "");
  return {
    path: filePath,
    name: path.basename(filePath),
    ext,
    size: stat.size,
  };
}

async function extractFile(filePath, settings) {
  const info = await fileInfo(filePath);
  const ext = info.ext;
  const textExts = new Set(["txt", "md", "csv", "json"]);

  if (textExts.has(ext)) {
    return {
      ...info,
      method: "text",
      text: await fs.readFile(filePath, "utf8"),
    };
  }

  const ocrText = await runUnlimitedOcr(filePath, settings);
  return {
    ...info,
    method: "unlimited-ocr",
    text: ocrText,
  };
}

async function runUnlimitedOcr(filePath, settings) {
  const scriptPath = settings.unlimitedOcrScript;
  if (!scriptPath) {
    throw new Error("还没有设置 Unlimited-OCR 的 infer.py 路径。");
  }

  const pythonPath = settings.pythonPath || "python";
  const concurrency = String(settings.ocrConcurrency || 2);
  const imageMode = settings.ocrImageMode || "gundam";
  const outputDir = await fs.mkdtemp(path.join(os.tmpdir(), "startthinking-ocr-"));
  const ext = path.extname(filePath).toLowerCase();
  const isPdf = ext === ".pdf";
  const isImage = [".png", ".jpg", ".jpeg", ".webp", ".bmp"].includes(ext);

  if (!isPdf && !isImage) {
    throw new Error(`${path.basename(filePath)} 需要先转成 PDF 或图片再交给 Unlimited-OCR。`);
  }

  const args = [
    scriptPath,
    isPdf ? "--pdf" : "--image_dir",
    isPdf ? filePath : await imageDirFor(filePath),
    "--output_dir",
    outputDir,
    "--concurrency",
    concurrency,
    "--image_mode",
    imageMode,
  ];

  await runProcess(pythonPath, args, { timeoutMs: Number(settings.ocrTimeoutMs || 20 * 60 * 1000) });
  const text = await collectText(outputDir);
  if (!text.trim()) {
    throw new Error("Unlimited-OCR 已执行，但没有找到可读取的文本输出。请检查 output_dir 文件结构。");
  }
  return text.trim();
}

async function imageDirFor(filePath) {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "startthinking-image-"));
  await fs.copyFile(filePath, path.join(dir, path.basename(filePath)));
  return dir;
}

function runProcess(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: ROOT,
      windowsHide: true,
      shell: false,
    });
    const chunks = [];
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`命令超时：${command}`));
    }, options.timeoutMs || 120000);

    child.stdout.on("data", (data) => chunks.push(data.toString()));
    child.stderr.on("data", (data) => chunks.push(data.toString()));
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code === 0) resolve(chunks.join(""));
      else reject(new Error(chunks.join("") || `${command} 退出码 ${code}`));
    });
  });
}

async function collectText(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const parts = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      parts.push(await collectText(fullPath));
      continue;
    }
    if (/\.(txt|md|json)$/i.test(entry.name)) {
      const raw = await fs.readFile(fullPath, "utf8");
      parts.push(extractReadableText(raw));
    }
  }

  return parts.filter(Boolean).join("\n\n");
}

function extractReadableText(raw) {
  const trimmed = raw.trim();
  if (!trimmed) return "";
  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) return trimmed;
  try {
    const parsed = JSON.parse(trimmed);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return trimmed;
  }
}

async function checkOllama(endpoint) {
  try {
    const response = await fetch(`${endpoint.replace(/\/$/, "")}/api/tags`, { signal: AbortSignal.timeout(4000) });
    return { ok: response.ok, message: response.ok ? "Ollama 可用" : `Ollama 返回 ${response.status}` };
  } catch (error) {
    return { ok: false, message: `Ollama 未连接：${error.message}` };
  }
}

async function checkUnlimitedOcr({ pythonPath, scriptPath }) {
  if (!scriptPath) return { ok: false, message: "未设置 infer.py 路径" };
  try {
    await fs.access(scriptPath);
    const output = await runProcess(pythonPath, ["--version"], { timeoutMs: 10000 });
    return { ok: true, message: `已找到 Unlimited-OCR 脚本；${output.trim()}` };
  } catch (error) {
    return { ok: false, message: error.message };
  }
}

async function generateWithOllama({ endpoint, model, text, title, count }) {
  const prompt = `你是严谨的个人复习出题助手。请只基于给定资料生成复习内容，不要编造资料外事实。

输出必须是严格 JSON，不要 Markdown，不要解释。结构如下：
{
  "title": "学习集标题",
  "questions": [
    {"type":"single","prompt":"题干","options":["A","B","C","D"],"answer":"正确答案文本","difficulty":"简单|中等|困难","topic":"知识点"},
    {"type":"short","prompt":"简答题","answer":"参考答案","difficulty":"简单|中等|困难","topic":"知识点"},
    {"type":"cloze","prompt":"带 ______ 的填空句","answer":"填空答案","difficulty":"简单|中等|困难","topic":"知识点"}
  ],
  "cards": [
    {"front":"卡片正面","back":"卡片背面","difficulty":"简单|中等|困难","topic":"知识点"}
  ]
}

要求：
- 题目总数约 ${count} 个，闪卡约 ${Math.max(4, Math.floor(count * 0.7))} 张。
- 题目要适合主动回忆和考试复习。
- 单选题选项必须互斥，答案必须与选项之一完全一致。
- 尽量覆盖定义、区别、步骤、原因、例子、易错点。

标题：${title}

资料：
${text.slice(0, 24000)}`;

  const response = await fetch(`${endpoint.replace(/\/$/, "")}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      stream: false,
      messages: [
        { role: "system", content: "你只输出严格 JSON。" },
        { role: "user", content: prompt },
      ],
      options: { temperature: 0.2 },
    }),
    signal: AbortSignal.timeout(180000),
  });

  if (!response.ok) throw new Error(`Ollama 返回 ${response.status}`);
  const data = await response.json();
  const content = data?.message?.content || "";
  return normalizeGeneratedJson(parseJsonFromText(content), title);
}

function parseJsonFromText(text) {
  const raw = text.trim();
  try {
    return JSON.parse(raw);
  } catch {
    const match = raw.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("本地模型没有返回 JSON。");
    return JSON.parse(match[0]);
  }
}

function normalizeGeneratedJson(data, fallbackTitle) {
  if (!data || !Array.isArray(data.questions) || !Array.isArray(data.cards)) {
    throw new Error("本地模型返回的 JSON 结构不符合要求。");
  }
  return {
    title: data.title || fallbackTitle,
    questions: data.questions.slice(0, 40),
    cards: data.cards.slice(0, 40),
  };
}
