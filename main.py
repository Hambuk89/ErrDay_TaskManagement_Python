
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import date, datetime, timedelta
import calendar
import sqlite3
import os

# ---------------- SETTINGS ----------------
BG = "#F4F6FA"
WHITE = "#FFFFFF"
TEXT = "#202938"
MUTED = "#778196"
BLUE = "#3478F6"
BORDER = "#E1E7F0"
GREEN = "#15966A"


CATEGORY_STYLES = {
    "Study": {
        "accent": "#3478F6",
        "background": "#E8F0FF",
        "text": "#245BCC",
    },
    "Assignment": {
        "accent": "#9333EA",
        "background": "#F3E8FF",
        "text": "#7E22CE",
    },
    "Personal": {
        "accent": "#0D9488",
        "background": "#CCFBF1",
        "text": "#0F766E",
    },
    "Work": {
        "accent": "#EA8A16",
        "background": "#FFF0D9",
        "text": "#B45309",
    },
}


root = tk.Tk()
root.title("ErrDay")
root.geometry("1440x1024")
root.minsize(800, 600)
root.configure(bg=BG)

today = date.today()
selected_date = today
view = "Today"


# ---------------- DATABASE ----------------

APP_DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "ErrDay"
)

os.makedirs(APP_DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(APP_DATA_DIR, "errday.db")


def init_database():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                task_date TEXT NOT NULL,
                task_time TEXT NOT NULL DEFAULT '',
                due_date TEXT NOT NULL DEFAULT '',
                done INTEGER NOT NULL DEFAULT 0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_title TEXT NOT NULL,
                session_date TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL
            )
        """)



def load_tasks():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT title, category, task_date,
                   task_time, due_date, done
            FROM tasks
            ORDER BY task_date, task_time, id
        """).fetchall()

    return [
        {
            "title": row[0],
            "category": row[1],
            "date": row[2],
            "time": row[3],
            "due": row[4],
            "done": bool(row[5]),
        }
        for row in rows
    ]


def save_tasks():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM tasks")

        conn.executemany("""
            INSERT INTO tasks
                (title, category, task_date, task_time, due_date, done)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (
                task["title"],
                task["category"],
                task["date"],
                task["time"],
                task["due"],
                int(task["done"]),
            )
            for task in tasks
        ])

def get_focus_seconds_for_day(day):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT COALESCE(SUM(duration_seconds), 0)
            FROM focus_sessions
            WHERE session_date = ?
        """, (day,)).fetchone()

    return row[0]


