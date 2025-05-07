import os
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

import pandas as pd

from config import *
from data import load_dataframe, save_dataframe

# Global data variables
df = load_dataframe()
case_ids = df["Case ID"].tolist()
current_index = 0
unsaved_changes = False


def change_theme(event, theme_combobox, style, root, notes_text):
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


def create_dark_theme(style):
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
        pass


def load_case(index, case_label_var, notes_text, checkbox_vars, case_done_var):
    global current_index, unsaved_changes, df
    if index < 0 or index >= len(case_ids):
        return
    current_index = index
    unsaved_changes = False
    case_id = case_ids[current_index]
    case_label_var.set(f"Case ID: {case_id}")
    row = df.loc[df["Case ID"] == case_id].iloc[0]
    for col in df.columns:
        if col in ["Case ID", "Notes", "Case Done"]:
            continue
        checkbox_vars[col].set(int(row[col] == 1))
    notes_val = row.get("Notes", "")
    if pd.isna(notes_val) or str(notes_val).lower() == "nan":
        notes_val = ""
    notes_text.delete("1.0", tk.END)
    notes_text.insert(tk.END, str(notes_val))
    case_done_val = row.get("Case Done", "")
    case_done_var.set(int(case_done_val == 1))


def save_case(checkbox_vars, notes_text, case_done_var):
    global unsaved_changes, df
    case_id = case_ids[current_index]
    for col in df.columns:
        if col in ["Case ID", "Notes", "Case Done"]:
            continue
        df.loc[df["Case ID"] == case_id, col] = 1 if checkbox_vars[col].get() else ""
    df.loc[df["Case ID"] == case_id, "Notes"] = notes_text.get("1.0", tk.END).strip()
    df.loc[df["Case ID"] == case_id, "Case Done"] = 1 if case_done_var.get() else ""
    save_dataframe(df)
    unsaved_changes = False
    messagebox.showinfo("Saved", f"Saved changes for Case ID: {case_id}")
    update_progress()


def next_case(load_func):
    global current_index
    if current_index + 1 < len(case_ids) and check_unsaved():
        load_func(current_index + 1)


def prev_case(load_func):
    global current_index
    if current_index - 1 >= 0 and check_unsaved():
        load_func(current_index - 1)


def jump_to_case(jump_entry, load_func):
    try:
        target_id = int(jump_entry.get())
        if target_id in case_ids and check_unsaved():
            index = case_ids.index(target_id)
            load_func(index)
        else:
            messagebox.showerror("Error", f"Case ID {target_id} not found.")
    except ValueError:
        messagebox.showerror("Error", "Invalid Case ID.")


def open_files():
    missing = []
    case_id = case_ids[current_index]
    pdf_path = os.path.join(PDF_FOLDER, f"case_{case_id}.pdf")
    txt_path = os.path.join(TXT_FOLDER, f"case_{case_id}.txt")
    if os.path.exists(pdf_path):
        webbrowser.open(pdf_path)
    else:
        missing.append("PDF")
    if os.path.exists(txt_path):
        webbrowser.open(txt_path)
    else:
        missing.append("TXT")
    if missing:
        if len(missing) == 2:
            messagebox.showerror(
                "File(s) Not Found",
                f"Both PDF and TXT files are missing for Case ID {case_id}",
            )
        else:
            messagebox.showwarning(
                "File Missing", f"{missing[0]} file is missing for Case ID {case_id}"
            )


def mark_unsaved(*args):
    global unsaved_changes
    unsaved_changes = True


def on_notes_modified(event, notes_text):
    global unsaved_changes
    unsaved_changes = True
    notes_text.edit_modified(False)


def check_unsaved():
    global unsaved_changes, unsaved_warning
    if unsaved_changes and unsaved_warning:
        result = messagebox.askyesnocancel(
            "Unsaved Changes", "You have unsaved changes. Would you like to save them?"
        )
        if result is None:
            return False
        elif result:
            # Caller should ensure save_case is properly invoked.
            return True
    return True


