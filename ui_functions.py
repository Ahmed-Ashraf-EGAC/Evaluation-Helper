import os
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

import pandas as pd

from config import *
from data import load_dataframe, save_dataframe
from global_vars import *

# Global data variables
df = load_dataframe()
case_ids = df["Case ID"].tolist()
current_index = 0
unsaved_changes = False
loading_case = False  # Add a flag to track when loading is happening


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


def load_case(
    index,
    case_label_var,
    notes_text,
    checkbox_vars,
    case_done_var,
    notes_text_judge=None,
):
    global current_index, unsaved_changes, df, loading_case
    if index < 0 or index >= len(case_ids):
        return
    current_index = index

    # Set the loading flag to prevent marking changes during loading
    loading_case = True
    unsaved_changes = False

    case_id = case_ids[current_index]
    case_label_var.set(f"Case ID: {case_id}")
    row = df.loc[df["Case ID"] == case_id].iloc[0]
    for col in df.columns:
        if col in ["Case ID", "Notes", "Case Done", "Judge Notes"]:
            continue
        checkbox_vars[col].set(int(row[col] == 1))
    notes_val = row.get("Notes", "")
    if pd.isna(notes_val) or str(notes_val).lower() == "nan":
        notes_val = ""
    notes_text.delete("1.0", tk.END)
    notes_text.insert(tk.END, str(notes_val))

    # Load Judge Notes if widget is provided
    if notes_text_judge is not None:
        judge_val = row.get("Judge Notes", "")
        if pd.isna(judge_val) or str(judge_val).lower() == "nan":
            judge_val = ""
        notes_text_judge.delete("1.0", tk.END)
        notes_text_judge.insert(tk.END, str(judge_val))

    case_done_val = row.get("Case Done", "")
    case_done_var.set(int(case_done_val == 1))

    # Done loading, reset the flag
    loading_case = False


def save_case(
    checkbox_vars,
    notes_text,
    case_done_var,
    progress_bar,
    status_label,
    notes_text_judge=None,
):
    global unsaved_changes, df
    case_id = case_ids[current_index]
    for col in df.columns:
        if col in ["Case ID", "Notes", "Case Done", "Judge Notes"]:
            continue
        df.loc[df["Case ID"] == case_id, col] = 1 if checkbox_vars[col].get() else ""
    df.loc[df["Case ID"] == case_id, "Notes"] = notes_text.get("1.0", tk.END).strip()
    df.loc[df["Case ID"] == case_id, "Case Done"] = 1 if case_done_var.get() else ""

    # Save Judge Notes if widget is provided
    if notes_text_judge is not None:
        # Add the column if it doesn't exist
        if "Judge Notes" not in df.columns:
            df["Judge Notes"] = ""
        df.loc[df["Case ID"] == case_id, "Judge Notes"] = notes_text_judge.get(
            "1.0", tk.END
        ).strip()

    save_dataframe(df)
    unsaved_changes = False

    # Replace messagebox with toast notification
    root = notes_text.winfo_toplevel()  # Get the root window from any widget
    show_toast(root, f"Saved changes for Case ID: {case_id}")

    update_progress(progress_bar, status_label)


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
    pdf_path = os.path.join(PDF_FOLDER, f"{case_id}.pdf")
    txt_path = os.path.join(TXT_FOLDER, f"{case_id}.txt")
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
    global unsaved_changes, loading_case
    if not loading_case:  # Only mark as unsaved if we're not loading a case
        unsaved_changes = True


def on_notes_modified(event, notes_text):
    global unsaved_changes, loading_case
    if not loading_case:  # Only mark as unsaved if we're not loading a case
        unsaved_changes = True
    notes_text.edit_modified(False)


def check_unsaved(closing=False):
    global unsaved_changes, unsaved_warning
    if (unsaved_changes and unsaved_warning) or closing:
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
    if check_unsaved(closing=True):
        root.destroy()


def update_progress(progress_bar, status_label):
    done_count = (df["Case Done"] == 1).sum()
    total = len(df)
    progress_bar["maximum"] = total
    progress_bar["value"] = done_count
    status_label.config(text=f"Cases Done: {done_count} / {total}")

    # Destroy existing tooltip if it exists
    if hasattr(status_label, "_tooltip"):
        status_label._tooltip.destroy()

    # Create new tooltip
    from tooltip import ToolTip

    ToolTip(status_label, get_progress_message())


def copy_case_id(case_label_var, root):
    case_id_text = case_label_var.get().replace("Case ID: ", "")
    root.clipboard_clear()
    root.clipboard_append(case_id_text)
    show_toast(root, f"Copied Case ID: {case_id_text}")


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


def get_progress_message():
    done_count = (df["Case Done"] == 1).sum()
    total = len(df)
    percentage = (done_count / total) * 100 if total > 0 else 0

    if percentage == 0:
        return "Still a long way to go :("
    elif percentage < 25:
        return "Getting the hang of it."
    elif percentage < 50:
        return "Making progress!."
    elif percentage < 75:
        return "Almost there!"
    elif percentage < 100:
        return "Final stretch!!"
    else:
        return "Congratulations! All cases are complete!"