def get_focus_seconds_for_week(monday):
    sunday = monday + timedelta(days=6)

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT session_date, SUM(duration_seconds)
            FROM focus_sessions
            WHERE session_date BETWEEN ? AND ?
            GROUP BY session_date
        """, (
            monday.isoformat(),
            sunday.isoformat(),
        )).fetchall()

    focus_by_day = {
        (monday + timedelta(days=i)).isoformat(): 0
        for i in range(7)
    }

    for session_date, seconds in rows:
        focus_by_day[session_date] = seconds

    return focus_by_day


def format_focus_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60

    if hours:
        return f"{hours} hr {minutes} min"

    return f"{minutes} min"



init_database()
tasks = load_tasks()


remaining = 25 * 60
timer_running = False
timer_job = None
mini_window = None
mini_timer_label = None
mini_task_label = None
month_offset = 0

# ---------------- HELPERS ----------------

def styled_button(parent, text, command, primary=False):
    return tk.Button(
        parent, text=text, command=command,
        font=("Segoe UI", 10, "bold" if primary else "normal"),
        bg=BLUE if primary else WHITE,
        fg=WHITE if primary else TEXT,
        activebackground=BLUE if primary else "#EDF1F7",
        activeforeground=WHITE if primary else TEXT,
        relief="flat", bd=0, cursor="hand2",
        padx=14, pady=9
    )


# ---------------- GLOBAL MOUSE WHEEL SCROLL ----------------

def on_mousewheel(event):
    widget = root.winfo_containing(event.x_root, event.y_root)

    # Find the scrollable Canvas containing the mouse pointer
    while widget is not None:
        if isinstance(widget, tk.Canvas):
            if getattr(event, "num", None) == 4:
                direction = -1
                amount = 1
            elif getattr(event, "num", None) == 5:
                direction = 1
                amount = 1
            else:
                delta = event.delta
                if delta == 0:
                    return

                direction = -1 if delta > 0 else 1
                amount = max(1, abs(delta) // 120)

            widget.yview_scroll(direction * amount, "units")
            return "break"

        widget = getattr(widget, "master", None)


# Windows mouse wheel
root.bind_all("<MouseWheel>", on_mousewheel)

# Linux mouse wheel compatibility
root.bind_all("<Button-4>", on_mousewheel)
root.bind_all("<Button-5>", on_mousewheel)


def task_count_for(day):
    day_tasks = [t for t in tasks if t["date"] == day.isoformat()]
    done = sum(t["done"] for t in day_tasks)
    return len(day_tasks), done


def card(parent, padding=14):
    return tk.Frame(
        parent, bg=WHITE, padx=padding, pady=padding,
        highlightbackground=BORDER, highlightthickness=1
    )


def clear_content():
    for widget in content.winfo_children():
        widget.destroy()


# ---------------- HEADER ----------------
header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=26, pady=(22, 12))

tk.Label(
    header, text="ErrDay",
    font=("Segoe UI", 23, "bold"), bg=BG, fg=TEXT
).pack(side="left")

tk.Label(
    header, text="집중해라, 오늘도, 집중하자!!!",
    font=("Segoe UI", 10), bg=BG, fg=MUTED
).pack(side="right", pady=10)

# ---------------- NAVIGATION ----------------
nav = tk.Frame(root, bg=BG)
nav.pack(fill="x", padx=26, pady=(0, 16))

nav_buttons = {}

def change_view(new_view):
    global view
    view = new_view
    render()

for name in ("Today", "Week", "Month"):
    btn = tk.Button(
        nav, text=name,
        command=lambda n=name: change_view(n),
        font=("Segoe UI", 10, "bold"),
        relief="flat", bd=0, padx=18, pady=9,
        cursor="hand2"
    )
    btn.pack(side="left", padx=(0, 7))
    nav_buttons[name] = btn

styled_button(nav, "+ Add Task", lambda: open_add_task(), True).pack(side="right")

# ---------------- MAIN CONTENT ----------------
content = tk.Frame(root, bg=BG)
content.pack(fill="both", expand=True, padx=26)

# ---------------- TIMER ----------------
timer_bar = card(root, 12)
timer_bar.pack(fill="x", padx=26, pady=16)

timer_info = tk.Frame(timer_bar, bg=WHITE)
timer_info.pack(side="left", fill="x", expand=True)

tk.Label(
    timer_info, text="FOCUS TIMER",
    font=("Segoe UI", 9, "bold"), bg=WHITE, fg=MUTED
).pack(anchor="w")

timer_label = tk.Label(
    timer_info, text="25:00",
    font=("Segoe UI", 21, "bold"), bg=WHITE, fg=BLUE
)
timer_label.pack(anchor="w")

timer_buttons = tk.Frame(timer_bar, bg=WHITE)
timer_buttons.pack(side="right")

# ---------------- TASK ACTIONS ----------------
def toggle_task(task):
    task["done"] = not task["done"]
    save_tasks()
    render()


def delete_task(task):
    if messagebox.askyesno("Delete task", f"Delete '{task['title']}'?"):
        tasks.remove(task)
        save_tasks()
        render()


def task_card(parent, task):
    style = CATEGORY_STYLES.get(
        task["category"],
        CATEGORY_STYLES["Study"]
    )
    
    item = tk.Frame(
        parent,
        bg=style["background"],
        padx=12,
        pady=12,
        highlightbackground=style["background"],
        highlightthickness=1
    )
    
    item.pack(fill="x", pady=5)

    top = tk.Frame(item, bg=style["background"])
    top.pack(fill="x")

    tk.Button(
        top,
        text="✓" if task["done"] else "○",
        command=lambda t=task: toggle_task(t),
        font=("Segoe UI", 13, "bold"),
        bg=style["background"], fg=GREEN if task["done"] else BLUE,
        relief="flat", bd=0, cursor="hand2"
    ).pack(side="left", padx=(0, 8))

    title_color = MUTED if task["done"] else TEXT
    title_font = ("Segoe UI", 11, "overstrike") if task["done"] else (
        "Segoe UI", 11, "bold"
    )

    tk.Label(
        top, text=task["title"],
        font=title_font, bg=style["background"], fg=title_color,
        anchor="w"
    ).pack(side="left", fill="x", expand=True)

    tk.Button(
        top, text="×", command=lambda t=task: delete_task(t),
        font=("Segoe UI", 13), bg=style["background"], fg=MUTED,
        relief="flat", bd=0, cursor="hand2"
    ).pack(side="right")

    details = tk.Frame(item, bg=style["background"])
    details.pack(fill="x", padx=(31, 0), pady=(5, 0))

    tk.Label(
        details,
        text=task["category"],
        font=("Segoe UI", 9, "bold"),
        bg=style["background"],
        fg=style["text"],
        padx=7,
        pady=3
    ).pack(side="left")

    tk.Label(
        details,
        text=f"  •  {task['time'] or 'No time set'}"
             + (f"  •  Due {task['due']}" if task["due"] else ""),
        font=("Segoe UI", 9),
        bg=style["background"],
        fg=style["text"]
    ).pack(side="left")


def empty_message(parent, text):
    tk.Label(
        parent, text=text,
        font=("Segoe UI", 10), bg=BG, fg=MUTED
    ).pack(pady=24)


# ---------------- TODAY VIEW ----------------
def render_today():
    date_text = selected_date.strftime("%A, %d %B %Y")

    top = tk.Frame(content, bg=BG)
    top.pack(fill="x", pady=(0, 12))

    left = tk.Frame(top, bg=BG)
    left.pack(side="left")

    tk.Label(
        left, text="Today's Tasks",
        font=("Segoe UI", 19, "bold"), bg=BG, fg=TEXT
    ).pack(anchor="w")

    tk.Label(
        left, text=date_text,
        font=("Segoe UI", 10), bg=BG, fg=MUTED
    ).pack(anchor="w", pady=(3, 0))

    day_tasks = [t for t in tasks if t["date"] == selected_date.isoformat()]
    completed = sum(t["done"] for t in day_tasks)

    tk.Label(
        top, text=f"{completed}/{len(day_tasks)} completed",
        font=("Segoe UI", 10), bg=BG, fg=MUTED
    ).pack(side="right", pady=12)

    if not day_tasks:
        empty_message(content, "No tasks planned for today.\nClick + Add Task to get started.")
        return

    # Two-column card layout
    grid = tk.Frame(content, bg=BG)
    grid.pack(fill="both", expand=True)

    for i, task in enumerate(sorted(day_tasks, key=lambda t: t["time"])):
        row, col = divmod(i, 2)
        grid.columnconfigure(col, weight=1)
        item = tk.Frame(grid, bg=BG)
        item.grid(row=row, column=col, sticky="ew",
                  padx=(0, 6) if col == 0 else (6, 0),
                  pady=3)
        task_card(item, task)


# ---------------- WEEK VIEW ----------------
def render_week():
    monday = selected_date - timedelta(days=selected_date.weekday())
    sunday = monday + timedelta(days=6)

    top = tk.Frame(content, bg=BG)
    top.pack(fill="x", pady=(0, 12))

    tk.Label(
        top, text="This Week",
        font=("Segoe UI", 19, "bold"), bg=BG, fg=TEXT
    ).pack(side="left")

    tk.Label(
        top, text=f"{monday:%d %b} – {sunday:%d %b}",
        font=("Segoe UI", 10), bg=BG, fg=MUTED
    ).pack(side="right", pady=8)

    # Scrollable week list
    canvas = tk.Canvas(content, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(content, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)

    inner.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.bind(
        "<Configure>",
        lambda e: canvas.itemconfigure(canvas_window, width=e.width)
    )

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    
    # ---------------- WEEKLY FOCUS STATISTICS ----------------
    focus_by_day = get_focus_seconds_for_week(monday)
    week_total_seconds = sum(focus_by_day.values())

    focus_section = card(inner, 12)
    focus_section.pack(fill="x", pady=4, padx=2)

    tk.Label(
        focus_section,
        text="Focus This Week",
        font=("Segoe UI", 14, "bold"),
        bg=WHITE,
        fg=TEXT,
    ).pack(anchor="w")

    tk.Label(
        focus_section,
        text=f"Total: {format_focus_duration(week_total_seconds)}",
        font=("Segoe UI", 11, "bold"),
        bg=WHITE,
        fg=BLUE,
    ).pack(anchor="w", pady=(4, 12))

    max_daily_seconds = max(
        max(focus_by_day.values()),
        1,
    )

    for offset in range(7):
        day = monday + timedelta(days=offset)
        seconds = focus_by_day[day.isoformat()]

        row = tk.Frame(focus_section, bg=WHITE)
        row.pack(fill="x", pady=3)

        tk.Label(
            row,
            text=day.strftime("%a"),
            width=5,
            anchor="w",
            font=("Segoe UI", 9),
            bg=WHITE,
            fg=TEXT,
        ).pack(side="left")

        progress = ttk.Progressbar(
            row,
            mode="determinate",
            maximum=max_daily_seconds,
            value=seconds,
        )
        progress.pack(
            side="left",
            fill="x",
            expand=True,
            padx=8,
        )

        tk.Label(
            row,
            text=format_focus_duration(seconds),
            width=13,
            anchor="e",
            font=("Segoe UI", 9),
            bg=WHITE,
            fg=MUTED,
        ).pack(side="right")


    for offset in range(7):
        day = monday + timedelta(days=offset)
        day_tasks = [t for t in tasks if t["date"] == day.isoformat()]

        section = card(inner, 10)
        section.pack(fill="x", pady=4, padx=2)

        heading = tk.Frame(section, bg=WHITE)
        heading.pack(fill="x")

        tk.Label(
            heading, text=day.strftime("%A, %d %b"),
            font=("Segoe UI", 11, "bold"), bg=WHITE, fg=TEXT
        ).pack(side="left")

        tk.Label(
            heading, text=f"{len(day_tasks)} tasks",
            font=("Segoe UI", 9), bg=WHITE, fg=MUTED
        ).pack(side="right")

        if day_tasks:
            for task in sorted(day_tasks, key=lambda t: t["time"]):
                task_card(section, task)
        else:
            tk.Label(
                section, text="No tasks planned",
                font=("Segoe UI", 9), bg=WHITE, fg=MUTED
            ).pack(anchor="w", pady=(8, 0))


# ---------------- MONTH VIEW ----------------
def render_month():
    year = today.year
    month = today.month + month_offset

    while month > 12:
        year += 1
        month -= 12
    while month < 1:
        year -= 1
        month += 12

    top = tk.Frame(content, bg=BG)
    top.pack(fill="x", pady=(0, 12))

    
    # Fixed-width month navigation
    month_controls = tk.Frame(top, bg=BG)
    month_controls.pack(anchor="center")

    month_controls.grid_columnconfigure(1, minsize=220)

    styled_button(
        month_controls,
        "‹",
        lambda: shift_month(-1),
    ).grid(row=0, column=0, sticky="ew")

    tk.Label(
        month_controls,
        text=f"{calendar.month_name[month]} {year}",
        font=("Segoe UI", 19, "bold"),
        bg=BG,
        fg=TEXT,
        width=18,
        anchor="center",
    ).grid(row=0, column=1, padx=14)

    styled_button(
        month_controls,
        "›",
        lambda: shift_month(1),
    ).grid(row=0, column=2, sticky="ew")


    month_grid = tk.Frame(content, bg=BG)
    month_grid.pack(fill="both", expand=True)

    for col, name in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
        month_grid.columnconfigure(col, weight=1)

        tk.Label(
            month_grid, text=name,
            font=("Segoe UI", 9, "bold"), bg=BG, fg=MUTED
        ).grid(row=0, column=col, sticky="ew", pady=(0, 7))

    weeks = calendar.monthcalendar(year, month)

    for row, week in enumerate(weeks, start=1):
        month_grid.rowconfigure(row, weight=1)

        for col, day_num in enumerate(week):
            cell = tk.Frame(
                month_grid, bg=WHITE,
                highlightbackground=BORDER, highlightthickness=1
            )
            cell.grid(
                row=row, column=col, sticky="nsew",
                padx=2, pady=2
            )

            if day_num == 0:
                continue

            day = date(year, month, day_num)
            day_tasks = [t for t in tasks if t["date"] == day.isoformat()]

            day_button = tk.Button(
                cell, text=str(day_num),
                command=lambda d=day: select_calendar_day(d),
                font=("Segoe UI", 10, "bold" if day == today else "normal"),
                bg=WHITE, fg=BLUE if day == today else TEXT,
                activebackground="#EAF1FF",
                relief="flat", bd=0, cursor="hand2"
            )
            day_button.pack(anchor="nw", padx=4, pady=3)

            for task in day_tasks[:2]:
                tk.Label(
                    cell, text="• " + task["title"][:15],
                    font=("Segoe UI", 8),
                    bg=WHITE, fg=GREEN if task["done"] else BLUE,
                    anchor="w"
                ).pack(fill="x", padx=4)

            if len(day_tasks) > 2:
                tk.Label(
                    cell, text=f"+{len(day_tasks)-2} more",
                    font=("Segoe UI", 8), bg=WHITE, fg=MUTED
                ).pack(anchor="w", padx=4)


def shift_month(amount):
    global month_offset
    month_offset += amount
    render()


def select_calendar_day(day):
    global selected_date, view
    selected_date = day
    view = "Today"
    render()


# ---------------- ADD TASK WINDOW ----------------
def open_add_task():
    dialog = tk.Toplevel(root)
    dialog.title("Add Task")
    dialog.geometry("560x680")
    dialog.minsize(440, 560)
    dialog.resizable(False, False)
    dialog.configure(bg=WHITE)
    dialog.transient(root)
    dialog.grab_set()

    tk.Label(
        dialog, text="Add a Task",
        font=("Segoe UI", 18, "bold"), bg=WHITE, fg=TEXT
    ).pack(anchor="w", padx=24, pady=(22, 16))

    fields = tk.Frame(dialog, bg=WHITE)
    fields.pack(fill="both", expand=True, padx=24, pady=(0, 5))

    def add_field(label, default=""):
        tk.Label(
            fields, text=label, font=("Segoe UI", 9, "bold"),
            bg=WHITE, fg=MUTED
        ).pack(anchor="w", pady=(3, 2))

        entry = tk.Entry(
            fields, font=("Segoe UI", 10), relief="solid", bd=1
        )
        entry.pack(fill="x", ipady=6)
        entry.insert(0, default)
        return entry

    title_entry = add_field("Task name")
    category_box = ttk.Combobox(
        fields, values=("Study", "Assignment", "Personal", "Work"),
        state="readonly", font=("Segoe UI", 10)
    )
    category_box.set("Study")

    tk.Label(
        fields, text="Category", font=("Segoe UI", 9, "bold"),
        bg=WHITE, fg=MUTED
    ).pack(anchor="w", pady=(10, 4))
    category_box.pack(fill="x")

    tk.Label(
        fields,
        text="Scheduled Date",
        font=("Segoe UI", 9, "bold"),
        bg=WHITE,
        fg=MUTED,
    ).pack(anchor="w", pady=(5, 4))

    date_entry = DateEntry(
        fields,
        width=18,
        date_pattern="yyyy-mm-dd",
        font=("Segoe UI", 10),
        background="#3478F6",
        foreground="white",
        borderwidth=1,
    )
    date_entry.set_date(selected_date)
    date_entry.pack(fill="x", ipady=4)

    time_entry = add_field("Start time (e.g. 19:00)")

    tk.Label(
        fields,
        text="Due Date (optional)",
        font=("Segoe UI", 9, "bold"),
        bg=WHITE,
        fg=MUTED,
    ).pack(anchor="w", pady=(5, 4))

    due_frame = tk.Frame(fields, bg=WHITE)
    due_frame.pack(fill="x")

    due_entry = DateEntry(
        due_frame,
        width=18,
        date_pattern="yyyy-mm-dd",
        font=("Segoe UI", 10),
        background="#3478F6",
        foreground="white",
        borderwidth=1,
    )
    due_entry.pack(side="left", fill="x", expand=True, ipady=4)
    due_entry.set_date(selected_date)
    due_enabled = tk.BooleanVar(value=False)
    
    def toggle_due_date():
        due_entry.configure(
            state="normal" if due_enabled.get() else "disabled"
        )
    
    tk.Checkbutton(
        due_frame,
        text="Set due date",
        variable=due_enabled,
        command=toggle_due_date,
        bg=WHITE,
        fg=TEXT,
        font=("Segoe UI", 9),
        activebackground=WHITE,
    ).pack(side="left", padx=(8, 0))  
    
    due_entry.configure(state="disabled")

    def save_task():
        title = title_entry.get().strip()
        task_date = date_entry.get_date().isoformat()
        task_time = time_entry.get().strip()
        due = due_entry.get_date().isoformat() if due_enabled.get() else ""

        if not title:
            messagebox.showwarning("Missing task", "Enter a task name.", parent=dialog)
            return

        try:
            if task_time:
                datetime.strptime(task_time, "%H:%M")
        except ValueError:
            messagebox.showwarning(
                "Invalid time",
                "Use HH:MM for the start time, e.g. 19:00.",
                parent=dialog
            )
            return

        tasks.append({
            "title": title,
            "category": category_box.get(),
            "date": task_date,
            "time": task_time,
            "due": due,
            "done": False,
        })

        save_tasks()

        global selected_date
        selected_date = date.fromisoformat(task_date)

        dialog.destroy()
        render()

    styled_button(dialog, "Save Task", save_task, True).pack(
        fill="x", padx=24, pady=(10, 16), side="bottom"
    )


# ---------------- FOCUS TIMER ----------------
import time

remaining = 25 * 60
timer_running = False
timer_job = None
end_time = None
focus_started_at = None
total_focus_seconds = get_focus_seconds_for_day(
    date.today().isoformat()
)

focus_task_at_start = "General focus"
focus_date_at_start = date.today().isoformat()

# Task selector
tk.Label(
    timer_info,
    text="Focus task",
    font=("Segoe UI", 9),
    bg=WHITE,
    fg=MUTED,
).pack(anchor="w", pady=(8, 2))

timer_task_box = ttk.Combobox(
    timer_info,
    state="readonly",
    width=28,
    font=("Segoe UI", 10),
)
timer_task_box.pack(anchor="w", pady=(0, 5))


def refresh_timer_task_options():
    titles = [t["title"] for t in tasks if not t["done"]]
    timer_task_box["values"] = titles

    if timer_task_box.get() not in titles:
        timer_task_box.set(titles[0] if titles else "")


def update_focus_total():
    minutes = total_focus_seconds // 60
    focus_total_label.config(
        text=f"Today's tracked focus: {minutes} min"
    )


focus_total_label = tk.Label(
    timer_info,
    text="Today's tracked focus: 0 min",
    font=("Segoe UI", 9),
    bg=WHITE,
    fg=MUTED,
)
focus_total_label.pack(anchor="w", pady=(2, 0))



def update_timer_display():
    global mini_timer_label, mini_task_label

    minutes = remaining // 60
    seconds = remaining % 60
    time_text = f"{minutes:02d}:{seconds:02d}"

    # Update the main window
    timer_label.config(text=time_text)

    # Update the floating focus window
    if mini_window is not None and mini_window.winfo_exists():
        if mini_timer_label is not None:
            mini_timer_label.config(text=time_text)

        if mini_task_label is not None:
            mini_task_label.config(
                text=timer_task_box.get() or "General focus"
            )



def commit_focus_time():
    global focus_started_at, total_focus_seconds

    if focus_started_at is not None:
        elapsed = max(
            0, int(time.monotonic() - focus_started_at)
        )

        if elapsed > 0:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    INSERT INTO focus_sessions (
                        task_title,
                        session_date,
                        duration_seconds
                    )
                    VALUES (?, ?, ?)
                """, (
                    focus_task_at_start,
                    focus_date_at_start,
                    elapsed,
                ))

            total_focus_seconds += elapsed

        focus_started_at = None
        update_focus_total()



