import json
import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import BooleanVar, END, StringVar, Tk, filedialog, messagebox
from tkinter import ttk


APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
DATA_FILE = DATA_DIR / "startthinking.json"

TEXT_EXTS = {".txt", ".md", ".csv", ".json"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

SAMPLE_TEXT = """机器学习是一种让计算机从数据中学习规律的方法。监督学习使用带标签的数据训练模型，常见任务包括分类和回归。
过拟合是指模型在训练集上表现很好，但在测试集或新数据上表现较差。常见缓解方法包括正则化、交叉验证、早停和增加数据。
梯度下降通过沿损失函数负梯度方向迭代更新参数，学习率决定每一步更新幅度。学习率过大可能震荡，过小会收敛缓慢。
特征缩放可以让不同量纲的特征处在相近范围，常见方法包括标准化和归一化。它通常能改善基于距离或梯度的模型训练效果。
混淆矩阵用于评估分类模型，包含真正例、假正例、真反例和假反例。准确率、精确率、召回率和 F1 值都可以从中计算。"""


def now_ms() -> int:
    return int(time.time() * 1000)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def split_material(text: str) -> list[str]:
    normalized = re.sub(r"[ \t]+", " ", text.replace("\r", "\n")).strip()
    parts = re.split(r"\n+|(?<=[。！？.!?])\s+", normalized)
    usable = [part.strip() for part in parts if len(part.strip()) > 18]
    return usable or ([normalized] if normalized else [])


def extract_keyword(sentence: str, index: int) -> str:
    clean = re.sub(r"[，。！？；：,.!?;:()（）《》“”\"']", " ", sentence)
    candidates = [
        word.strip()
        for word in re.split(r"\s+|、", clean)
        if 2 <= len(word.strip()) <= 18
        and word.strip()
        not in {"一种", "一个", "可以", "用于", "通过", "常见", "包括", "如果", "因为", "所以", "以及", "进行", "方法"}
    ]
    if candidates:
        return candidates[index % len(candidates)]
    chinese = re.findall(r"[\u4e00-\u9fa5]{2,8}", sentence)
    return chinese[index % max(1, len(chinese))] if chinese else f"知识点 {index + 1}"


def guess_title(text: str) -> str:
    parts = split_material(text)
    return (parts[0] if parts else "新复习资料")[:22].rstrip("。！？,.!?")


def local_generate(title: str, text: str, source: str, count: int) -> dict:
    paragraphs = split_material(text)[: max(4, min(30, count))]
    keywords = [extract_keyword(p, i) for i, p in enumerate(paragraphs)]
    questions = []
    cards = []
    defaults = ["正则化", "混淆矩阵", "梯度下降", "监督学习", "特征缩放", "交叉验证", "召回率"]

    for index, paragraph in enumerate(paragraphs):
        keyword = keywords[index]
        difficulty = "困难" if index % 4 == 0 else "简单" if index % 3 == 0 else "中等"
        if index % 5 == 2:
            questions.append(
                {
                    "type": "short",
                    "prompt": f"简述「{keyword}」相关知识点。",
                    "answer": paragraph,
                    "difficulty": difficulty,
                    "topic": keyword,
                }
            )
        elif index % 4 == 1:
            questions.append(
                {
                    "type": "cloze",
                    "prompt": paragraph.replace(keyword, "______"),
                    "answer": keyword,
                    "difficulty": difficulty,
                    "topic": keyword,
                }
            )
        else:
            distractors = [x for x in [*keywords, *defaults] if x != keyword][:3]
            questions.append(
                {
                    "type": "single",
                    "prompt": "关于这段资料，最关键的概念是哪一个？",
                    "options": [keyword, *distractors][:4],
                    "answer": keyword,
                    "difficulty": difficulty,
                    "topic": keyword,
                }
            )

    for index, paragraph in enumerate(paragraphs[: max(4, int(len(paragraphs) * 0.7))]):
        keyword = extract_keyword(paragraph, index + 2)
        cards.append(
            {
                "front": keyword,
                "back": paragraph,
                "difficulty": "中等" if index % 3 == 0 else "简单",
                "topic": keyword,
            }
        )

    return {"title": title, "source": source, "text": text, "questions": questions, "cards": cards}


def normalize_generated(data: dict, title: str, text: str, source: str) -> dict:
    if not isinstance(data, dict):
        raise ValueError("模型返回内容不是 JSON 对象")
    questions = data.get("questions") or []
    cards = data.get("cards") or []
    if not isinstance(questions, list) or not isinstance(cards, list):
        raise ValueError("模型 JSON 缺少 questions/cards 数组")
    return {
        "title": data.get("title") or title,
        "source": source,
        "text": text,
        "questions": questions[:40],
        "cards": cards[:40],
    }


def parse_json_from_text(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))


