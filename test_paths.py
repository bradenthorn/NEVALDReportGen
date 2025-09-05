import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

# Ensure project root is on path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import OUTPUT_DIR, PDF_OUTPUT_DIR
from ReportScripts.GenerateReports.data_loader import DataLoader


def test_data_loader_uses_config_default():
    loader = DataLoader()
    assert loader.base_dir == Path(OUTPUT_DIR)


def test_cross_platform_resolution():
    components = ["Athlete", "CMJ.csv"]
    posix_path = PurePosixPath(OUTPUT_DIR, *components)
    windows_path = PureWindowsPath(OUTPUT_DIR, *components)
    assert posix_path.as_posix().endswith("Athlete/CMJ.csv")
    assert str(windows_path).endswith("Athlete\\CMJ.csv")


def test_pdf_path_cross_platform():
    components = ["example.pdf"]
    posix_path = PurePosixPath(PDF_OUTPUT_DIR, *components)
    windows_path = PureWindowsPath(PDF_OUTPUT_DIR, *components)
    assert posix_path.as_posix().endswith("example.pdf")
    assert str(windows_path).endswith("example.pdf")
