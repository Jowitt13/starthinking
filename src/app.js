const STORAGE_KEY = "startthinking-desktop-state-v2";
const desktop = window.StartThinkingDesktop;

const icons = {
  brain:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 3a3 3 0 0 0-3 3v1a3 3 0 0 0-2 5.2A3.6 3.6 0 0 0 6.6 19H9"/><path d="M15 3a3 3 0 0 1 3 3v1a3 3 0 0 1 2 5.2A3.6 3.6 0 0 1 17.4 19H15"/><path d="M9 3v18M15 3v18M9 8h3M12 14h3M6 12h3M15 9h3"/></svg>',
  home:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></svg>',
  book:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5z"/></svg>',
  spark:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v5M12 16v5M5.6 5.6l3.5 3.5M14.9 14.9l3.5 3.5M3 12h5M16 12h5M5.6 18.4l3.5-3.5M14.9 9.1l3.5-3.5"/></svg>',
  clock:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  network:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><circle cx="12" cy="14" r="2"/><path d="M12 7v5M10.4 15.3 6.6 17.7M13.6 15.3l3.8 2.4"/></svg>',
  gear:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2 3.4-.2-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V22h-4v-.5a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.2.1-2-3.4.1-.1A1.7 1.7 0 0 0 4.6 15 1.7 1.7 0 0 0 3 14H2v-4h1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1 2-3.4.2.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5V2h4v.5a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.2-.1 2 3.4-.1.1A1.7 1.7 0 0 0 19.4 9 1.7 1.7 0 0 0 21 10h1v4h-1a1.7 1.7 0 0 0-1.6 1z"/></svg>',
  upload:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15V3"/><path d="m7 8 5-5 5 5"/><path d="M5 15v4h14v-4"/></svg>',
  plus:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>',
  close:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>',
  file:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6v20h12V8z"/><path d="M14 2v6h6"/><path d="M9 13h6M9 17h6"/></svg>',
  trash:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M6 6l1 16h10l1-16"/></svg>',
};

const sampleText = `机器学习是一种让计算机从数据中学习规律的方法。监督学习使用带标签的数据训练模型，常见任务包括分类和回归。
过拟合是指模型在训练集上表现很好，但在测试集或新数据上表现较差。常见缓解方法包括正则化、交叉验证、早停和增加数据。
梯度下降通过沿损失函数负梯度方向迭代更新参数，学习率决定每一步更新幅度。学习率过大可能震荡，过小会收敛缓慢。
特征缩放可以让不同量纲的特征处在相近范围，常见方法包括标准化和归一化。它通常能改善基于距离或梯度的模型训练效果。
混淆矩阵用于评估分类模型，包含真正例、假正例、真反例和假反例。准确率、精确率、召回率和 F1 值都可以从中计算。`;

const initialState = {
  view: "dashboard",
  mode: "smart",
  drawerOpen: false,
  drawerTab: "questions",
  revealAnswer: false,
  currentReviewId: null,
  pasteText: sampleText,
  busy: "",
  serviceStatus: null,
  settings: {
    dailyTarget: 35,
    generationCount: 12,
    autoAddQueue: true,
    llmProvider: "ollama",
    ollamaUrl: "http://127.0.0.1:11434",
    ollamaModel: "qwen3.5:4b",
    pythonPath: "python",
    unlimitedOcrScript: "",
    ocrConcurrency: 2,
    ocrImageMode: "gundam",
    ocrTimeoutMs: 1200000,
  },
  sets: [],
  reviewLog: [],
};

let state = loadState();

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return seedState();
    return mergeState(initialState, JSON.parse(raw));
  } catch {
    return seedState();
  }
}

function mergeState(base, saved) {
  return {
    ...base,
    ...saved,
    settings: { ...base.settings, ...(saved.settings || {}) },
  };
}

