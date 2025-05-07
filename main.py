import os
import tkinter as tk
import webbrowser
from tkinter import messagebox, scrolledtext, ttk

import pandas as pd


# Add this utility class near the top (after your imports)
class ToolTip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
        widget.bind("<Enter>", self.enter)
        widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            background="yellow",
            relief="solid",
            borderwidth=1,
            font=("tahoma", "8", "normal"),
        )
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


# === Configuration ===
EXCEL_PATH = "cases_review_ashraf.xlsx"
PDF_FOLDER = "./pdfs"
TXT_FOLDER = "./txts"

# === Load Data ===
df = pd.read_excel(EXCEL_PATH)
if "Notes" not in df.columns:
    df["Notes"] = ""
if "Case Done" not in df.columns:
    df["Case Done"] = ""

case_ids = df["Case ID"].tolist()
current_index = 0
unsaved_changes = False

# At the top, add a global flag for unsaved warning:
unsaved_warning = True

# === GUI Setup ===
root = tk.Tk()
root.title("Case Reviewer")
root.geometry("700x550")  # Updated window size
root.configure(bg="SystemButtonFace")

style = ttk.Style(root)
default_theme = "clam"
style.theme_use(default_theme)

# === Global Variables for "Case Done" and Progress ===
case_done_var = tk.IntVar(master=root)  # For the "Case Done" checkbox
progress_var = tk.IntVar(master=root)


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
    global current_index, unsaved_changes
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
    # Load the "Case Done" status.
    case_done_val = row.get("Case Done", "")
    case_done_var.set(int(case_done_val == 1))


def save_case():
    global unsaved_changes
    case_id = case_ids[current_index]
    for col in df.columns:
        if col in ["Case ID", "Notes", "Case Done"]:
            continue
        df.loc[df["Case ID"] == case_id, col] = 1 if checkbox_vars[col].get() else ""
    df.loc[df["Case ID"] == case_id, "Notes"] = notes_text.get("1.0", tk.END).strip()
    # Update "Case Done" status.
    df.loc[df["Case ID"] == case_id, "Case Done"] = 1 if case_done_var.get() else ""
    df.to_excel(EXCEL_PATH, index=False)
    unsaved_changes = False
    messagebox.showinfo("Saved", f"Saved changes for Case ID: {case_id}")
    update_progress()  # Refresh status bar.


def next_case():
    if current_index + 1 < len(case_ids) and check_unsaved():
        load_case(current_index + 1)


def prev_case():
    if current_index - 1 >= 0 and check_unsaved():
        load_case(current_index - 1)


def jump_to_case():
    try:
        target_id = int(jump_entry.get())
        if target_id in case_ids and check_unsaved():
            index = case_ids.index(target_id)
            load_case(index)
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


# Helper to mark changes as unsaved.
def mark_unsaved(*args):
    global unsaved_changes
    unsaved_changes = True


# Bind the text widget modification event.
def on_notes_modified(event):
    global unsaved_changes
    unsaved_changes = True
    # Reset modified flag so that the event fires again.
    notes_text.edit_modified(False)


# Wrap navigation functions to check for unsaved changes.
def check_unsaved():
    global unsaved_changes
    if unsaved_changes and unsaved_warning:
        result = messagebox.askyesnocancel(
            "Unsaved Changes", "You have unsaved changes. Would you like to save them?"
        )
        if result is None:  # Cancelled
            return False
        elif result:  # Yes, save changes.
            save_case()
    # Either there were no unsaved changes or user opted not to save.
    return True


# Override window close to warn about unsaved changes.
def on_closing():
    if check_unsaved():
        root.destroy()


def update_progress():
    # Calculate how many cases are marked done.
    done_count = (df["Case Done"] == 1).sum()
    total = len(df)
    progress_bar["maximum"] = total
    progress_bar["value"] = done_count
    status_label.config(text=f"Cases Done: {done_count} / {total}")


def copy_case_id(event):
    # Remove the "Case ID: " prefix and copy the raw ID.
    case_id_text = case_label_var.get().replace("Case ID: ", "")
    root.clipboard_clear()
    root.clipboard_append(case_id_text)
    # messagebox.showinfo("Copied", f"Case ID {case_id_text} copied to clipboard")


# --- Settings Dialog ---
def open_settings():
    settings = tk.Toplevel(root)
    settings.title("Settings")
    settings.grab_set()  # Make the dialog modal

    # Excel Path
    tk.Label(settings, text="Excel Path:").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )
    excel_path_var = tk.StringVar(value=EXCEL_PATH)
    tk.Entry(settings, textvariable=excel_path_var, width=40).grid(
        row=0, column=1, padx=5, pady=5
    )

    # PDF Folder
    tk.Label(settings, text="PDF Folder:").grid(
        row=1, column=0, sticky="w", padx=5, pady=5
    )
    pdf_folder_var = tk.StringVar(value=PDF_FOLDER)
    tk.Entry(settings, textvariable=pdf_folder_var, width=40).grid(
        row=1, column=1, padx=5, pady=5
    )

    # TXT Folder
    tk.Label(settings, text="TXT Folder:").grid(
        row=2, column=0, sticky="w", padx=5, pady=5
    )
    txt_folder_var = tk.StringVar(value=TXT_FOLDER)
    tk.Entry(settings, textvariable=txt_folder_var, width=40).grid(
        row=2, column=1, padx=5, pady=5
    )

    # Unsaved Changes Warning Option
    unsaved_warning_var = tk.BooleanVar(value=unsaved_warning)
    tk.Checkbutton(
        settings, text="Enable Unsaved Changes Warning", variable=unsaved_warning_var
    ).grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    # Theme Selection
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
        global EXCEL_PATH, PDF_FOLDER, TXT_FOLDER, unsaved_warning, default_theme
        EXCEL_PATH = excel_path_var.get()
        PDF_FOLDER = pdf_folder_var.get()
        TXT_FOLDER = txt_folder_var.get()
        unsaved_warning = unsaved_warning_var.get()
        default_theme = theme_var.get()
        theme_combobox.set(default_theme)
        change_theme(None)  # update theme based on default_theme
        settings.destroy()
        messagebox.showinfo(
            "Settings", "Settings updated. Please restart the application if necessary."
        )

    tk.Button(settings, text="Save Settings", command=save_settings).grid(
        row=5, column=0, columnspan=2, pady=10
    )


