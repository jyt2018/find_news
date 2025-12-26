import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.simpledialog import Dialog

class ParentConfigDialog(Dialog):
    def __init__(self, parent, title=None):
        super().__init__(parent, title=title)

    def body(self, master):
        tk.Label(master, text="Type:").grid(row=0, column=0, sticky=tk.W)
        self.type_var = tk.StringVar(value="bs4_find")
        self.type_menu = ttk.OptionMenu(master, self.type_var, "bs4_find", "bs4_find", "bs4_find_all", "xpath")
        self.type_menu.grid(row=0, column=1, sticky=tk.W)

        tk.Label(master, text="Selector (JSON dict):").grid(row=1, column=0, sticky=tk.W)
        self.selector_entry = tk.Entry(master, width=50)
        self.selector_entry.grid(row=1, column=1, sticky=tk.W)
        tk.Label(master, text='e.g. {"name": "div", "class_": "card-body"}').grid(row=1, column=2, sticky=tk.W)

        tk.Label(master, text="Extract:").grid(row=2, column=0, sticky=tk.W)
        self.extract_var = tk.StringVar(value="text")
        self.extract_menu = ttk.OptionMenu(master, self.extract_var, "text", "text", "href", "src")
        self.extract_menu.grid(row=2, column=1, sticky=tk.W)

        tk.Label(master, text="Limit:").grid(row=3, column=0, sticky=tk.W)
        self.limit_entry = tk.Entry(master, width=10)
        self.limit_entry.insert(0, "1")
        self.limit_entry.grid(row=3, column=1, sticky=tk.W)

        # Filters for parent
        tk.Label(master, text="Filters:").grid(row=4, column=0, sticky=tk.W)
        self.filters_listbox = tk.Listbox(master, height=5, width=50)
        self.filters_listbox.grid(row=4, column=1, columnspan=2, sticky=tk.W)

        self.add_filter_btn = tk.Button(master, text="Add Filter", command=self.add_filter)
        self.add_filter_btn.grid(row=5, column=0, sticky=tk.W)
        self.edit_filter_btn = tk.Button(master, text="Edit Filter", command=self.edit_filter)
        self.edit_filter_btn.grid(row=5, column=1, sticky=tk.W)
        self.delete_filter_btn = tk.Button(master, text="Delete Filter", command=self.delete_filter)
        self.delete_filter_btn.grid(row=5, column=2, sticky=tk.W)

        # Post process for parent
        tk.Label(master, text="Post Process (replace from:to):").grid(row=6, column=0, sticky=tk.W)
        self.post_from_entry = tk.Entry(master, width=20)
        self.post_from_entry.grid(row=6, column=1, sticky=tk.W)
        self.post_to_entry = tk.Entry(master, width=20)
        self.post_to_entry.grid(row=6, column=2, sticky=tk.W)

        self.filters = []

    def add_filter(self):
        filter_dialog = FilterConfigDialog(self, title="Add Filter")
        if filter_dialog.result:
            self.filters.append(filter_dialog.result)
            self.update_filters_listbox()

    def edit_filter(self):
        selected = self.filters_listbox.curselection()
        if selected:
            idx = selected[0]
            filter_dialog = FilterConfigDialog(self, title="Edit Filter", initial= self.filters[idx])
            if filter_dialog.result:
                self.filters[idx] = filter_dialog.result
                self.update_filters_listbox()

    def delete_filter(self):
        selected = self.filters_listbox.curselection()
        if selected:
            del self.filters[selected[0]]
            self.update_filters_listbox()

    def update_filters_listbox(self):
        self.filters_listbox.delete(0, tk.END)
        for f in self.filters:
            self.filters_listbox.insert(tk.END, str(f))

    def apply(self):
        parent_conf = {
            "type": self.type_var.get(),
            "selector": self.try_parse_json(self.selector_entry.get()),
            "extract": self.extract_var.get(),
            "limit": int(self.limit_entry.get()) if self.limit_entry.get() else None,
            "filters": self.filters,
        }
        post_from = self.post_from_entry.get().strip()
        post_to = self.post_to_entry.get().strip()
        if post_from:
            parent_conf["post_process"] = [{"replace": {"from": post_from, "to": post_to}}]
        self.result = parent_conf if any(parent_conf.values()) else None

    def try_parse_json(self, s):
        try:
            return json.loads(s)
        except:
            return s