def on_closing(root):
    if check_unsaved():
        root.destroy()


def update_progress(progress_bar, status_label):
    done_count = (df["Case Done"] == 1).sum()
    total = len(df)
    progress_bar["maximum"] = total
    progress_bar["value"] = done_count
    status_label.config(text=f"Cases Done: {done_count} / {total}")


def copy_case_id(case_label_var, root):
    case_id_text = case_label_var.get().replace("Case ID: ", "")
    root.clipboard_clear()
    root.clipboard_append(case_id_text)


def open_settings(root, theme_combobox):
    import tkinter as tk
    from tkinter import messagebox, ttk

    # Import save_config from config.py so settings persist.
    from config import (
        EXCEL_PATH,
        PDF_FOLDER,
        TXT_FOLDER,
        default_theme,
        load_config,
        save_config,
        unsaved_warning,
    )

    settings = tk.Toplevel(root)
    settings.title("Settings")
    settings.grab_set()
    tk.Label(settings, text="Excel Path:").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )
    excel_path_var = tk.StringVar(value=EXCEL_PATH)
    tk.Entry(settings, textvariable=excel_path_var, width=40).grid(
        row=0, column=1, padx=5, pady=5
    )

    tk.Label(settings, text="PDF Folder:").grid(
        row=1, column=0, sticky="w", padx=5, pady=5
    )
    pdf_folder_var = tk.StringVar(value=PDF_FOLDER)
    tk.Entry(settings, textvariable=pdf_folder_var, width=40).grid(
        row=1, column=1, padx=5, pady=5
    )

    tk.Label(settings, text="TXT Folder:").grid(
        row=2, column=0, sticky="w", padx=5, pady=5
    )
    txt_folder_var = tk.StringVar(value=TXT_FOLDER)
    tk.Entry(settings, textvariable=txt_folder_var, width=40).grid(
        row=2, column=1, padx=5, pady=5
    )

    unsaved_warning_var = tk.BooleanVar(value=unsaved_warning)
    tk.Checkbutton(
        settings, text="Enable Unsaved Changes Warning", variable=unsaved_warning_var
    ).grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    tk.Label(settings, text="Default Theme:").grid(
        row=4, column=0, sticky="w", padx=5, pady=5
    )
    theme_var = tk.StringVar(value=default_theme)
    ttk.Combobox(
        settings,
        textvariable=theme_var,
        values=["clam", "alt", "default", "classic", "dark"],
        width=10,
    ).grid(row=4, column=1, padx=5, pady=5)

    def save_settings():
        new_config = {
            "EXCEL_PATH": excel_path_var.get(),
            "PDF_FOLDER": pdf_folder_var.get(),
            "TXT_FOLDER": txt_folder_var.get(),
            "unsaved_warning": unsaved_warning_var.get(),
            "default_theme": theme_var.get(),
        }
        # Save the new configuration to disk.
        save_config(new_config)
        # Reload the config so that global variables can be updated.
        cfg = load_config()
        global EXCEL_PATH, PDF_FOLDER, TXT_FOLDER, unsaved_warning, default_theme
        EXCEL_PATH = cfg["EXCEL_PATH"]
        PDF_FOLDER = cfg["PDF_FOLDER"]
        TXT_FOLDER = cfg["TXT_FOLDER"]
        unsaved_warning = cfg["unsaved_warning"]
        default_theme = cfg["default_theme"]
        theme_combobox.set(default_theme)
        # Update the theme immediately.
        style = ttk.Style(root)
        change_theme(None, theme_combobox, style, root, None)
        settings.destroy()
        messagebox.showinfo("Settings", "Settings updated and saved.")

    tk.Button(settings, text="Save Settings", command=save_settings).grid(
        row=5, column=0, columnspan=2, pady=10
    )
