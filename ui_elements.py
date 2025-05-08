import tkinter as tk
from tkinter import scrolledtext, ttk

from config import default_theme
from data import load_dataframe
from global_vars import *
from tooltip import ToolTip
from ui_functions import *


def build_ui(root):
    global notes_text, theme_combobox, case_label_var, progress_bar, status_label, jump_entry, checkbox_vars, case_done_var

    style = ttk.Style(root)
    style.theme_use(default_theme)
    create_dark_theme(style)

    # Top Frame: Case Label & Theme Selector
    top_frame = ttk.Frame(root, padding=10)
    top_frame.pack(pady=10, fill=tk.X)
    case_label_var = tk.StringVar()
    case_label = ttk.Label(top_frame, textvariable=case_label_var, font=("Arial", 14))
    case_label.pack(side=tk.LEFT, padx=(0, 20))
    case_label.bind("<Button-1>", lambda event: copy_case_id(case_label_var, root))
    ToolTip(case_label, "Click to copy the Case ID.")
    ttk.Label(top_frame, text="Theme:").pack(side=tk.LEFT)
    theme_combobox = ttk.Combobox(
        top_frame, values=["clam", "alt", "default", "classic", "dark"], width=10
    )
    theme_combobox.set(default_theme)
    theme_combobox.pack(side=tk.LEFT, padx=5)
    theme_combobox.bind(
        "<<ComboboxSelected>>",
        lambda event: change_theme(event, theme_combobox, style, root, notes_text),
    )

    # Now that theme_combobox is defined, set up the menu.
    menubar = tk.Menu(root)
    options_menu = tk.Menu(menubar, tearoff=0)
    options_menu.add_command(
        label="Settings", command=lambda: open_settings(root, theme_combobox)
    )
    menubar.add_cascade(label="Options", menu=options_menu)
    root.config(menu=menubar)

    # Navigation Frame
    nav_frame = ttk.Frame(root, padding=5)
    nav_frame.pack(pady=5)
    prev_btn = ttk.Button(
        nav_frame,
        text="<< Previous",
        command=lambda: prev_case(
            lambda i: load_case(
                i, case_label_var, notes_text, checkbox_vars, case_done_var
            )
        ),
    )
    prev_btn.pack(side=tk.LEFT, padx=5)
    ToolTip(prev_btn, "Go to the previous case.")
    next_btn = ttk.Button(
        nav_frame,
        text="Next >>",
        command=lambda: next_case(
            lambda i: load_case(
                i, case_label_var, notes_text, checkbox_vars, case_done_var
            )
        ),
    )
    next_btn.pack(side=tk.LEFT, padx=5)
    ToolTip(next_btn, "Go to the next case.")

    # Jump Frame
    jump_frame = ttk.Frame(root, padding=5)
    jump_frame.pack(pady=5)
    jump_entry = ttk.Entry(jump_frame, width=10)
    jump_entry.pack(side=tk.LEFT, padx=(0, 5))
    jump_btn = ttk.Button(
        jump_frame,
        text="Jump to Case ID",
        command=lambda: jump_to_case(
            jump_entry,
            lambda i: load_case(
                i, case_label_var, notes_text, checkbox_vars, case_done_var
            ),
        ),
    )
    jump_btn.pack(side=tk.LEFT)
    ToolTip(jump_btn, "Jump to a specific Case ID.")

    # File Frame
    file_frame = ttk.Frame(root, padding=5)
    file_frame.pack(pady=5)
    files_btn = ttk.Button(file_frame, text="Open Files", command=open_files)
    files_btn.pack(side=tk.LEFT, padx=5)
    ToolTip(files_btn, "Open associated PDF and TXT files.")

    # New Button to view all open (not done) cases
    open_cases_btn = ttk.Button(
        file_frame,
        text="View Open Cases",
        command=lambda: view_open_cases(
            case_label_var, notes_text, checkbox_vars, case_done_var
        ),
    )
    open_cases_btn.pack(side=tk.LEFT, padx=5)
    ToolTip(open_cases_btn, "Display a list of all cases not marked as done.")

    # Status / Progress Bar
    status_frame = ttk.Frame(root, padding=5)
    status_frame.pack(pady=5, fill=tk.X)
    progress_bar = ttk.Progressbar(
        status_frame, orient="horizontal", mode="determinate"
    )
    progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    status_label = ttk.Label(
        status_frame, text=f"Cases Done: 0 / {len(load_dataframe())}"
    )
    status_label.pack(side=tk.LEFT)

    # Bottom Controls: "Case Done" Checkbox & Save Button
    case_done_var = tk.IntVar(master=root)
    bottom_frame = ttk.Frame(root)
    bottom_frame.pack(pady=10)
    case_done_checkbox = ttk.Checkbutton(
        bottom_frame, text="Case Done", variable=case_done_var
    )
    case_done_checkbox.pack(side=tk.LEFT, padx=10)
    save_button = ttk.Button(
        bottom_frame,
        text="Save",
        command=lambda: save_case(checkbox_vars, notes_text, case_done_var),
    )
    save_button.pack(side=tk.LEFT, padx=10)
    ToolTip(save_button, "Save current case edits.")

    # Checkboxes Grid
    checkbox_vars = {}
    checkbox_frame = ttk.Frame(root, padding=10)
    checkbox_frame.pack(pady=10)
    df = load_dataframe()
    columns = [
        col for col in df.columns if col not in ["Case ID", "Notes", "Case Done"]
    ]
    for i, col in enumerate(columns):
        var = tk.IntVar(master=root)
        var.trace_add("write", mark_unsaved)
        wrapper = ttk.Frame(checkbox_frame, padding=5)
        wrapper.grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=4)
        cb = ttk.Checkbutton(wrapper, text=col, variable=var)
        cb.pack(anchor="w")
        checkbox_vars[col] = var

    # Notes Area
    notes_frame = ttk.Frame(root, padding=10)
    notes_frame.pack(pady=10, fill=tk.BOTH, expand=True)
    ttk.Label(notes_frame, text="Notes:").pack(anchor="w")
    notes_text = scrolledtext.ScrolledText(
        notes_frame, wrap=tk.WORD, width=60, height=5, undo=True
    )
    notes_text.pack(fill=tk.BOTH, expand=True)
    if theme_combobox.get() == "dark":
        notes_text.configure(bg="#3e3e3e", fg="#ffffff", insertbackground="#ffffff")
    else:
        notes_text.configure(bg="white", fg="black", insertbackground="black")
    # Bind Ctrl+Z for undo and Ctrl+Y for redo
    notes_text.bind("<Control-z>", lambda event: notes_text.edit_undo())
    notes_text.bind("<Control-y>", lambda event: notes_text.edit_redo())
    notes_text.bind("<<Modified>>", lambda event: on_notes_modified(event, notes_text))

    # Keyboard Shortcuts
    root.bind(
        "<Left>",
        lambda event: prev_case(
            lambda i: load_case(
                i, case_label_var, notes_text, checkbox_vars, case_done_var
            )
        ),
    )
    root.bind(
        "<Right>",
        lambda event: next_case(
            lambda i: load_case(
                i, case_label_var, notes_text, checkbox_vars, case_done_var
            )
        ),
    )
    root.bind(
        "<Control-s>", lambda event: save_case(checkbox_vars, notes_text, case_done_var)
    )


def start_app():
    root = tk.Tk()
    # Set to a larger size and allow resizing
    root.geometry("800x600")
    root.minsize(800, 600)
    build_ui(root)
    # Load the initial case (index 0)
    from ui_functions import load_case

    load_case(
        0,
        globals().get("case_label_var"),
        globals().get("notes_text"),
        globals().get("checkbox_vars"),
        globals().get("case_done_var"),
    )
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    root.mainloop()