function seedState() {
  const seed = mergeState(initialState, {});
  const generated = createStudySet("机器学习：监督学习笔记", sampleText, "示例资料");
  generated.createdAt = new Date(Date.now() - 1000 * 60 * 60 * 28).toISOString();
  seed.sets = [generated];
  seed.currentReviewId = dueItems(seed)[0]?.id || null;
  return seed;
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function setState(patch) {
  state = mergeState(state, patch);
  saveState();
  render();
}

function uid(prefix = "id") {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function splitMaterial(text) {
  const normalized = String(text || "")
    .replace(/\r/g, "\n")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  const paragraphs = normalized
    .split(/\n+|(?<=[。！？.!?])\s+/)
    .map((part) => part.trim())
    .filter((part) => part.length > 18);
  return paragraphs.length ? paragraphs : [normalized].filter(Boolean);
}

function extractKeyword(sentence, index) {
  const clean = sentence.replace(/[，。！？；：,.!?;:()（）《》“”"']/g, " ");
  const candidates = clean
    .split(/\s+|、/)
    .map((word) => word.trim())
    .filter((word) => word.length >= 2 && word.length <= 18)
    .filter((word) => !/^(一种|一个|可以|用于|通过|常见|包括|如果|因为|所以|以及|进行|方法)$/.test(word));
  if (candidates.length) return candidates[index % candidates.length];
  const chinese = sentence.match(/[\u4e00-\u9fa5]{2,8}/g) || [];
  return chinese[index % Math.max(1, chinese.length)] || `知识点 ${index + 1}`;
}

function makeDistractors(keyword, pool) {
  const defaults = ["正则化", "混淆矩阵", "梯度下降", "监督学习", "特征缩放", "交叉验证", "召回率"];
  return [...new Set([...pool, ...defaults].filter((item) => item && item !== keyword))].slice(0, 3);
}

function createStudySet(title, text, sourceName = "粘贴资料") {
  const paragraphs = splitMaterial(text);
  const keywords = paragraphs.map(extractKeyword);
  const count = clamp(Number(state?.settings?.generationCount || 12), 4, 30);
  const selected = paragraphs.slice(0, count);
  const setId = uid("set");

  const items = selected.map((paragraph, index) => {
    const keyword = extractKeyword(paragraph, index);
    const type = index % 5 === 2 ? "short" : index % 4 === 1 ? "cloze" : "single";
    const base = baseReviewItem({ setId, type, topic: keyword, source: sourceName, index });

    if (type === "cloze") {
      base.prompt = paragraph.replace(keyword, "______");
      base.answer = keyword;
      base.context = paragraph;
    } else if (type === "short") {
      base.prompt = `简述「${keyword}」相关知识点。`;
      base.answer = paragraph;
    } else {
      const distractors = makeDistractors(keyword, keywords);
      base.prompt = "关于这段资料，最关键的概念是哪一个？";
      base.options = shuffle([keyword, ...distractors]).slice(0, 4);
      base.answer = keyword;
      base.context = paragraph;
    }
    return base;
  });

  const cards = selected.slice(0, Math.max(4, Math.floor(count * 0.7))).map((paragraph, index) => {
    const keyword = extractKeyword(paragraph, index + 2);
    return {
      ...baseReviewItem({ setId, type: "card", topic: keyword, source: sourceName, index }),
      prompt: keyword,
      answer: paragraph,
      difficulty: index % 3 === 0 ? "中等" : "简单",
    };
  });

  return {
    id: setId,
    title: title || guessTitle(text),
    sourceName,
    createdAt: new Date().toISOString(),
    text,
    items,
    cards,
  };
}

function createStudySetFromAi(payload, text, sourceName) {
  const setId = uid("set");
  const title = payload.title || guessTitle(text);
  const questions = (payload.questions || []).map((question, index) => ({
    ...baseReviewItem({
      setId,
      type: question.type || "short",
      topic: question.topic || extractKeyword(question.prompt || question.answer || text, index),
      source: sourceName,
      index,
    }),
    prompt: question.prompt || "请回忆这个知识点。",
    options: Array.isArray(question.options) ? question.options.slice(0, 4) : undefined,
    answer: question.answer || "",
    difficulty: normalizeDifficulty(question.difficulty),
  }));

  const cards = (payload.cards || []).map((card, index) => ({
    ...baseReviewItem({
      setId,
      type: "card",
      topic: card.topic || extractKeyword(card.front || card.back || text, index),
      source: sourceName,
      index,
    }),
    prompt: card.front || card.prompt || "知识卡片",
    answer: card.back || card.answer || "",
    difficulty: normalizeDifficulty(card.difficulty),
  }));

  return {
    id: setId,
    title,
    sourceName,
    createdAt: new Date().toISOString(),
    text,
    items: questions.length ? questions : createStudySet(title, text, sourceName).items,
    cards: cards.length ? cards : createStudySet(title, text, sourceName).cards,
  };
}

function baseReviewItem({ setId, type, topic, source, index }) {
  return {
    id: uid(type === "card" ? "card" : "item"),
    setId,
    type,
    topic,
    source,
    prompt: "",
    answer: "",
    difficulty: index % 4 === 0 ? "困难" : index % 3 === 0 ? "简单" : "中等",
    interval: 0,
    ease: 2.45,
    dueAt: new Date(Date.now() + (index < 5 ? -1 : index * 1000 * 60 * 7)).toISOString(),
    lapses: 0,
    reviewed: 0,
    createdAt: new Date().toISOString(),
  };
}

function normalizeDifficulty(value) {
  return ["简单", "中等", "困难"].includes(value) ? value : "中等";
}

function guessTitle(text) {
  const first = splitMaterial(text)[0] || "新复习资料";
  return first.slice(0, 22).replace(/[。！？,.!?]$/, "");
}

function shuffle(items) {
  return [...items].sort(() => Math.random() - 0.5);
}

function allItems(current = state) {
  return current.sets.flatMap((set) => [...set.items, ...set.cards]);
}

function dueItems(current = state) {
  const now = Date.now();
  return allItems(current)
    .filter((item) => new Date(item.dueAt).getTime() <= now)
    .sort((a, b) => new Date(a.dueAt) - new Date(b.dueAt));
}

function weakTopics() {
  const map = new Map();
  allItems().forEach((item) => {
    const current = map.get(item.topic) || { topic: item.topic, lapses: 0, reviewed: 0, total: 0 };
    current.lapses += item.lapses || 0;
    current.reviewed += item.reviewed || 0;
    current.total += 1;
    map.set(item.topic, current);
  });
  return [...map.values()]
    .map((entry) => ({
      ...entry,
      weakness: clamp(35 + entry.lapses * 18 - entry.reviewed * 4 + (entry.total > 1 ? 8 : 0), 12, 92),
    }))
    .sort((a, b) => b.weakness - a.weakness)
    .slice(0, 5);
}

function studyStats() {
  const items = allItems();
  const totalReviews = items.reduce((sum, item) => sum + (item.reviewed || 0), 0);
  const mastered = items.filter((item) => (item.interval || 0) >= 5).length;
  const correctRate = state.reviewLog.length
    ? Math.round((state.reviewLog.filter((entry) => entry.grade >= 3).length / state.reviewLog.length) * 100)
    : 78;
  return {
    totalItems: items.length,
    totalCards: state.sets.reduce((sum, set) => sum + set.cards.length, 0),
    totalQuestions: state.sets.reduce((sum, set) => sum + set.items.length, 0),
    totalReviews,
    mastered,
    correctRate,
    due: dueItems().length,
  };
}

function navItems() {
  return [
    ["dashboard", "今日概览", "Dashboard", icons.home],
    ["library", "资料库", "Library", icons.book],
    ["generate", "生成", "Generate", icons.spark],
    ["review", "复习", "Review", icons.clock],
    ["knowledge", "知识点", "Knowledge", icons.network],
    ["settings", "设置", "Settings", icons.gear],
  ];
}

function render() {
  const stats = studyStats();
  document.querySelector("#app").innerHTML = `
    <div class="app-shell ${state.drawerOpen ? "drawer-open" : ""}">
      ${renderSidebar(stats)}
      <main class="main">
        ${renderTopbar(stats)}
        <section class="workspace">${renderView()}</section>
      </main>
      ${renderDrawer()}
      <div class="toast ${state.busy ? "show" : ""}" id="toast">${escapeHtml(state.busy)}</div>
    </div>
  `;
  bindEvents();
}

function renderSidebar(stats) {
  return `
    <aside class="sidebar">
      <div class="brand">${icons.brain}<span>StartThinking</span></div>
      <nav class="nav">
        ${navItems()
          .map(
            ([key, zh, en, icon]) => `
              <button class="nav-button ${state.view === key ? "active" : ""}" data-view="${key}" title="${zh}">
                ${icon}
                <span-wrap><strong>${zh}</strong><span>${en}</span></span-wrap>
              </button>
            `,
          )
          .join("")}
      </nav>
      <div class="streak-card">
        <div class="mini-label">今日连续学习</div>
        <div class="streak-number">12 天</div>
        <div class="mini-label">连续学习，加油</div>
        <div class="week-dots">${[0, 1, 2, 3, 4, 5, 6]
          .map((day) => `<span class="dot ${day < 6 ? "done" : ""}">${day < 6 ? "✓" : ""}</span>`)
          .join("")}</div>
      </div>
      <div class="profile-card">
        <div class="avatar">L</div>
        <div><strong>Local</strong><div class="mini-label">${stats.totalItems} 个复习项</div></div>
      </div>
    </aside>
  `;
}

function renderTopbar(stats) {
  const title = navItems().find(([key]) => key === state.view)?.[1] || "今日概览";
  return `
    <header class="topbar">
      <h1>${title}</h1>
      <div class="topbar-actions">
        <div class="stat-inline">今日待复习 <strong>${stats.due}</strong></div>
        <div class="stat-inline">${icons.clock} 预计用时 <strong>${Math.max(8, Math.ceil(stats.due * 1.4))}</strong> 分钟</div>
        <button class="btn primary" data-action="choose-file">${icons.upload} 导入资料</button>
        <input class="file-input" type="file" id="file-input" multiple accept=".txt,.md,.csv,.json,.pdf,.docx,.pptx,.png,.jpg,.jpeg,.webp" />
      </div>
    </header>
  `;
}

function renderView() {
  const map = {
    dashboard: renderDashboard,
    library: renderLibrary,
    generate: renderGenerate,
    review: renderReview,
    knowledge: renderKnowledge,
    settings: renderSettings,
  };
  return (map[state.view] || renderDashboard)();
}

function renderDashboard() {
  return `
    <div class="stack">
      ${renderImportPanel()}
      ${renderModePanel()}
      ${renderQueuePanel()}
    </div>
    <div class="stack">
      ${renderRecentPanel()}
      ${renderWeakPanel()}
      ${renderProgressPanel()}
    </div>
  `;
}

function renderImportPanel() {
  return `
    <section class="panel">
      <div class="panel-body">
        <div class="drop-zone" id="drop-zone">
          <div>
            <div class="upload-icon">${icons.upload}</div>
            <h2>导入学习资料</h2>
            <p>${desktop ? "PDF、图片会交给 Unlimited-OCR；TXT、MD、CSV 直接读取。" : "当前是浏览器模式；桌面版才支持 Unlimited-OCR 文件识别。"}</p>
            <button class="btn primary" data-action="choose-file">选择文件</button>
          </div>
        </div>
        <div class="paste-box">
          <textarea id="paste-text" placeholder="把课堂笔记、教材段落、错题解析粘贴在这里...">${escapeHtml(state.pasteText)}</textarea>
          <div class="pill-row">
            <button class="btn ghost" data-action="use-sample">填入示例</button>
            <button class="btn primary" data-action="generate-from-paste">${icons.spark} ${desktop ? "用本地模型生成" : "从文本生成"}</button>
          </div>
        </div>
      </div>
    </section>
  `;
}

function renderModePanel() {
  const modes = [
    ["smart", "智能复习（推荐）", "基于问题重复"],
    ["quiz", "刷题模式", "以题目为中心"],
    ["cards", "闪卡模式", "以卡片为中心"],
  ];
  return `
    <section class="panel flush">
      <div class="panel-head"><h2>学习模式</h2></div>
      <div class="panel-body mode-grid">
        ${modes
          .map(
            ([key, title, desc]) => `
              <button class="mode-card ${state.mode === key ? "active" : ""}" data-mode="${key}">
                <span><strong>${title}</strong><span>${desc}</span></span><span>›</span>
              </button>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderQueuePanel(limit = 5) {
  const queue = dueItems().slice(0, limit);
  return `
    <section class="panel flush">
      <div class="panel-head">
        <h2>今日复习队列（${dueItems().length}）</h2>
        <button class="btn ghost" data-view="review">查看全部</button>
      </div>
      <div class="list">
        ${queue.length ? queue.map(renderQueueRow).join("") : `<div class="empty">今天暂时清空了。可以导入新资料。</div>`}
      </div>
    </section>
  `;
}

function renderQueueRow(item) {
  const badgeClass = item.type === "card" ? "card" : item.type === "cloze" ? "cloze" : "";
  return `
    <div class="row queue-row">
      <div class="type-badge ${badgeClass}">${item.type === "card" ? "卡" : "题"}</div>
      <div class="row-title">
        <strong>${escapeHtml(item.prompt)}</strong>
        <span>${escapeHtml(item.source)} · ${escapeHtml(item.topic)}</span>
      </div>
      <span class="pill ${difficultyClass(item.difficulty)}">${item.difficulty}</span>
      <button class="small-action" data-action="start-review" data-id="${item.id}">开始</button>
    </div>
  `;
}

function renderRecentPanel() {
  const sets = [...state.sets].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 4);
  return `
    <section class="panel flush">
      <div class="panel-head">
        <h2>最近生成的学习集</h2>
        <button class="btn ghost" data-view="library">查看全部</button>
      </div>
      <div class="list">${sets.length ? sets.map(renderSetRow).join("") : `<div class="empty">还没有资料。</div>`}</div>
    </section>
  `;
}

function renderSetRow(set) {
  return `
    <div class="row">
      <div class="doc-icon">${icons.file}</div>
      <div class="row-title">
        <strong>${escapeHtml(set.title)}</strong>
        <span>${escapeHtml(set.sourceName)} · ${formatDate(set.createdAt)}</span>
      </div>
      <div class="pill-row">
        <span class="pill">${set.items.length} 题目</span>
        <span class="pill green">${set.cards.length} 卡片</span>
        <button class="small-action" data-action="open-set" data-id="${set.id}">查看</button>
      </div>
    </div>
  `;
}

function renderWeakPanel() {
  const weak = weakTopics();
  return `
    <section class="panel flush">
      <div class="panel-head"><div><h2>薄弱知识点</h2><p>基于错题、重复次数和掌握间隔估算</p></div></div>
      <div class="panel-body weak-list">
        ${
          weak.length
            ? weak
                .map((item) => {
                  const color = item.weakness > 72 ? "var(--coral)" : item.weakness > 48 ? "var(--amber)" : "var(--green)";
                  return `<div class="weak-row"><strong>${escapeHtml(item.topic)}</strong><div class="bar" style="--bar-color:${color}"><span style="--value:${item.weakness}%"></span></div><span style="color:${color};font-weight:800">${item.weakness}%</span></div>`;
                })
                .join("")
            : `<div class="empty">复习几轮后，这里会显示最值得回炉的知识点。</div>`
        }
      </div>
    </section>
  `;
}

function renderProgressPanel() {
  const stats = studyStats();
  const bars = [18, 45, 38, 43, 72, 80, Math.max(28, Math.min(118, stats.totalReviews * 10 + 28))];
  return `
    <section class="panel flush">
      <div class="panel-head"><h2>学习进度</h2><span class="pill">近 7 天</span></div>
      <div class="panel-body metric-grid">
        <div class="metrics">
          <div class="metric"><span>复习卡片</span><strong>${stats.totalCards}</strong></div>
          <div class="metric"><span>正确率</span><strong>${stats.correctRate}%</strong></div>
          <div class="metric"><span>已掌握</span><strong>${stats.mastered}</strong></div>
        </div>
        <div class="chart">${bars
          .map((bar, index) => `<div class="chart-col"><div class="chart-bar" style="--h:${bar}px"></div><div class="chart-label">05/${14 + index}</div></div>`)
          .join("")}</div>
      </div>
    </section>
  `;
}

function renderLibrary() {
  return `
    <div class="stack" style="grid-column:1 / -1">
      ${renderRecentPanel()}
      <section class="panel flush">
        <div class="panel-head">
          <div><h2>全部复习项</h2><p>题目、填空和闪卡统一进入间隔复习。</p></div>
          <button class="btn danger" data-action="clear-data">${icons.trash} 清空数据</button>
        </div>
        <div class="list">${allItems().slice(0, 60).map(renderQueueRow).join("") || `<div class="empty">还没有复习项。</div>`}</div>
      </section>
    </div>
  `;
}

function renderGenerate() {
  return `
    <div class="stack">
      ${renderImportPanel()}
      <section class="panel flush">
        <div class="panel-head"><h2>生成偏好</h2></div>
        <div class="panel-body settings-grid">
          <label class="setting-row"><span>生成数量</span><input class="field" data-setting="generationCount" type="number" min="4" max="30" value="${state.settings.generationCount}" /></label>
          <label class="setting-row"><span>默认加入复习队列</span><select class="select" data-setting="autoAddQueue"><option value="true" ${state.settings.autoAddQueue ? "selected" : ""}>开启</option><option value="false" ${!state.settings.autoAddQueue ? "selected" : ""}>关闭</option></select></label>
        </div>
      </section>
    </div>
    <div class="stack">
      ${renderRecentPanel()}
      ${renderWeakPanel()}
    </div>
  `;
}

function renderReview() {
  const queue = dueItems();
  const current = allItems().find((item) => item.id === state.currentReviewId) || queue[0] || allItems()[0];
  if (!current) {
    return `<div class="stack" style="grid-column:1 / -1"><section class="panel"><div class="empty">还没有可以复习的内容。先导入资料。</div></section>${renderImportPanel()}</div>`;
  }
  return `
    <div class="stack" style="grid-column:1 / -1">
      <section class="panel review-card">
        <div class="panel-head">
          <div><h2>${current.type === "card" ? "闪卡复习" : "主动回忆"}</h2><p>${escapeHtml(current.source)} · ${escapeHtml(current.topic)}</p></div>
          <span class="pill ${difficultyClass(current.difficulty)}">${current.difficulty}</span>
        </div>
        <div class="review-question">
          <div>
            <h2>${escapeHtml(current.prompt)}</h2>
            ${current.options ? `<div class="options">${current.options.map((option, index) => `<div class="option">${String.fromCharCode(65 + index)}. ${escapeHtml(option)}</div>`).join("")}</div>` : ""}
            ${
              state.revealAnswer
                ? `<div class="review-answer"><strong>参考答案：</strong>${escapeHtml(current.answer)}${current.context ? `<br /><span class="mini-label">${escapeHtml(current.context)}</span>` : ""}</div>`
                : `<button class="btn primary" style="margin-top:22px" data-action="reveal-answer">显示答案</button>`
            }
          </div>
        </div>
        <div class="grade-row">
          <button class="grade bad" data-grade="1">忘记</button>
          <button class="grade ok" data-grade="2">模糊</button>
          <button class="grade good" data-grade="3">记住</button>
          <button class="grade easy" data-grade="4">熟练</button>
        </div>
      </section>
      ${renderQueuePanel(10)}
    </div>
  `;
}

function renderKnowledge() {
  const topics = weakTopics()
    .concat(allItems().slice(0, 12).map((item) => ({ topic: item.topic, weakness: 40, reviewed: item.reviewed, total: 1 })))
    .slice(0, 18);
  return `
    <div class="stack" style="grid-column:1 / -1">
      ${renderWeakPanel()}
      <section class="panel flush">
        <div class="panel-head"><h2>知识点清单</h2></div>
        <div class="list">
          ${topics
            .map(
              (item) => `
                <div class="row">
                  <div class="type-badge">${item.weakness > 60 ? "弱" : "知"}</div>
                  <div class="row-title"><strong>${escapeHtml(item.topic)}</strong><span>复习 ${item.reviewed || 0} 次 · 关联 ${item.total || 1} 个题卡</span></div>
                  <span class="pill ${item.weakness > 60 ? "red" : "green"}">掌握度 ${100 - item.weakness}%</span>
                </div>
              `,
            )
            .join("") || `<div class="empty">知识点会从导入资料中自动抽取。</div>`}
        </div>
      </section>
    </div>
  `;
}

function renderSettings() {
  const status = state.serviceStatus;
  return `
    <div class="stack" style="grid-column:1 / -1">
      <section class="panel flush">
        <div class="panel-head">
          <div><h2>本地后端设置</h2><p>桌面版会在本机调用 Unlimited-OCR 和 Ollama，资料不上传云端。</p></div>
          <button class="btn primary" data-action="check-services">检测服务</button>
        </div>
        <div class="panel-body settings-grid">
          <label class="setting-row"><span>每日目标</span><input class="field" data-setting="dailyTarget" type="number" min="5" max="200" value="${state.settings.dailyTarget}" /></label>
          <label class="setting-row"><span>生成数量</span><input class="field" data-setting="generationCount" type="number" min="4" max="30" value="${state.settings.generationCount}" /></label>
          <label class="setting-row"><span>本地模型</span><input class="field" data-setting="ollamaModel" value="${escapeHtml(state.settings.ollamaModel)}" placeholder="qwen3.5:4b" /></label>
          <label class="setting-row"><span>Ollama 地址</span><input class="field" data-setting="ollamaUrl" value="${escapeHtml(state.settings.ollamaUrl)}" /></label>
          <label class="setting-row"><span>Python</span><input class="field" data-setting="pythonPath" value="${escapeHtml(state.settings.pythonPath)}" placeholder="python" /></label>
          <label class="setting-row"><span>Unlimited-OCR infer.py</span><input class="field" data-setting="unlimitedOcrScript" value="${escapeHtml(state.settings.unlimitedOcrScript)}" placeholder="C:\\path\\Unlimited-OCR\\infer.py" /></label>
          <label class="setting-row"><span>OCR 并发</span><input class="field" data-setting="ocrConcurrency" type="number" min="1" max="8" value="${state.settings.ocrConcurrency}" /></label>
          <label class="setting-row"><span>OCR 图像模式</span><select class="select" data-setting="ocrImageMode"><option value="gundam" ${state.settings.ocrImageMode === "gundam" ? "selected" : ""}>gundam（单图推荐）</option><option value="base" ${state.settings.ocrImageMode === "base" ? "selected" : ""}>base（多页/PDF稳）</option></select></label>
          ${
            status
              ? `<div class="setting-row"><span>服务状态</span><div><p class="mini-label">Ollama：${escapeHtml(status.ollama.message)}</p><p class="mini-label">Unlimited-OCR：${escapeHtml(status.unlimitedOcr.message)}</p></div></div>`
              : ""
          }
          <div class="pill-row" style="justify-content:flex-start">
            <button class="btn" data-action="open-unlimited-ocr">打开 Unlimited-OCR</button>
            <button class="btn" data-action="open-ollama-qwen">打开 Qwen3/Ollama</button>
            <button class="btn" data-action="export-json">导出备份</button>
            <button class="btn danger" data-action="clear-data">清空本地数据</button>
          </div>
        </div>
      </section>
    </div>
  `;
}

function renderDrawer() {
  const latest = state.sets[0];
  const rows = state.drawerTab === "questions" ? latest?.items || [] : latest?.cards || [];
  return `
    <aside class="drawer ${state.drawerOpen ? "open" : ""}">
      <div class="drawer-head">
        <div><h2>生成的题目</h2><div class="mini-label">${latest ? escapeHtml(latest.title) : "等待导入资料"}</div></div>
        <button class="btn ghost" data-action="toggle-drawer">${icons.close}</button>
      </div>
      <div class="tabs">
        <button class="tab ${state.drawerTab === "questions" ? "active" : ""}" data-tab="questions">题目</button>
        <button class="tab ${state.drawerTab === "cards" ? "active" : ""}" data-tab="cards">闪卡</button>
      </div>
      <div class="drawer-list">${rows.length ? rows.map(renderQuestionCard).join("") : `<div class="empty">生成内容会出现在这里。</div>`}</div>
      <div class="drawer-foot">
        <button class="btn" data-action="export-json">导出题目</button>
        <button class="btn primary" data-view="review">${icons.plus} 开始复习</button>
      </div>
    </aside>
  `;
}

function renderQuestionCard(item, index) {
  return `
    <article class="question-card">
      <h3>${index + 1}. ${escapeHtml(item.prompt)}</h3>
      ${item.options ? `<div class="options">${item.options.map((option, optionIndex) => `<div class="option">${String.fromCharCode(65 + optionIndex)}. ${escapeHtml(option)}</div>`).join("")}</div>` : ""}
      <div class="answer-line"><span>答案：${escapeHtml(item.answer)}</span><span>难度：${escapeHtml(item.difficulty)}</span></div>
    </article>
  `;
}

function difficultyClass(difficulty) {
  if (difficulty === "困难") return "red";
  if (difficulty === "中等") return "amber";
  return "green";
}

function bindEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => setState({ view: button.dataset.view }));
  });
  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.addEventListener("click", () => setState({ mode: button.dataset.mode }));
  });
  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => setState({ drawerTab: button.dataset.tab }));
  });
  document.querySelectorAll("[data-setting]").forEach((input) => {
    input.addEventListener("change", () => {
      const value = input.type === "number" ? Number(input.value) : input.value === "true" ? true : input.value === "false" ? false : input.value;
      state.settings[input.dataset.setting] = value;
      saveState();
      toast("设置已保存");
    });
  });
  document.querySelector("#paste-text")?.addEventListener("input", (event) => {
    state.pasteText = event.target.value;
    saveState();
  });
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => handleAction(button.dataset.action, button.dataset.id));
  });
  document.querySelectorAll("[data-grade]").forEach((button) => {
    button.addEventListener("click", () => gradeCurrent(Number(button.dataset.grade)));
  });
  document.querySelector("#file-input")?.addEventListener("change", (event) => handleBrowserFiles([...event.target.files]));
  const dropZone = document.querySelector("#drop-zone");
  if (dropZone && !desktop) {
    ["dragenter", "dragover"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("dragging");
      });
    });
    ["dragleave", "drop"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("dragging");
      });
    });
    dropZone.addEventListener("drop", (event) => handleBrowserFiles([...event.dataTransfer.files]));
  }
}

