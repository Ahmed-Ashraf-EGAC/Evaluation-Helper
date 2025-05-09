import tkinter as tk
from tkinter import scrolledtext, ttk

from config import default_theme
from data import load_dataframe
from global_vars import *
from tooltip import ToolTip
from ui_functions import *


def build_ui(root):
    global notes_text, theme_combobox, case_label_var, progress_bar, status_label, jump_entry, checkbox_vars, case_done_var, main_canvas, main_frame, checkbox_canvas, checkbox_frame

    style = ttk.Style(root)
    style.theme_use(default_theme)
    create_dark_theme(style)

    # Create a main frame inside a canvas for scrolling
    main_canvas = tk.Canvas(root)
    main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add scrollbar to the canvas
    main_scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=main_canvas.yview)
    main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the canvas
    main_canvas.configure(yscrollcommand=main_scrollbar.set)

    # Create main frame inside canvas - set height to properly fill space
    main_frame = ttk.Frame(main_canvas)
    main_canvas_window = main_canvas.create_window(
        (0, 0), window=main_frame, anchor="nw", width=main_canvas.winfo_width()
    )

    # Make the frame expand to fill canvas width only
    def configure_scroll_region(event):
        # Prevent recursion by checking if we're already processing a similar event
        if (
            hasattr(configure_scroll_region, "processing")
            and configure_scroll_region.processing
        ):
            return

        try:
            configure_scroll_region.processing = True

            # Configure the scroll region to be only as tall as needed
            canvas_width = (
                event.width if hasattr(event, "width") else main_canvas.winfo_width()
            )
            main_canvas.itemconfig(main_canvas_window, width=canvas_width)

            # Update scroll region based on content
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))

            # Only show scrollbar if content height exceeds canvas height
            if main_frame.winfo_reqheight() <= main_canvas.winfo_height():
                main_scrollbar.pack_forget()
            else:
                main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        finally:
            configure_scroll_region.processing = False

    # Bind to both canvas and frame changes
    main_canvas.bind("<Configure>", configure_scroll_region)
    main_frame.bind("<Configure>", configure_scroll_region)

    # Top Frame: Case Label & Theme Selector
    top_frame = ttk.Frame(main_frame, padding=10)
    top_frame.pack(pady=10, fill=tk.X, expand=True)
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
    nav_frame = ttk.Frame(main_frame, padding=5)
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
    jump_frame = ttk.Frame(main_frame, padding=5)
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
    file_frame = ttk.Frame(main_frame, padding=5)
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
    status_frame = ttk.Frame(main_frame, padding=5)
    status_frame.pack(pady=5, fill=tk.X, expand=True)
    progress_bar = ttk.Progressbar(
        status_frame, orient="horizontal", mode="determinate"
    )
    progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    status_label = ttk.Label(
        status_frame, text=f"Cases Done: 0 / {len(load_dataframe())}"
    )
    status_label.pack(side=tk.LEFT)
    ToolTip(status_label, get_progress_message())

    update_progress(progress_bar, status_label)

    # Bottom Controls: "Case Done" Checkbox & Save Button
    case_done_var = tk.IntVar(master=root)
    bottom_frame = ttk.Frame(main_frame)
    bottom_frame.pack(pady=10)
    case_done_checkbox = ttk.Checkbutton(
        bottom_frame, text="Case Done", variable=case_done_var
    )
    case_done_checkbox.pack(side=tk.LEFT, padx=10)
    save_button = ttk.Button(
        bottom_frame,
        text="Save",
        command=lambda: save_case(
            checkbox_vars, notes_text, case_done_var, progress_bar, status_label
        ),
    )
    save_button.pack(side=tk.LEFT, padx=10)
    ToolTip(save_button, "Save current case edits.")

    # Checkboxes in a scrollable frame with fixed height
    checkbox_outer_frame = ttk.Frame(main_frame, padding=10)
    checkbox_outer_frame.pack(pady=10, fill=tk.X)

    # Create canvas with scrollbar - use 1/4 of window height instead of fixed pixels
    window_height = root.winfo_height()
    checkbox_height = max(
        150, window_height // 4
    )  # Use 1/4 of window height with minimum 150px
    checkbox_canvas = tk.Canvas(checkbox_outer_frame, height=checkbox_height)
    checkbox_scrollbar = ttk.Scrollbar(
        checkbox_outer_frame, orient=tk.VERTICAL, command=checkbox_canvas.yview
    )
    checkbox_frame = ttk.Frame(checkbox_canvas)

    # Configure scrolling
    checkbox_canvas.configure(yscrollcommand=checkbox_scrollbar.set)

    # Pack canvas and scrollbar properly
    checkbox_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    checkbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Make checkbox frame fill width of canvas - KEY FIX
    def configure_checkbox_canvas(event):
        # Prevent recursion
        if (
            hasattr(configure_checkbox_canvas, "processing")
            and configure_checkbox_canvas.processing
        ):
            return

        try:
            configure_checkbox_canvas.processing = True

            # Set the checkbox frame to be the width of the canvas
            canvas_width = event.width
            checkbox_canvas.itemconfig(checkbox_canvas_window, width=canvas_width)

            # Update the scroll region to match content height
            checkbox_canvas.configure(scrollregion=checkbox_canvas.bbox("all"))
        finally:
            configure_checkbox_canvas.processing = False

    # Create window and bind configuration
    checkbox_canvas_window = checkbox_canvas.create_window(
        (0, 0), window=checkbox_frame, anchor="nw"
    )

    # Bind canvas resize and frame changes to update scroll region
    checkbox_canvas.bind("<Configure>", configure_checkbox_canvas)
    checkbox_frame.bind(
        "<Configure>",
        lambda e: checkbox_canvas.configure(scrollregion=checkbox_canvas.bbox("all")),
    )

    # Fixed mouse wheel scrolling - check bounds
    def on_checkbox_scroll(event):
        # Get the current position and total height
        current_pos = checkbox_canvas.yview()

        # Only scroll if not at the boundaries
        if (event.delta > 0 and current_pos[0] > 0) or (
            event.delta < 0 and current_pos[1] < 1.0
        ):
            checkbox_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # Use direct bindings with the fixed scroll function
    checkbox_canvas.bind("<MouseWheel>", on_checkbox_scroll)
    checkbox_frame.bind("<MouseWheel>", on_checkbox_scroll)

    # Add checkboxes as before
    checkbox_vars = {}
    df = load_dataframe()
    columns = [
        col for col in df.columns if col not in ["Case ID", "Notes", "Case Done"]
    ]

    # Calculate how many columns to use based on window width
    # Default to 4 columns
    num_columns = 4

    # Configure the grid for centering - KEY FIX
    for i in range(num_columns):
        checkbox_frame.columnconfigure(i, weight=1, uniform="checkbox_col")

    # Add checkboxes with proper grid positioning
    for i, col in enumerate(columns):
        var = tk.IntVar(master=root)
        var.trace_add("write", mark_unsaved)
        # Create wrapper frame for each checkbox with proper grid settings
        wrapper = ttk.Frame(checkbox_frame, padding=5)
        wrapper.grid(
            row=i // num_columns,
            column=i % num_columns,
            sticky="w",  # Align checkbox left within cell
            padx=10,
            pady=4,
        )
        cb = ttk.Checkbutton(wrapper, text=col, variable=var)
        cb.pack(anchor="w")
        checkbox_vars[col] = var

    # Notes Area that fills remaining window space - key modifications here
    notes_frame = ttk.Frame(
        main_frame, padding=(10, 10, 10, 0)
    )  # Remove bottom padding
    notes_frame.pack(pady=(10, 0), fill=tk.BOTH, expand=True)  # Remove bottom padding
    ttk.Label(notes_frame, text="Notes:").pack(anchor="w")

    # Create ScrolledText with a weight to make it expand more aggressively
    notes_text = scrolledtext.ScrolledText(
        notes_frame,
        wrap=tk.WORD,
        width=60,
        height=15,
        undo=True,  # Increased height more
    )
    notes_text.pack(
        fill=tk.BOTH, expand=True, padx=0, pady=(5, 0)
    )  # Remove bottom padding

    # Configure text appearance based on theme
    if theme_combobox.get() == "dark":
        notes_text.configure(bg="#3e3e3e", fg="#ffffff", insertbackground="#ffffff")
    else:
        notes_text.configure(bg="white", fg="black", insertbackground="black")

    # Keyboard Shortcuts
    root.bind(
        "<Control-Shift-Left>",
        lambda event: prev_case(
            lambda i: load_case(
                i, case_label_var, notes_text, checkbox_vars, case_done_var
            )
        ),
    )
    root.bind(
        "<Control-Shift-Right>",
        lambda event: next_case(
            lambda i: load_case(
                i, case_label_var, notes_text, checkbox_vars, case_done_var
            )
        ),
    )
    root.bind(
        "<Control-s>",
        lambda event: save_case(
            checkbox_vars, notes_text, case_done_var, progress_bar, status_label
        ),
    )


