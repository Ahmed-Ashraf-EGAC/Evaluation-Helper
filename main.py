import os
import tkinter as tk
import webbrowser
from tkinter import ttk  # use themed widgets
from tkinter import messagebox, scrolledtext

import pandas as pd

# === Configuration ===
EXCEL_PATH = "cases_review_ashraf.xlsx"
PDF_FOLDER = "./pdfs"
TXT_FOLDER = "./txts"

# === Load Data ===
df = pd.read_excel(EXCEL_PATH)
if "Notes" not in df.columns:
    df["Notes"] = ""

case_ids = df["Case ID"].tolist()
current_index = 0

# === GUI Setup ===
root = tk.Tk()
root.title("Case Reviewer")
root.geometry("700x550")  # Updated window size

style = ttk.Style(root)
default_theme = "clam"
style.theme_use(default_theme)
root.configure(bg="SystemButtonFace")  # default background for non-ttk widgets


# Create a dark theme if it doesn't already exist.
def create_dark_theme():
    try:
        style.theme_create(
            "dark",
            parent="clam",
            settings={
                ".": {"configure": {"background": "#2e2e2e", "foreground": "#ffffff"}},
                "TButton": {
                    "configure": {
                        "padding": 5,
                        "background": "#3e3e3e",
                        "foreground": "#ffffff",
                    }
                },
                "TLabel": {
                    "configure": {"background": "#2e2e2e", "foreground": "#ffffff"}
                },
                "TFrame": {"configure": {"background": "#2e2e2e"}},
                "TEntry": {
                    "configure": {"fieldbackground": "#3e3e3e", "foreground": "#ffffff"}
                },
                "TCombobox": {
                    "configure": {"fieldbackground": "#3e3e3e", "foreground": "#ffffff"}
                },
            },
        )
    except tk.TclError:
        # Theme already exists
        pass


create_dark_theme()

checkbox_vars = {}
checkbox_widgets = {}

# We'll later reference this widget to update its background color.
notes_text = None


# Function to change theme using the combobox selection.
def change_theme(event):
    selected_theme = theme_combobox.get()
    try:
        if selected_theme == "dark":
            style.theme_use("dark")
            root.configure(bg="#2e2e2e")
            if notes_text is not None:
                notes_text.configure(
                    bg="#3e3e3e", fg="#ffffff", insertbackground="#ffffff"
                )
        else:
            style.theme_use(selected_theme)
            root.configure(bg="SystemButtonFace")
            if notes_text is not None:
                notes_text.configure(bg="white", fg="black", insertbackground="black")
    except tk.TclError:
        messagebox.showerror("Error", f"Theme '{selected_theme}' not found.")


# === Functions ===
def load_case(index):
    global current_index
    if index < 0 or index >= len(case_ids):
        return
    current_index = index
    case_id = case_ids[current_index]
    case_label_var.set(f"Case ID: {case_id}")

    row = df.loc[df["Case ID"] == case_id].iloc[0]
    for col in df.columns:
        if col in ["Case ID", "Notes"]:
            continue
        val = row[col]
        checkbox_vars[col].set(int(val == 1))

    # Ensure notes is empty if NaN
    notes_val = row.get("Notes", "")
    if pd.isna(notes_val) or str(notes_val).lower() == "nan":
        notes_val = ""
    notes_text.delete("1.0", tk.END)
    notes_text.insert(tk.END, str(notes_val))


def save_case():
    case_id = case_ids[current_index]
    for col in df.columns:
        if col in ["Case ID", "Notes"]:
            continue
        df.loc[df["Case ID"] == case_id, col] = 1 if checkbox_vars[col].get() else ""
    df.loc[df["Case ID"] == case_id, "Notes"] = notes_text.get("1.0", tk.END).strip()
    df.to_excel(EXCEL_PATH, index=False)
    messagebox.showinfo("Saved", f"Saved changes for Case ID: {case_id}")


def next_case():
    if current_index + 1 < len(case_ids):
        load_case(current_index + 1)


def prev_case():
    if current_index - 1 >= 0:
        load_case(current_index - 1)