async function handleAction(action, id) {
  if (action === "choose-file") return chooseFiles();
  if (action === "generate-from-paste") return generateFromPaste();
  if (action === "use-sample") {
    state.pasteText = sampleText;
    saveState();
    render();
    toast("已填入示例资料");
  }
  if (action === "toggle-drawer") setState({ drawerOpen: !state.drawerOpen });
  if (action === "open-set") openSet(id);
  if (action === "start-review") setState({ view: "review", currentReviewId: id, revealAnswer: false });
  if (action === "reveal-answer") setState({ revealAnswer: true });
  if (action === "clear-data" && confirm("确定清空所有本地学习数据吗？")) {
    localStorage.removeItem(STORAGE_KEY);
    state = seedState();
    saveState();
    render();
    toast("已重置为示例数据");
  }
  if (action === "export-json") exportJson();
  if (action === "check-services") checkServices();
  if (action === "open-unlimited-ocr") desktop?.openExternal("https://github.com/baidu/Unlimited-OCR");
  if (action === "open-ollama-qwen") desktop?.openExternal("https://ollama.com/library/qwen3");
}

function openSet(id) {
  const set = state.sets.find((item) => item.id === id);
  if (!set) return;
  state.sets = [set, ...state.sets.filter((item) => item.id !== id)];
  setState({ drawerOpen: true, drawerTab: "questions" });
}

