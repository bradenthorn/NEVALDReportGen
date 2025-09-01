# =================================================================================
# This script is used to create a desktop app for the VALD-API
# The app will allow users to input an athlete's name and get a report
# The report will be generated using the data from the GCP BigQuery database
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
import sys
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QFormLayout, QComboBox, QDateEdit, QSpinBox, QPushButton,
                               QLabel, QProgressBar, QMessageBox, QListWidget, QLineEdit,
                               QCompleter)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from datetime import datetime
import pathlib
# -- BACKEND TO PATH --------------------------------------------------------------
# Add the project root to Python path
project_root = pathlib.Path(__file__).parent
sys.path.append(str(project_root))
# -- IMPORTS FROM BACKEND ---------------------------------------------------------
from ReportScripts.VALD_API.VALDapiHelpers import (get_profiles, FD_Tests_by_Profile)
from ReportScripts.VALD_API.token_gen import get_vald_token
from ReportScripts.GenerateReports.FD_PDF_V1 import generate_athlete_pdf

# -- MAIN WINDOW CLASS -------------------------------------------------------------
class AthleteReporterApp(QMainWindow):
    # -- INITIALIZE WINDOW ---------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VALD Athlete Report Generator")
        self.setGeometry(100, 100, 600, 400)  # x, y, width, height
        # Initialize the UI
        self.init_ui()

    # -- INITIALIZE UI --------------------------------------------------------------
    def init_ui(self):
        """Initialize the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Create main layout
        layout = QVBoxLayout(central_widget)
        # Title
        title_label = QLabel("VALD Athlete Report Generator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        # Create main layout
        form_layout = QFormLayout()
        # Generate a VALD API token
        self.token = get_vald_token()
        # Generate a df of athlete profiles
        self.athletes_df = get_profiles(self.token)
        # Create a tool to select an athlete (searchbox with autocomplete)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search athlete name...")
        self.search_box.setFixedWidth(300)
        # Create the auto complete aspect
        athlete_names = self.athletes_df['fullName'].tolist()
        athlete_names.sort()
        completer = QCompleter(athlete_names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_box.setCompleter(completer)
        form_layout.addRow("Athlete:", self.search_box)
        # Create a button to select the athlete
        self.select_athlete_btn = QPushButton("Select Athlete")
        self.select_athlete_btn.clicked.connect(self.on_select_athlete)
        form_layout.addRow(self.select_athlete_btn)
        # Add the form layout to the main layout
        layout.addLayout(form_layout)
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        # Test date selector (initially will be hidden)
        self.test_date_container = QWidget()
        self.test_date_layout = QVBoxLayout(self.test_date_container)
        # Test date selection widgets
        self.test_date_label = QLabel("Select Test Date:")
        self.test_date_list = QListWidget()
        self.select_date_btn = QPushButton("Select Date")
        # Add the test date selection widgets to the layout
        self.test_date_layout.addWidget(self.test_date_label)
        self.test_date_layout.addWidget(self.test_date_list)
        self.test_date_layout.addWidget(self.select_date_btn)
        self.select_date_btn.clicked.connect(self.on_select_date)
        # Add the test date container to the main layout
        layout.addWidget(self.test_date_container)
        self.test_date_container.hide()
        # Age range selector
        self.age_range_container = QWidget()
        self.age_range_layout = QVBoxLayout(self.age_range_container)
        # Age range selection widgets
        self.age_range_label = QLabel("Select Age Range for Reference Data:")
        self.age_range_combo = QComboBox()
        self.age_range_combo.addItems(["Youth (8-13)",
                                       "High School (14-18)", 
                                       "College (19-24)",
                                       "Professional (25-40)"])
        self.confirm_age_btn = QPushButton("Confirm Age Range")
        self.confirm_age_btn.clicked.connect(self.on_confirm_age_range)
        # Add the age range selection widgets to the layout
        self.age_range_layout.addWidget(self.age_range_label)
        self.age_range_layout.addWidget(self.age_range_combo)
        self.age_range_layout.addWidget(self.confirm_age_btn)
        # Add the age range container to the main layout
        layout.addWidget(self.age_range_container)
        self.age_range_container.hide()
        # Add age range container to main layout (initially hidden)
        layout.addWidget(self.age_range_container)
        self.age_range_container.hide()
        # Generate report button (initially hidden)
        self.generate_report_btn = QPushButton("Generate Report")
        self.generate_report_btn.clicked.connect(self.generate_report)
        self.generate_report_btn.setFixedWidth(200)  # set width
        # Center the button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.generate_report_btn)
        button_layout.addStretch()
        # Add to main layout (initially hidden)
        layout.addLayout(button_layout)
        self.generate_report_btn.hide()
        # Add some spacing
        layout.addStretch()

    # -- SELECTION TOOLS ------------------------------------------------------------
    def on_select_athlete(self):
        """Handle when an athlete is selected from the dropdown."""
        # Clear the list widget
        self.test_date_list.clear()
        # Get the athlete's name
        athlete_name = self.search_box.text().strip()
        # Check if the athletes name is in the df
        if athlete_name in self.athletes_df['fullName'].values:
            # Get the athlete's profile id
            athlete_id = self.athletes_df[self.athletes_df['fullName'] == athlete_name]['profileId'].values[0]
            # Get the athlete's test dates
            start_date = datetime(2020, 1, 1, 0, 0, 0)
            test_dates = FD_Tests_by_Profile(start_date, athlete_id, self.token)
            # Check if the test dates are not None
            if test_dates is not None and not test_dates.empty:
                # Get unique dates
                unique_dates = test_dates['modifiedDateUtc'].unique()
                # Add the test dates to the list widget
                for date in unique_dates:
                    self.test_date_list.addItem(date.strftime("%Y-%m-%d"))
                # Show the test date container
                self.status_label.setText(f"Found {len(unique_dates)} test dates for {athlete_name}")
                self.test_date_container.show()
            else:
                self.status_label.setText(f"{athlete_name} has no valid test sessions. Must have HJ, CMJ, PPU, and IMTP tests on the same day.")
                self.test_date_container.hide()
        else:
            self.status_label.setText("Athlete not found in VALD database.")
            self.test_date_container.hide()

    def on_select_date(self):
        """Handle when a test date is selected."""
        current_row = self.test_date_list.currentRow()
        if current_row >= 0:
            selected_item = self.test_date_list.item(current_row)
            selected_date_str = selected_item.text()
            athlete_name = self.search_box.text().strip()
            # Store the selection
            self.selected_athlete = athlete_name
            self.selected_date = selected_date_str
            # Update status
            self.status_label.setText(f"Selected: {athlete_name} - {selected_date_str}")
            # Hide test date container and show age range
            self.test_date_container.hide()
            self.age_range_container.show()
        else:
            QMessageBox.warning(self, "Selection Error", "Please select a test date from the list.")
    
    def on_confirm_age_range(self):
        """Handle when age range is confirmed."""
        selected_range = self.age_range_combo.currentText()
        # Parse the age range
        if "Youth" in selected_range:
            age_range = (8, 13)
        elif "High School" in selected_range:
            age_range = (14, 18)
        elif "College" in selected_range:
            age_range = (19, 24)
        elif "Professional" in selected_range:
            age_range = (25, 40)
        else:
            age_range = (18, 25)  # Default fallback
        # Store the age range
        self.selected_age_range = age_range
        # Update status
        self.status_label.setText(f"Ready to generate report for {self.selected_athlete} on {self.selected_date} (Age range: {age_range[0]}-{age_range[1]})")
        # Hide age range container
        self.age_range_container.hide()
        self.generate_report_btn.show()

    def generate_report(self):
        """Generate the report for the selected athlete and date."""
        if hasattr(self, 'selected_athlete') and hasattr(self, 'selected_date') and hasattr(self, 'selected_age_range'):
            print(f"Generating report for {self.selected_athlete} on {self.selected_date} with age range {self.selected_age_range}")
            # Update status
            self.status_label.setText("Generating report... Please wait.")
            # Set the output path
            self.output_path = f"/Users/owenmccandless/Desktop/NextEra Work/PDF Reports/{self.selected_athlete}_{self.selected_date}.pdf"
            # Generate the report
            generate_athlete_pdf(self.selected_athlete,
                                 datetime.strptime(self.selected_date, "%Y-%m-%d").date(),
                                 self.selected_age_range[0],
                                 self.selected_age_range[1],
                                 self.output_path)
            # For now, show a success message
            QMessageBox.information(self, "Report Generated", 
                                f"Report generated successfully!\n"
                                f"Athlete: {self.selected_athlete}\n"
                                f"Date: {self.selected_date}\n"
                                f"Age Range: {self.selected_age_range[0]}-{self.selected_age_range[1]}")
            # Reset the UI
            self.generate_report_btn.hide()
            self.status_label.setText("Report generation complete!")
        else:
            QMessageBox.warning(self, "Error", "Please complete all selections first.")

       




def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    # Create and show main window
    window = AthleteReporterApp()
    window.show()
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()