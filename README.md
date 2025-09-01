# VALD Report Generator

A desktop application for generating performance reports from VALD data using Google Cloud Platform BigQuery integration.

## Features

- Desktop GUI application built with PySide6
- Integration with VALD API for athlete data retrieval
- Google Cloud Platform BigQuery integration for reference data
- Automated report generation with charts and analysis
- Support for multiple performance tests (CMJ, HJ, IMTP, PPU)

## Setup

### Prerequisites

- Python 3.11+
- Google Cloud Platform account with BigQuery access
- VALD API credentials

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd NEVALDReportGen
   ```

2. Create a virtual environment:
   ```bash
   python -m venv MyVenv
   MyVenv\Scripts\activate  # Windows
   # or
   source MyVenv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure credentials:
   - Copy `gcp_credentials.json.example` to `gcp_credentials.json`
   - Fill in your actual Google Cloud service account credentials
   - Ensure your service account has BigQuery access

### Running the Application

```bash
python desktop_app.py
```

## Project Structure

```
├── desktop_app.py              # Main desktop application
├── ReportScripts/              # Report generation modules
│   ├── GenerateReports/        # Report generation logic
│   ├── PullRefData/           # Reference data retrieval
│   └── VALD_API/              # VALD API integration
├── Output CSVs/               # Generated output files
├── Media/                     # Application media assets
└── requirements.txt           # Python dependencies
```

## Security Note

**Never commit actual credentials to the repository.** Use the provided example file and configure your actual credentials locally.

## Contributing

This is a private repository for internal use. Please follow standard development practices and ensure all sensitive data is properly secured.