async function chooseFiles() {
  if (!desktop) {
    document.querySelector("#file-input")?.click();
    return;
  }
  try {
    const files = await desktop.chooseFiles();
    if (!files.length) return;
    await withBusy("正在识别文件，首次运行 Unlimited-OCR 可能需要较久...", async () => {
      const docs = await desktop.extractFiles({ files, settings: state.settings });
      for (const doc of docs) await addDocumentAsSet(doc);
      toast(`已导入 ${docs.length} 个文件`);
    });
  } catch (error) {
    toast(error.message || "导入失败");
  }
}

async function handleBrowserFiles(files) {
  if (!files.length) return;
  await withBusy("正在读取浏览器文件...", async () => {
    for (const file of files) {
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (!["txt", "md", "csv", "json"].includes(ext)) {
        throw new Error("浏览器模式不能识别 PDF/图片；请运行桌面版。");
      }
      await addDocumentAsSet({ name: file.name, text: await file.text(), method: "browser" });
    }
  });
}

async function addDocumentAsSet(doc) {
  const title = doc.name?.replace(/\.[^.]+$/, "") || guessTitle(doc.text);
  const set = await buildStudySet(title, doc.text, `${doc.name || "资料"} · ${doc.method || "文本"}`);
  state.sets = [set, ...state.sets];
  state.drawerOpen = true;
  state.drawerTab = "questions";
  state.currentReviewId = dueItems(state)[0]?.id || set.items[0]?.id;
  saveState();
  render();
}

