# gui/float_window.py — POE2 AI 助手悬浮窗（游戏友好型深色界面）

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os

from ai.llm_engine import ask_ai, handle_special_command
from ai.memory_retriever import set_version_priority, get_current_version
from utils.memory_manager import export_memory, import_memory
from config import FLOAT_WINDOW, SUPPORTED_VERSIONS


class POE2FloatWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("POE2 全版本 AI 助手")
        self.root.overrideredirect(True)          # 无标题栏
        w = FLOAT_WINDOW["width"]
        h = FLOAT_WINDOW["height"]
        pos = FLOAT_WINDOW["position"]
        self.root.geometry(f"{w}x{h}{pos}")
        self.root.attributes("-topmost", FLOAT_WINDOW["always_on_top"])
        self.root.attributes("-alpha",   FLOAT_WINDOW["alpha"])
        self.root.config(bg="#111111")

        self.dragging  = False
        self.offset_x  = 0
        self.offset_y  = 0
        self._thinking = False

        self._setup_styles()
        self._build_ui()
        self._bind_events()

        # 欢迎消息
        self._append_msg(
            "系统",
            "🎮 POE2 全版本 AI 助手已启动！\n"
            "· 直接提问，例如：0.5赛季符咒怎么玩？\n"
            "· 指令：初始化[版本]赛季总结：<内容>\n"
            "· 指令：做装心得：<内容>  |  收藏BD：<内容>\n"
            "· 指令：记录：<你的新发现>",
            tag="system"
        )

    # ──────────────────────────────────────────────
    # 样式
    # ──────────────────────────────────────────────

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        # 通用
        s.configure("TFrame",    background="#111111")
        s.configure("TLabel",    background="#111111", foreground="#cccccc", font=("Consolas", 10))
        # 标题栏
        s.configure("Bar.TFrame",  background="#1e1e2e")
        s.configure("Bar.TLabel",  background="#1e1e2e", foreground="#e0aaff", font=("Consolas", 11, "bold"))
        s.configure("Close.TButton",  background="#c0392b", foreground="white", borderwidth=0, relief="flat", padding=2)
        s.configure("Hide.TButton",   background="#444466", foreground="white", borderwidth=0, relief="flat", padding=2)
        s.map("Close.TButton", background=[("active","#e74c3c")])
        s.map("Hide.TButton",  background=[("active","#5555aa")])
        # 版本区
        s.configure("Ver.TFrame",    background="#161625")
        s.configure("Ver.TLabel",    background="#161625", foreground="#aaaacc", font=("Consolas", 9))
        s.configure("Switch.TButton",background="#3d5a80", foreground="white", borderwidth=0, relief="flat", padding=3)
        s.map("Switch.TButton", background=[("active","#5588bb")])
        # 发送按钮
        s.configure("Send.TButton",  background="#2e7d32", foreground="white", borderwidth=0, relief="flat", padding=4)
        s.map("Send.TButton", background=[("active","#43a047")])
        # 记忆按钮
        s.configure("Mem.TButton",   background="#4a148c", foreground="white", borderwidth=0, relief="flat", padding=3)
        s.map("Mem.TButton", background=[("active","#7b1fa2")])
        # 爬虫按钮
        s.configure("Crawl.TButton", background="#1a237e", foreground="white", borderwidth=0, relief="flat", padding=3)
        s.map("Crawl.TButton", background=[("active","#283593")])

    # ──────────────────────────────────────────────
    # UI 构建
    # ──────────────────────────────────────────────

    def _build_ui(self):
        # ─ 标题栏 ─
        bar = ttk.Frame(self.root, style="Bar.TFrame", height=30)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)
        ttk.Label(bar, text="⚡ POE2 AI 助手", style="Bar.TLabel").pack(side=tk.LEFT, padx=10)
        ttk.Button(bar, text="×", width=3, command=self._quit,   style="Close.TButton").pack(side=tk.RIGHT, padx=2)
        ttk.Button(bar, text="−", width=3, command=self._hide,   style="Hide.TButton").pack(side=tk.RIGHT, padx=2)
        bar.bind("<ButtonPress-1>",   self._drag_start)
        bar.bind("<B1-Motion>",       self._drag_move)

        # ─ 版本切换 ─
        ver_frame = ttk.Frame(self.root, style="Ver.TFrame")
        ver_frame.pack(fill=tk.X, padx=8, pady=(4, 0))
        ttk.Label(ver_frame, text="当前版本：", style="Ver.TLabel").pack(side=tk.LEFT)
        self.ver_var = tk.StringVar(value=get_current_version())
        self.ver_box = ttk.Combobox(
            ver_frame, textvariable=self.ver_var,
            values=SUPPORTED_VERSIONS, state="readonly", width=6,
            font=("Consolas", 9)
        )
        self.ver_box.pack(side=tk.LEFT, padx=4)
        ttk.Button(ver_frame, text="切换版本", command=self._switch_version, style="Switch.TButton").pack(side=tk.LEFT, padx=4)
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(ver_frame, textvariable=self.status_var, style="Ver.TLabel").pack(side=tk.RIGHT, padx=6)

        # ─ 对话区域 ─
        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD,
            bg="#0d0d1a", fg="#e0e0e0",
            font=("Consolas", 10),
            insertbackground="white",
            relief="flat", bd=0,
            padx=6, pady=4,
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.chat.config(state=tk.DISABLED)
        # 文字颜色标签
        self.chat.tag_config("system", foreground="#7986cb")
        self.chat.tag_config("user",   foreground="#80cbc4")
        self.chat.tag_config("ai",     foreground="#a5d6a7")
        self.chat.tag_config("error",  foreground="#ef9a9a")

        # ─ 输入框 + 发送 ─
        inp_frame = ttk.Frame(self.root)
        inp_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        self.entry = tk.Entry(
            inp_frame, bg="#1a1a2e", fg="#ffffff",
            insertbackground="white", relief="flat",
            font=("Consolas", 10), bd=4,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.entry.bind("<Return>", lambda e: self._send())
        ttk.Button(inp_frame, text="发送", command=self._send, style="Send.TButton").pack(side=tk.RIGHT)

        # ─ 功能按钮行 ─
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 6))
        ttk.Button(btn_frame, text="导出记忆", command=self._export_mem, style="Mem.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="导入记忆", command=self._import_mem, style="Mem.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="立即爬取", command=self._crawl_now,  style="Crawl.TButton").pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="清屏",     command=self._clear_chat, style="Crawl.TButton").pack(side=tk.RIGHT, padx=2)

    # ──────────────────────────────────────────────
    # 事件绑定
    # ──────────────────────────────────────────────

    def _bind_events(self):
        self.root.bind("<Escape>", self._hide)
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    def _drag_start(self, event):
        self.dragging = True
        self.offset_x = event.x
        self.offset_y = event.y

    def _drag_move(self, event):
        if self.dragging:
            x = self.root.winfo_x() + event.x - self.offset_x
            y = self.root.winfo_y() + event.y - self.offset_y
            self.root.geometry(f"+{x}+{y}")

    def _hide(self, _=None):
        self.root.withdraw()

    def show(self):
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.lift()

    def _quit(self):
        self.root.destroy()

    # ──────────────────────────────────────────────
    # 对话逻辑
    # ──────────────────────────────────────────────

    def _send(self):
        text = self.entry.get().strip()
        if not text or self._thinking:
            return
        self.entry.delete(0, tk.END)
        self._append_msg("你", text, tag="user")

        # 先检查特殊指令
        result = handle_special_command(text)
        if result is not None:
            self._append_msg("系统", result, tag="system")
            return

        # 异步调用 AI，避免冻结 UI
        self._thinking = True
        self.status_var.set("思考中…")
        threading.Thread(target=self._ask_thread, args=(text,), daemon=True).start()

    def _ask_thread(self, question: str):
        try:
            answer = ask_ai(question)
        except Exception as e:
            answer = f"❌ AI 调用失败：{e}"
        self.root.after(0, self._on_answer, answer)

    def _on_answer(self, answer: str):
        self._thinking = False
        self.status_var.set("就绪")
        self._append_msg("AI助手", answer, tag="ai")

    def _append_msg(self, sender: str, text: str, tag: str = "ai"):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, f"[{sender}]\n{text}\n\n", tag)
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _clear_chat(self):
        self.chat.config(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        self.chat.config(state=tk.DISABLED)

    # ──────────────────────────────────────────────
    # 版本切换
    # ──────────────────────────────────────────────

    def _switch_version(self):
        ver = self.ver_var.get()
        set_version_priority(ver)
        from crawler import set_crawler_version
        set_crawler_version(ver)
        self._append_msg("系统", f"✅ 已切换至 {ver} 版本，AI 将优先使用该版本记忆与资讯", tag="system")

    # ──────────────────────────────────────────────
    # 记忆操作
    # ──────────────────────────────────────────────

    def _export_mem(self):
        save_path = filedialog.asksaveasfilename(
            title="导出记忆包",
            defaultextension=".zip",
            initialfile="POE2_AI记忆包",
            filetypes=[("ZIP文件", "*.zip")],
        )
        if save_path:
            # 去掉 .zip 后缀（export_memory 会自动加）
            base = save_path[:-4] if save_path.endswith(".zip") else save_path
            result = export_memory(base)
            self._append_msg("系统", result, tag="system")

    def _import_mem(self):
        zip_path = filedialog.askopenfilename(
            title="选择记忆包",
            filetypes=[("ZIP文件", "*.zip")],
        )
        if zip_path:
            result = import_memory(zip_path)
            self._append_msg("系统", result, tag="system")

    # ──────────────────────────────────────────────
    # 立即爬取
    # ──────────────────────────────────────────────

    def _crawl_now(self):
        self._append_msg("系统", "⏳ 正在立即爬取所有资讯，请稍候…", tag="system")
        self.status_var.set("爬取中…")
        threading.Thread(target=self._crawl_thread, daemon=True).start()

    def _crawl_thread(self):
        from crawler import _run_all_once
        result = _run_all_once()
        self.root.after(0, self._on_crawl_done, result)

    def _on_crawl_done(self, result: str):
        self.status_var.set("就绪")
        self._append_msg("系统", f"✅ 爬取完成：\n{result}", tag="system")

    # ──────────────────────────────────────────────
    # 启动
    # ──────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


def start_float_window():
    win = POE2FloatWindow()
    win.run()
