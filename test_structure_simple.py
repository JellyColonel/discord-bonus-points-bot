#!/usr/bin/env python3
"""Test script to verify the new structure (without external deps)."""

import sys
from pathlib import Path

def test_structure():
    """Test that the directory structure is correct."""
    
    print("🧪 Testing project structure...")
    
    root = Path(__file__).parent
    
    # Check main directories
    dirs_to_check = [
        ("bot", "Bot package"),
        ("bot/core", "Core modules"),
        ("bot/commands", "Commands modules"),
        ("bot/data", "Data modules"),
        ("bot/utils", "Utils modules"),
        ("data", "Data directory"),
        ("logs", "Logs directory"),
    ]
    
    all_good = True
    
    for dir_path, description in dirs_to_check:
        full_path = root / dir_path
        if full_path.exists():
            print(f"  ✅ {description}: {dir_path}/")
        else:
            print(f"  ❌ Missing {description}: {dir_path}/")
            all_good = False
    
    print("\n📁 Checking Python files...")
    
    files_to_check = [
        ("run.py", "Entry point"),
        ("bot/__init__.py", "Bot package init"),
        ("bot/main.py", "Main bot module"),
        ("bot/core/__init__.py", "Core package init"),
        ("bot/core/bot.py", "Bot class"),
        ("bot/core/config.py", "Configuration"),
        ("bot/core/database.py", "Database operations"),
        ("bot/commands/__init__.py", "Commands package init"),
        ("bot/commands/activities.py", "Activity commands"),
        ("bot/commands/balance.py", "Balance commands"),
        ("bot/commands/admin.py", "Admin commands"),
        ("bot/commands/help.py", "Help command"),
        ("bot/data/__init__.py", "Data package init"),
        ("bot/data/activities.py", "Activity definitions"),
        ("bot/utils/__init__.py", "Utils package init"),
        ("bot/utils/embeds.py", "Embed utilities"),
        ("bot/utils/helpers.py", "Helper functions"),
    ]
    
    for file_path, description in files_to_check:
        full_path = root / file_path
        if full_path.exists():
            print(f"  ✅ {description}: {file_path}")
        else:
            print(f"  ❌ Missing {description}: {file_path}")
            all_good = False
    
    print("\n📄 Checking configuration files...")
    
    config_files = [
        (".env.example", "Example environment file"),
        (".gitignore", "Git ignore rules"),
        ("requirements.txt", "Python dependencies"),
        ("README.md", "Documentation"),
    ]
    
    for file_path, description in config_files:
        full_path = root / file_path
        if full_path.exists():
            print(f"  ✅ {description}: {file_path}")
        else:
            print(f"  ⚠️  Optional - {description}: {file_path}")
    
    if all_good:
        print("\n✅ All required files and directories are in place!")
        print("\n📝 Next steps:")
        print("1. Copy your .env file with Discord token")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run the bot: python run.py")
    else:
        print("\n❌ Some files or directories are missing!")
        print("Please ensure all files have been created correctly.")
    
    return all_good


if __name__ == "__main__":
    success = test_structure()
    sys.exit(0 if success else 1)