def jump_to_case():
    try:
        target_id = int(jump_entry.get())
        if target_id in case_ids:
            index = case_ids.index(target_id)
            load_case(index)
        else:
            messagebox.showerror("Error", f"Case ID {target_id} not found.")
    except ValueError:
        messagebox.showerror("Error", "Invalid Case ID.")


def open_pdf():
    case_id = case_ids[current_index]
    path = os.path.join(PDF_FOLDER, f"case_{case_id}.pdf")
    if os.path.exists(path):
        webbrowser.open(path)
    else:
        messagebox.showerror("File Not Found", f"No PDF found for Case ID {case_id}")


def open_txt():
    case_id = case_ids[current_index]
    path = os.path.join(TXT_FOLDER, f"case_{case_id}.txt")
    if os.path.exists(path):
        webbrowser.open(path)
    else:
        messagebox.showerror("File Not Found", f"No TXT found for Case ID {case_id}")


# === GUI Layout ===

# Top frame containing the case label and theme selector
top_frame = ttk.Frame(root, padding=10)
top_frame.pack(pady=10, fill=tk.X)

case_label_var = tk.StringVar()
case_label = ttk.Label(top_frame, textvariable=case_label_var, font=("Arial", 14))
case_label.pack(side=tk.LEFT, padx=(0, 20))

# Theme Selection
theme_label = ttk.Label(top_frame, text="Theme:")
theme_label.pack(side=tk.LEFT)
theme_options = ["clam", "alt", "default", "classic", "dark"]
theme_combobox = ttk.Combobox(top_frame, values=theme_options, width=10)
theme_combobox.set(default_theme)
theme_combobox.pack(side=tk.LEFT, padx=5)
theme_combobox.bind("<<ComboboxSelected>>", change_theme)

# Navigation Frame
nav_frame = ttk.Frame(root, padding=5)
nav_frame.pack(pady=5)

ttk.Button(nav_frame, text="<< Previous", command=prev_case).pack(side=tk.LEFT, padx=5)
ttk.Button(nav_frame, text="Next >>", command=next_case).pack(side=tk.LEFT, padx=5)

# Jump To Case
jump_frame = ttk.Frame(root, padding=5)
jump_frame.pack(pady=5)

jump_entry = ttk.Entry(jump_frame, width=10)
jump_entry.pack(side=tk.LEFT, padx=(0, 5))
ttk.Button(jump_frame, text="Jump to Case ID", command=jump_to_case).pack(side=tk.LEFT)

# File Buttons
file_frame = ttk.Frame(root, padding=5)
file_frame.pack(pady=5)

ttk.Button(file_frame, text="Open PDF", command=open_pdf).pack(side=tk.LEFT, padx=5)
ttk.Button(file_frame, text="Open TXT", command=open_txt).pack(side=tk.LEFT, padx=5)

# Checkboxes grid
checkbox_frame = ttk.Frame(root, padding=10)
checkbox_frame.pack(pady=10)

columns = [col for col in df.columns if col not in ["Case ID", "Notes"]]
for i, col in enumerate(columns):
    var = tk.IntVar()
    cb = ttk.Checkbutton(checkbox_frame, text=col, variable=var)
    cb.grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=3)
    checkbox_vars[col] = var
    checkbox_widgets[col] = cb

# Notes area
notes_frame = ttk.Frame(root, padding=10)
notes_frame.pack(pady=10, fill=tk.BOTH, expand=True)

ttk.Label(notes_frame, text="Notes:").pack(anchor="w")
notes_text = scrolledtext.ScrolledText(notes_frame, wrap=tk.WORD, width=60, height=5)
notes_text.pack(fill=tk.BOTH, expand=True)
# Initially set the background based on the default theme.
if default_theme == "dark":
    notes_text.configure(bg="#3e3e3e", fg="#ffffff", insertbackground="#ffffff")
else:
    notes_text.configure(bg="white", fg="black", insertbackground="black")

# Save Button
save_button = ttk.Button(root, text="Save", command=save_case)
save_button.pack(pady=10)

# === Start ===
load_case(current_index)
root.mainloop()
