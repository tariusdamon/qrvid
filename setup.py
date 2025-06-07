#!/usr/bin/env python3
"""
setup.py - Quick setup script for QRVid

This script helps users set up the QRVid project quickly.
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def main():
    print("🎯 QRVid Setup Script")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("\n❌ Setup failed - could not install dependencies")
        print("Please run manually: pip install -r requirements.txt")
        sys.exit(1)
    
    # Run installation test
    if not run_command("python test_installation.py", "Running installation test"):
        print("\n❌ Setup failed - installation test failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Quick Start Guide:")
    print("1. Place your ZIP file in the project directory")
    print("2. Run: python encode_direct.py --input-zip yourfile.zip")
    print("3. Run: python decode_direct.py --qr-dir images")
    print("4. Create video: python quick_video.py images output.mp4")
    print("\n📚 For more options, see README.md or run --help on any script")
    print("\n⚖️  License: Non-commercial use free, commercial license required")
    print("   See LICENSE file for details")

if __name__ == "__main__":
    main()
