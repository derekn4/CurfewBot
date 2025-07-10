#!/usr/bin/env python3
"""
CurfewBot Setup Script
Helps users set up the bot for local development or deployment
"""

import os
import shutil
import sys

def setup_environment():
    """Set up the environment for CurfewBot"""
    print("🤖 CurfewBot Setup Script")
    print("=" * 40)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        try:
            shutil.copy('config/.env.example', '.env')
            print("   ✅ .env file created")
            print("   ⚠️  Please edit .env with your Discord bot token and guild ID")
        except FileNotFoundError:
            print("   ❌ config/.env.example not found")
            return False
    else:
        print("📝 .env file already exists")
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("   ⚠️  Python 3.8+ recommended for best compatibility")
    else:
        print("   ✅ Python version is compatible")
    
    # Check if requirements are installed
    print("📦 Checking dependencies...")
    try:
        import discord
        print(f"   ✅ discord.py version: {discord.__version__}")
    except ImportError:
        print("   ❌ discord.py not installed")
        print("   💡 Run: pip install -r config/requirements.txt")
        return False
    
    try:
        import sqlite3
        print(f"   ✅ SQLite version: {sqlite3.version}")
    except ImportError:
        print("   ❌ SQLite not available")
        return False
    
    try:
        import pytz
        print(f"   ✅ pytz available")
    except ImportError:
        print("   ❌ pytz not installed")
        print("   💡 Run: pip install -r config/requirements.txt")
        return False
    
    # Check project structure
    print("📁 Checking project structure...")
    required_dirs = ['src', 'docs', 'config', 'tests']
    required_files = [
        'src/curfewbot.py',
        'config/requirements.txt',
        'docs/DEPLOYMENT_GUIDE.md',
        'Procfile'
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"   ✅ {directory}/ directory exists")
        else:
            print(f"   ❌ {directory}/ directory missing")
            return False
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path} exists")
        else:
            print(f"   ❌ {file_path} missing")
            return False
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env with your Discord bot token and guild ID")
    print("2. Run: python src/curfewbot.py")
    print("3. For deployment, see: docs/DEPLOYMENT_GUIDE.md")
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'config/requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Dependencies installed successfully")
            return True
        else:
            print(f"   ❌ Failed to install dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error installing dependencies: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        install_dependencies()
    
    setup_environment()
