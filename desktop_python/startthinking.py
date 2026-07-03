import base64
import json
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


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


COLORS = {
    "app": "#eef3fb",
    "shell": "#ffffff",
    "sidebar": "#fbfcff",
    "panel": "#ffffff",
    "panel_soft": "#f7f9fe",
    "line": "#dfe6f1",
    "line_soft": "#edf1f7",
    "text": "#152033",
    "muted": "#717b8c",
    "blue": "#2f66f6",
    "blue_dark": "#1f55e6",
    "blue_soft": "#eaf1ff",
    "green": "#38b979",
    "green_soft": "#e8f7ef",
    "orange": "#ec7d2b",
    "orange_soft": "#fff0e7",
    "red": "#e95050",
    "red_soft": "#fff0f0",
    "cyan": "#46c4d1",
    "cyan_soft": "#e9fbfc",
}


def now_ms() -> int:
    return int(time.time() * 1000)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def safe_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def split_material(text: str) -> list[str]:
    normalized = re.sub(r"[ \t]+", " ", str(text or "").replace("\r", "\n")).strip()
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


def parse_json_from_text(text: str) -> dict:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))


def local_generate(title: str, text: str, source: str, count: int) -> dict:
    source_parts = split_material(text) or [text.strip() or title]
    target_count = max(4, min(40, count))
    paragraphs = [source_parts[index % len(source_parts)] for index in range(target_count)]
    keywords = [extract_keyword(p, i) for i, p in enumerate(paragraphs)]
    defaults = ["正则化", "混淆矩阵", "梯度下降", "监督学习", "特征缩放", "交叉验证", "召回率"]
    questions = []
    cards = []

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
            distractors = [item for item in [*keywords, *defaults] if item != keyword][:3]
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


@dataclass
class Settings:
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3.5:4b"
    python_path: str = sys.executable
    unlimited_ocr_script: str = str(APP_DIR / "third_party" / "Unlimited-OCR" / "infer.py")
    ocr_concurrency: int = 2
    ocr_image_mode: str = "gundam"
    generation_count: int = 20
    question_type: str = "选择题"
    difficulty: str = "基础"


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
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            settings = Settings(**{**Settings().__dict__, **raw.get("settings", {})})
            return cls(settings=settings, sets=raw.get("sets", []), review_log=raw.get("review_log", []))
        except Exception:
            backup = DATA_FILE.with_suffix(f".broken-{int(time.time())}.json")
            shutil.copy2(DATA_FILE, backup)
            DATA_FILE.unlink(missing_ok=True)
            return cls.load()

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

    def add_set(self, generated: dict, status: str = "已解析") -> dict:
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
        study_set = {
            "id": set_id,
            "title": generated.get("title", "新学习集"),
            "source": generated.get("source", "资料"),
            "text": generated.get("text", ""),
            "created_at": created_at,
            "status": status,
            "items": items,
        }
        self.sets.insert(0, study_set)
        self.save()
        return study_set

    def all_items(self) -> list[dict]:
        return [item for study_set in self.sets for item in study_set.get("items", [])]

    def due_items(self) -> list[dict]:
        return sorted([item for item in self.all_items() if item.get("due_at", 0) <= now_ms()], key=lambda item: item.get("due_at", 0))


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


class RoundedCanvas(tk.Canvas):
    def round_rect(self, x1, y1, x2, y2, radius=14, **kwargs):
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)


class StartThinkingApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.store = Store.load()
        self.queue: queue.Queue = queue.Queue()
        self.current_item_id = None
        self.active_nav = "home"
        self.busy = False
        self.uploaded_files: list[Path] = []
        self.status_text = "就绪"

        self.question_type = tk.StringVar(value=self.store.settings.question_type)
        self.difficulty = tk.StringVar(value=self.store.settings.difficulty)
        self.question_count = tk.IntVar(value=self.store.settings.generation_count)
        self.search_text = tk.StringVar(value="")

        self.root.title("AI 出题助手")
        self.root.geometry("1440x820")
        self.root.minsize(1180, 720)
        self.root.configure(bg=COLORS["app"])

        self.canvas = RoundedCanvas(root, bg=COLORS["app"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.render())
        self.root.after(200, self.consume_queue)

    def render(self):
        self.canvas.delete("all")
        w = max(self.canvas.winfo_width(), 1180)
        h = max(self.canvas.winfo_height(), 720)
        margin = 28
        shell = (margin, 18, w - margin, h - 20)
        side_w = 208
        top_h = 74
        right_w = 520

        self.canvas.round_rect(*shell, radius=24, fill=COLORS["shell"], outline="#e8edf5")
        self.canvas.create_line(shell[0] + side_w, shell[1] + top_h, shell[0] + side_w, shell[3], fill=COLORS["line"])
        self.canvas.create_line(shell[0], shell[1] + top_h, shell[2], shell[1] + top_h, fill=COLORS["line"])
        self.canvas.create_line(shell[2] - right_w, shell[1] + top_h, shell[2] - right_w, shell[3], fill=COLORS["line"])

        self.draw_sidebar(shell[0], shell[1], side_w, shell[3] - shell[1])
        self.draw_topbar(shell[0] + side_w, shell[1], shell[2] - shell[0] - side_w, top_h)

        content_x = shell[0] + side_w + 30
        content_y = shell[1] + top_h + 26
        center_w = shell[2] - right_w - content_x - 28
        right_x = shell[2] - right_w + 30
        right_y = content_y
        right_inner_w = right_w - 58

        self.draw_upload_section(content_x, content_y, center_w)
        self.draw_config_section(content_x, content_y + 270, center_w)
        self.draw_recent_section(content_x, content_y + 500, center_w)
        self.draw_preview_section(right_x, right_y, right_inner_w, shell[3] - right_y - 20)

    def text(self, x, y, value, size=12, fill=None, weight="normal", anchor="nw", width=None):
        font = ("Microsoft YaHei UI", size, weight)
        return self.canvas.create_text(x, y, text=value, fill=fill or COLORS["text"], font=font, anchor=anchor, width=width)

    def draw_button(self, x, y, w, h, text, fill, fg, command=None, outline=None, radius=8, tag=None):
        tag = tag or f"btn-{new_id('ui')}"
        self.canvas.round_rect(x, y, x + w, y + h, radius=radius, fill=fill, outline=outline or fill, tags=(tag,))
        label_id = self.text(x + w / 2, y + h / 2, text, size=12, fill=fg, weight="bold", anchor="center")
        if command:
            for target in (tag, label_id):
                self.canvas.tag_bind(target, "<Button-1>", lambda _event: command())
                self.canvas.tag_bind(target, "<Enter>", lambda _event: self.canvas.configure(cursor="hand2"))
                self.canvas.tag_bind(target, "<Leave>", lambda _event: self.canvas.configure(cursor=""))

    def draw_sidebar(self, x, y, w, h):
        self.canvas.round_rect(x, y, x + w, y + h, radius=24, fill=COLORS["sidebar"], outline="")
        self.canvas.round_rect(x + 38, y + 28, x + 68, y + 58, radius=8, fill=COLORS["blue"], outline="")
        self.text(x + 53, y + 43, "A", size=16, fill="white", weight="bold", anchor="center")
        self.text(x + 88, y + 34, "AI 出题助手", size=17, weight="bold")

        nav = [("home", "⌂", "首页"), ("library", "□", "资料库"), ("generate", "✦", "智能出题"), ("manage", "▤", "题目管理"), ("record", "⌁", "学习记录"), ("settings", "⚙", "设置")]
        for i, (key, icon, label) in enumerate(nav):
            yy = y + 110 + i * 56
            active = key == self.active_nav
            if active:
                self.canvas.round_rect(x + 22, yy - 10, x + w - 22, yy + 34, radius=8, fill=COLORS["blue_soft"], outline="")
            self.text(x + 44, yy + 2, icon, size=17, fill=COLORS["blue"] if active else "#526071", weight="bold")
            self.text(x + 78, yy + 2, label, size=13, fill=COLORS["blue"] if active else "#526071", weight="bold" if active else "normal")

        box_y = y + h - 170
        self.canvas.round_rect(x + 22, box_y, x + w - 22, box_y + 120, radius=10, fill="#ffffff", outline=COLORS["line"])
        self.text(x + 38, box_y + 18, "AI 生成额度", size=11, fill=COLORS["muted"])
        self.text(x + 38, box_y + 46, "2,450", size=18, weight="bold")
        self.text(x + 92, box_y + 50, "/ 5,000", size=11, fill=COLORS["muted"])
        self.canvas.create_line(x + 38, box_y + 78, x + w - 58, box_y + 78, fill="#e3e8f1", width=4)
        self.canvas.create_line(x + 38, box_y + 78, x + 118, box_y + 78, fill=COLORS["blue"], width=4)
        self.text(x + 38, box_y + 96, "本地模型可用", size=11, fill=COLORS["blue"])

    def draw_topbar(self, x, y, w, h):
        search_w = 430
        sx = x + (w - search_w) / 2 - 90
        self.canvas.round_rect(sx, y + 20, sx + search_w, y + 56, radius=10, fill=COLORS["panel_soft"], outline=COLORS["line"])
        self.text(sx + 20, y + 38, "⌕", size=14, fill=COLORS["muted"], anchor="center")
        self.text(sx + 42, y + 30, "搜索资料、题目或知识点", size=11, fill=COLORS["muted"])
        self.canvas.round_rect(sx + search_w - 42, y + 26, sx + search_w - 12, y + 50, radius=6, fill="#ffffff", outline=COLORS["line"])
        self.text(sx + search_w - 27, y + 38, "⌘ K", size=9, fill=COLORS["muted"], anchor="center")
        self.text(x + w - 180, y + 37, "🔔", size=16, anchor="center")
        self.canvas.create_oval(x + w - 164, y + 23, x + w - 158, y + 29, fill=COLORS["red"], outline="")
        self.canvas.create_oval(x + w - 120, y + 24, x + w - 92, y + 52, fill="#dbe6f5", outline="")
        self.text(x + w - 106, y + 38, "我", size=10, anchor="center", weight="bold")
        self.text(x + w - 80, y + 31, "张同学⌄", size=12, weight="bold")
        status_fill = COLORS["blue_soft"] if self.busy else "#f5f7fb"
        status_fg = COLORS["blue"] if self.busy else COLORS["muted"]
        self.canvas.round_rect(x + 28, y + 22, x + 250, y + 54, radius=8, fill=status_fill, outline=COLORS["line"])
        self.text(x + 44, y + 38, "●", size=10, fill=status_fg, anchor="center")
        self.text(x + 62, y + 30, self.status_text[:22], size=11, fill=status_fg, weight="bold" if self.busy else "normal")

    def draw_upload_section(self, x, y, w):
        self.text(x, y, "1. 上传学习资料", size=14, weight="bold")
        self.text(x + 116, y + 2, "ⓘ", size=11, fill=COLORS["muted"])
        uy = y + 32
        self.canvas.round_rect(x, uy, x + w, uy + 210, radius=10, fill="#fbfdff", outline="#b7cdfd", dash=(3, 2))
        self.text(x + w / 2, uy + 54, "☁", size=40, fill="#6f96f7", anchor="center")
        self.text(x + w / 2, uy + 92, "拖拽文件到此处，或点击上传", size=14, weight="bold", anchor="center")
        self.text(x + w / 2, uy + 120, "支持 PDF、DOCX、PPT、TXT 格式，单个文件不超过 100MB", size=11, fill=COLORS["muted"], anchor="center")
        self.draw_button(x + w / 2 - 72, uy + 148, 144, 34, "↥  选择文件", COLORS["blue"], "white", self.choose_files)
        labels = [("PDF", COLORS["red_soft"], COLORS["red"]), ("DOCX", COLORS["blue_soft"], COLORS["blue"]), ("PPT", COLORS["orange_soft"], COLORS["orange"]), ("TXT", "#f6f8fb", "#526071")]
        start = x + w / 2 - 204
        for i, (label, bg, fg) in enumerate(labels):
            self.canvas.round_rect(start + i * 98, uy + 188, start + i * 98 + 84, uy + 214, radius=6, fill=bg, outline=COLORS["line"])
            self.text(start + i * 98 + 42, uy + 201, label, size=10, fill=fg, anchor="center", weight="bold")

    def draw_config_section(self, x, y, w):
        self.text(x, y, "2. 出题配置", size=14, weight="bold")
        rows = [("题目类型", ["选择题", "填空题", "判断题"], self.question_type), ("难度等级", ["基础", "进阶", "综合"], self.difficulty)]
        for row_index, (label, values, var) in enumerate(rows):
            yy = y + 44 + row_index * 48
            self.text(x, yy + 8, label, size=11, fill="#475266")
            for i, value in enumerate(values):
                bx = x + 120 + i * 140
                active = var.get() == value
                tag = f"choice-{row_index}-{i}"
                self.canvas.round_rect(
                    bx,
                    yy,
                    bx + 122,
                    yy + 32,
                    radius=6,
                    fill=COLORS["blue_soft"] if active else "#ffffff",
                    outline="#b9cdf8" if active else COLORS["line"],
                    tags=(tag,),
                )
                label_id = self.text(
                    bx + 61,
                    yy + 16,
                    ("●  " if active else "○  ") + value,
                    size=11,
                    fill=COLORS["blue"] if active else "#526071",
                    weight="bold" if active else "normal",
                    anchor="center",
                )
                for target in (tag, label_id):
                    self.canvas.tag_bind(target, "<Button-1>", lambda _e, v=value, variable=var: self.set_choice(variable, v))
                    self.canvas.tag_bind(target, "<Enter>", lambda _e: self.canvas.configure(cursor="hand2"))
                    self.canvas.tag_bind(target, "<Leave>", lambda _e: self.canvas.configure(cursor=""))

        yy = y + 145
        self.text(x, yy + 8, "题目数量", size=11, fill="#475266")
        self.canvas.create_line(x + 120, yy + 16, x + 520, yy + 16, fill="#d8e0ec", width=4)
        count = self.question_count.get()
        ratio = (count - 5) / 45
        px = x + 120 + max(0, min(1, ratio)) * 400
        self.canvas.create_line(x + 120, yy + 16, px, yy + 16, fill=COLORS["blue"], width=4)
        self.canvas.create_oval(px - 7, yy + 9, px + 7, yy + 23, fill="white", outline=COLORS["blue"], width=3)
        for value in [5, 10, 20, 30, 50]:
            vx = x + 120 + (value - 5) / 45 * 400
            self.text(vx, yy + 30, str(value), size=10, fill=COLORS["muted"], anchor="center")
        self.canvas.round_rect(x + 550, yy, x + 594, yy + 32, radius=6, fill=COLORS["blue_soft"], outline="")
        self.text(x + 572, yy + 16, str(count), size=11, fill=COLORS["blue"], weight="bold", anchor="center")
        self.text(x + 608, yy + 9, "题", size=11, fill=COLORS["text"])

        self.draw_button(x + w / 2 - 86, y + 190, 172, 36, "✦  开始生成", COLORS["blue"], "white", self.generate_from_current_files)
        self.text(x + w / 2, y + 232, "预计需要 10–60 秒，PDF 首次识别会更久", size=10, fill=COLORS["muted"], anchor="center")

    def draw_recent_section(self, x, y, w):
        self.text(x, y, "3. 最近资料", size=14, weight="bold")
        self.canvas.round_rect(x, y + 30, x + w, y + 180, radius=10, fill="#ffffff", outline=COLORS["line"])
        headers = [("文件名", x + 18), ("类型", x + w - 360), ("大小", x + w - 270), ("上传时间", x + w - 185), ("状态", x + w - 72)]
        for label, hx in headers:
            self.text(hx, y + 48, label, size=10, fill=COLORS["muted"])
        recent = self.store.sets[:3]
        if not recent:
            self.text(x + w / 2, y + 105, "暂无资料，上传 PDF 后会自动识别并生成题目", size=12, fill=COLORS["muted"], anchor="center")
        for i, study_set in enumerate(recent):
            yy = y + 76 + i * 34
            self.canvas.create_line(x + 16, yy - 8, x + w - 16, yy - 8, fill=COLORS["line_soft"])
            ext = Path(study_set.get("source", "")).suffix.replace(".", "").upper() or "TXT"
            color = COLORS["red"] if ext == "PDF" else COLORS["orange"] if ext in {"PPT", "PPTX"} else COLORS["blue"]
            self.text(x + 18, yy, "▣", size=12, fill=color)
            self.text(x + 42, yy, study_set.get("title", "学习资料")[:26], size=11, weight="bold")
            self.text(x + w - 360, yy, ext[:5], size=10, fill="#526071")
            self.text(x + w - 270, yy, f"{len(study_set.get('text', '')) / 1024:.1f} KB", size=10, fill="#526071")
            created = time.strftime("%m-%d %H:%M", time.localtime(study_set.get("created_at", 0)))
            self.text(x + w - 185, yy, created, size=10, fill="#526071")
            status = study_set.get("status", "已解析")
            pill_bg = COLORS["green_soft"] if "失败" not in status else COLORS["red_soft"]
            pill_fg = COLORS["green"] if "失败" not in status else COLORS["red"]
            self.canvas.round_rect(x + w - 82, yy - 4, x + w - 24, yy + 20, radius=6, fill=pill_bg, outline="")
            self.text(x + w - 53, yy + 8, status[:4], size=9, fill=pill_fg, anchor="center", weight="bold")
        self.text(x + w / 2, y + 160, "查看全部资料  ›", size=11, fill=COLORS["blue"], anchor="center")

    def draw_preview_section(self, x, y, w, h):
        self.text(x, y, "4. 题目预览", size=14, weight="bold")
        self.text(x + 110, y + 1, "✦", size=14, fill=COLORS["blue"])
        self.draw_button(x + w - 80, y - 4, 72, 32, "查看全部", "#ffffff", "#526071", None, outline=COLORS["line"])
        items = self.store.all_items()[:6]
        if not items:
            self.draw_empty_preview(x, y + 48, w)
            return
        card_y = y + 48
        for index, item in enumerate(items[:2]):
            height = 260 if index == 0 else 220
            self.draw_question_card(x, card_y, w, height, item, index + 1)
            card_y += height + 16
        self.text(x + 6, min(y + h - 20, card_y + 8), "ⓘ  以上为 AI 生成示例，内容仅供参考，请结合实际情况使用。", size=10, fill=COLORS["muted"])

    def draw_empty_preview(self, x, y, w):
        self.canvas.round_rect(x, y, x + w, y + 220, radius=10, fill="#ffffff", outline=COLORS["line"])
        self.text(x + w / 2, y + 86, "上传 PDF 后会自动生成题目预览", size=13, fill=COLORS["muted"], anchor="center")
        self.draw_button(x + w / 2 - 70, y + 124, 140, 34, "选择文件", COLORS["blue"], "white", self.choose_files)

    def draw_question_card(self, x, y, w, h, item, index):
        self.canvas.round_rect(x, y, x + w, y + h, radius=10, fill="#ffffff", outline=COLORS["line"])
        type_label = {"single": "选择题", "cloze": "填空题", "short": "简答题", "card": "闪卡"}.get(item.get("type"), "题目")
        type_bg = COLORS["blue_soft"] if type_label == "选择题" else COLORS["cyan_soft"] if type_label == "填空题" else COLORS["orange_soft"]
        type_fg = COLORS["blue"] if type_label == "选择题" else COLORS["cyan"] if type_label == "填空题" else COLORS["orange"]
        self.canvas.round_rect(x + 20, y + 18, x + 78, y + 46, radius=6, fill=type_bg, outline="")
        self.text(x + 49, y + 32, type_label, size=10, fill=type_fg, weight="bold", anchor="center")
        diff = "基础" if item.get("difficulty") == "简单" else "进阶" if item.get("difficulty") == "中等" else "综合"
        diff_bg = COLORS["green_soft"] if diff == "基础" else COLORS["orange_soft"]
        diff_fg = COLORS["green"] if diff == "基础" else COLORS["orange"]
        self.canvas.round_rect(x + w - 70, y + 18, x + w - 22, y + 46, radius=6, fill=diff_bg, outline="")
        self.text(x + w - 46, y + 32, diff, size=10, fill=diff_fg, weight="bold", anchor="center")
        prompt = f"{index}. {item.get('prompt', '')}"
        self.text(x + 20, y + 74, prompt, size=12, weight="bold", width=w - 54)
        yy = y + 116
        options = item.get("options") or []
        if options:
            for i, option in enumerate(options[:4]):
                self.canvas.create_oval(x + 24, yy + i * 34 - 2, x + 50, yy + i * 34 + 24, fill="#ffffff", outline=COLORS["line"])
                self.text(x + 37, yy + i * 34 + 11, chr(65 + i), size=10, fill="#526071", anchor="center")
                self.text(x + 66, yy + i * 34 + 2, str(option), size=11, fill="#3b4659", width=w - 96)
        else:
            self.canvas.round_rect(x + 20, yy, x + w - 20, yy + 48, radius=6, fill="#f7fcfd", outline="#bceaf0")
            self.text(x + 34, yy + 16, f"答案：{item.get('answer', '')[:80]}", size=11, fill="#18808b")
        self.canvas.create_line(x, y + h - 56, x + w, y + h - 56, fill=COLORS["line_soft"])
        self.canvas.round_rect(x + 20, y + h - 38, x + 92, y + h - 14, radius=6, fill=COLORS["blue_soft"], outline="")
        self.text(x + 56, y + h - 26, f"答案：{item.get('answer', '')[:12]}", size=10, fill=COLORS["blue"], weight="bold", anchor="center")
        self.text(x + w - 140, y + h - 28, "⧉  复制", size=10, fill=COLORS["muted"])
        self.text(x + w - 74, y + h - 28, "☆  收藏", size=10, fill=COLORS["muted"])

    def set_choice(self, variable, value):
        variable.set(value)
        self.store.settings.question_type = self.question_type.get()
        self.store.settings.difficulty = self.difficulty.get()
        self.store.save()
        self.render()

    def choose_files(self):
        paths = filedialog.askopenfilenames(
            title="选择学习资料",
            filetypes=[
                ("学习资料", "*.pdf *.png *.jpg *.jpeg *.webp *.txt *.md *.csv *.json"),
                ("所有文件", "*.*"),
            ],
        )
        if not paths:
            return
        self.uploaded_files = [Path(path) for path in paths]
        self.run_background(lambda: self.process_files(self.uploaded_files), "正在识别文件并自动生成题目...")

    def generate_from_current_files(self):
        if self.uploaded_files:
            self.run_background(lambda: self.process_files(self.uploaded_files), "正在重新生成题目...")
        else:
            self.choose_files()

    def run_background(self, fn, status):
        if self.busy:
            return
        self.busy = True
        self.status_text = status
        self.render()
        threading.Thread(target=self.safe_run, args=(fn,), daemon=True).start()

    def safe_run(self, fn):
        try:
            fn()
        except Exception as exc:
            self.queue.put(("error", str(exc)))
        finally:
            self.queue.put(("idle", "就绪"))

    def process_files(self, paths: list[Path]):
        created = 0
        for file_path in paths:
            try:
                self.queue.put(("info", f"正在识别：{file_path.name}"))
                text = self.extract_text(file_path)
                if len(text.strip()) < 20:
                    raise RuntimeError("识别文本太短，无法生成题目")
                self.queue.put(("info", f"正在出题：{file_path.name}"))
                generated = self.generate_questions(file_path.stem, text, file_path.name)
                self.store.add_set(generated, status="已解析")
                created += 1
            except Exception as exc:
                fallback = local_generate(file_path.stem, f"文件 {file_path.name} 处理失败：{exc}", file_path.name, 4)
                self.store.add_set(fallback, status="失败")
                self.queue.put(("error", f"{file_path.name} 处理失败：{exc}"))
        self.queue.put(("done", f"已处理 {len(paths)} 个文件，生成 {created} 个学习集"))

    def extract_text(self, file_path: Path) -> str:
        if file_path.suffix.lower() in TEXT_EXTS:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        try:
            return self.run_unlimited_ocr(file_path)
        except Exception as exc:
            self.queue.put(("info", f"Unlimited-OCR 暂不可用，改用 qwen3.5:4b 视觉识别：{exc}"))
            return self.run_ollama_vision_ocr(file_path)

    def run_unlimited_ocr(self, file_path: Path) -> str:
        settings = self.store.settings
        script = Path(settings.unlimited_ocr_script)
        if not script.exists():
            raise RuntimeError("未找到 Unlimited-OCR infer.py")
        output_dir = Path(tempfile.mkdtemp(prefix="startthinking-ocr-"))
        args = [settings.python_path, str(script)]
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
            raise RuntimeError((result.stderr or result.stdout or "Unlimited-OCR 执行失败")[:400])
        text = self.collect_text(output_dir)
        if not text.strip():
            raise RuntimeError("Unlimited-OCR 没有输出可读取文本")
        return text

    def run_ollama_vision_ocr(self, file_path: Path) -> str:
        images = self.file_to_images(file_path)
        parts = []
        for index, image_path in enumerate(images):
            self.queue.put(("info", f"正在用 qwen3.5:4b 识别第 {index + 1}/{len(images)} 页..."))
            parts.append(self.ocr_image_with_ollama(image_path, index + 1))
        text = "\n\n".join(part for part in parts if part.strip())
        if not text.strip():
            raise RuntimeError("qwen3.5:4b 视觉识别没有返回文本")
        return text

    def file_to_images(self, file_path: Path) -> list[Path]:
        suffix = file_path.suffix.lower()
        if suffix in IMAGE_EXTS:
            return [file_path]
        if suffix != ".pdf":
            raise RuntimeError(f"{file_path.name} 不是支持的 OCR 文件类型")
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PDF 识别需要 PyMuPDF，请先运行 scripts\\setup_unlimited_ocr.bat") from exc
        output_dir = Path(tempfile.mkdtemp(prefix="startthinking-pdf-"))
        doc = fitz.open(file_path)
        image_paths = []
        mat = fitz.Matrix(160 / 72, 160 / 72)
        for page_index, page in enumerate(doc):
            image_path = output_dir / f"page_{page_index + 1:04d}.png"
            page.get_pixmap(matrix=mat).save(image_path)
            image_paths.append(image_path)
        doc.close()
        return image_paths

    def ocr_image_with_ollama(self, image_path: Path, page_number: int) -> str:
        payload = {
            "model": self.store.settings.ollama_model,
            "stream": False,
            "think": False,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "请对这张学习资料图片做 OCR。只输出可复制的正文文本，保留标题、段落、列表、公式和表格中的关键信息。"
                        "不要解释，不要总结，不要添加资料中没有的内容。"
                        f"这是第 {page_number} 页。"
                    ),
                    "images": [base64.b64encode(image_path.read_bytes()).decode("utf-8")],
                }
            ],
            "options": {"temperature": 0, "num_predict": 4096},
        }
        response = self.ollama_post("/api/chat", payload, timeout=180)
        message = response.get("message", {})
        return message.get("content", "") or message.get("thinking", "")

    def collect_text(self, directory: Path) -> str:
        parts = []
        for path in directory.rglob("*"):
            if path.suffix.lower() in {".txt", ".md", ".json"}:
                parts.append(path.read_text(encoding="utf-8", errors="ignore"))
        return "\n\n".join(parts)

    def generate_questions(self, title: str, text: str, source: str) -> dict:
        try:
            payload = {
                "model": self.store.settings.ollama_model,
                "stream": False,
                "think": False,
                "messages": [
                    {"role": "system", "content": "你只输出严格 JSON。"},
                    {"role": "user", "content": self.build_prompt(title, text)},
                ],
                "options": {"temperature": 0.2, "num_predict": 8192},
            }
            response = self.ollama_post("/api/chat", payload, timeout=240)
            message = response.get("message", {})
            content = message.get("content", "") or message.get("thinking", "")
            return normalize_generated(parse_json_from_text(content), title, text, source)
        except Exception as exc:
            self.queue.put(("info", f"Ollama JSON 出题失败，已回退本地规则：{exc}"))
            return local_generate(title, text, source, self.store.settings.generation_count)

    def build_prompt(self, title: str, text: str) -> str:
        count = self.store.settings.generation_count
        return f"""你是严谨的个人复习出题助手。请只基于给定资料生成复习内容，不要编造资料外事实。
输出必须是严格 JSON，不要 Markdown，不要解释。结构如下：
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
要求：
- 题目总数约 {count} 个，闪卡约 {max(4, count // 2)} 张。
- 题目类型偏向：{self.question_type.get()}。
- 难度等级偏向：{self.difficulty.get()}。
- 单选题选项必须互斥，答案必须与选项之一完全一致。

标题：{title}

资料：
{text[:24000]}"""

    def ollama_post(self, path, payload, timeout=180):
        req = urllib.request.Request(
            self.store.settings.ollama_url.rstrip("/") + path,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def consume_queue(self):
        try:
            while True:
                kind, message = self.queue.get_nowait()
                if kind == "error":
                    self.status_text = message
                    messagebox.showerror("处理失败", message)
                elif kind == "info":
                    self.status_text = message
                elif kind == "done":
                    self.status_text = message
                elif kind == "idle":
                    self.busy = False
                    self.status_text = message
                self.render()
        except queue.Empty:
            pass
        self.root.after(200, self.consume_queue)


def normalize_generated(data: dict, title: str, text: str, source: str) -> dict:
    if not isinstance(data, dict):
        raise ValueError("模型返回内容不是 JSON 对象")
    questions = data.get("questions") or []
    cards = data.get("cards") or []
    if not isinstance(questions, list) or not isinstance(cards, list):
        raise ValueError("模型 JSON 缺少 questions/cards 数组")
    return {"title": data.get("title") or title, "source": source, "text": text, "questions": questions[:40], "cards": cards[:40]}


def main():
    root = tk.Tk()
    StartThinkingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