def timer_tick():
    global remaining, timer_running, timer_job

    timer_job = None

    if not timer_running or end_time is None:
        return

    remaining = max(0, int(end_time - time.monotonic() + 0.999))
    update_timer_display()

    if remaining <= 0:
        timer_running = False
        commit_focus_time()
        root.bell()
        messagebox.showinfo(
            "EVERYDAY",
            f"Focus session complete!\n"
            f"Task: {timer_task_box.get() or 'General focus'}",
        )
        return

    timer_job = root.after(250, timer_tick)


def start_timer():
    global timer_running, timer_job, end_time
    global focus_started_at
    global focus_task_at_start, focus_date_at_start

    if timer_running:
        return

    if remaining <= 0:
        messagebox.showinfo("EVERYDAY", "Reset the timer first.")
        return

    timer_running = True
    end_time = time.monotonic() + remaining
    focus_started_at = time.monotonic()

    focus_task_at_start = (
        timer_task_box.get() or "General focus"
    )
    focus_date_at_start = date.today().isoformat()
    
    if timer_job is not None:
        root.after_cancel(timer_job)

    timer_job = root.after(100, timer_tick)


def pause_timer():
    global timer_running, timer_job, remaining, end_time

    if not timer_running:
        return

    remaining = max(
        0, int(end_time - time.monotonic() + 0.999)
    )
    timer_running = False
    end_time = None

    if timer_job is not None:
        root.after_cancel(timer_job)
        timer_job = None

    commit_focus_time()
    update_timer_display()


