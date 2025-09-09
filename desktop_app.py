"""Minimal desktop interface for generating athlete reports.

The application allows staff to search for an athlete, choose a test date
containing all required test types (CMJ, HJ, IMTP and PPU) and then generate
the ForceDecks PDF report directly into their local ``Downloads`` folder.  The
goal is to provide a simple script that can be packaged and emailed to other
coaches.
"""

import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')

from ReportScripts.VALD_API.vald_client import ValdClient
from ReportScripts.GenerateReports.data_loader import DataLoader
from ReportScripts.GenerateReports.FD_PDF_V1 import generate_athlete_pdf


class DesktopApp(tk.Tk):
    """Simple GUI for generating athlete PDF reports."""

    def __init__(self):
        super().__init__()
        self.title("VALD Report Generator")
        self.geometry("500x500")
        self.client = ValdClient()
        # Cache all profiles so we can provide auto-complete suggestions
        self.profiles = self.client.get_profiles()
        self.current_profiles = self.profiles
        self.current_dates = []
        self.age_ranges = {
            "HS (14-18)": (14, 18),
            "College (18-22)": (18, 22),
            "Pro (21-35)": (21, 35),
        }
        self._build_widgets()
        # Populate list with all athlete names on start
        self._update_athlete_list()

    # ------------------------------------------------------------------
    def _build_widgets(self):
        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(search_frame, text="Athlete Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._update_athlete_list())
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)

        self.athlete_listbox = tk.Listbox(self, exportselection=False)
        self.athlete_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.athlete_listbox.bind("<<ListboxSelect>>", self.on_athlete_select)

        tk.Label(self, text="Available Test Dates:").pack(padx=10, anchor="w")
        self.date_listbox = tk.Listbox(self)
        self.date_listbox.pack(fill="both", expand=True, padx=10, pady=5)

        age_frame = tk.Frame(self)
        age_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(age_frame, text="Reference Age Range:").pack(side="left")
        self.age_var = tk.StringVar(value="College (18-22)")
        tk.OptionMenu(age_frame, self.age_var, *self.age_ranges.keys()).pack(
            side="left", padx=5
        )

        self.generate_button = tk.Button(self, text="Generate PDF", command=self.generate_pdf)
        self.generate_button.pack(pady=10)
    

        self.status_label = tk.Label(self, text="")
        self.status_label.pack(pady=5)

    # ------------------------------------------------------------------
    def _update_athlete_list(self):
        """Refresh the athlete list based on the current search query."""
        query = self.search_var.get().strip().lower()
        self.athlete_listbox.delete(0, tk.END)
        self.date_listbox.delete(0, tk.END)
        if query:
            matches = self.profiles[self.profiles["fullName"].str.contains(query, case=False)]
        else:
            matches = self.profiles
        self.current_profiles = matches.reset_index(drop=True)
        for name in self.current_profiles["fullName"]:
            # Display athlete names with capitalized first and last names
            self.athlete_listbox.insert(tk.END, name.title())

    # ------------------------------------------------------------------
    def on_athlete_select(self, _event):
        sel = self.athlete_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        athlete_name = self.athlete_listbox.get(index)
        profile_id = self.current_profiles.iloc[index]["profileId"]
        first_date = datetime(2020, 1, 1)
        tests = self.client.get_tests_by_profile(first_date, profile_id)
        self.date_listbox.delete(0, tk.END)
        self.current_dates = []
        if tests is None or tests.empty:
            self.status_label.config(text="No valid tests found.")
            return
        dates = sorted(tests["modifiedDateUtc"].unique(), reverse=True)
        for d in dates:
            self.current_dates.append(d)
            self.date_listbox.insert(tk.END, d.strftime("%Y-%m-%d"))
        self.status_label.config(text=f"Loaded {len(dates)} test dates for {athlete_name}.")

    # ------------------------------------------------------------------
    def generate_pdf(self):
        sel_ath = self.athlete_listbox.curselection()
        sel_date = self.date_listbox.curselection()
        if not sel_ath or not sel_date:
            messagebox.showwarning("Selection Required", "Please select an athlete and test date.")
            return
        athlete_name = self.athlete_listbox.get(sel_ath)
        test_date = self.current_dates[sel_date[0]]
        self.status_label.config(text="Generating report... this may take a moment.")
        self.generate_button.config(state=tk.DISABLED)

        def worker():
            try:
                loader = DataLoader()
                min_age, max_age = self.age_ranges[self.age_var.get()]
                athlete_df, ref_data = loader.load(
                    athlete_name, test_date, min_age, max_age, client=self.client
                )
                output_path = (
                    Path.home()
                    / "Downloads"
                    / f"{athlete_name.replace(' ', '_')}_{test_date:%Y%m%d}.pdf"
                )
                generate_athlete_pdf(
                    athlete_name, test_date, output_path, athlete_df, ref_data
                )
            except Exception as exc:  # pragma: no cover - UI thread
                self.after(0, lambda: self._on_pdf_done(error=exc))
            else:
                self.after(0, lambda: self._on_pdf_done(path=output_path))

        threading.Thread(target=worker, daemon=True).start()

    def _on_pdf_done(self, path=None, error=None):
        if error:
            self.status_label.config(text=f"Error generating report: {error}")
            messagebox.showerror("Error", f"Failed to generate report: {error}")
        else:
            self.status_label.config(text=f"Report saved to {path}")
            messagebox.showinfo("Success", f"Report saved to {path}")
        self.generate_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    app = DesktopApp()
    app.mainloop()
