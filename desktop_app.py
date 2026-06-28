import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from config import MASTER_PROFILE_PATH
from desktop_ui_model import (
    DesktopAction,
    DesktopSettings,
    actions_by_category,
    build_output_snapshot,
    command_text,
    desktop_actions,
    read_preview_text,
)
from file_utils import read_text_file


APP_BG = "#f5f7fb"
SIDEBAR_BG = "#101828"
SIDEBAR_ACTIVE = "#1d4ed8"
PANEL_BG = "#ffffff"
TEXT = "#1f2937"
MUTED = "#667085"
ACCENT = "#2563eb"
SUCCESS = "#047857"
WARNING = "#b45309"
MISSING = "#98a2b3"


class JobHunterDesktopApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("JobHunterAI Desktop")
        self.geometry("1180x760")
        self.minsize(1060, 680)
        self.configure(bg=APP_BG)

        self.job_path_var = tk.StringVar(value="examples/sample_job.txt")
        self.output_dir_var = tk.StringVar(value="outputs/desktop-run")
        self.answers_path_var = tk.StringVar(value="profiles/application_answers.md")
        self.use_ai_var = tk.BooleanVar(value=False)
        self.use_ai_review_var = tk.BooleanVar(value=False)
        self.open_browser_var = tk.BooleanVar(value=False)
        self.active_view = tk.StringVar(value="Dashboard")
        self.command_running = False
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.visual_status_labels: dict[str, tk.Label] = {}
        self.visual_summary_label: tk.Label | None = None
        self.visual_latest_label: tk.Label | None = None
        self.visual_preview: tk.Text | None = None

        self._configure_styles()
        self._build_shell()
        self._show_view("Dashboard")
        self.after(120, self._drain_log_queue)
        self.after(1200, self._refresh_live_visual_loop)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=APP_BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("TLabel", background=APP_BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure(
            "Title.TLabel",
            background=APP_BG,
            foreground=TEXT,
            font=("Segoe UI Semibold", 22),
        )
        style.configure(
            "Section.TLabel",
            background=PANEL_BG,
            foreground=TEXT,
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "Muted.TLabel",
            background=PANEL_BG,
            foreground=MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Primary.TButton",
            font=("Segoe UI Semibold", 10),
            padding=(14, 8),
        )
        style.configure("TCheckbutton", background=PANEL_BG, foreground=TEXT)
        style.configure("TEntry", padding=6)

    def _build_shell(self) -> None:
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        brand = tk.Label(
            self.sidebar,
            text="JobHunterAI",
            bg=SIDEBAR_BG,
            fg="#ffffff",
            font=("Segoe UI Semibold", 18),
            anchor="w",
            padx=18,
            pady=22,
        )
        brand.pack(fill=tk.X)

        subtitle = tk.Label(
            self.sidebar,
            text="Application automation studio",
            bg=SIDEBAR_BG,
            fg="#98a2b3",
            font=("Segoe UI", 9),
            anchor="w",
            padx=18,
        )
        subtitle.pack(fill=tk.X, pady=(0, 20))

        self.nav_buttons: dict[str, tk.Button] = {}
        for view in ["Dashboard", "Pipeline", "Jobs", "Profile", "Automation", "Settings"]:
            button = tk.Button(
                self.sidebar,
                text=view,
                command=lambda selected=view: self._show_view(selected),
                bg=SIDEBAR_BG,
                fg="#e5e7eb",
                activebackground=SIDEBAR_ACTIVE,
                activeforeground="#ffffff",
                relief=tk.FLAT,
                anchor="w",
                padx=20,
                pady=12,
                font=("Segoe UI", 10),
            )
            button.pack(fill=tk.X, padx=10, pady=2)
            self.nav_buttons[view] = button

        footer = tk.Label(
            self.sidebar,
            text="Safe mode: no auto-submit",
            bg=SIDEBAR_BG,
            fg="#bfdbfe",
            font=("Segoe UI Semibold", 9),
            anchor="w",
            padx=18,
            pady=16,
        )
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        self.content = ttk.Frame(self, style="TFrame")
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.header = ttk.Frame(self.content, style="TFrame")
        self.header.pack(fill=tk.X, padx=26, pady=(24, 10))
        self.title_label = ttk.Label(self.header, text="", style="Title.TLabel")
        self.title_label.pack(side=tk.LEFT)

        self.main = ttk.Frame(self.content, style="TFrame")
        self.main.pack(fill=tk.BOTH, expand=True, padx=26, pady=(0, 18))

        self.console_panel = ttk.Frame(self.content, style="Panel.TFrame")
        self.console_panel.pack(fill=tk.X, padx=26, pady=(0, 22))
        console_title = ttk.Label(
            self.console_panel,
            text="AI Pipeline Console",
            style="Section.TLabel",
        )
        console_title.pack(anchor="w", padx=14, pady=(12, 4))
        self.console = tk.Text(
            self.console_panel,
            height=8,
            bg="#0b1220",
            fg="#d1e7ff",
            insertbackground="#d1e7ff",
            relief=tk.FLAT,
            font=("Consolas", 9),
            wrap=tk.WORD,
        )
        self.console.pack(fill=tk.X, padx=14, pady=(0, 14))
        self._log("Desktop UI ready. Choose a workflow from the sidebar.")

    def _settings(self) -> DesktopSettings:
        return DesktopSettings(
            job_path=Path(self.job_path_var.get()),
            output_dir=Path(self.output_dir_var.get()),
            answers_path=Path(self.answers_path_var.get()),
            use_ai=self.use_ai_var.get(),
            use_ai_review=self.use_ai_review_var.get(),
            open_browser=self.open_browser_var.get(),
        )

    def _show_view(self, view: str) -> None:
        self.active_view.set(view)
        self.title_label.configure(text=view)
        for name, button in self.nav_buttons.items():
            button.configure(bg=SIDEBAR_ACTIVE if name == view else SIDEBAR_BG)
        for child in self.main.winfo_children():
            child.destroy()
        builders = {
            "Dashboard": self._build_dashboard_view,
            "Pipeline": self._build_pipeline_view,
            "Jobs": self._build_jobs_view,
            "Profile": self._build_profile_view,
            "Automation": self._build_automation_view,
            "Settings": self._build_settings_view,
        }
        builders[view]()
        self._refresh_live_visual()

    def _panel(self, parent: tk.Widget, title: str, description: str = "") -> ttk.Frame:
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.pack(fill=tk.X, pady=8)
        ttk.Label(panel, text=title, style="Section.TLabel").pack(
            anchor="w", padx=16, pady=(14, 2)
        )
        if description:
            ttk.Label(panel, text=description, style="Muted.TLabel").pack(
                anchor="w", padx=16, pady=(0, 10)
            )
        return panel

    def _build_dashboard_view(self) -> None:
        summary = self._panel(
            self.main,
            "Command Center",
            "Run the safest high-level workflows without typing terminal commands.",
        )
        grid = ttk.Frame(summary, style="Panel.TFrame")
        grid.pack(fill=tk.X, padx=14, pady=(4, 14))
        for index, action in enumerate(desktop_actions(self._settings())[:4]):
            button = ttk.Button(
                grid,
                text=action.label,
                style="Primary.TButton",
                command=lambda selected=action: self._run_action(selected),
            )
            button.grid(row=index // 2, column=index % 2, sticky="ew", padx=6, pady=6)
            grid.columnconfigure(index % 2, weight=1)

        status = self._panel(
            self.main,
            "Current Workspace",
            "These paths control where the desktop workflow reads and writes files.",
        )
        self._path_row(status, "Job description", self.job_path_var, self._choose_job_file)
        self._path_row(status, "Output folder", self.output_dir_var, self._choose_output_dir)
        self._path_row(status, "Answers file", self.answers_path_var, self._choose_answers_file)
        self._build_live_visual_panel(self.main)

    def _build_pipeline_view(self) -> None:
        panel = self._panel(
            self.main,
            "Application Pipeline",
            "Generate, review, and package a tailored application from one job file.",
        )
        for action in actions_by_category(self._settings()).get("Pipeline", []):
            self._action_row(panel, action)
        self._action_row(panel, desktop_actions(self._settings())[0])

    def _build_jobs_view(self) -> None:
        panel = self._panel(
            self.main,
            "Jobs",
            "Review local tracker status and prepare batch inputs.",
        )
        for action in actions_by_category(self._settings()).get("Jobs", []):
            self._action_row(panel, action)
        self._info_line(panel, "Saved job descriptions live in the ignored jobs/ folder.")

    def _build_profile_view(self) -> None:
        panel = self._panel(
            self.main,
            "Profile Source Of Truth",
            "Profile files are the factual source for generated applications.",
        )
        self._action_row(panel, desktop_actions(self._settings())[0])
        preview = tk.Text(
            panel,
            height=12,
            bg="#f8fafc",
            fg=TEXT,
            relief=tk.FLAT,
            font=("Segoe UI", 9),
            wrap=tk.WORD,
        )
        preview.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 16))
        preview.insert(tk.END, read_text_file(MASTER_PROFILE_PATH, required=False))
        preview.configure(state=tk.DISABLED)

    def _build_automation_view(self) -> None:
        panel = self._panel(
            self.main,
            "Automation Preparation",
            "Prepare browser review, form plans, gates, and status reports without submitting.",
        )
        for action in actions_by_category(self._settings()).get("Automation", []):
            self._action_row(panel, action)
        for action in actions_by_category(self._settings()).get("Dashboard", []):
            self._action_row(panel, action)
        self._info_line(panel, "Final submit remains disabled until a future explicit approval stage.")
        self._build_live_visual_panel(self.main)

    def _build_settings_view(self) -> None:
        panel = self._panel(
            self.main,
            "Settings",
            "Configure paths and AI options for desktop workflow buttons.",
        )
        self._path_row(panel, "Job description", self.job_path_var, self._choose_job_file)
        self._path_row(panel, "Output folder", self.output_dir_var, self._choose_output_dir)
        self._path_row(panel, "Answers file", self.answers_path_var, self._choose_answers_file)
        checks = ttk.Frame(panel, style="Panel.TFrame")
        checks.pack(fill=tk.X, padx=16, pady=8)
        ttk.Checkbutton(checks, text="Use AI draft generation", variable=self.use_ai_var).pack(
            anchor="w", pady=3
        )
        ttk.Checkbutton(
            checks,
            text="Run optional AI recruiter review",
            variable=self.use_ai_review_var,
        ).pack(anchor="w", pady=3)
        ttk.Checkbutton(
            checks,
            text="Allow browser opening during review",
            variable=self.open_browser_var,
        ).pack(anchor="w", pady=3)

    def _path_row(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        command,
    ) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill=tk.X, padx=16, pady=6)
        ttk.Label(row, text=label, style="Muted.TLabel", width=18).pack(side=tk.LEFT)
        entry = ttk.Entry(row, textvariable=variable)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 8))
        ttk.Button(row, text="Browse", command=command).pack(side=tk.LEFT)

    def _action_row(self, parent: tk.Widget, action: DesktopAction) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill=tk.X, padx=16, pady=8)
        text_frame = ttk.Frame(row, style="Panel.TFrame")
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(text_frame, text=action.label, style="Section.TLabel").pack(anchor="w")
        ttk.Label(text_frame, text=action.description, style="Muted.TLabel").pack(anchor="w")
        ttk.Button(
            row,
            text="Run",
            style="Primary.TButton",
            command=lambda selected=action: self._run_action(selected),
        ).pack(side=tk.RIGHT, padx=(10, 0))

    def _info_line(self, parent: tk.Widget, text: str) -> None:
        ttk.Label(parent, text=text, style="Muted.TLabel").pack(
            anchor="w", padx=16, pady=(4, 14)
        )

    def _build_live_visual_panel(self, parent: tk.Widget) -> None:
        panel = self._panel(
            parent,
            "Live Output Monitor",
            "Watch generated package files, reports, and automation prep artifacts update.",
        )
        toolbar = ttk.Frame(panel, style="Panel.TFrame")
        toolbar.pack(fill=tk.X, padx=16, pady=(2, 8))
        self.visual_summary_label = tk.Label(
            toolbar,
            text="Checking output folder...",
            bg=PANEL_BG,
            fg=TEXT,
            font=("Segoe UI Semibold", 10),
            anchor="w",
        )
        self.visual_summary_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(toolbar, text="Refresh", command=self._refresh_live_visual).pack(side=tk.RIGHT)

        body = ttk.Frame(panel, style="Panel.TFrame")
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        status_frame = ttk.Frame(body, style="Panel.TFrame")
        status_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        self.visual_status_labels = {}
        for row, artifact in enumerate(build_output_snapshot(Path(self.output_dir_var.get())).artifacts):
            name = tk.Label(
                status_frame,
                text=artifact.label,
                bg=PANEL_BG,
                fg=TEXT,
                font=("Segoe UI", 9),
                anchor="w",
                width=20,
            )
            name.grid(row=row, column=0, sticky="w", pady=2)
            status = tk.Label(
                status_frame,
                text="Missing",
                bg=PANEL_BG,
                fg=MISSING,
                font=("Segoe UI Semibold", 9),
                anchor="w",
                width=10,
            )
            status.grid(row=row, column=1, sticky="w", padx=(8, 0), pady=2)
            self.visual_status_labels[artifact.key] = status

        preview_frame = ttk.Frame(body, style="Panel.TFrame")
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.visual_latest_label = tk.Label(
            preview_frame,
            text="Latest generated file",
            bg=PANEL_BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.visual_latest_label.pack(fill=tk.X, pady=(0, 5))
        self.visual_preview = tk.Text(
            preview_frame,
            height=10,
            bg="#f8fafc",
            fg=TEXT,
            relief=tk.FLAT,
            font=("Consolas", 9),
            wrap=tk.WORD,
        )
        self.visual_preview.pack(fill=tk.BOTH, expand=True)

    def _choose_job_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose job description",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.job_path_var.set(path)
            self._refresh_live_visual()

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Choose output folder")
        if path:
            self.output_dir_var.set(path)
            self._refresh_live_visual()

    def _choose_answers_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose application answers file",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
        )
        if path:
            self.answers_path_var.set(path)
            self._refresh_live_visual()

    def _run_action(self, action: DesktopAction) -> None:
        if self.command_running:
            self._log("Another command is still running. Wait for it to finish.")
            return
        self.command_running = True
        command = [sys.executable, *action.command]
        self._log("")
        self._log(f"Starting: {action.label}")
        self._log(f"$ {command_text(command)}")
        self._refresh_live_visual()
        thread = threading.Thread(target=self._run_command_thread, args=(command,), daemon=True)
        thread.start()

    def _run_command_thread(self, command: list[str]) -> None:
        try:
            process = subprocess.Popen(
                command,
                cwd=Path(__file__).resolve().parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            assert process.stdout is not None
            for line in process.stdout:
                self.log_queue.put(line.rstrip())
            returncode = process.wait()
            self.log_queue.put(f"Finished with exit code {returncode}.")
        except OSError as error:
            self.log_queue.put(f"Command failed: {error}")
        finally:
            self.log_queue.put("__COMMAND_DONE__")

    def _drain_log_queue(self) -> None:
        while True:
            try:
                message = self.log_queue.get_nowait()
            except queue.Empty:
                break
            if message == "__COMMAND_DONE__":
                self.command_running = False
                self._refresh_live_visual()
            else:
                self._log(message)
        self.after(120, self._drain_log_queue)

    def _refresh_live_visual_loop(self) -> None:
        self._refresh_live_visual()
        self.after(1500, self._refresh_live_visual_loop)

    def _refresh_live_visual(self) -> None:
        if not self.visual_summary_label or not self.visual_summary_label.winfo_exists():
            return
        snapshot = build_output_snapshot(Path(self.output_dir_var.get()))
        running_text = "Running" if self.command_running else "Idle"
        self.visual_summary_label.configure(
            text=(
                f"{running_text}: {snapshot.generated_count}/"
                f"{snapshot.total_count} tracked artifacts generated"
            )
        )
        for artifact in snapshot.artifacts:
            label = self.visual_status_labels.get(artifact.key)
            if not label or not label.winfo_exists():
                continue
            label.configure(
                text="Found" if artifact.exists else "Missing",
                fg=SUCCESS if artifact.exists else MISSING,
            )
        latest_text = (
            f"Latest generated file: {snapshot.latest_path}"
            if snapshot.latest_path
            else f"Watching output folder: {snapshot.output_dir}"
        )
        if self.visual_latest_label and self.visual_latest_label.winfo_exists():
            self.visual_latest_label.configure(text=latest_text)
        if self.visual_preview and self.visual_preview.winfo_exists():
            self.visual_preview.configure(state=tk.NORMAL)
            self.visual_preview.delete("1.0", tk.END)
            self.visual_preview.insert(tk.END, read_preview_text(snapshot.latest_path))
            self.visual_preview.configure(state=tk.DISABLED)

    def _log(self, message: str) -> None:
        self.console.configure(state=tk.NORMAL)
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.configure(state=tk.DISABLED)


def main() -> None:
    app = JobHunterDesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