def reset_timer():
    global remaining, timer_running, timer_job, end_time

    if timer_running:
        pause_timer()

    timer_running = False
    end_time = None
    remaining = 25 * 60

    if timer_job is not None:
        root.after_cancel(timer_job)
        timer_job = None

    update_timer_display()


def open_mini_focus():
    global mini_window, mini_timer_label, mini_task_label

    # Reuse the existing floating window if it is open
    if mini_window is not None and mini_window.winfo_exists():
        mini_window.deiconify()
        mini_window.lift()
        return

    mini_window = tk.Toplevel(root)
    mini_window.title("EVERYDAY - Focus")
    mini_window.geometry("360x250")
    mini_window.minsize(280, 220)
    mini_window.resizable(True, True)
    mini_window.configure(bg=BG)

    # Keep the window above other windows if requested
    always_on_top = tk.BooleanVar(value=False)

    container = tk.Frame(mini_window, bg=BG, padx=16, pady=12)
    container.pack(fill="both", expand=True)

    tk.Label(
        container,
        text="EVERYDAY  /  FOCUS",
        font=("Segoe UI", 9, "bold"),
        bg=BG,
        fg=MUTED,
    ).pack(anchor="w")

    mini_task_label = tk.Label(
        container,
        text=timer_task_box.get() or "General focus",
        font=("Segoe UI", 13, "bold"),
        bg=BG,
        fg=TEXT,
        anchor="w",
    )
    mini_task_label.pack(fill="x", pady=(10, 2))

    mini_timer_label = tk.Label(
        container,
        text="25:00",
        font=("Segoe UI", 30, "bold"),
        bg=BG,
        fg=BLUE,
    )
    mini_timer_label.pack(pady=8)

    controls = tk.Frame(container, bg=BG)
    controls.pack()

    styled_button(
        controls, "Start", start_timer, True
    ).pack(side="left", padx=3)

    styled_button(
        controls, "Pause", pause_timer
    ).pack(side="left", padx=3)

    styled_button(
        controls, "Reset", reset_timer
    ).pack(side="left", padx=3)

    def restore_full_app():
        root.deiconify()
        root.lift()
        root.focus_force()
    
    styled_button(
        container,
        "Full App",
        restore_full_app,
    ).pack(fill="x", pady=(8, 0))


    tk.Checkbutton(
        container,
        text="Always on top",
        variable=always_on_top,
        command=lambda: mini_window.attributes(
            "-topmost", always_on_top.get()
        ),
        bg=BG,
        fg=MUTED,
        activebackground=BG,
        font=("Segoe UI", 9),
    ).pack(anchor="w", pady=(8, 0))

    def close_mini_focus():
        global mini_window, mini_timer_label, mini_task_label

        mini_window.destroy()
        mini_window = None
        mini_timer_label = None
        mini_task_label = None

    mini_window.protocol("WM_DELETE_WINDOW", close_mini_focus)

    update_timer_display()

    # Show Mini Focus and minimize the main window
    mini_window.deiconify()
    mini_window.lift()
    root.iconify()