async function generateFromPaste() {
  const text = document.querySelector("#paste-text")?.value.trim() || "";
  if (text.length < 30) {
    toast("资料太短了，至少粘贴一小段完整笔记");
    return;
  }
  await withBusy(desktop ? "正在调用本地模型生成题卡..." : "正在生成题卡...", async () => {
    const title = guessTitle(text);
    const set = await buildStudySet(title, text, "粘贴资料");
    state.sets = [set, ...state.sets];
    state.drawerOpen = true;
    state.drawerTab = "questions";
    state.currentReviewId = dueItems(state)[0]?.id || set.items[0]?.id;
    saveState();
    render();
    toast(`已生成 ${set.items.length} 道题和 ${set.cards.length} 张闪卡`);
  });
}

async function buildStudySet(title, text, sourceName) {
  if (!desktop) return createStudySet(title, text, sourceName);
  try {
    const generated = await desktop.generateStudySet({ title, text, settings: state.settings });
    return createStudySetFromAi(generated, text, sourceName);
  } catch (error) {
    toast(`本地模型不可用，已用离线规则生成：${error.message}`);
    return createStudySet(title, text, sourceName);
  }
}

async function checkServices() {
  if (!desktop) {
    toast("请在桌面版中检测服务");
    return;
  }
  await withBusy("正在检测本地服务...", async () => {
    state.serviceStatus = await desktop.checkServices({ settings: state.settings });
    saveState();
    render();
  });
}

