import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from pathlib import Path

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
        self.current_profiles = None
        self.current_dates = []
        self._build_widgets()

    # ------------------------------------------------------------------
    def _build_widgets(self):
        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(search_frame, text="Athlete Search:").pack(side="left")
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(search_frame, text="Search", command=self.search_athletes).pack(side="left")

        self.athlete_listbox = tk.Listbox(self)
        self.athlete_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.athlete_listbox.bind("<<ListboxSelect>>", self.on_athlete_select)

        tk.Label(self, text="Available Test Dates:").pack(padx=10, anchor="w")
        self.date_listbox = tk.Listbox(self)
        self.date_listbox.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Button(self, text="Generate PDF", command=self.generate_pdf).pack(pady=10)

        self.status_label = tk.Label(self, text="")
        self.status_label.pack(pady=5)

    # ------------------------------------------------------------------
    def search_athletes(self):
        query = self.search_entry.get().strip().lower()
        self.athlete_listbox.delete(0, tk.END)
        self.date_listbox.delete(0, tk.END)
        if not query:
            return
        profiles = self.client.get_profiles()
        matches = profiles[profiles["fullName"].str.contains(query, case=False)]
        self.current_profiles = matches.reset_index(drop=True)
        for name in matches["fullName"]:
            self.athlete_listbox.insert(tk.END, name)

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
        self.update_idletasks()
        loader = DataLoader()
        loader.refresh_cache(athlete_name, test_date, 18, 30, client=self.client)
        athlete_df, ref_data = loader.load()
        output_path = Path.home() / "Downloads" / f"{athlete_name.replace(' ', '_')}_{test_date:%Y%m%d}.pdf"
        generate_athlete_pdf(athlete_name, test_date, output_path, athlete_df, ref_data)
        self.status_label.config(text=f"Report saved to {output_path}")
        messagebox.showinfo("Success", f"Report saved to {output_path}")


if __name__ == "__main__":
    app = DesktopApp()
    app.mainloop()