class FilterConfigDialog(Dialog):
    def __init__(self, parent, title=None, initial=None):
        self.initial = initial or {}
        super().__init__(parent, title=title)

    def body(self, master):
        tk.Label(master, text="Attr:").grid(row=0, column=0, sticky=tk.W)
        self.attr_entry = tk.Entry(master)
        self.attr_entry.insert(0, self.initial.get("attr", ""))
        self.attr_entry.grid(row=0, column=1)

        tk.Label(master, text="Type:").grid(row=1, column=0, sticky=tk.W)
        self.type_var = tk.StringVar(value=self.initial.get("type", "startswith"))
        self.type_menu = ttk.OptionMenu(master, self.type_var, "startswith", "startswith", "not_in")
        self.type_menu.grid(row=1, column=1)

        tk.Label(master, text="Value:").grid(row=2, column=0, sticky=tk.W)
        self.value_entry = tk.Entry(master, width=50)
        self.value_entry.insert(0, str(self.initial.get("value", "")))
        self.value_entry.grid(row=2, column=1)

    def apply(self):
        filt_type = self.type_var.get()
        value = self.value_entry.get().strip()
        if filt_type == "not_in":
            value = [v.strip() for v in value.split(",") if v.strip()]
        self.result = {
            "attr": self.attr_entry.get().strip(),
            filt_type: value
        }