def _on_mousewheel_universal(event, main_frame=None):
    """Universal mouse wheel handler that finds the widget under cursor"""
    widget = event.widget

    # Find the canvas the mouse is over
    x, y = event.x_root, event.y_root
    widget_under_mouse = widget.winfo_containing(x, y)

    # First check if mouse is over the checkbox canvas specifically
    if "checkbox_canvas" in globals() and "checkbox_frame" in globals():
        checkbox_canvas = globals()["checkbox_canvas"]

        # Check if mouse is over the checkbox canvas or its children
        parent = widget_under_mouse
        while parent:
            if parent == checkbox_canvas or parent == globals()["checkbox_frame"]:
                # Only scroll if content exceeds visible area
                if checkbox_canvas.winfo_height() < checkbox_canvas.bbox("all")[3]:
                    checkbox_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return  # Exit early in any case to prevent scrolling main canvas
            try:
                parent = parent.master
            except:
                break

    # Then check main canvas - only if content actually overflows
    if "main_canvas" in globals() and "main_frame" in globals():
        main_canvas = globals()["main_canvas"]
        main_frame = globals()["main_frame"]

        # Get actual required height vs visible height
        content_height = main_frame.winfo_reqheight()
        visible_height = main_canvas.winfo_height()

        # Only allow scrolling if there's actual overflow content
        if content_height > visible_height:
            # Check if mouse is over main canvas
            parent = widget_under_mouse
            while parent:
                if parent == main_canvas:
                    main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return
                try:
                    parent = parent.master
                except:
                    break