@dataclass
class Settings:
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3.5:4b"
    python_path: str = "python"
    unlimited_ocr_script: str = ""
    ocr_concurrency: int = 2
    ocr_image_mode: str = "gundam"
    generation_count: int = 12


@dataclass
class Store:
    settings: Settings = field(default_factory=Settings)
    sets: list[dict] = field(default_factory=list)
    review_log: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls) -> "Store":
      DATA_DIR.mkdir(exist_ok=True)
      if not DATA_FILE.exists():
          store = cls()
          store.add_set(local_generate("机器学习：监督学习笔记", SAMPLE_TEXT, "示例资料", 12))
          store.save()
          return store
      raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
      settings = Settings(**{**Settings().__dict__, **raw.get("settings", {})})
      return cls(settings=settings, sets=raw.get("sets", []), review_log=raw.get("review_log", []))

    def save(self) -> None:
        DATA_DIR.mkdir(exist_ok=True)
        DATA_FILE.write_text(
            json.dumps(
                {"settings": self.settings.__dict__, "sets": self.sets, "review_log": self.review_log},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def add_set(self, generated: dict) -> None:
        set_id = new_id("set")
        created_at = int(time.time())
        items = []
        for index, question in enumerate(generated.get("questions", [])):
            items.append(make_item(set_id, question, generated.get("source", "资料"), index, is_card=False))
        for index, card in enumerate(generated.get("cards", [])):
            question = {
                "type": "card",
                "prompt": card.get("front") or card.get("prompt") or "知识卡片",
                "answer": card.get("back") or card.get("answer") or "",
                "difficulty": card.get("difficulty", "中等"),
                "topic": card.get("topic") or card.get("front") or "知识点",
            }
            items.append(make_item(set_id, question, generated.get("source", "资料"), index, is_card=True))
        self.sets.insert(
            0,
            {
                "id": set_id,
                "title": generated.get("title", "新学习集"),
                "source": generated.get("source", "资料"),
                "text": generated.get("text", ""),
                "created_at": created_at,
                "items": items,
            },
        )
        self.save()

    def all_items(self) -> list[dict]:
        return [item for study_set in self.sets for item in study_set.get("items", [])]

    def due_items(self) -> list[dict]:
        now = now_ms()
        return sorted([item for item in self.all_items() if item.get("due_at", 0) <= now], key=lambda item: item.get("due_at", 0))


def make_item(set_id: str, question: dict, source: str, index: int, is_card: bool) -> dict:
    return {
        "id": new_id("card" if is_card else "item"),
        "set_id": set_id,
        "type": "card" if is_card else question.get("type", "short"),
        "prompt": question.get("prompt") or question.get("front") or "请回忆这个知识点。",
        "options": question.get("options") if isinstance(question.get("options"), list) else [],
        "answer": question.get("answer") or question.get("back") or "",
        "difficulty": question.get("difficulty") if question.get("difficulty") in {"简单", "中等", "困难"} else "中等",
        "topic": question.get("topic") or "知识点",
        "source": source,
        "interval": 0,
        "ease": 2.45,
        "due_at": now_ms() - 1 if index < 5 else now_ms() + index * 7 * 60 * 1000,
        "lapses": 0,
        "reviewed": 0,
    }


class StartThinkingApp:
    def __init__(self, root: Tk):
        self.root = root
        self.store = Store.load()
        self.queue: queue.Queue = queue.Queue()
        self.current_item_id: str | None = None
        self.status = StringVar(value="就绪")

        self.root.title("StartThinking - 本地 AI 复习软件")
        self.root.geometry("1120x760")
        self.root.minsize(980, 680)

        self.build_ui()
        self.refresh_all()
        self.root.after(200, self.consume_queue)

    def build_ui(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.import_tab = ttk.Frame(self.notebook, padding=16)
        self.review_tab = ttk.Frame(self.notebook, padding=16)
        self.library_tab = ttk.Frame(self.notebook, padding=16)
        self.settings_tab = ttk.Frame(self.notebook, padding=16)

        self.notebook.add(self.import_tab, text="导入 / 生成")
        self.notebook.add(self.review_tab, text="复习")
        self.notebook.add(self.library_tab, text="资料库")
        self.notebook.add(self.settings_tab, text="设置")

        self.build_import_tab()
        self.build_review_tab()
        self.build_library_tab()
        self.build_settings_tab()

        status_bar = ttk.Label(self.root, textvariable=self.status, padding=(10, 5))
        status_bar.pack(fill="x")

    def build_import_tab(self) -> None:
        top = ttk.Frame(self.import_tab)
        top.pack(fill="x")
        ttk.Button(top, text="选择文件并识别", command=self.choose_files).pack(side="left")
        ttk.Button(top, text="用粘贴文本生成", command=self.generate_from_text).pack(side="left", padx=8)
        ttk.Button(top, text="填入示例", command=self.fill_sample).pack(side="left")

        self.text_input = ttk.Frame(self.import_tab)
        self.text_input.pack(fill="both", expand=True, pady=12)
        self.material_text = TextWithScrollbar(self.text_input)
        self.material_text.pack(fill="both", expand=True)
        self.material_text.set(SAMPLE_TEXT)

        note = "PDF/图片会调用 Unlimited-OCR；TXT/MD/CSV/JSON 直接读取；出题使用 Ollama qwen3.5:4b。"
        ttk.Label(self.import_tab, text=note).pack(anchor="w")

    def build_review_tab(self) -> None:
        header = ttk.Frame(self.review_tab)
        header.pack(fill="x")
        ttk.Label(header, text="今日复习队列").pack(side="left")
        ttk.Button(header, text="刷新", command=self.refresh_review).pack(side="right")

        self.review_list = ttk.Treeview(self.review_tab, columns=("topic", "difficulty", "source"), show="headings", height=8)
        self.review_list.heading("topic", text="知识点")
        self.review_list.heading("difficulty", text="难度")
        self.review_list.heading("source", text="来源")
        self.review_list.pack(fill="x", pady=8)
        self.review_list.bind("<<TreeviewSelect>>", self.select_review_item)

        self.question_text = TextWithScrollbar(self.review_tab, height=8)
        self.question_text.pack(fill="both", expand=True, pady=8)

        actions = ttk.Frame(self.review_tab)
        actions.pack(fill="x")
        ttk.Button(actions, text="显示答案", command=self.show_answer).pack(side="left")
        for label, grade in [("忘记", 1), ("模糊", 2), ("记住", 3), ("熟练", 4)]:
            ttk.Button(actions, text=label, command=lambda g=grade: self.grade_current(g)).pack(side="left", padx=4)

    def build_library_tab(self) -> None:
        self.library = ttk.Treeview(self.library_tab, columns=("count", "source", "created"), show="headings")
        self.library.heading("count", text="题卡数")
        self.library.heading("source", text="来源")
        self.library.heading("created", text="创建时间")
        self.library.pack(fill="both", expand=True)
        ttk.Button(self.library_tab, text="导出备份 JSON", command=self.export_backup).pack(anchor="e", pady=8)

    def build_settings_tab(self) -> None:
        self.vars = {
            "ollama_url": StringVar(value=self.store.settings.ollama_url),
            "ollama_model": StringVar(value=self.store.settings.ollama_model),
            "python_path": StringVar(value=self.store.settings.python_path),
            "unlimited_ocr_script": StringVar(value=self.store.settings.unlimited_ocr_script),
            "ocr_concurrency": StringVar(value=str(self.store.settings.ocr_concurrency)),
            "ocr_image_mode": StringVar(value=self.store.settings.ocr_image_mode),
            "generation_count": StringVar(value=str(self.store.settings.generation_count)),
        }
        labels = {
            "ollama_url": "Ollama 地址",
            "ollama_model": "本地模型",
            "python_path": "Python 路径",
            "unlimited_ocr_script": "Unlimited-OCR infer.py",
            "ocr_concurrency": "OCR 并发",
            "ocr_image_mode": "OCR 图像模式",
            "generation_count": "生成数量",
        }
        for key, label in labels.items():
            row = ttk.Frame(self.settings_tab)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label, width=24).pack(side="left")
            ttk.Entry(row, textvariable=self.vars[key]).pack(side="left", fill="x", expand=True)
            if key == "unlimited_ocr_script":
                ttk.Button(row, text="浏览", command=self.pick_ocr_script).pack(side="left", padx=6)

        actions = ttk.Frame(self.settings_tab)
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="保存设置", command=self.save_settings).pack(side="left")
        ttk.Button(actions, text="检测服务", command=self.check_services).pack(side="left", padx=8)
        ttk.Button(actions, text="拉取 Qwen3.5-4B", command=self.pull_qwen).pack(side="left")

        self.service_text = TextWithScrollbar(self.settings_tab, height=10)
        self.service_text.pack(fill="both", expand=True)

    def refresh_all(self) -> None:
        self.refresh_review()
        self.refresh_library()

    def refresh_review(self) -> None:
        for item in self.review_list.get_children():
            self.review_list.delete(item)
        for item in self.store.due_items():
            self.review_list.insert("", END, iid=item["id"], values=(item["topic"], item["difficulty"], item["source"]))
        due = self.store.due_items()
        if due:
            self.current_item_id = due[0]["id"]
            self.render_question(due[0], show_answer=False)
        else:
            self.current_item_id = None
            self.question_text.set("今天没有到期复习项。可以导入新资料生成题卡。")

    def refresh_library(self) -> None:
        for item in self.library.get_children():
            self.library.delete(item)
        for study_set in self.store.sets:
            self.library.insert(
                "",
                END,
                iid=study_set["id"],
                text=study_set["title"],
                values=(len(study_set.get("items", [])), study_set.get("source", ""), time.strftime("%Y-%m-%d %H:%M", time.localtime(study_set.get("created_at", 0)))),
            )

    def select_review_item(self, _event=None) -> None:
        selected = self.review_list.selection()
        if not selected:
            return
        self.current_item_id = selected[0]
        item = self.find_item(self.current_item_id)
        if item:
            self.render_question(item, show_answer=False)

    def render_question(self, item: dict, show_answer: bool) -> None:
        lines = [f"题目：{item['prompt']}"]
        if item.get("options"):
            for index, option in enumerate(item["options"]):
                lines.append(f"{chr(65 + index)}. {option}")
        if show_answer:
            lines.append("")
            lines.append(f"参考答案：{item.get('answer', '')}")
        self.question_text.set("\n".join(lines))

    def show_answer(self) -> None:
        item = self.find_item(self.current_item_id)
        if item:
            self.render_question(item, show_answer=True)

    def grade_current(self, grade: int) -> None:
        item = self.find_item(self.current_item_id)
        if not item:
            return
        old_interval = item.get("interval", 0)
        interval = 0 if grade == 1 else max(1, old_interval) if grade == 2 else round(old_interval * (2.4 if grade == 4 else 1.8)) if old_interval else grade
        days = 0.15 if grade == 1 else interval
        item["interval"] = interval
        item["ease"] = max(1.3, min(3.2, item.get("ease", 2.4) + (grade - 3) * 0.15))
        item["reviewed"] = item.get("reviewed", 0) + 1
        item["lapses"] = item.get("lapses", 0) + (1 if grade == 1 else 0)
        item["due_at"] = now_ms() + int(days * 24 * 60 * 60 * 1000)
        item["difficulty"] = "困难" if grade == 1 else "中等" if grade == 2 else "简单"
        self.store.review_log.append({"item_id": item["id"], "grade": grade, "at": int(time.time())})
        self.store.save()
        self.refresh_all()

    def find_item(self, item_id: str | None) -> dict | None:
        for item in self.store.all_items():
            if item["id"] == item_id:
                return item
        return None

    def choose_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="选择复习资料",
            filetypes=[
                ("学习资料", "*.pdf *.png *.jpg *.jpeg *.webp *.txt *.md *.csv *.json"),
                ("所有文件", "*.*"),
            ],
        )
        if not paths:
            return
        self.run_background(lambda: self.process_files([Path(path) for path in paths]), "正在识别文件...")

    def process_files(self, paths: list[Path]) -> None:
        for file_path in paths:
            text = self.extract_text(file_path)
            generated = self.generate_questions(file_path.stem, text, file_path.name)
            self.store.add_set(generated)
        self.queue.put(("done", f"已导入 {len(paths)} 个文件"))

    def extract_text(self, file_path: Path) -> str:
        if file_path.suffix.lower() in TEXT_EXTS:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        return self.run_unlimited_ocr(file_path)

    def run_unlimited_ocr(self, file_path: Path) -> str:
        settings = self.store.settings
        if not settings.unlimited_ocr_script:
            raise RuntimeError("请先在设置里填写 Unlimited-OCR infer.py 路径")
        output_dir = Path(tempfile.mkdtemp(prefix="startthinking-ocr-"))
        args = [settings.python_path, settings.unlimited_ocr_script]
        if file_path.suffix.lower() == ".pdf":
            args += ["--pdf", str(file_path)]
        elif file_path.suffix.lower() in IMAGE_EXTS:
            image_dir = Path(tempfile.mkdtemp(prefix="startthinking-image-"))
            shutil.copy2(file_path, image_dir / file_path.name)
            args += ["--image_dir", str(image_dir)]
        else:
            raise RuntimeError(f"{file_path.name} 不是支持的 OCR 文件类型")
        args += ["--output_dir", str(output_dir), "--concurrency", str(settings.ocr_concurrency), "--image_mode", settings.ocr_image_mode]
        result = subprocess.run(args, cwd=APP_DIR, text=True, capture_output=True, timeout=1200)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "Unlimited-OCR 执行失败")
        text = self.collect_text(output_dir)
        if not text.strip():
            raise RuntimeError("Unlimited-OCR 没有输出可读取文本")
        return text

    def collect_text(self, directory: Path) -> str:
        parts = []
        for path in directory.rglob("*"):
            if path.suffix.lower() in {".txt", ".md", ".json"}:
                parts.append(path.read_text(encoding="utf-8", errors="ignore"))
        return "\n\n".join(parts)

    def generate_from_text(self) -> None:
        text = self.material_text.get().strip()
        if len(text) < 30:
            messagebox.showwarning("资料太短", "请至少粘贴一小段完整笔记。")
            return
        self.run_background(lambda: self.process_pasted_text(text), "正在调用 qwen3.5:4b 生成题卡...")

    def process_pasted_text(self, text: str) -> None:
        generated = self.generate_questions(guess_title(text), text, "粘贴资料")
        self.store.add_set(generated)
        self.queue.put(("done", "已生成新的学习集"))

    def generate_questions(self, title: str, text: str, source: str) -> dict:
        settings = self.store.settings
        try:
            payload = {
                "model": settings.ollama_model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": "你只输出严格 JSON。"},
                    {"role": "user", "content": self.build_prompt(title, text)},
                ],
                "options": {"temperature": 0.2},
            }
            req = urllib.request.Request(
                settings.ollama_url.rstrip("/") + "/api/chat",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as response:
                raw = json.loads(response.read().decode("utf-8"))
            content = raw.get("message", {}).get("content", "")
            return normalize_generated(parse_json_from_text(content), title, text, source)
        except Exception as exc:
            self.queue.put(("info", f"Ollama 不可用，已回退本地规则：{exc}"))
            return local_generate(title, text, source, settings.generation_count)

    def build_prompt(self, title: str, text: str) -> str:
        return f"""你是严谨的个人复习出题助手。请只基于给定资料生成复习内容，不要编造资料外事实。
输出必须是严格 JSON，不要 Markdown，不要解释。结构：
{{
  "title": "学习集标题",
  "questions": [
    {{"type":"single","prompt":"题干","options":["A","B","C","D"],"answer":"正确答案文本","difficulty":"简单|中等|困难","topic":"知识点"}},
    {{"type":"short","prompt":"简答题","answer":"参考答案","difficulty":"简单|中等|困难","topic":"知识点"}},
    {{"type":"cloze","prompt":"带 ______ 的填空句","answer":"填空答案","difficulty":"简单|中等|困难","topic":"知识点"}}
  ],
  "cards": [
    {{"front":"卡片正面","back":"卡片背面","difficulty":"简单|中等|困难","topic":"知识点"}}
  ]
}}
题目总数约 {self.store.settings.generation_count} 个，闪卡约 {max(4, self.store.settings.generation_count // 2)} 张。

标题：{title}

资料：
{text[:24000]}"""

    def fill_sample(self) -> None:
        self.material_text.set(SAMPLE_TEXT)

    def pick_ocr_script(self) -> None:
        path = filedialog.askopenfilename(title="选择 Unlimited-OCR infer.py", filetypes=[("Python", "*.py"), ("所有文件", "*.*")])
        if path:
            self.vars["unlimited_ocr_script"].set(path)

    def save_settings(self) -> None:
        settings = self.store.settings
        settings.ollama_url = self.vars["ollama_url"].get().strip()
        settings.ollama_model = self.vars["ollama_model"].get().strip() or "qwen3.5:4b"
        settings.python_path = self.vars["python_path"].get().strip() or "python"
        settings.unlimited_ocr_script = self.vars["unlimited_ocr_script"].get().strip()
        settings.ocr_concurrency = int(self.vars["ocr_concurrency"].get() or 2)
        settings.ocr_image_mode = self.vars["ocr_image_mode"].get().strip() or "gundam"
        settings.generation_count = int(self.vars["generation_count"].get() or 12)
        self.store.save()
        self.status.set("设置已保存")

    def check_services(self) -> None:
        self.save_settings()
        self.run_background(self.do_check_services, "正在检测服务...")

    def do_check_services(self) -> None:
        lines = []
        try:
            with urllib.request.urlopen(self.store.settings.ollama_url.rstrip("/") + "/api/tags", timeout=5) as response:
                lines.append(f"Ollama：可用 ({response.status})，默认模型 {self.store.settings.ollama_model}")
        except Exception as exc:
            lines.append(f"Ollama：不可用，{exc}")
        script = self.store.settings.unlimited_ocr_script
        if script and Path(script).exists():
            lines.append(f"Unlimited-OCR：已找到 {script}")
        else:
            lines.append("Unlimited-OCR：未设置 infer.py 或文件不存在")
        self.queue.put(("service", "\n".join(lines)))

    def pull_qwen(self) -> None:
        self.run_background(lambda: self.run_command(["ollama", "pull", "qwen3.5:4b"]), "正在拉取 qwen3.5:4b...")

    def run_command(self, args: list[str]) -> None:
        result = subprocess.run(args, text=True, capture_output=True, timeout=1800)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "命令失败")
        self.queue.put(("done", result.stdout[-500:] or "命令完成"))

    def export_backup(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], initialfile="startthinking-backup.json")
        if path:
            shutil.copy2(DATA_FILE, path)
            self.status.set(f"已导出：{path}")

    def run_background(self, fn, status: str) -> None:
        self.status.set(status)
        threading.Thread(target=self.safe_run, args=(fn,), daemon=True).start()

    def safe_run(self, fn) -> None:
        try:
            fn()
        except Exception as exc:
            self.queue.put(("error", str(exc)))

    def consume_queue(self) -> None:
        try:
            while True:
                kind, message = self.queue.get_nowait()
                if kind == "error":
                    messagebox.showerror("操作失败", message)
                    self.status.set("失败")
                elif kind == "service":
                    self.service_text.set(message)
                    self.status.set("检测完成")
                elif kind == "info":
                    self.status.set(message)
                else:
                    self.status.set(message)
                    self.refresh_all()
        except queue.Empty:
            pass
        self.root.after(200, self.consume_queue)


class TextWithScrollbar(ttk.Frame):
    def __init__(self, parent, height: int | None = None):
        super().__init__(parent)
        import tkinter as tk

        self.text = tk.Text(self, wrap="word", height=height or 18, font=("Microsoft YaHei UI", 11))
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def set(self, value: str) -> None:
        self.text.delete("1.0", END)
        self.text.insert("1.0", value)

    def get(self) -> str:
        return self.text.get("1.0", END)


def main() -> None:
    root = Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    StartThinkingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