class ConfigTab(ttk.Frame):
    def __init__(self, parent, is_item=False, field_name=None):
        super().__init__(parent)
        self.field_name = field_name
        self.is_item = is_item
        self.parent_conf = None
        self.filters = []

        if not is_item:
            self.enable_var = tk.BooleanVar(value=False)
            self.checkbox_1 = tk.Checkbutton(self, text=f"Enable {field_name}", variable=self.enable_var, command=self.toggle_enable)
            self.checkbox_1.pack(anchor=tk.W)

            self.frame_a = tk.LabelFrame(self, text=f"Config for {field_name}")
            self.frame_a.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            container = self.frame_a
        else:
            container = self

        # Type
        tk.Label(container, text="Type:").grid(row=0, column=0, sticky=tk.W)
        self.type_var = tk.StringVar(value="bs4_find_all" if is_item else "bs4_find")
        self.optionmenu_2 = ttk.OptionMenu(container, self.type_var, "bs4_find", "bs4_find", "bs4_find_all", "xpath")
        self.optionmenu_2.grid(row=0, column=1, sticky=tk.W)

        # Selector
        tk.Label(container, text="Selector (JSON dict or str):").grid(row=1, column=0, sticky=tk.W)
        self.entry_1 = tk.Entry(container, width=50)
        self.entry_1.grid(row=1, column=1, sticky=tk.W)
        self.label_1 = tk.Label(container, text='e.g. {"name": "div", "class_": "card-body"} or "article"')
        self.label_1.grid(row=1, column=2, sticky=tk.W)

        # Extract
        tk.Label(container, text="Extract:").grid(row=2, column=0, sticky=tk.W)
        self.extract_var = tk.StringVar(value="text")
        self.optionmenu_3 = ttk.OptionMenu(container, self.extract_var, "text", "text", "href", "src")
        self.optionmenu_3.grid(row=2, column=1, sticky=tk.W)

        # Limit
        tk.Label(container, text="Limit:").grid(row=3, column=0, sticky=tk.W)
        self.entry_13 = tk.Entry(container, width=10)
        self.entry_13.insert(0, "1")
        self.entry_13.grid(row=3, column=1, sticky=tk.W)

        # Filters
        tk.Label(container, text="Filters:").grid(row=4, column=0, sticky=tk.W)
        self.listbox_4 = tk.Listbox(container, height=5, width=50)
        self.listbox_4.grid(row=4, column=1, columnspan=2, sticky=tk.W)

        self.button_5 = tk.Button(container, text="Add Filter", command=self.add_filter)
        self.button_5.grid(row=5, column=0, sticky=tk.W)
        self.button_9 = tk.Button(container, text="Edit Filter", command=self.edit_filter)
        self.button_9.grid(row=5, column=1, sticky=tk.W)
        self.button_10 = tk.Button(container, text="Delete Filter", command=self.delete_filter)
        self.button_10.grid(row=5, column=2, sticky=tk.W)

        # Post Process
        self.frame_b = tk.LabelFrame(container, text="Post Process (replace)")
        self.frame_b.grid(row=6, column=0, columnspan=3, sticky=tk.W)
        tk.Label(self.frame_b, text="From:").pack(side=tk.LEFT)
        self.entry_11 = tk.Entry(self.frame_b, width=20)
        self.entry_11.pack(side=tk.LEFT)
        tk.Label(self.frame_b, text="To:").pack(side=tk.LEFT)
        self.entry_12 = tk.Entry(self.frame_b, width=20)
        self.entry_12.pack(side=tk.LEFT)

        # Save button for article_item tab
        if is_item:
            self.button_15 = tk.Button(container, text="保存配置", command=self.save_article_item_config)
            self.button_15.grid(row=7, column=0, sticky=tk.W)
        # Parent
        elif not is_item:
            self.button_14 = tk.Button(container, text="Configure Parent", command=self.configure_parent)
            self.button_14.grid(row=7, column=0, sticky=tk.W)

        if not is_item:
            self.toggle_enable()

    def toggle_enable(self):
        state = tk.NORMAL if self.enable_var.get() else tk.DISABLED
        for child in self.frame_a.winfo_children():
            # Only configure state for widgets that support it
            try:
                child.configure(state=state)
            except tk.TclError:
                pass

    def add_filter(self):
        filter_dialog = FilterConfigDialog(self, title="Add Filter")
        if filter_dialog.result:
            self.filters.append(filter_dialog.result)
            self.update_listbox()

    def edit_filter(self):
        selected = self.listbox_4.curselection()
        if selected:
            idx = selected[0]
            filter_dialog = FilterConfigDialog(self, title="Edit Filter", initial=self.filters[idx])
            if filter_dialog.result:
                self.filters[idx] = filter_dialog.result
                self.update_listbox()

    def delete_filter(self):
        selected = self.listbox_4.curselection()
        if selected:
            del self.filters[selected[0]]
            self.update_listbox()

    def update_listbox(self):
        self.listbox_4.delete(0, tk.END)
        for f in self.filters:
            self.listbox_4.insert(tk.END, str(f))

    def configure_parent(self):
        dialog = ParentConfigDialog(self, title="Configure Parent")
        if dialog.result:
            self.parent_conf = {"parent": dialog.result}

    def get_config(self):
        conf = {
            "type": self.type_var.get(),
            "selector": self.try_parse_json(self.entry_1.get()),
            "extract": self.extract_var.get(),
        }
        limit = self.entry_13.get().strip()
        if limit:
            conf["limit"] = int(limit)
        if self.filters:
            conf["filters"] = self.filters
        post_from = self.entry_11.get().strip()
        post_to = self.entry_12.get().strip()
        if post_from:
            conf["post_process"] = [{"replace": {"from": post_from, "to": post_to}}]
        if hasattr(self, "parent_conf") and self.parent_conf:
            conf.update(self.parent_conf)
        return conf

    def set_config(self, conf):
        if not self.is_item:
            self.enable_var.set(True)
            self.toggle_enable()
        self.type_var.set(conf.get("type", "bs4_find"))
        selector = conf.get("selector", "")
        self.entry_1.insert(0, json.dumps(selector) if isinstance(selector, dict) else selector)
        self.extract_var.set(conf.get("extract", "text"))
        limit = conf.get("limit")
        self.entry_13.delete(0, tk.END)
        self.entry_13.insert(0, str(limit) if limit else "1")
        self.filters = conf.get("filters", [])
        self.update_listbox()
        post_process = conf.get("post_process", [])
        if post_process and "replace" in post_process[0]:
            repl = post_process[0]["replace"]
            self.entry_11.insert(0, repl.get("from", ""))
            self.entry_12.insert(0, repl.get("to", ""))
        if "parent" in conf:
            self.parent_conf = {"parent": conf["parent"]}
    
    def save_article_item_config(self):
        # 获取当前配置
        config = {
            "article_item": self.get_config()
        }
        # 弹出保存文件对话框
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json", 
            filetypes=[("JSON files", "*.json")],
            title="保存文章定位配置"
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("保存成功", f"配置已保存到：{filepath}")
            except Exception as e:
                messagebox.showerror("保存失败", f"保存配置时出错：{str(e)}")

    def try_parse_json(self, s):
        try:
            return json.loads(s)
        except:
            return s

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Build scrapy_article.json")
        self.geometry("800x600")

        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load JSON", command=self.load_json)
        filemenu.add_command(label="Save JSON", command=self.save_json)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_A = ConfigTab(self.notebook, is_item=True)
        self.notebook.add(self.tab_A, text="定位文章 (article_item)")

        self.tabs = {}
        fields = ["article_url", "article_title", "author", "article_date", "excerpt", "tag", "thumbnail"]
        letters = "B C D E F G H".split()
        for letter, field in zip(letters, fields):
            tab = ConfigTab(self.notebook, field_name=field)
            self.notebook.add(tab, text=f"定位{field.split('_')[-1]}")
            self.tabs[field] = tab

    def load_json(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            article_meta_conf = config.get("article_meta", {})
            for field, conf in article_meta_conf.items():
                if field in self.tabs:
                    self.tabs[field].set_config(conf)

    def save_json(self):
        config = {
            "article_meta": {}
        }
        for field, tab in self.tabs.items():
            if tab.enable_var.get():
                config["article_meta"][field] = tab.get_config()
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", "JSON saved successfully.")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()