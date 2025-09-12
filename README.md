# NEVALD Report Generator

Professional VALD ForceDecks Report Generation Tool for Next Era Performance Technology.

## Overview

This application generates comprehensive PDF reports from VALD ForceDecks data, providing coaches and sports scientists with detailed performance analytics and comparative insights.

## Features

- **Desktop Application**: Easy-to-use GUI for coaches without technical expertise
- **Automated Data Processing**: Pulls athlete data from VALD Hub API
- **Reference Comparisons**: Compares athlete performance against age-matched reference data
- **Professional PDF Reports**: Generates polished reports with charts and analytics
- **Standalone Distribution**: Single executable file for easy deployment

## Quick Start

### For Coaches (End Users)
1. Download the `VALD_Report_Generator_Package` folder
2. Run `VALD_Report_Generator.exe`
3. Search for athlete, select test date, and generate reports

No configuration needed. Credentials are bundled for distribution use.

### For Developers

#### Setup Development Environment
```bash
# Clone the repository
git clone <repository-url>
cd NEVALDReportGen

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

#### Project Structure
```
NEVALDReportGen/
├── src/nevald_report_gen/     # Main package
│   ├── api/                   # VALD API integration
│   ├── reports/               # PDF generation
│   ├── data/                  # Data processing
│   ├── config.py              # Configuration
│   └── desktop_app.py         # GUI application
├── dist/                      # Distribution builds
├── assets/                    # Static assets
├── data/                      # Runtime data
├── tests/                     # Test suite
├── scripts/                   # Build utilities
└── docs/                      # Documentation
```

#### Development Commands
```bash
# Run the desktop app (from project root)
python -m src.nevald_report_gen.desktop_app

# Run tests
pytest

# Format code
black src/ tests/

# Type checking
mypy src/

# Build distribution
python scripts/build_dist.py
```

## Configuration

### Environment Variables
Create a `.env` file with:
```
VALD_CLIENT_ID=your_client_id
VALD_CLIENT_SECRET=your_client_secret
VALD_AUTH_URL=https://security.valdperformance.com/connect/token
GCP_PROJECT_ID=your_project_id
```

### GCP Credentials
During development, place `gcp_credentials.json` in the project root or set `GCP_CREDENTIALS_PATH` in `.env`. The app auto-detects credentials in common locations.

## Building Distribution

To create a standalone executable for coaches:

```bash
# Install build dependencies
pip install -r requirements/build.txt

# Build executable
python scripts/build_dist.py
```

This creates a complete distribution package in `dist/VALD_Report_Generator_Package/` ready for deployment.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/nevald_report_gen

# Run specific test modules
pytest tests/test_api/
pytest tests/test_reports/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For technical support or questions:
- Email: info@nexteraperformance.com
- Issues: GitHub Issues page

## Changelog

### v0.1.0
- Initial release
- Desktop GUI application
- VALD API integration
- PDF report generation
- Reference data comparison