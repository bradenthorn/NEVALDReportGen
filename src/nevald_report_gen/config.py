# =================================================================================
# Configuration file for VALD Report Generator
# This file centralizes all configuration settings and makes the project portable
# =================================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# GCP Configuration - look for credentials in multiple locations
def find_gcp_credentials():
    """Find GCP credentials in order of preference."""
    # Check environment variable first
    env_path = os.getenv('GCP_CREDENTIALS_PATH')
    if env_path and Path(env_path).exists():
        return env_path
    
    # Check in current directory (for direct execution)
    current_dir_creds = PROJECT_ROOT / 'gcp_credentials.json'
    if current_dir_creds.exists():
        return str(current_dir_creds)
    
    # Check in project root (for module execution)
    project_root_creds = PROJECT_ROOT.parent.parent / 'gcp_credentials.json'
    if project_root_creds.exists():
        return str(project_root_creds)
    
    # Default fallback
    return str(PROJECT_ROOT / 'gcp_credentials.json')

GCP_CREDENTIALS_PATH = find_gcp_credentials()
print(f"Using GCP credentials from: {GCP_CREDENTIALS_PATH}")
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'vald-ref-data')

# VALD API Configuration
VALD_CLIENT_ID = os.getenv('VALD_CLIENT_ID')
VALD_CLIENT_SECRET = os.getenv('VALD_CLIENT_SECRET')
VALD_AUTH_URL = os.getenv('VALD_AUTH_URL', 'https://security.valdperformance.com/connect/token')

# File paths
OUTPUT_DIR = os.getenv('OUTPUT_DIR', str(PROJECT_ROOT / 'Output CSVs'))
MEDIA_DIR = os.getenv('MEDIA_DIR', str(PROJECT_ROOT / 'Media'))
PDF_OUTPUT_DIR = os.getenv('PDF_OUTPUT_DIR', str(PROJECT_ROOT / 'PDF Reports'))

# Create directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

# Database table names
CMJ_TABLE = f"{GCP_PROJECT_ID}.athlete_performance_db.cmj_results"
HJ_TABLE = f"{GCP_PROJECT_ID}.athlete_performance_db.hj_results"
IMTP_TABLE = f"{GCP_PROJECT_ID}.athlete_performance_db.imtp_results"
PPU_TABLE = f"{GCP_PROJECT_ID}.athlete_performance_db.ppu_results"

# Token cache file
TOKEN_CACHE_FILE = os.getenv('TOKEN_CACHE_FILE', str(PROJECT_ROOT / '.token_cache.json'))