def on_window_resize(event=None):
    # Skip events from widgets other than the root window to prevent infinite recursion
    if event is None:
        return

    # Get the root window from the event
    root_window = event.widget.winfo_toplevel()

    # Skip events from widgets other than the root window
    if event.widget is not root_window:
        return

    # Prevent recursion
    if hasattr(on_window_resize, "processing") and on_window_resize.processing:
        return

    try:
        on_window_resize.processing = True

        # Resize the main canvas to fill the window
        if "main_canvas" in globals():
            main_canvas = globals()["main_canvas"]

            # Update checkbox area height to 1/4 of window height
            if "checkbox_canvas" in globals():
                checkbox_canvas = globals()["checkbox_canvas"]
                window_height = root_window.winfo_height()
                checkbox_height = max(
                    150, window_height // 4
                )  # 1/4 of window height, min 150px
                checkbox_canvas.configure(height=checkbox_height)

            # Get the notes text widget and make sure it expands properly
            if "notes_text" in globals():
                notes_widget = globals()["notes_text"]
                # Calculate available height and adjust notes height
                avail_height = root_window.winfo_height() - notes_widget.winfo_y() - 20
                if avail_height > 100:  # Ensure reasonable minimum height
                    notes_widget.configure(height=max(15, int(avail_height / 20)))

            # Use update_idletasks to process layout changes
            root_window.update_idletasks()
    finally:
        on_window_resize.processing = False


def start_app():
    root = tk.Tk()
    # Set to a larger size and allow resizing
    root.geometry("800x600")
    root.minsize(800, 600)

    # Configure the root window to give weight to rows/columns for better resizing
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    build_ui(root)

    # Window resize handler to help ensure notes area expands properly
    root.bind("<Configure>", on_window_resize, add="+")

    # After loading case, force layout update
    load_case(
        0,
        globals().get("case_label_var"),
        globals().get("notes_text"),
        globals().get("checkbox_vars"),
        globals().get("case_done_var"),
    )

    # Force a resize event after everything else is initialized
    root.update_idletasks()
    on_window_resize()  # Call once at startup

    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
    root.mainloop()
