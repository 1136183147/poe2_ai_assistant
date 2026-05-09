# gui/float_window.py — POE2 AI 助手悬浮窗（游戏友好型深色界面）

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
import time
from typing import Dict

from ai.llm_engine import ask_ai, handle_special_command
from ai.memory_retriever import set_version_priority, get_current_version
from utils.memory_manager import export_memory, import_memory
from config import FLOAT_WINDOW, SUPPORTED_VERSIONS, DEFAULT_SERVER, DEFAULT_LEAGUE, LLM_CONFIG, LLM_PROVIDER

try:
    from price_checker.trade_api import PriceChecker, get_server_list, quick_check
    HAS_PRICE_CHECKER = True
except ImportError:
    HAS_PRICE_CHECKER = False

try:
    from price_checker.screenshot_ocr import ScreenshotOCR
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


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
            "· 指令：记录：<你的新发现>\n"
            "· 指令：查价 <装备名称> （需配置 POESESSID）",
            tag="system"
        )
        
        # 查价器状态
        self._price_checker = None
        self._current_server = DEFAULT_SERVER

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
        # 查价按钮
        s.configure("Price.TButton", background="#e65100", foreground="white", borderwidth=0, relief="flat", padding=3)
        s.map("Price.TButton", background=[("active","#ff7043")])

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
        
        # LLM模型选择
        ttk.Label(ver_frame, text=" | ", style="Ver.TLabel").pack(side=tk.LEFT)
        ttk.Label(ver_frame, text="模型：", style="Ver.TLabel").pack(side=tk.LEFT)
        self.llm_var = tk.StringVar(value=LLM_PROVIDER)
        self.llm_box = ttk.Combobox(
            ver_frame, textvariable=self.llm_var,
            values=list(LLM_CONFIG.keys()), state="readonly", width=8,
            font=("Consolas", 9)
        )
        self.llm_box.pack(side=tk.LEFT, padx=4)
        ttk.Button(ver_frame, text="切换", command=self._switch_llm, style="Switch.TButton").pack(side=tk.LEFT, padx=4)
        
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
        ttk.Button(btn_frame, text="配置",     command=self._open_config, style="Price.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="导出记忆", command=self._export_mem, style="Mem.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="导入记忆", command=self._import_mem, style="Mem.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="查价器",   command=self._open_price_checker, style="Price.TButton").pack(side=tk.RIGHT, padx=2)
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
    
    def _switch_llm(self):
        """切换LLM模型"""
        llm_provider = self.llm_var.get()
        
        # 更新全局配置
        import config
        config.LLM_PROVIDER = llm_provider
        
        # 检查是否配置了API Key
        llm_config = LLM_CONFIG.get(llm_provider, {})
        api_key = llm_config.get("api_key", "")
        
        if api_key.startswith("YOUR_"):
            self._append_msg("系统", f"⚠️ 已切换至 {llm_provider} 模型，但尚未配置 API Key", tag="system")
        else:
            self._append_msg("系统", f"✅ 已切换至 {llm_provider} 模型，当前模型: {llm_config.get('model', '')}", tag="system")

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
    # 查价器功能
    # ──────────────────────────────────────────────

    def _open_price_checker(self):
        """打开查价器窗口"""
        if not HAS_PRICE_CHECKER:
            self._append_msg("系统", "❌ 查价器模块未加载", tag="error")
            return
        
        # 创建查价器窗口
        price_win = tk.Toplevel(self.root)
        price_win.title("POE2 装备查价器")
        price_win.geometry("500x600")
        price_win.attributes("-topmost", True)
        price_win.config(bg="#111111")
        
        # 配置区域
        config_frame = ttk.Frame(price_win)
        config_frame.pack(fill=tk.X, padx=8, pady=8)
        
        # POESESSID 输入
        ttk.Label(config_frame, text="POESESSID：", background="#111111", foreground="#aaaacc").pack(side=tk.TOP, anchor=tk.W)
        self._poessid_entry = tk.Entry(
            config_frame, bg="#1a1a2e", fg="#ffffff",
            insertbackground="white", relief="flat",
            font=("Consolas", 9), bd=3, width=40
        )
        self._poessid_entry.pack(side=tk.TOP, fill=tk.X)
        # 读取当前配置
        current_poessid = self._get_poessid()
        self._poessid_entry.insert(0, current_poessid)
        
        # 服务器选择
        server_frame = ttk.Frame(config_frame)
        server_frame.pack(fill=tk.X, pady=4)
        ttk.Label(server_frame, text="服务器：", background="#111111", foreground="#aaaacc").pack(side=tk.LEFT)
        server_list = get_server_list()
        self._server_var = tk.StringVar(value=self._current_server)
        server_box = ttk.Combobox(
            server_frame, textvariable=self._server_var,
            values=[s[0] for s in server_list], state="readonly", width=12,
            font=("Consolas", 9)
        )
        server_box.pack(side=tk.LEFT, padx=4)
        ttk.Button(server_frame, text="保存配置", command=self._save_price_config, style="Send.TButton").pack(side=tk.RIGHT)
        
        # 截图识别按钮
        ocr_frame = ttk.Frame(price_win)
        ocr_frame.pack(fill=tk.X, padx=8, pady=4)
        self._ocr_btn = ttk.Button(
            ocr_frame, 
            text="📷 截图识别（F9）", 
            command=self._capture_and_recognize, 
            style="Price.TButton"
        )
        self._ocr_btn.pack(side=tk.LEFT)
        
        # 手动输入按钮（作为OCR的备用方案）
        ttk.Button(
            ocr_frame, 
            text="✏️ 手动输入", 
            command=self._open_manual_input, 
            style="Price.TButton"
        ).pack(side=tk.LEFT, padx=4)
        
        if not HAS_OCR:
            ttk.Label(ocr_frame, text="（OCR未安装，可使用手动输入）", 
                      background="#111111", foreground="#ffaa00", font=("Consolas", 8)).pack(side=tk.LEFT, padx=4)
        
        # 装备名称输入
        name_frame = ttk.Frame(price_win)
        name_frame.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(name_frame, text="装备名称：", background="#111111", foreground="#aaaacc").pack(side=tk.LEFT)
        self._price_entry = tk.Entry(
            name_frame, bg="#1a1a2e", fg="#ffffff",
            insertbackground="white", relief="flat",
            font=("Consolas", 10), bd=4, width=35
        )
        self._price_entry.pack(side=tk.LEFT)
        self._price_entry.bind("<Return>", lambda e: self._check_price())
        
        # 装备类型筛选（仿照官方交易界面）
        type_frame = ttk.Frame(price_win)
        type_frame.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(type_frame, text="类型：", background="#111111", foreground="#aaaacc").pack(side=tk.LEFT)
        self._item_type_var = tk.StringVar(value="全部")
        self._item_type_box = ttk.Combobox(
            type_frame, textvariable=self._item_type_var,
            values=["全部", "武器", "护甲", "首饰", "武器-剑", "武器-斧", "武器-锤", "武器-匕首", "武器-法杖", "武器-弓"],
            state="readonly", width=12, font=("Consolas", 9)
        )
        self._item_type_box.pack(side=tk.LEFT, padx=4)
        
        # 稀有度筛选
        ttk.Label(type_frame, text="稀有度：", background="#111111", foreground="#aaaacc").pack(side=tk.LEFT)
        self._rarity_var = tk.StringVar(value="全部")
        self._rarity_box = ttk.Combobox(
            type_frame, textvariable=self._rarity_var,
            values=["全部", "普通", "魔法", "稀有", "传奇"],
            state="readonly", width=8, font=("Consolas", 9)
        )
        self._rarity_box.pack(side=tk.LEFT, padx=4)
        
        # 等级范围
        lvl_frame = ttk.Frame(type_frame)
        lvl_frame.pack(side=tk.LEFT, padx=4)
        ttk.Label(lvl_frame, text="等级：", background="#111111", foreground="#aaaacc").pack(side=tk.LEFT)
        self._min_lvl_entry = tk.Entry(lvl_frame, bg="#1a1a2e", fg="#ffffff", insertbackground="white", 
                                       relief="flat", font=("Consolas", 9), width=4)
        self._min_lvl_entry.pack(side=tk.LEFT)
        ttk.Label(lvl_frame, text="-", background="#111111", foreground="#666666").pack(side=tk.LEFT)
        self._max_lvl_entry = tk.Entry(lvl_frame, bg="#1a1a2e", fg="#ffffff", insertbackground="white", 
                                       relief="flat", font=("Consolas", 9), width=4)
        self._max_lvl_entry.pack(side=tk.LEFT)
        
        # 词缀输入区域（仿照官方的词缀搜索）
        affix_frame = ttk.Frame(price_win)
        affix_frame.pack(fill=tk.X, padx=8, pady=4)
        
        # 词缀搜索框（类似官方的自由搜索）
        ttk.Label(affix_frame, text="词缀搜索：", background="#111111", foreground="#aaaacc").pack(side=tk.LEFT)
        self._affix_entry = tk.Entry(
            affix_frame, bg="#1a1a2e", fg="#ffffff",
            insertbackground="white", relief="flat",
            font=("Consolas", 9), bd=2, width=40,
            placeholder="输入词缀关键词，如：物理伤害、攻击速度、最大生命"
        )
        self._affix_entry.pack(side=tk.LEFT, padx=4)
        
        # 快速词缀按钮（常用词缀一键添加）
        quick_affix_frame = ttk.Frame(price_win)
        quick_affix_frame.pack(fill=tk.X, padx=8, pady=2)
        quick_affixes = ["物理伤害", "攻击速度", "暴击几率", "最大生命", "施法速度", "技能等级"]
        for affix in quick_affixes:
            ttk.Button(quick_affix_frame, text=affix, command=lambda a=affix: self._add_quick_affix(a),
                      style="Price.TButton").pack(side=tk.LEFT, padx=2)
        
        # 搜索按钮
        btn_frame = ttk.Frame(price_win)
        btn_frame.pack(fill=tk.X, padx=8, pady=4)
        ttk.Button(btn_frame, text="🔍 查询价格", command=self._check_price, style="Send.TButton").pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="🗑️ 清空选择", command=self._clear_affixes, style="Crawl.TButton").pack(side=tk.RIGHT)
        
        # 结果显示区
        self._price_result = scrolledtext.ScrolledText(
            price_win, wrap=tk.WORD,
            bg="#0d0d1a", fg="#e0e0e0",
            font=("Consolas", 9),
            insertbackground="white",
            relief="flat", bd=0,
            padx=6, pady=4,
            height=18
        )
        self._price_result.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._price_result.config(state=tk.DISABLED)
        
        # 提示信息
        self._price_result.config(state=tk.NORMAL)
        self._price_result.insert(tk.END, "💡 使用方式：\n")
        self._price_result.insert(tk.END, "1. 点击「截图识别」按钮截取装备界面\n")
        self._price_result.insert(tk.END, "2. 或手动输入装备名称和词缀\n")
        self._price_result.insert(tk.END, "3. 点击「查询价格」搜索\n\n")
        self._price_result.insert(tk.END, "当前服务器：\n")
        for key, name in server_list:
            status = "✓" if key == self._current_server else ""
            self._price_result.insert(tk.END, f"  - {key}: {name} {status}\n")
        self._price_result.config(state=tk.DISABLED)
        
        # 绑定 F9 快捷键
        price_win.bind("<F9>", lambda e: self._capture_and_recognize())
    
    def _clear_affixes(self):
        """清空搜索条件"""
        # 清空装备名称
        self._price_entry.delete(0, tk.END)
        # 重置类型和稀有度
        self._item_type_var.set("全部")
        self._rarity_var.set("全部")
        # 清空等级范围
        self._min_lvl_entry.delete(0, tk.END)
        self._max_lvl_entry.delete(0, tk.END)
        # 清空词缀搜索
        self._affix_entry.delete(0, tk.END)
    
    def _add_quick_affix(self, affix):
        """快速添加常用词缀"""
        current = self._affix_entry.get()
        if current:
            self._affix_entry.insert(tk.END, f", {affix}")
        else:
            self._affix_entry.insert(tk.END, affix)
    
    def _open_manual_input(self):
        """打开手动输入装备信息的窗口"""
        manual_win = tk.Toplevel(self.root)
        manual_win.title("✏️ 手动输入装备信息")
        manual_win.geometry("400x380")
        manual_win.configure(bg="#111111")
        manual_win.resizable(False, False)
        
        # 装备名称
        ttk.Label(manual_win, text="装备名称：", background="#111111", foreground="#aaaacc").pack(padx=8, pady=(10, 2), anchor=tk.W)
        name_entry = tk.Entry(manual_win, bg="#1a1a2e", fg="#ffffff", insertbackground="white", 
                             relief="flat", font=("Consolas", 10), bd=2, width=40)
        name_entry.pack(padx=8, pady=2, fill=tk.X)
        
        # 装备类型
        ttk.Label(manual_win, text="装备类型：", background="#111111", foreground="#aaaacc").pack(padx=8, pady=4, anchor=tk.W)
        type_var = tk.StringVar(value="武器")
        type_box = ttk.Combobox(manual_win, textvariable=type_var,
                                values=["武器", "护甲", "首饰", "武器-剑", "武器-斧", "武器-锤", "武器-匕首", "武器-法杖", "武器-弓"],
                                state="readonly", width=38, font=("Consolas", 9))
        type_box.pack(padx=8, pady=2, fill=tk.X)
        
        # 等级
        ttk.Label(manual_win, text="等级：", background="#111111", foreground="#aaaacc").pack(padx=8, pady=4, anchor=tk.W)
        level_entry = tk.Entry(manual_win, bg="#1a1a2e", fg="#ffffff", insertbackground="white", 
                               relief="flat", font=("Consolas", 10), bd=2, width=10)
        level_entry.pack(padx=8, pady=2, anchor=tk.W)
        
        # 稀有度
        ttk.Label(manual_win, text="稀有度：", background="#111111", foreground="#aaaacc").pack(padx=8, pady=4, anchor=tk.W)
        rarity_var = tk.StringVar(value="稀有")
        rarity_box = ttk.Combobox(manual_win, textvariable=rarity_var,
                                  values=["普通", "魔法", "稀有", "传奇"],
                                  state="readonly", width=38, font=("Consolas", 9))
        rarity_box.pack(padx=8, pady=2, fill=tk.X)
        
        # 前缀词缀
        ttk.Label(manual_win, text="前缀词缀（每行一个）：", background="#111111", foreground="#aaaacc").pack(padx=8, pady=4, anchor=tk.W)
        prefix_text = scrolledtext.ScrolledText(manual_win, wrap=tk.WORD, bg="#1a1a2e", fg="#4ade80",
                                                font=("Consolas", 9), height=4, width=40)
        prefix_text.pack(padx=8, pady=2, fill=tk.X)
        
        # 后缀词缀
        ttk.Label(manual_win, text="后缀词缀（每行一个）：", background="#111111", foreground="#aaaacc").pack(padx=8, pady=4, anchor=tk.W)
        suffix_text = scrolledtext.ScrolledText(manual_win, wrap=tk.WORD, bg="#1a1a2e", fg="#60a5fa",
                                                font=("Consolas", 9), height=4, width=40)
        suffix_text.pack(padx=8, pady=2, fill=tk.X)
        
        # 确认按钮
        def confirm_input():
            equipment = {
                "name": name_entry.get().strip(),
                "type": type_var.get(),
                "level": int(level_entry.get()) if level_entry.get().isdigit() else 0,
                "rarity": rarity_var.get(),
                "prefixes": [line.strip() for line in prefix_text.get("1.0", tk.END).split("\n") if line.strip()],
                "suffixes": [line.strip() for line in suffix_text.get("1.0", tk.END).split("\n") if line.strip()]
            }
            
            # 保存到装备库
            try:
                from memory.equipment_storage import EquipmentStorage
                storage = EquipmentStorage()
                equip_id = storage.save_equipment(equipment)
                save_info = f"✅ 已保存到装备库 (ID: {equip_id})"
            except Exception as e:
                save_info = f"⚠️ 保存失败: {e}"
            
            # 在悬浮窗显示结果
            result_lines = [
                f"📷 装备名称: {equipment['name']}",
                f"📦 装备类型: {equipment['type']}",
                f"📊 等级: {equipment['level']}",
                f"💎 稀有度: {equipment['rarity']}"
            ]
            if equipment['prefixes']:
                result_lines.append(f"🔸 前缀: {', '.join(equipment['prefixes'])}")
            if equipment['suffixes']:
                result_lines.append(f"🔹 后缀: {', '.join(equipment['suffixes'])}")
            
            self._append_msg("手动输入", "\n".join(result_lines) + f"\n{save_info}", tag="system")
            
            # 如果查价器窗口已打开，自动填充数据
            if hasattr(self, '_price_result') and self._price_result is not None:
                if equipment['name']:
                    self._price_entry.delete(0, tk.END)
                    self._price_entry.insert(0, equipment['name'])
                
                all_affixes = equipment['prefixes'] + equipment['suffixes']
                if all_affixes:
                    self._affix_entry.delete(0, tk.END)
                    self._affix_entry.insert(0, ', '.join(all_affixes))
            
            manual_win.destroy()
        
        ttk.Button(manual_win, text="确认输入", command=confirm_input, style="Send.TButton").pack(pady=10)
        manual_win.focus_set()
    
    def _capture_and_recognize(self):
        """截图识别装备信息（直接在悬浮窗显示结果）"""
        if not HAS_OCR:
            self._append_msg("系统", "❌ OCR 模块未加载，请安装：pip install pillow pytesseract", tag="error")
            return
        
        # 直接在悬浮窗消息区域显示提示
        self._append_msg("系统", "📷 请将鼠标移动到装备界面，3秒后自动截图...", tag="system")
        
        threading.Thread(target=self._capture_thread, daemon=True).start()
    
    def _capture_thread(self):
        """后台线程执行截图识别"""
        try:
            # 延迟3秒让用户准备
            time.sleep(3)
            
            ocr = ScreenshotOCR()
            text, equipment = ocr.capture_and_parse()
            
            # 更新UI
            self.root.after(0, self._on_capture_done, text, equipment)
        except Exception as e:
            self.root.after(0, self._on_capture_done, f"❌ 识别失败：{e}", {})
    
    def _on_capture_done(self, text: str, equipment: Dict):
        """处理截图识别结果（直接在悬浮窗显示）"""
        if "❌" in text:
            self._append_msg("系统", text, tag="error")
            return
        
        # 保存装备数据到记忆库
        try:
            from memory.equipment_storage import EquipmentStorage
            storage = EquipmentStorage()
            equipment["ocr_text"] = text
            equip_id = storage.save_equipment(equipment)
            save_info = f"✅ 已保存到装备库 (ID: {equip_id})"
        except Exception as e:
            save_info = f"⚠️ 保存失败: {e}"
        
        # 在悬浮窗显示识别结果
        result_lines = [
            f"📷 装备名称: {equipment.get('name', '未识别')}",
            f"📦 装备类型: {equipment.get('type', '未识别')}",
            f"📊 等级: {equipment.get('level', 0)}",
            f"💎 稀有度: {equipment.get('rarity', '未识别')}"
        ]
        
        if equipment.get('prefixes'):
            result_lines.append(f"🔸 前缀: {', '.join(equipment['prefixes'])}")
        if equipment.get('suffixes'):
            result_lines.append(f"🔹 后缀: {', '.join(equipment['suffixes'])}")
        
        self._append_msg("截图识别", "\n".join(result_lines) + f"\n{save_info}", tag="system")
        
        # 如果查价器窗口已打开，自动填充数据
        if hasattr(self, '_price_result') and self._price_result is not None:
            if equipment.get('name'):
                self._price_entry.delete(0, tk.END)
                self._price_entry.insert(0, equipment['name'])
            
            # 填充词缀到搜索框
            all_affixes = []
            if equipment.get('prefixes'):
                all_affixes.extend(equipment['prefixes'])
            if equipment.get('suffixes'):
                all_affixes.extend(equipment['suffixes'])
            
            if all_affixes:
                self._affix_entry.delete(0, tk.END)
                self._affix_entry.insert(0, ', '.join(all_affixes))
            
            # 填充识别到的装备名称
            if equipment.get('name'):
                self._price_entry.delete(0, tk.END)
                self._price_entry.insert(0, equipment['name'])
        
        self._price_result.config(state=tk.DISABLED)
        self._price_result.see(tk.END)
    
    def _switch_server(self):
        """切换服务器"""
        self._current_server = self._server_var.get()
        self._price_checker = None
        self._append_msg("系统", f"✅ 已切换至 {self._current_server} 服务器", tag="system")
    
    def _check_price(self):
        """执行价格查询（仿照官方交易界面）"""
        item_name = self._price_entry.get().strip()
        
        # 获取搜索条件
        item_type = self._item_type_var.get()
        rarity = self._rarity_var.get()
        min_lvl = self._min_lvl_entry.get().strip()
        max_lvl = self._max_lvl_entry.get().strip()
        affix_text = self._affix_entry.get().strip()
        
        # 解析词缀列表
        selected_affixes = []
        if affix_text:
            selected_affixes.extend([a.strip() for a in affix_text.split(",") if a.strip()])
        
        self._price_result.config(state=tk.NORMAL)
        self._price_result.delete("1.0", tk.END)
        
        # 构建搜索条件描述
        search_desc = f"⏳ 正在查询"
        if item_name:
            search_desc += f" '{item_name}'"
        if item_type != "全部":
            search_desc += f" 类型:{item_type}"
        if rarity != "全部":
            search_desc += f" 稀有度:{rarity}"
        if min_lvl or max_lvl:
            search_desc += f" 等级:{min_lvl}-{max_lvl}"
        if selected_affixes:
            search_desc += f" 词缀:{','.join(selected_affixes)}"
        
        self._price_result.insert(tk.END, search_desc + "...\n")
        if selected_affixes:
            self._price_result.insert(tk.END, f"词缀筛选: {', '.join(selected_affixes)}\n")
        self._price_result.config(state=tk.DISABLED)
        
        threading.Thread(target=self._price_check_thread, args=(item_name, selected_affixes), daemon=True).start()
    
    def _price_check_thread(self, item_name: str, affixes: list = None):
        """后台线程执行价格查询"""
        try:
            if self._price_checker is None:
                self._price_checker = PriceChecker(server=self._current_server)
            
            message, prices = self._price_checker.check_price(item_name, affixes=affixes)
            result = self._price_checker.format_price_result(message, prices)
        except Exception as e:
            result = f"❌ 查询失败：{e}"
        
        self.root.after(0, self._on_price_check_done, result)
    
    def _on_price_check_done(self, result: str):
        """处理价格查询结果"""
        self._price_result.config(state=tk.NORMAL)
        self._price_result.delete("1.0", tk.END)
        self._price_result.insert(tk.END, result)
        self._price_result.config(state=tk.DISABLED)
        self._price_result.see(tk.END)

    # ──────────────────────────────────────────────
    # 配置界面
    # ──────────────────────────────────────────────

    def _open_config(self):
        """打开配置窗口"""
        # 创建配置窗口
        config_win = tk.Toplevel(self.root)
        config_win.title("POE2 AI 助手配置")
        config_win.geometry("400x350")
        config_win.attributes("-topmost", True)
        config_win.config(bg="#111111")
        
        # 获取当前配置
        current_poessid = self._get_current_poessid()
        current_server = DEFAULT_SERVER
        
        # POESESSID 配置
        poessid_frame = ttk.Frame(config_win)
        poessid_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(poessid_frame, text="POESESSID：", background="#111111", foreground="#aaaacc").pack(side=tk.TOP, anchor=tk.W)
        self._config_poessid = tk.Entry(
            poessid_frame, bg="#1a1a2e", fg="#ffffff",
            insertbackground="white", relief="flat",
            font=("Consolas", 9), bd=4, width=50
        )
        self._config_poessid.insert(0, current_poessid)
        self._config_poessid.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(poessid_frame, text="（登录游戏官网后在浏览器开发者工具中获取）", 
                  background="#111111", foreground="#666666", font=("Consolas", 8)).pack(side=tk.TOP, anchor=tk.W)
        
        # 服务器配置
        server_frame = ttk.Frame(config_win)
        server_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(server_frame, text="默认服务器：", background="#111111", foreground="#aaaacc").pack(side=tk.LEFT)
        server_list = get_server_list() if HAS_PRICE_CHECKER else []
        self._config_server = tk.StringVar(value=current_server)
        server_box = ttk.Combobox(
            server_frame, textvariable=self._config_server,
            values=[s[0] for s in server_list] if server_list else ["international"], 
            state="readonly", width=12,
            font=("Consolas", 9)
        )
        server_box.pack(side=tk.LEFT, padx=4)
        
        # 服务器名称显示
        if server_list:
            for key, name in server_list:
                if key == current_server:
                    ttk.Label(server_frame, text=f"({name})", background="#111111", foreground="#7986cb").pack(side=tk.LEFT)
                    break
        
        # 保存按钮
        ttk.Button(config_win, text="💾 保存配置", command=self._save_config, style="Send.TButton").pack(pady=8)
        
        # 提示信息
        tips_frame = ttk.Frame(config_win)
        tips_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(tips_frame, text="📌 配置说明：", background="#111111", foreground="#e0aaff", font=("Consolas", 9, "bold")).pack(anchor=tk.W)
        tips_text = """
1. POESESSID 是登录游戏官网后的 Cookie
2. 获取方式：登录官网 → F12 → Application → Cookies → POESESSID
3. 配置保存后立即生效，无需重启
4. 不同服务器需使用对应官网的 POESESSID
"""
        ttk.Label(tips_frame, text=tips_text.strip(), background="#111111", foreground="#888888", 
                  font=("Consolas", 8), justify=tk.LEFT).pack(anchor=tk.W)
    
    def _get_poessid(self):
        """获取当前配置文件中的 POESESSID"""
        try:
            with open("config.py", "r", encoding="utf-8") as f:
                content = f.read()
                # 提取 POESESSID 值
                import re
                match = re.search(r'POESESSID\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return ""
    
    def _save_price_config(self):
        """保存查价器配置到 config.py"""
        poessid = self._poessid_entry.get().strip()
        server = self._server_var.get()
        
        try:
            with open("config.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # 更新 POESESSID
            import re
            content = re.sub(r"POESESSID\s*=\s*[\"'][^\"']+[\"']", f'POESESSID = "{poessid}"', content)
            
            # 更新 DEFAULT_SERVER
            content = re.sub(r"DEFAULT_SERVER\s*=\s*[\"'][^\"']+[\"']", f'DEFAULT_SERVER = "{server}"', content)
            
            with open("config.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            # 更新当前服务器
            self._current_server = server
            self._price_checker = None
            
            self._append_msg("系统", "✅ 配置已保存！POESESSID 和服务器设置已更新", tag="system")
            
        except Exception as e:
            self._append_msg("系统", f"❌ 保存失败：{e}", tag="error")
    
    def _save_config(self):
        """保存配置到 config.py（原配置窗口使用）"""
        poessid = self._config_poessid.get().strip()
        server = self._config_server.get()
        
        try:
            with open("config.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # 更新 POESESSID
            import re
            content = re.sub(r"POESESSID\s*=\s*[\"'][^\"']+[\"']", f'POESESSID = "{poessid}"', content)
            
            # 更新 DEFAULT_SERVER
            content = re.sub(r"DEFAULT_SERVER\s*=\s*[\"'][^\"']+[\"']", f'DEFAULT_SERVER = "{server}"', content)
            
            with open("config.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            # 更新当前服务器
            self._current_server = server
            self._price_checker = None
            
            self._append_msg("系统", "✅ 配置已保存！POESESSID 和服务器设置已更新", tag="system")
            
            # 关闭配置窗口
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Toplevel) and widget.title() == "POE2 AI 助手配置":
                    widget.destroy()
                    
        except Exception as e:
            self._append_msg("系统", f"❌ 保存失败：{e}", tag="error")

    # ──────────────────────────────────────────────
    # 启动
    # ──────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


def start_float_window():
    win = POE2FloatWindow()
    win.run()
