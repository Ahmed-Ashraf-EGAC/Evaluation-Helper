import os
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox

import pandas as pd

# === Configuration ===
EXCEL_PATH = "cases_review_ashraf.xlsx"  # path to your Excel file
PDF_FOLDER = "./pdfs"  # path to PDF files
TXT_FOLDER = "./txts"  # path to TXT files

# === Load Data ===
df = pd.read_excel(EXCEL_PATH)
case_ids = df["Case ID"].tolist()
current_index = 0

# === GUI Setup ===
root = tk.Tk()
root.title("Case Reviewer")

checkbox_vars = {}
checkbox_widgets = {}


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
        if col == "Case ID":
            continue
        val = row[col]
        checkbox_vars[col].set(int(val == 1))


def save_case():
    case_id = case_ids[current_index]
    for col in df.columns:
        if col == "Case ID":
            continue
        df.loc[df["Case ID"] == case_id, col] = 1 if checkbox_vars[col].get() else ""
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

top_frame = tk.Frame(root)
top_frame.pack(pady=10)

case_label_var = tk.StringVar()
case_label = tk.Label(top_frame, textvariable=case_label_var, font=("Arial", 14))
case_label.pack()

nav_frame = tk.Frame(root)
nav_frame.pack()

tk.Button(nav_frame, text="<< Previous", command=prev_case).pack(side=tk.LEFT, padx=5)
tk.Button(nav_frame, text="Next >>", command=next_case).pack(side=tk.LEFT, padx=5)

jump_frame = tk.Frame(root)
jump_frame.pack(pady=5)
jump_entry = tk.Entry(jump_frame)
jump_entry.pack(side=tk.LEFT)
tk.Button(jump_frame, text="Jump to Case ID", command=jump_to_case).pack(
    side=tk.LEFT, padx=5
)

file_frame = tk.Frame(root)
file_frame.pack(pady=5)
tk.Button(file_frame, text="Open PDF", command=open_pdf).pack(side=tk.LEFT, padx=5)
tk.Button(file_frame, text="Open TXT", command=open_txt).pack(side=tk.LEFT, padx=5)

checkbox_frame = tk.Frame(root)
checkbox_frame.pack(pady=10)

for col in df.columns:
    if col == "Case ID":
        continue
    var = tk.IntVar()
    checkbox = tk.Checkbutton(checkbox_frame, text=col, variable=var)
    checkbox.pack(anchor="w")
    checkbox_vars[col] = var
    checkbox_widgets[col] = checkbox

save_button = tk.Button(root, text="Save", command=save_case, bg="lightgreen")
save_button.pack(pady=10)

# === Start ===
load_case(current_index)
root.mainloop()
