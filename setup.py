#!/usr/bin/env python3
# =================================================================================
# Setup script for VALD Report Generator
# This script helps set up the project on any machine
# =================================================================================

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_requirements():
    """Install required packages."""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_env_file():
    """Create .env file from example if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        print("📝 Creating .env file from template...")
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file created! Please edit it with your actual credentials.")
        return True
    else:
        print("❌ env.example file not found")
        return False

def check_credentials():
    """Check if required credential files exist."""
    print("🔐 Checking credentials...")
    
    # Check GCP credentials
    gcp_creds = Path("gcp_credentials.json")
    if gcp_creds.exists():
        print("✅ GCP credentials found")
    else:
        print("⚠️  GCP credentials not found. Please:")
        print("   1. Copy gcp_credentials.json.example to gcp_credentials.json")
        print("   2. Fill in your actual Google Cloud service account credentials")
    
    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if 'your_vald_client_id_here' in content:
                print("⚠️  VALD API credentials not configured. Please edit .env file")
            else:
                print("✅ VALD API credentials configured")
    else:
        print("❌ .env file not found")

def main():
    """Main setup function."""
    print("🚀 Setting up VALD Report Generator...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create environment file
    create_env_file()
    
    # Check credentials
    check_credentials()
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your VALD API credentials")
    print("2. Copy gcp_credentials.json.example to gcp_credentials.json")
    print("3. Fill in your Google Cloud service account credentials")
    print("4. Run: python desktop_app.py")
    
    print("\nFor more help, see README.md")

if __name__ == "__main__":
    main()
