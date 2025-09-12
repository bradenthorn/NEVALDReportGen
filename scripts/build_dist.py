#!/usr/bin/env python3
"""Build distribution executable for coaches."""
import os
import subprocess
import sys
from pathlib import Path

def build_executable():
    """Build PyInstaller executable."""
    print("Building VALD Report Generator executable...")
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Use absolute paths for add-data
    assets_path = str(project_root / "assets")
    config_path = str(project_root / "src" / "nevald_report_gen" / "config.py")
    env_path = str(project_root / ".env")
    gcp_creds_path = str(project_root / "gcp_credentials.json")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=VALD_Report_Generator",
        f"--add-data={assets_path};assets",
        f"--add-data={config_path};.",
        f"--add-data={env_path};.",
        f"--add-data={gcp_creds_path};.",
        "--distpath=dist",
        "--workpath=build",
        "--specpath=build",
        "src/nevald_report_gen/desktop_app.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Build successful! Executable created in dist/")
        
        # Create distribution package
        create_dist_package()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)

def create_dist_package():
    """Create a complete distribution package for coaches."""
    import shutil
    from pathlib import Path
    
    dist_dir = Path("dist")
    package_dir = dist_dir / "VALD_Report_Generator_Package"
    
    # Create package directory
    package_dir.mkdir(exist_ok=True)
    
    # Copy executable
    exe_path = dist_dir / "VALD_Report_Generator.exe"
    if exe_path.exists():
        shutil.copy2(exe_path, package_dir)
    
    # No config directory needed - credentials are embedded in the executable
    
    # Create data directories
    (package_dir / "data").mkdir(exist_ok=True)
    (package_dir / "data" / "output_csvs").mkdir(exist_ok=True)
    (package_dir / "data" / "pdf_reports").mkdir(exist_ok=True)
    
    # Create README for coaches
    readme_content = """# VALD Report Generator

## Quick Start
1. Double-click VALD_Report_Generator.exe
2. Search for an athlete
3. Select a test date
4. Choose reference age range
5. Click "Generate PDF"

## That's it! No configuration needed.
All credentials and settings are pre-configured.

## Support
Contact: info@nexteraperformance.com
"""
    
    (package_dir / "README.txt").write_text(readme_content)
    
    print(f"✅ Distribution package created at {package_dir}")
    print("📦 Ready to distribute to coaches!")

if __name__ == "__main__":
    build_executable()