async function withBusy(message, task) {
  state.busy = message;
  render();
  try {
    await task();
  } catch (error) {
    toast(error.message || "操作失败");
  } finally {
    state.busy = "";
    saveState();
    render();
  }
}

function gradeCurrent(grade) {
  const currentId = state.currentReviewId || dueItems()[0]?.id;
  if (!currentId) return;
  state.sets = state.sets.map((set) => {
    const updateItem = (item) => {
      if (item.id !== currentId) return item;
      const oldInterval = item.interval || 0;
      const interval =
        grade === 1 ? 0 : grade === 2 ? Math.max(1, oldInterval) : oldInterval ? Math.round(oldInterval * (grade === 4 ? 2.4 : 1.8)) : grade;
      const ease = clamp((item.ease || 2.4) + (grade - 3) * 0.15, 1.3, 3.2);
      const days = grade === 1 ? 0.15 : interval;
      return {
        ...item,
        interval,
        ease,
        reviewed: (item.reviewed || 0) + 1,
        lapses: (item.lapses || 0) + (grade === 1 ? 1 : 0),
        dueAt: new Date(Date.now() + days * 24 * 60 * 60 * 1000).toISOString(),
        difficulty: grade === 1 ? "困难" : grade === 2 ? "中等" : "简单",
      };
    };
    return { ...set, items: set.items.map(updateItem), cards: set.cards.map(updateItem) };
  });
  state.reviewLog = [...state.reviewLog, { id: uid("log"), itemId: currentId, grade, at: new Date().toISOString() }];
  state.currentReviewId = dueItems(state).find((item) => item.id !== currentId)?.id || allItems(state).find((item) => item.id !== currentId)?.id || null;
  state.revealAnswer = false;
  saveState();
  render();
  toast(grade >= 3 ? "已安排下次复习" : "已加入近期回炉");
}

function exportJson() {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `startthinking-backup-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
  toast("已导出备份");
}

function toast(message) {
  const node = document.querySelector("#toast");
  if (!node) return;
  node.textContent = message;
  node.classList.add("show");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => node.classList.remove("show"), 2400);
}

render();