def set_timer_minutes(minutes):
    global remaining

    if timer_running:
        messagebox.showinfo(
            "EVERYDAY",
            "Pause the timer before changing its duration.",
        )
        return

    remaining = minutes * 60
    update_timer_display()


def set_custom_timer():
    import tkinter.simpledialog as simpledialog

    minutes = simpledialog.askinteger(
        "Custom Focus Timer",
        "How many minutes would you like to focus?",
        parent=root,
        minvalue=1,
        maxvalue=600,
    )

    if minutes is not None:
        set_timer_minutes(minutes)


# Preset duration buttons
preset_frame = tk.Frame(timer_info, bg=WHITE)
preset_frame.pack(anchor="w", pady=(5, 0))

for minutes in (15, 25, 50):
    styled_button(
        preset_frame,
        f"{minutes} min",
        lambda m=minutes: set_timer_minutes(m),
    ).pack(side="left", padx=(0, 5))

styled_button(
    preset_frame,
    "Custom",
    set_custom_timer,
).pack(side="left")


styled_button(
    timer_buttons, "Start", start_timer, True
).pack(side="left", padx=3)

styled_button(
    timer_buttons, "Pause", pause_timer
).pack(side="left", padx=3)

styled_button(
    timer_buttons, "Reset", reset_timer
).pack(side="left", padx=3)

styled_button(
    timer_buttons, "Mini Focus", open_mini_focus
).pack(side="left", padx=3)


refresh_timer_task_options()
update_timer_display()
update_focus_total()


# ---------------- RENDER ----------------
def render():
    refresh_timer_task_options()

    for name, btn in nav_buttons.items():
        btn.configure(
            bg=BLUE if name == view else WHITE,
            fg=WHITE if name == view else TEXT,
            activebackground=BLUE if name == view else "#EDF1F7",
            activeforeground=WHITE if name == view else TEXT
        )

    clear_content()

    if view == "Today":
        render_today()
    elif view == "Week":
        render_week()
    else:
        render_month()


render()
root.mainloop()
