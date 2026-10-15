# ErrDay

A simple desktop planner built with Python and Tkinter.

## Features
- Today, Week, and Month calendar views
- Task creation, editing, and deletion
- Task priorities and due-date reminders
- Windows task notifications
- Focus timer with tracked focus sessions
- System tray support
- Automatic database backup

## How to Run
1. Extract the entire ErrDay folder from the ZIP file.
2. Keep `ErrDay.exe`, `errday_icon.ico`, and `_internal` together.
3. Double-click `ErrDay.exe` to launch the application.

Do not run the application directly from inside the ZIP file.

## Data Storage
Task data and focus-session records are stored in `errday.db` in the application folder.

A backup database, `errday_backup.db`, is also created in the same folder.

These database files are created when the application runs for the first time. Keep them if you want to preserve your data.

## Important
- Do not delete the database files while ErrDay is running.
- Keep the application folder in a location where you have permission to create and modify files.
- If moving ErrDay to another computer, copy the database files separately if you want to transfer your existing data.