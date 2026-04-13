#!/usr/bin/env python3
from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from migrator import MigrationError, prepare_input


I18N = {
    "zh-CN": {
        "title": "ChatGPT -> OpenWebUI 转换器",
        "header_title": "ChatGPT -> OpenWebUI 转换器",
        "header_sub": "将 ChatGPT 导出文件转换为 OpenWebUI 可导入 JSON",
        "menu_file": "文件",
        "menu_open_input": "选择输入文件",
        "menu_open_output": "选择输出位置",
        "menu_convert": "开始转换",
        "menu_exit": "退出",
        "menu_help": "帮助",
        "menu_usage": "使用说明",
        "menu_about": "关于",
        "lang": "语言",
        "lang_zh": "中文",
        "lang_en": "英文",
        "section_file": "文件设置",
        "input_label": "输入文件（ChatGPT 导出 .zip 或 conversations.json）",
        "output_label": "输出文件（OpenWebUI 导入 JSON）",
        "input_pick": "📂 选择输入",
        "output_pick": "💾 选择输出",
        "convert": "▶ 开始转换",
        "usage_btn": "❓ 使用说明",
        "quick_note": "导入路径：OpenWebUI -> Settings -> Data Controls -> Import Chats",
        "status_ready": "状态：就绪",
        "status_working": "状态：正在转换...",
        "status_done": "状态：完成：{path}",
        "status_failed": "状态：失败：{msg}",
        "progress_label": "转换进度",
        "dlg_input_title": "选择 ChatGPT 导出文件",
        "dlg_output_title": "保存 OpenWebUI 导入 JSON",
        "err_missing_input_title": "缺少输入文件",
        "err_missing_input": "请先选择输入 .zip 或 .json 文件。",
        "err_missing_output_title": "缺少输出文件",
        "err_missing_output": "请先选择输出 .json 文件。",
        "err_convert_title": "转换失败",
        "ok_convert_title": "转换成功",
        "ok_convert_msg": "已生成文件：\n{path}\n\n下一步在 OpenWebUI 中导入：\nSettings -> Data Controls -> Import Chats",
        "help_title": "使用说明",
        "help_text": "1) 选择输入文件（ChatGPT 导出 zip 或 conversations.json）\n2) 选择输出文件位置\n3) 点击“开始转换”\n4) 到 OpenWebUI: Settings -> Data Controls -> Import Chats 导入",
        "about_title": "关于",
        "about_text": "ChatGPT -> OpenWebUI 转换器\nVersion 1.4.0\nTarget: OpenWebUI v0.8.12",
        "filetypes_chat": "聊天导出",
        "filetypes_zip": "ZIP 压缩包",
        "filetypes_json": "JSON 文件",
        "filetypes_all": "所有文件",
    },
    "en": {
        "title": "ChatGPT -> OpenWebUI Converter",
        "header_title": "ChatGPT -> OpenWebUI Converter",
        "header_sub": "Convert ChatGPT export into OpenWebUI importable JSON",
        "menu_file": "File",
        "menu_open_input": "Choose Input File",
        "menu_open_output": "Choose Output Path",
        "menu_convert": "Convert",
        "menu_exit": "Exit",
        "menu_help": "Help",
        "menu_usage": "Usage",
        "menu_about": "About",
        "lang": "Language",
        "lang_zh": "Chinese",
        "lang_en": "English",
        "section_file": "File Settings",
        "input_label": "Input file (ChatGPT export .zip or conversations.json)",
        "output_label": "Output file (OpenWebUI import JSON)",
        "input_pick": "📂 Choose Input",
        "output_pick": "💾 Choose Output",
        "convert": "▶ Convert",
        "usage_btn": "❓ Usage",
        "quick_note": "Import path: OpenWebUI -> Settings -> Data Controls -> Import Chats",
        "status_ready": "Status: Ready",
        "status_working": "Status: Converting...",
        "status_done": "Status: Done: {path}",
        "status_failed": "Status: Failed: {msg}",
        "progress_label": "Conversion Progress",
        "dlg_input_title": "Select ChatGPT export file",
        "dlg_output_title": "Save OpenWebUI import JSON",
        "err_missing_input_title": "Missing Input",
        "err_missing_input": "Please choose input .zip or .json file first.",
        "err_missing_output_title": "Missing Output",
        "err_missing_output": "Please choose output .json file first.",
        "err_convert_title": "Conversion Failed",
        "ok_convert_title": "Conversion Succeeded",
        "ok_convert_msg": "Generated file:\n{path}\n\nNext step in OpenWebUI:\nSettings -> Data Controls -> Import Chats",
        "help_title": "Usage",
        "help_text": "1) Choose input file (ChatGPT export zip or conversations.json)\n2) Choose output path\n3) Click Convert\n4) Import in OpenWebUI: Settings -> Data Controls -> Import Chats",
        "about_title": "About",
        "about_text": "ChatGPT -> OpenWebUI Converter\nVersion 1.4.0\nTarget: OpenWebUI v0.8.12",
        "filetypes_chat": "Chat export",
        "filetypes_zip": "ZIP",
        "filetypes_json": "JSON",
        "filetypes_all": "All files",
    },
}


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.geometry("920x560")
        self.root.minsize(760, 500)

        self.lang_var = tk.StringVar(value="en")
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd() / "openwebui_import.json"))
        self.status_var = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0)

        self._result_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._busy = False

        self.style = ttk.Style(self.root)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self._build_menu()
        self._build_ui()
        self._bind_macos_help()
        self._apply_texts()

    def t(self, key: str) -> str:
        return I18N[self.lang_var.get()][key]

    def _build_menu(self) -> None:
        self.menubar = tk.Menu(self.root, tearoff=False)

        self.file_menu = tk.Menu(self.menubar, tearoff=False)
        self.file_menu.add_command(command=self.pick_input)
        self.file_menu.add_command(command=self.pick_output)
        self.file_menu.add_separator()
        self.file_menu.add_command(command=self.convert)
        self.file_menu.add_separator()
        self.file_menu.add_command(command=self.root.quit)

        self.lang_menu = tk.Menu(self.menubar, tearoff=False)
        self.lang_menu.add_command(command=lambda: self.set_language("zh-CN"))
        self.lang_menu.add_command(command=lambda: self.set_language("en"))

        self.help_menu = tk.Menu(self.menubar, tearoff=False)
        self.help_menu.add_command(command=self.show_help)
        self.help_menu.add_command(command=self.show_about)

        self.menubar.add_cascade(menu=self.file_menu)
        self.menubar.add_cascade(menu=self.lang_menu)
        self.menubar.add_cascade(menu=self.help_menu)
        self.root.config(menu=self.menubar)

    def _bind_macos_help(self) -> None:
        if self.root.tk.call("tk", "windowingsystem") == "aqua":
            self.root.createcommand("tk::mac::ShowHelp", self.show_help)

    def _build_ui(self) -> None:
        self.outer = tk.Frame(self.root, bg="#F5F5F7", padx=20, pady=20)
        self.outer.pack(fill=tk.BOTH, expand=True)
        self.outer.columnconfigure(0, weight=1)
        self.outer.rowconfigure(2, weight=1)

        header = tk.Frame(self.outer, bg="#F5F5F7")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        self.header_title = tk.Label(header, bg="#F5F5F7", fg="#1D1D1F", font=("Helvetica", 20, "bold"))
        self.header_title.grid(row=0, column=0, sticky="w")
        self.header_sub = tk.Label(header, bg="#F5F5F7", fg="#6E6E73", font=("Helvetica", 12))
        self.header_sub.grid(row=1, column=0, sticky="w", pady=(5, 0))

        selectors = tk.Frame(header, bg="#F5F5F7")
        selectors.grid(row=0, column=1, rowspan=2, sticky="e")
        self.lang_label = tk.Label(selectors, bg="#F5F5F7", fg="#1D1D1F")
        self.lang_label.grid(row=0, column=0, sticky="e", padx=(0, 6))
        self.lang_box = ttk.Combobox(selectors, state="readonly", width=10, textvariable=self.lang_var, values=["en", "zh-CN"])
        self.lang_box.grid(row=0, column=1, sticky="e")
        self.lang_box.bind("<<ComboboxSelected>>", lambda _e: self._apply_texts())

        self.toolbar = tk.Frame(self.outer, bg="#EEF2FF", height=60, highlightbackground="#D2D2D7", highlightthickness=1)
        self.toolbar.grid(row=1, column=0, sticky="ew", pady=(14, 12))
        self.toolbar.grid_propagate(False)
        self.toolbar.columnconfigure((0, 1, 2, 3), weight=1, uniform="toolbar")
        self.toolbar.rowconfigure(0, weight=1)

        self.btn_pick_input = tk.Button(self.toolbar, command=self.pick_input)
        self.btn_pick_output = tk.Button(self.toolbar, command=self.pick_output)
        self.btn_convert_top = tk.Button(self.toolbar, command=self.convert)
        self.btn_help_top = tk.Button(self.toolbar, command=self.show_help)

        self.btn_pick_input.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        self.btn_pick_output.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        self.btn_convert_top.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")
        self.btn_help_top.grid(row=0, column=3, padx=8, pady=8, sticky="nsew")

        self.form_card = tk.Frame(self.outer, bg="#FFFFFF", highlightbackground="#D2D2D7", highlightthickness=1)
        self.form_card.grid(row=2, column=0, sticky="nsew")
        self.form_card.columnconfigure(0, weight=1)
        self.form_card.columnconfigure(1, minsize=150)

        self.section_label = tk.Label(self.form_card, bg="#FFFFFF", fg="#1D1D1F", font=("Helvetica", 13, "bold"))
        self.section_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 8))

        self.input_label = ttk.Label(self.form_card)
        self.input_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 4))
        self.input_entry = ttk.Entry(self.form_card, textvariable=self.input_var)
        self.input_entry.grid(row=2, column=0, sticky="ew", padx=(14, 8), pady=(0, 10))
        self.input_btn = ttk.Button(self.form_card, command=self.pick_input)
        self.input_btn.grid(row=2, column=1, sticky="ew", padx=(0, 14), pady=(0, 10))

        self.output_label = ttk.Label(self.form_card)
        self.output_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 4))
        self.output_entry = ttk.Entry(self.form_card, textvariable=self.output_var)
        self.output_entry.grid(row=4, column=0, sticky="ew", padx=(14, 8), pady=(0, 10))
        self.output_btn = ttk.Button(self.form_card, command=self.pick_output)
        self.output_btn.grid(row=4, column=1, sticky="ew", padx=(0, 14), pady=(0, 10))

        self.convert_btn = ttk.Button(self.form_card, command=self.convert)
        self.convert_btn.grid(row=5, column=0, columnspan=2, sticky="ew", padx=14, pady=(2, 10))

        self.note_label = ttk.Label(self.form_card)
        self.note_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 6))

        self.progress_label = ttk.Label(self.form_card)
        self.progress_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=14, pady=(8, 4))
        self.progress = ttk.Progressbar(self.form_card, mode="determinate", maximum=100, variable=self.progress_var)
        self.progress.grid(row=8, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 10))

        self.status_label = ttk.Label(self.form_card, textvariable=self.status_var)
        self.status_label.grid(row=9, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 14))

        self._style_toolbar_button(self.btn_pick_input, "#0A84FF")
        self._style_toolbar_button(self.btn_pick_output, "#8E8E93")
        self._style_toolbar_button(self.btn_convert_top, "#30D158")
        self._style_toolbar_button(self.btn_help_top, "#5E5CE6")

    def _style_toolbar_button(self, btn: tk.Button, bg: str) -> None:
        btn.configure(
            bg=bg,
            fg="#FFFFFF",
            activebackground=bg,
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            padx=10,
            pady=6,
            font=("Helvetica", 12, "bold"),
            cursor="hand2",
        )

    def _apply_texts(self) -> None:
        self.root.title(self.t("title"))

        self.menubar.entryconfig(0, label=self.t("menu_file"))
        self.menubar.entryconfig(1, label=self.t("lang"))
        self.menubar.entryconfig(2, label=self.t("menu_help"))

        self.file_menu.entryconfig(0, label=self.t("menu_open_input"))
        self.file_menu.entryconfig(1, label=self.t("menu_open_output"))
        self.file_menu.entryconfig(3, label=self.t("menu_convert"))
        self.file_menu.entryconfig(5, label=self.t("menu_exit"))

        self.lang_menu.entryconfig(0, label=self.t("lang_zh"))
        self.lang_menu.entryconfig(1, label=self.t("lang_en"))

        self.help_menu.entryconfig(0, label=self.t("menu_usage"))
        self.help_menu.entryconfig(1, label=self.t("menu_about"))

        self.header_title.config(text=self.t("header_title"))
        self.header_sub.config(text=self.t("header_sub"))
        self.lang_label.config(text=f"{self.t('lang')}:")

        self.section_label.config(text=self.t("section_file"))
        self.input_label.config(text=self.t("input_label"))
        self.output_label.config(text=self.t("output_label"))
        self.input_btn.config(text=self.t("menu_open_input"))
        self.output_btn.config(text=self.t("menu_open_output"))
        self.convert_btn.config(text=self.t("convert"))
        self.note_label.config(text=self.t("quick_note"))
        self.progress_label.config(text=self.t("progress_label"))

        self.btn_pick_input.config(text=self.t("input_pick"))
        self.btn_pick_output.config(text=self.t("output_pick"))
        self.btn_convert_top.config(text=self.t("convert"))
        self.btn_help_top.config(text=self.t("usage_btn"))

        if not self.status_var.get() or "Ready" in self.status_var.get() or "就绪" in self.status_var.get():
            self.status_var.set(self.t("status_ready"))

    def set_language(self, lang: str) -> None:
        self.lang_var.set(lang)
        self._apply_texts()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for widget in [
            self.btn_pick_input,
            self.btn_pick_output,
            self.btn_convert_top,
            self.btn_help_top,
            self.input_btn,
            self.output_btn,
            self.convert_btn,
            self.lang_box,
        ]:
            widget.configure(state=state)

    def pick_input(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("dlg_input_title"),
            filetypes=[
                (self.t("filetypes_chat"), "*.zip *.json"),
                (self.t("filetypes_zip"), "*.zip"),
                (self.t("filetypes_json"), "*.json"),
                (self.t("filetypes_all"), "*.*"),
            ],
        )
        if path:
            self.input_var.set(path)

    def pick_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title=self.t("dlg_output_title"),
            defaultextension=".json",
            initialfile="openwebui_import.json",
            filetypes=[(self.t("filetypes_json"), "*.json"), (self.t("filetypes_all"), "*.*")],
        )
        if path:
            self.output_var.set(path)

    def convert(self) -> None:
        if self._busy:
            return

        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()

        if not input_path:
            messagebox.showerror(self.t("err_missing_input_title"), self.t("err_missing_input"))
            return
        if not output_path:
            messagebox.showerror(self.t("err_missing_output_title"), self.t("err_missing_output"))
            return

        self._set_busy(True)
        self.status_var.set(self.t("status_working"))
        self.progress_var.set(10)
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)

        thread = threading.Thread(target=self._convert_worker, args=(input_path, output_path), daemon=True)
        thread.start()
        self.root.after(100, self._poll_worker)

    def _convert_worker(self, input_path: str, output_path: str) -> None:
        try:
            out = prepare_input(Path(input_path).expanduser(), Path(output_path).expanduser())
            self._result_queue.put(("ok", str(out)))
        except MigrationError as exc:
            self._result_queue.put(("err", str(exc)))
        except Exception as exc:
            self._result_queue.put(("err", str(exc)))

    def _poll_worker(self) -> None:
        try:
            kind, payload = self._result_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_worker)
            return

        self.progress.stop()
        self.progress.configure(mode="determinate")

        if kind == "ok":
            self.progress_var.set(100)
            self.status_var.set(self.t("status_done").format(path=payload))
            self._set_busy(False)
            messagebox.showinfo(self.t("ok_convert_title"), self.t("ok_convert_msg").format(path=payload))
            return

        self.progress_var.set(0)
        self.status_var.set(self.t("status_failed").format(msg=payload))
        self._set_busy(False)
        messagebox.showerror(self.t("err_convert_title"), payload)

    def show_help(self) -> None:
        messagebox.showinfo(self.t("help_title"), self.t("help_text"))

    def show_about(self) -> None:
        messagebox.showinfo(self.t("about_title"), self.t("about_text"))


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
