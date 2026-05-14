# gui/float_window.py — POE2 AI 助手悬浮窗 v3（修复所有已知 bug）

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import time
import re
import os
from typing import Dict

from ai.llm_engine import ask_ai, handle_special_command
from ai.memory_retriever import set_version_priority, get_current_version
from utils.memory_manager import export_memory, import_memory
from config import (FLOAT_WINDOW, SUPPORTED_VERSIONS, DEFAULT_SERVER,
                    DEFAULT_LEAGUE, LLM_CONFIG, LLM_PROVIDER, TRADE_API)

try:
    from price_checker.trade_api import PriceChecker, get_server_list, quick_check
    HAS_PRICE = True
except ImportError:
    HAS_PRICE = False

try:
    from price_checker.screenshot_ocr import ScreenshotOCR
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


class POE2FloatWindow:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("POE2 AI 助手")
        self.root.overrideredirect(True)
        w, h = FLOAT_WINDOW["width"], FLOAT_WINDOW["height"]
        self.root.geometry(f"{w}x{h}{FLOAT_WINDOW['position']}")
        self.root.attributes("-topmost", FLOAT_WINDOW["always_on_top"])
        self.root.attributes("-alpha",   FLOAT_WINDOW["alpha"])
        self.root.config(bg="#0d0d14")

        self._thinking  = False
        self._ox = self._oy = 0
        self._price_checker = None
        self._current_server = DEFAULT_SERVER
        self._price_win = None   # 查价器子窗口引用

        self._styles()
        self._build()
        self._greet()

    # ── 样式 ──────────────────────────────────
    def _styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        bg, bg2, bg3 = "#0d0d14", "#13131f", "#1a1a2e"
        for name, clr in [
            ("X",    "#dc2626"), ("Min",   "#374151"),
            ("Ver",  "#1d4ed8"), ("Send",  "#16a34a"),
            ("Crawl","#0f766e"), ("Mem",   "#7c3aed"),
            ("Price","#ea580c"), ("Cfg",   "#b45309"),
        ]:
            s.configure(f"{name}.TButton", background=clr, foreground="white",
                        borderwidth=0, relief="flat", padding=3, font=("微软雅黑", 9))
            s.map(f"{name}.TButton", background=[("active", clr)])
        s.configure("Bar.TFrame",  background=bg2)
        s.configure("Bar.TLabel",  background=bg2, foreground="#c4b5fd",
                    font=("微软雅黑", 10, "bold"))
        s.configure("Top.TFrame",  background=bg3)
        s.configure("Top.TLabel",  background=bg3, foreground="#9090b0",
                    font=("微软雅黑", 9))
        s.configure("TFrame",      background=bg)

    # ── UI 构建 ───────────────────────────────
    def _build(self):
        # 标题栏
        bar = ttk.Frame(self.root, style="Bar.TFrame", height=32)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        ttk.Label(bar, text="⚡ POE2 AI 助手", style="Bar.TLabel").pack(side=tk.LEFT, padx=10)
        ttk.Button(bar, text="×", width=2, command=self.root.destroy, style="X.TButton").pack(side=tk.RIGHT, padx=2, pady=3)
        ttk.Button(bar, text="−", width=2, command=lambda: self.root.withdraw(), style="Min.TButton").pack(side=tk.RIGHT, padx=2, pady=3)
        bar.bind("<ButtonPress-1>", lambda e: (setattr(self,"_ox",e.x), setattr(self,"_oy",e.y)))
        bar.bind("<B1-Motion>",     lambda e: self.root.geometry(
            f"+{self.root.winfo_x()+e.x-self._ox}+{self.root.winfo_y()+e.y-self._oy}"))

        # 顶部工具栏：版本 + 模型
        top = ttk.Frame(self.root, style="Top.TFrame")
        top.pack(fill=tk.X, padx=6, pady=2)
        ttk.Label(top, text="版本：", style="Top.TLabel").pack(side=tk.LEFT)
        self.ver_var = tk.StringVar(value=get_current_version())
        cb = ttk.Combobox(top, textvariable=self.ver_var, values=SUPPORTED_VERSIONS,
                          state="readonly", width=5, font=("微软雅黑", 9))
        cb.pack(side=tk.LEFT, padx=2)
        cb.bind("<<ComboboxSelected>>", lambda e: self._switch_version())

        ttk.Label(top, text=" 模型：", style="Top.TLabel").pack(side=tk.LEFT)
        self.llm_var = tk.StringVar(value=LLM_PROVIDER)
        lb = ttk.Combobox(top, textvariable=self.llm_var, values=list(LLM_CONFIG.keys()),
                          state="readonly", width=9, font=("微软雅黑", 9))
        lb.pack(side=tk.LEFT, padx=2)
        lb.bind("<<ComboboxSelected>>", lambda e: self._switch_llm())

        self.status = tk.StringVar(value="就绪")
        ttk.Label(top, textvariable=self.status, style="Top.TLabel").pack(side=tk.RIGHT, padx=6)

        # 对话区
        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg="#080810", fg="#e0e0f0",
            font=("微软雅黑", 10), insertbackground="white",
            relief="flat", bd=0, padx=8, pady=6, state=tk.DISABLED)
        self.chat.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.chat.tag_config("sys",  foreground="#818cf8")
        self.chat.tag_config("you",  foreground="#34d399")
        self.chat.tag_config("ai",   foreground="#e0e0f0")
        self.chat.tag_config("warn", foreground="#fb923c")

        # 输入框和发送按钮
        inp = tk.Frame(self.root, bg="#0d0d14")
        inp.pack(fill=tk.X, padx=6, pady=(0, 2))
        
        self.entry = tk.Entry(inp, bg="#13131f", fg="white", insertbackground="white",
                              relief="flat", font=("微软雅黑", 10), bd=4)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.entry.bind("<Return>", lambda e: self._send())
        
        send_btn = ttk.Button(inp, text="发送", command=self._send, style="Send.TButton", width=4)
        send_btn.pack(side=tk.RIGHT, padx=0)

        # 功能按钮行（统一大小）
        btns = tk.Frame(self.root, bg="#0d0d14")
        btns.pack(fill=tk.X, padx=6, pady=(0, 4))
        
        # 左侧按钮
        left_btns = tk.Frame(btns, bg="#0d0d14")
        left_btns.pack(side=tk.LEFT)
        
        ttk.Button(left_btns, text="⚙ 配置",   command=self._open_config,   style="Cfg.TButton", width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_btns, text="🕷 爬取",   command=self._crawl,         style="Crawl.TButton", width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_btns, text="🗑 清屏",   command=self._clear,         style="Min.TButton", width=6).pack(side=tk.LEFT, padx=2)
        
        # 右侧按钮
        right_btns = tk.Frame(btns, bg="#0d0d14")
        right_btns.pack(side=tk.RIGHT)
        
        ttk.Button(right_btns, text="💾 导出",   command=self._export,        style="Mem.TButton", width=6).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_btns, text="💰 查价器", command=self._open_price,    style="Price.TButton", width=7).pack(side=tk.RIGHT, padx=2)

    def _greet(self):
        from ai.llm_engine import _has_valid_api_key
        mode = "🟢 LLM 对话" if _has_valid_api_key() else "🟡 本地搜索（建议在配置里填 API Key）"
        self._msg("系统",
            f"⚡ POE2 AI 助手已启动  {mode}\n\n"
            "直接提问：现在什么BD强？混沌石多少钱？\n"
            "特殊指令：记录：<内容> | /clear 清空对话\n"
            "查价：点右下角「查价器」，先配置 POESESSID", tag="sys")

    # ── 对话 ──────────────────────────────────
    def _send(self):
        text = self.entry.get().strip()
        if not text or self._thinking:
            return
        self.entry.delete(0, tk.END)
        self._msg("你", text, tag="you")

        result = handle_special_command(text)
        if result is not None:
            self._msg("系统", result, tag="sys")
            return

        self._thinking = True
        self.status.set("思考中…")
        threading.Thread(target=self._ask_thread, args=(text,), daemon=True).start()

    def _ask_thread(self, q):
        try:
            ans = ask_ai(q)
        except Exception as e:
            ans = f"❌ 出错：{e}"
        self.root.after(0, self._on_ans, ans)

    def _on_ans(self, ans):
        self._thinking = False
        self.status.set("就绪")
        self._msg("AI", ans, tag="ai")

    def _msg(self, sender, text, tag="ai"):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, f"【{sender}】\n{text}\n\n", tag)
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    # ── 功能 ──────────────────────────────────
    def _switch_version(self):
        ver = self.ver_var.get()
        set_version_priority(ver)
        try:
            from crawler import set_crawler_version
            set_crawler_version(ver)
        except Exception:
            pass
        self._msg("系统", f"✅ 已切换至 {ver} 版本", tag="sys")

    def _switch_llm(self):
        provider = self.llm_var.get()
        import config as _cfg
        _cfg.LLM_PROVIDER = provider
        cfg = LLM_CONFIG.get(provider, {})
        key = cfg.get("api_key", "")
        if key.startswith("YOUR_"):
            self._msg("系统", f"⚠️ 已选择 {provider}，但 API Key 未配置", tag="warn")
        else:
            self._msg("系统", f"✅ 已切换至 {provider} / {cfg.get('model','')}", tag="sys")

    def _clear(self):
        from ai.llm_engine import clear_chat_history
        clear_chat_history()
        self.chat.config(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        self.chat.config(state=tk.DISABLED)
        self._msg("系统", "对话已清空", tag="sys")

    def _crawl(self):
        self._msg("系统", "⏳ 爬取中，请稍候…", tag="sys")
        self.status.set("爬取中…")
        threading.Thread(target=self._crawl_thread, daemon=True).start()

    def _crawl_thread(self):
        try:
            from crawler import _run_all_once
            result = _run_all_once()
        except Exception as e:
            result = f"❌ 爬取失败：{e}"
        self.root.after(0, lambda: (
            self.status.set("就绪"),
            self._msg("系统", f"✅ 爬取完成：\n{result}", tag="sys")
        ))

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".zip", initialfile="POE2_AI记忆包",
            filetypes=[("ZIP", "*.zip")])
        if path:
            base = path[:-4] if path.endswith(".zip") else path
            self._msg("系统", export_memory(base), tag="sys")

    # ── 配置窗口 ──────────────────────────────
    def _open_config(self):
        win = tk.Toplevel(self.root)
        win.title("⚙ 配置")
        win.geometry("430x360")
        win.attributes("-topmost", True)
        win.config(bg="#0d0d14")

        def label(parent, text):
            tk.Label(parent, text=text, bg="#0d0d14", fg="#9090b0",
                     font=("微软雅黑", 9)).pack(anchor=tk.W, padx=10, pady=(8,2))

        def entry_row(parent, default="", width=50):
            e = tk.Entry(parent, bg="#13131f", fg="white", insertbackground="white",
                         relief="flat", font=("微软雅黑", 9), bd=4, width=width)
            e.insert(0, default)
            e.pack(fill=tk.X, padx=10, pady=2)
            return e

        label(win, "POESESSID（登录官网 → F12 → Application → Cookies → POESESSID）")
        poessid_e = entry_row(win, self._read_config("POESESSID"))

        label(win, "默认服务器")
        server_var = tk.StringVar(value=self._read_config("DEFAULT_SERVER") or DEFAULT_SERVER)
        servers = [k for k in TRADE_API.keys()]
        server_names = {k: v["name"] for k,v in TRADE_API.items()}
        srv_cb = ttk.Combobox(win, textvariable=server_var,
                              values=[f"{k} ({server_names[k]})" for k in servers],
                              state="readonly", font=("微软雅黑", 9))
        srv_cb.pack(fill=tk.X, padx=10, pady=4)

        label(win, "默认赛季（如 Dawn，留空则自动获取）")
        league_e = entry_row(win, self._read_config("DEFAULT_LEAGUE") or "")

        label(win, "DeepSeek API Key（可选，有 Key 才能使用 AI 对话）")
        key_e = entry_row(win, self._read_config_llm_key("deepseek"))

        def save():
            poessid  = poessid_e.get().strip()
            srv_raw  = server_var.get().split(" ")[0]
            league   = league_e.get().strip() or DEFAULT_LEAGUE
            ds_key   = key_e.get().strip()
            try:
                self._write_config("POESESSID",      poessid)
                self._write_config("DEFAULT_SERVER",  srv_raw)
                self._write_config("DEFAULT_LEAGUE",  league)
                if ds_key:
                    self._write_config_llm_key("deepseek", ds_key)
                self._current_server = srv_raw
                self._price_checker  = None
                self._msg("系统", "✅ 配置已保存，重启后完全生效", tag="sys")
                win.destroy()
            except Exception as e:
                self._msg("系统", f"❌ 保存失败：{e}", tag="warn")

        tk.Button(win, text="💾 保存配置", command=save,
                  bg="#16a34a", fg="white", relief="flat",
                  font=("微软雅黑", 10), padx=20, pady=6).pack(pady=14)

    def _read_config(self, key: str) -> str:
        try:
            with open("config.py", encoding="utf-8") as f:
                m = re.search(rf'{key}\s*=\s*["\']([^"\']*)["\']', f.read())
                return m.group(1) if m else ""
        except Exception:
            return ""

    def _read_config_llm_key(self, provider: str) -> str:
        try:
            with open("config.py", encoding="utf-8") as f:
                content = f.read()
            # 找到 provider 块内的 api_key
            block_m = re.search(rf'"{provider}".*?"api_key":\s*"([^"]*)"', content, re.S)
            return block_m.group(1) if block_m else ""
        except Exception:
            return ""

    def _write_config(self, key: str, value: str):
        with open("config.py", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(rf'{key}\s*=\s*["\'][^"\']*["\']',
                         f'{key} = "{value}"', content)
        with open("config.py", "w", encoding="utf-8") as f:
            f.write(content)

    def _write_config_llm_key(self, provider: str, key_val: str):
        with open("config.py", encoding="utf-8") as f:
            content = f.read()
        # 替换 provider 块内的 api_key
        content = re.sub(
            rf'("{provider}".*?"api_key":\s*")[^"]*(")',
            lambda m: m.group(1) + key_val + m.group(2),
            content, flags=re.S
        )
        with open("config.py", "w", encoding="utf-8") as f:
            f.write(content)

    # ── 查价器窗口 ────────────────────────────
    def _open_price(self):
        if self._price_win and tk.Toplevel.winfo_exists(self._price_win):
            self._price_win.lift()
            return

        if not HAS_PRICE:
            self._msg("系统", "❌ 查价模块加载失败", tag="warn")
            return

        win = tk.Toplevel(self.root)
        self._price_win = win
        win.title("💰 POE2 装备查价器")
        win.geometry("520x640")
        win.attributes("-topmost", True)
        win.config(bg="#0d0d14")

        def lbl(parent, text, fg="#9090b0"):
            tk.Label(parent, text=text, bg="#0d0d14", fg=fg,
                     font=("微软雅黑", 9)).pack(anchor=tk.W, padx=10, pady=(6,1))

        def ent(parent, placeholder="", width=55):
            e = tk.Entry(parent, bg="#13131f", fg="white", insertbackground="white",
                         relief="flat", font=("微软雅黑", 9), bd=4, width=width)
            if placeholder:
                e.insert(0, placeholder)
            e.pack(fill=tk.X, padx=10, pady=2)
            return e

        # 服务器选择
        top_f = tk.Frame(win, bg="#0d0d14")
        top_f.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(top_f, text="服务器：", bg="#0d0d14", fg="#9090b0",
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)
        srv_var = tk.StringVar(value=self._current_server)
        srv_cb  = ttk.Combobox(top_f, textvariable=srv_var,
                                values=[k for k in TRADE_API],
                                state="readonly", width=14, font=("微软雅黑", 9))
        srv_cb.pack(side=tk.LEFT, padx=4)

        # 截图/剪贴板按钮
        clip_btn = tk.Button(top_f, text="📋 读取剪贴板 (Ctrl+C后点)",
                             bg="#1d4ed8", fg="white", relief="flat",
                             font=("微软雅黑", 9), padx=6)
        clip_btn.pack(side=tk.RIGHT, padx=4)

        ocr_btn = tk.Button(top_f, text="📷 截图识别",
                            bg="#ea580c", fg="white", relief="flat",
                            font=("微软雅黑", 9), padx=6)
        ocr_btn.pack(side=tk.RIGHT, padx=2)

        # 搜索字段
        lbl(win, "装备名称（传奇填名称，稀有可留空）")
        name_e = ent(win)

        lbl(win, "底材类型（如 Titanium Kite Shield）")
        base_e = ent(win)

        # 稀有度 + 物品等级
        row2 = tk.Frame(win, bg="#0d0d14")
        row2.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(row2, text="稀有度：", bg="#0d0d14", fg="#9090b0", font=("微软雅黑",9)).pack(side=tk.LEFT)
        rar_var = tk.StringVar(value="全部")
        ttk.Combobox(row2, textvariable=rar_var,
                     values=["全部","普通","魔法","稀有","传奇"],
                     state="readonly", width=7, font=("微软雅黑",9)).pack(side=tk.LEFT, padx=4)
        tk.Label(row2, text="最低物品等级：", bg="#0d0d14", fg="#9090b0", font=("微软雅黑",9)).pack(side=tk.LEFT, padx=(12,0))
        ilvl_e = tk.Entry(row2, bg="#13131f", fg="white", insertbackground="white",
                          relief="flat", font=("微软雅黑",9), bd=3, width=5)
        ilvl_e.pack(side=tk.LEFT, padx=2)

        lbl(win, "词条筛选（每行一条，自动匹配，最多3条生效）")
        aff_txt = tk.Text(win, bg="#13131f", fg="#a5f3fc", insertbackground="white",
                          relief="flat", font=("微软雅黑", 9), bd=4, height=5)
        aff_txt.pack(fill=tk.X, padx=10, pady=2)

        # 常用词条快捷按钮
        quick_f = tk.Frame(win, bg="#0d0d14")
        quick_f.pack(fill=tk.X, padx=10, pady=2)
        for q in ["最大生命值","全元素抗性","物理伤害","攻击速度","施法速度","暴击率"]:
            tk.Button(quick_f, text=q,
                      bg="#1e1e2e", fg="#a5f3fc", relief="flat",
                      font=("微软雅黑", 8), padx=4,
                      command=lambda v=q: aff_txt.insert(tk.END, v+"\n")
                      ).pack(side=tk.LEFT, padx=2, pady=2)

        # 搜索按钮
        search_btn = tk.Button(win, text="🔍 查询价格",
                               bg="#16a34a", fg="white", relief="flat",
                               font=("微软雅黑", 10), padx=20, pady=5)
        search_btn.pack(pady=6)

        # 结果区
        lbl(win, "查价结果")
        result_txt = scrolledtext.ScrolledText(
            win, wrap=tk.WORD, bg="#080810", fg="#e0e0f0",
            font=("Consolas", 9), relief="flat", bd=0, padx=6, pady=4,
            state=tk.DISABLED, height=14)
        result_txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,8))

        # POESESSID 提示
        if not self._read_config("POESESSID") or \
           self._read_config("POESESSID").startswith("YOUR_"):
            result_txt.config(state=tk.NORMAL)
            result_txt.insert(tk.END,
                "⚠️ 尚未配置 POESESSID，查价功能无法使用。\n\n"
                "获取方法：\n"
                "1. 用浏览器登录 pathofexile.com（国际服）\n"
                "   或 poe.game.qq.com（国服）\n"
                "2. 按 F12 → Application → Cookies\n"
                "3. 找到 POESESSID 的值\n"
                "4. 点主界面「⚙ 配置」粘贴进去\n\n"
                "📋 推荐使用剪贴板模式：\n"
                "在游戏中鼠标悬停装备 → Ctrl+C → 点「读取剪贴板」")
            result_txt.config(state=tk.DISABLED)

        def show_result(text):
            result_txt.config(state=tk.NORMAL)
            result_txt.delete("1.0", tk.END)
            result_txt.insert(tk.END, text)
            result_txt.config(state=tk.DISABLED)
            result_txt.see(tk.END)

        def do_search():
            name    = name_e.get().strip()
            base    = base_e.get().strip()
            rarity  = rar_var.get() if rar_var.get() != "全部" else ""
            affixes = [l.strip() for l in aff_txt.get("1.0", tk.END).splitlines() if l.strip()]
            server  = srv_var.get()

            show_result("⏳ 查询中，请稍候…")
            def _thread():
                try:
                    checker = PriceChecker(server=server)
                    msg, prices = checker.check_price(
                        item_name=name, base_type=base,
                        rarity=rarity, affixes=affixes)
                    text = checker.format_result(msg, prices)
                except Exception as e:
                    text = f"❌ 查询失败：{e}"
                win.after(0, show_result, text)
            threading.Thread(target=_thread, daemon=True).start()

        search_btn.config(command=do_search)
        win.bind("<Return>", lambda e: do_search())

        # 剪贴板识别
        def do_clipboard():
            if not HAS_OCR:
                show_result("❌ OCR 模块未加载：pip install pillow")
                return
            try:
                ocr  = ScreenshotOCR()
                text = ocr.read_clipboard()
                if not ocr.is_poe2_item(text):
                    show_result("⚠️ 剪贴板内容不像 POE2 装备\n\n请先在游戏里鼠标悬停装备，然后按 Ctrl+C，再点这个按钮")
                    return
                item = ocr.parse_equipment(text)
                # 自动填入字段
                name_e.delete(0, tk.END)
                name_e.insert(0, item.get("name", ""))
                base_e.delete(0, tk.END)
                base_e.insert(0, item.get("base_type", ""))
                if item.get("rarity"):
                    rar_var.set(item["rarity"])
                aff_txt.delete("1.0", tk.END)
                for s in item.get("explicit", []):
                    aff_txt.insert(tk.END, s.get("text","") + "\n")
                show_result(f"✅ 已识别装备：{item.get('name') or item.get('base_type')}\n"
                            f"稀有度：{item.get('rarity')}  物品等级：{item.get('level')}\n\n"
                            f"词条已自动填入，点「查询价格」开始查价")
            except Exception as e:
                show_result(f"❌ 读取失败：{e}")
        clip_btn.config(command=do_clipboard)

        # 截图识别
        def do_ocr():
            if not HAS_OCR:
                show_result("❌ OCR 模块未加载\n需安装：pip install pillow pytesseract\n还需安装 Tesseract-OCR 程序")
                return
            show_result("📷 3秒后截图，请将鼠标移到装备上…")
            def _thread():
                time.sleep(3)
                try:
                    ocr  = ScreenshotOCR()
                    img  = ocr.capture_near_mouse()
                    if img is None:
                        win.after(0, show_result, "❌ 截图失败")
                        return
                    text = ocr.ocr_image(img)
                    item = ocr.parse_equipment(text)
                    def _fill():
                        name_e.delete(0, tk.END)
                        name_e.insert(0, item.get("name", ""))
                        base_e.delete(0, tk.END)
                        base_e.insert(0, item.get("base_type", ""))
                        if item.get("rarity"):
                            rar_var.set(item["rarity"])
                        aff_txt.delete("1.0", tk.END)
                        for s in item.get("explicit", []):
                            aff_txt.insert(tk.END, s.get("text","") + "\n")
                        show_result(f"✅ OCR 识别完成\n原始文本：\n{text[:300]}")
                    win.after(0, _fill)
                except Exception as e:
                    win.after(0, show_result, f"❌ OCR 失败：{e}")
            threading.Thread(target=_thread, daemon=True).start()
        ocr_btn.config(command=do_ocr)

    def run(self):
        self.root.mainloop()


def start_float_window():
    POE2FloatWindow().run()
