import json
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


MOD_ID = "nanohsadditionalenchants"
PACK_FORMAT = 101
DISABLED_ITEM_TAG = f"#{MOD_ID}:disabled_enchant"
DEFAULTS_FILE = "nae_enchant_defaults.json"


class EnchantRow:
    def __init__(self, parent, row, name, data):
        self.name = name
        self.data = data
        self.override = tk.BooleanVar(value=False)
        self.disable = tk.BooleanVar(value=False)

        self.weight = tk.StringVar(value=str(data.get("weight", 1)))
        self.max_level = tk.StringVar(value=str(data.get("max_level", 1)))
        self.anvil_cost = tk.StringVar(value=str(data.get("anvil_cost", 1)))
        self.min_base = tk.StringVar(value=str(data.get("min_cost", {}).get("base", 1)))
        self.min_per_level = tk.StringVar(value=str(data.get("min_cost", {}).get("per_level_above_first", 1)))
        self.max_base = tk.StringVar(value=str(data.get("max_cost", {}).get("base", 1)))
        self.max_per_level = tk.StringVar(value=str(data.get("max_cost", {}).get("per_level_above_first", 1)))

        ttk.Checkbutton(parent, variable=self.override).grid(row=row, column=0, padx=4, pady=2)
        ttk.Checkbutton(parent, variable=self.disable, command=self.on_disable_changed).grid(row=row, column=1, padx=4, pady=2)
        ttk.Label(parent, text=pretty_name(name), width=24, anchor="w").grid(row=row, column=2, padx=4, pady=2, sticky="w")

        self.entries = []
        for column, var in enumerate([
            self.weight,
            self.max_level,
            self.anvil_cost,
            self.min_base,
            self.min_per_level,
            self.max_base,
            self.max_per_level,
        ], start=3):
            entry = ttk.Entry(parent, textvariable=var, width=7)
            entry.grid(row=row, column=column, padx=3, pady=2)
            self.entries.append(entry)

    def on_disable_changed(self):
        if self.disable.get():
            self.override.set(True)

    def values(self):
        return {
            "weight": parse_int(self.weight.get(), self.name, "weight", minimum=0),
            "max_level": parse_int(self.max_level.get(), self.name, "max level", minimum=1),
            "anvil_cost": parse_int(self.anvil_cost.get(), self.name, "anvil cost", minimum=0),
            "min_base": parse_int(self.min_base.get(), self.name, "min base", minimum=0),
            "min_per_level": parse_int(self.min_per_level.get(), self.name, "min per level", minimum=0),
            "max_base": parse_int(self.max_base.get(), self.name, "max base", minimum=0),
            "max_per_level": parse_int(self.max_per_level.get(), self.name, "max per level", minimum=0),
        }


class OverrideBuilder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NAE Override Datapack Builder")
        self.geometry("1040x720")
        self.minsize(940, 520)

        self.tool_dir = Path(__file__).resolve().parent
        self.defaults_path = self.tool_dir / DEFAULTS_FILE
        self.rows = []

        self.output_dir = tk.StringVar(value="")
        self.pack_name = tk.StringVar(value="nae_overrides")

        self.build_ui()
        self.load_enchants()

    def build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="World folder or datapacks folder").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.output_dir).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(top, text="Browse", command=self.choose_output).grid(row=1, column=1)

        ttk.Label(top, text="Override pack folder name").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(top, textvariable=self.pack_name, width=32).grid(row=3, column=0, sticky="w", padx=(0, 8))
        ttk.Button(top, text="Build Datapack", command=self.build_pack).grid(row=3, column=1, sticky="e")
        top.columnconfigure(0, weight=1)

        note = ttk.Label(
            self,
            padding=(10, 0, 10, 8),
            text="Override checked rows are written. Disable keeps the enchant registered but makes it support no items.",
        )
        note.pack(fill="x")

        container = ttk.Frame(self, padding=(10, 0, 10, 10))
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.table = ttk.Frame(canvas)

        self.table.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.table, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        headers = [
            "Write",
            "Disable",
            "Enchant",
            "Weight",
            "Max Lvl",
            "Anvil",
            "Min Base",
            "Min/Lvl",
            "Max Base",
            "Max/Lvl",
        ]
        for column, text in enumerate(headers):
            ttk.Label(self.table, text=text, font=("", 9, "bold")).grid(row=0, column=column, padx=4, pady=(0, 5))

    def load_enchants(self):
        if not self.defaults_path.exists():
            messagebox.showerror(
                "Missing defaults",
                f"Could not find enchant defaults:\n{self.defaults_path}",
            )
            return

        with self.defaults_path.open("r", encoding="utf-8-sig") as file:
            defaults = json.load(file)

        for index, (name, data) in enumerate(sorted(defaults.get("enchants", {}).items()), start=1):
            self.rows.append(EnchantRow(self.table, index, name, data))

    def choose_output(self):
        path = filedialog.askdirectory(title="Choose world folder or datapacks folder")
        if path:
            self.output_dir.set(path)

    def build_pack(self):
        try:
            base = Path(self.output_dir.get()).expanduser()
            if not base:
                raise ValueError("Choose a world folder or datapacks folder.")

            datapacks_dir = base if base.name == "datapacks" else base / "datapacks"
            pack_name = sanitize_pack_name(self.pack_name.get())
            if not pack_name:
                raise ValueError("Pack name cannot be empty.")

            selected = [row for row in self.rows if row.override.get() or row.disable.get()]
            if not selected:
                raise ValueError("Select at least one enchant to override or disable.")

            pack_dir = datapacks_dir / pack_name
            enchant_dir = pack_dir / "data" / MOD_ID / "enchantment"
            enchant_dir.mkdir(parents=True, exist_ok=True)

            write_json(pack_dir / "pack.mcmeta", {
                "pack": {
                    "description": "NAE Overrides",
                    "min_format": PACK_FORMAT,
                    "max_format": PACK_FORMAT,
                }
            })

            needs_disabled_tag = False
            for row in selected:
                data = dict(row.data)
                values = row.values()

                data["weight"] = values["weight"]
                data["max_level"] = values["max_level"]
                data["anvil_cost"] = values["anvil_cost"]
                data["min_cost"] = {
                    "base": values["min_base"],
                    "per_level_above_first": values["min_per_level"],
                }
                data["max_cost"] = {
                    "base": values["max_base"],
                    "per_level_above_first": values["max_per_level"],
                }

                if row.disable.get():
                    needs_disabled_tag = True
                    data["supported_items"] = DISABLED_ITEM_TAG
                    data["primary_items"] = DISABLED_ITEM_TAG
                    data["weight"] = 1

                write_json(enchant_dir / f"{row.name}.json", data)

            if needs_disabled_tag:
                tag_dir = pack_dir / "data" / MOD_ID / "tags" / "item"
                tag_dir.mkdir(parents=True, exist_ok=True)
                write_json(tag_dir / "disabled_enchant.json", {"values": []})

            messagebox.showinfo("Datapack built", f"Wrote override datapack:\n{pack_dir}")
        except Exception as error:
            messagebox.showerror("Could not build datapack", str(error))


def parse_int(value, enchant_name, field_name, minimum):
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{pretty_name(enchant_name)} has an invalid {field_name}: {value}") from error

    if parsed < minimum:
        raise ValueError(f"{pretty_name(enchant_name)} {field_name} must be at least {minimum}.")
    return parsed


def pretty_name(name):
    return name.replace("_", " ").title()


def sanitize_pack_name(value):
    value = value.strip().lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_.-]", "", value)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")


if __name__ == "__main__":
    OverrideBuilder().mainloop()