def view_open_cases(case_label_var, notes_text, checkbox_vars, case_done_var):
    """Display a popup listing all case IDs separated into categories."""
    import tkinter as tk
    from tkinter import messagebox, ttk

    # Filter cases by status
    done_df = df[df["Case Done"] == 1]
    not_done_df = df[df["Case Done"] != 1]

    # Filter AI correct cases
    ai_correct_df = df[df["Is AI Correct"] == 1]

    # Filter done but incorrect cases (done but AI not correct)
    done_incorrect_df = done_df[done_df["Is AI Correct"] != 1]

    # Separate into unreviewed (completely empty) and open (started but not done)
    checkbox_columns = [
        col for col in df.columns if col not in ["Case ID", "Notes", "Case Done"]
    ]

    # Unreviewed cases have no checkboxes ticked and no notes
    unreviewed_mask = (not_done_df[checkbox_columns] != 1).all(axis=1) & (
        not_done_df["Notes"].isna() | (not_done_df["Notes"] == "")
    )
    unreviewed_df = not_done_df[unreviewed_mask]
    open_df = not_done_df[~unreviewed_mask]

    # Create popup window
    window = tk.Toplevel()
    window.title("Case Status")
    window.grab_set()

    # Create notebook for tabs
    notebook = ttk.Notebook(window)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)

    # Create tabs for all categories
    def create_case_list(parent, cases_df, title):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        # Add count label
        count_label = ttk.Label(frame, text=f"Total {title}: {len(cases_df)}")
        count_label.pack(pady=(5, 0))

        # Create listbox with scrollbar
        listbox = tk.Listbox(frame, width=50)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)

        # Populate listbox
        for _, row in cases_df.iterrows():
            case_id = int(row["Case ID"])
            listbox.insert("end", case_id)

        # Bind double-click event
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                selected_case_id = listbox.get(idx)
                if selected_case_id in case_ids:
                    case_idx = case_ids.index(selected_case_id)
                    load_case(
                        case_idx,
                        case_label_var,
                        notes_text,
                        checkbox_vars,
                        case_done_var,
                    )
                    window.destroy()

        listbox.bind("<Double-Button-1>", on_double_click)
        return frame

    # Create and add tabs
    unreviewed_tab = create_case_list(notebook, unreviewed_df, "Unreviewed")
    open_tab = create_case_list(notebook, open_df, "Open")
    done_tab = create_case_list(notebook, done_df, "Done")
    ai_correct_tab = create_case_list(notebook, ai_correct_df, "AI Correct")
    done_incorrect_tab = create_case_list(
        notebook, done_incorrect_df, "Done but Incorrect"
    )

    notebook.add(unreviewed_tab, text=f"Unreviewed ({len(unreviewed_df)})")
    notebook.add(open_tab, text=f"Open ({len(open_df)})")
    notebook.add(done_tab, text=f"Done ({len(done_df)})")
    notebook.add(ai_correct_tab, text=f"AI Correct ({len(ai_correct_df)})")
    notebook.add(done_incorrect_tab, text=f"Done Incorrect ({len(done_incorrect_df)})")


# Add this new function for toast notifications
def show_toast(root, message, duration=2000, bg_color="#4CAF50", fg_color="white"):
    """Show a toast notification that automatically disappears after duration (ms)"""
    # Create a toplevel window without decorations
    toast = tk.Toplevel(root)
    toast.overrideredirect(True)  # Remove window decorations

    # Create a frame with padding and background color
    frame = tk.Frame(toast, bg=bg_color, padx=15, pady=10)
    frame.pack(fill=tk.BOTH, expand=True)

    # Add the message
    label = tk.Label(
        frame,
        text=message,
        bg=bg_color,
        fg=fg_color,
        font=("Arial", 11),
        wraplength=300,
    )
    label.pack(pady=5)

    # Position the toast at the bottom center of the root window
    toast.update_idletasks()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()

    toast_width = toast.winfo_width()
    toast_height = toast.winfo_height()

    x = root_x + (root_width // 2) - (toast_width // 2)
    y = root_y + root_height - toast_height - 20

    toast.geometry(f"+{x}+{y}")

    # Bring toast to front
    toast.lift()

    # Set a timer to destroy the toast
    toast.after(duration, toast.destroy)

    return toast


def paste_to_notes(event, text_widget):
    """Handle paste operation from keyboard shortcut"""
    try:
        text_widget.delete("sel.first", "sel.last")
    except tk.TclError:
        # No selection to delete
        pass
    text_widget.insert(tk.INSERT, text_widget.clipboard_get())
    mark_unsaved()  # Mark as unsaved after pasting
    return "break"  # Prevent default paste behavior


def paste_from_clipboard(text_widget):
    """Paste text from clipboard at current position"""
    try:
        clip_text = text_widget.clipboard_get()
        try:
            text_widget.delete("sel.first", "sel.last")
        except tk.TclError:
            # No selection to delete
            pass
        text_widget.insert(tk.INSERT, clip_text)
        mark_unsaved()  # Mark as unsaved after pasting
    except tk.TclError:
        # Clipboard is empty or contains non-text data
        pass


def show_context_menu(event, text_widget, menu):
    """Show context menu at mouse position"""
    # Update paste command availability based on clipboard content
    try:
        text_widget.clipboard_get()
        menu.entryconfig("Paste", state="normal")
    except tk.TclError:
        menu.entryconfig("Paste", state="disabled")
    menu.tk_popup(event.x_root, event.y_root)
