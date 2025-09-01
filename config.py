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

# GCP Configuration
GCP_CREDENTIALS_PATH = os.getenv('GCP_CREDENTIALS_PATH', str(PROJECT_ROOT / 'gcp_credentials.json'))
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