# Add an Options menu to open the settings dialog.
menubar = tk.Menu(root)
options_menu = tk.Menu(menubar, tearoff=0)
options_menu.add_command(label="Settings", command=open_settings)
menubar.add_cascade(label="Options", menu=options_menu)
root.config(menu=menubar)

# === GUI Layout ===

# Top frame containing the case label and theme selector
top_frame = ttk.Frame(root, padding=10)
top_frame.pack(pady=10, fill=tk.X)

case_label_var = tk.StringVar()
case_label = ttk.Label(top_frame, textvariable=case_label_var, font=("Arial", 14))
case_label.pack(side=tk.LEFT, padx=(0, 20))
case_label.bind("<Button-1>", copy_case_id)

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

# After creating the navigation buttons:
prev_btn = ttk.Button(nav_frame, text="<< Previous", command=prev_case)
prev_btn.pack(side=tk.LEFT, padx=5)
ToolTip(prev_btn, "Go to the previous case.")

next_btn = ttk.Button(nav_frame, text="Next >>", command=next_case)
next_btn.pack(side=tk.LEFT, padx=5)
ToolTip(next_btn, "Go to the next case.")

jump_frame = ttk.Frame(root, padding=5)
jump_frame.pack(pady=5)

jump_entry = ttk.Entry(jump_frame, width=10)
jump_entry.pack(side=tk.LEFT, padx=(0, 5))

jump_btn = ttk.Button(jump_frame, text="Jump to Case ID", command=jump_to_case)
jump_btn.pack(side=tk.LEFT)
ToolTip(jump_btn, "Jump to a specific Case ID.")

# File Buttons
file_frame = ttk.Frame(root, padding=5)
file_frame.pack(pady=5)

# For the File button:
files_btn = ttk.Button(file_frame, text="Open Files", command=open_files)
files_btn.pack(side=tk.LEFT, padx=5)
ToolTip(files_btn, "Open associated PDF and TXT files.")

# --- GUI Layout Additions ---

# Add a Status/Progress Bar at the bottom.
status_frame = ttk.Frame(root, padding=5)
status_frame.pack(pady=5, fill=tk.X)
progress_bar = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate")
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
status_label = ttk.Label(status_frame, text=f"Cases Done: 0 / {df.shape[0]}")
status_label.pack(side=tk.LEFT)

# After the File Buttons section, add a frame for the "Case Done" checkbox.
case_done_frame = ttk.Frame(root, padding=5)
case_done_frame.pack(pady=5)

# Frame to hold both Case Done checkbox and Save button
bottom_controls_frame = ttk.Frame(root)
bottom_controls_frame.pack(pady=10)

# "Case Done" Checkbox
case_done_checkbox = ttk.Checkbutton(
    bottom_controls_frame, text="Case Done", variable=case_done_var
)
case_done_checkbox.pack(side=tk.LEFT, padx=10)

# Save Button
save_button = ttk.Button(bottom_controls_frame, text="Save", command=save_case)
save_button.pack(side=tk.LEFT, padx=10)

# For the Save button:
ToolTip(save_button, "Save current case edits.")

# For the case label, which copies the case ID when clicked:
ToolTip(case_label, "Click to copy the Case ID.")

# Checkboxes grid
checkbox_frame = ttk.Frame(root, padding=10)
checkbox_frame.pack(pady=10)

columns = [col for col in df.columns if col not in ["Case ID", "Notes"]]
for i, col in enumerate(columns):
    if col == "Case Done":
        continue
    var = tk.IntVar()
    var.trace_add("write", mark_unsaved)

    # Create a frame to wrap the checkbutton
    wrapper = ttk.Frame(checkbox_frame, padding=5)
    wrapper.grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=4)

    cb = ttk.Checkbutton(wrapper, text=col, variable=var)
    cb.pack(anchor="w")  # Pack inside the frame
    checkbox_vars[col] = var
    checkbox_widgets[col] = cb

    # Make the frame clickable as well
    def toggle_cb(event, v=var):
        v.set(0 if v.get() else 1)

    wrapper.bind("<Button-1>", toggle_cb)
    cb.bind("<Button-1>", lambda e: None)  # Prevent double toggle on checkbox itself

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

# Bind the <<Modified>> event to the notes text widget.
notes_text.bind("<<Modified>>", on_notes_modified)

# --- Keyboard Shortcuts ---
root.bind("<Left>", lambda event: prev_case())
root.bind("<Right>", lambda event: next_case())
root.bind("<Control-s>", lambda event: save_case())

# Attach WM_DELETE_WINDOW protocol to warn on closing.
root.protocol("WM_DELETE_WINDOW", on_closing)

# === Start ===
load_case(current_index)
root.mainloop()
