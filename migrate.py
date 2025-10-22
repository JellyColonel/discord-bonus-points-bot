#!/usr/bin/env python3
"""
Migration script to move from old structure to new structure.
This will copy your existing database and configuration.
"""

import os
import shutil
from pathlib import Path


def migrate_project():
    """Migrate existing bot to new structure."""
    
    print("🔄 Starting migration to new project structure...")
    
    # Define paths
    old_root = Path(".")  # Current directory
    new_root = Path(".")  # We're restructuring in place
    
    # Check if already migrated
    if (new_root / "bot").exists():
        print("✅ Project already appears to be migrated!")
        return
    
    # Create new structure
    print("📁 Creating new directory structure...")
    (new_root / "bot" / "core").mkdir(parents=True, exist_ok=True)
    (new_root / "bot" / "commands").mkdir(parents=True, exist_ok=True)
    (new_root / "bot" / "data").mkdir(parents=True, exist_ok=True)
    (new_root / "bot" / "utils").mkdir(parents=True, exist_ok=True)
    (new_root / "data").mkdir(exist_ok=True)
    (new_root / "logs").mkdir(exist_ok=True)
    
    # Move database if exists
    if (old_root / "bonus_points.db").exists():
        print("💾 Moving database...")
        shutil.move(str(old_root / "bonus_points.db"), str(new_root / "data" / "bonus_points.db"))
    
    # Move log file if exists
    if (old_root / "bot.log").exists():
        print("📄 Moving log file...")
        shutil.move(str(old_root / "bot.log"), str(new_root / "logs" / "bot.log"))
    
    # Copy .env if exists (don't move, user might need it)
    if (old_root / ".env").exists():
        print("🔑 Copying .env file...")
        shutil.copy2(str(old_root / ".env"), str(new_root / ".env"))
    
    print("✅ Migration complete!")
    print("\n📝 Next steps:")
    print("1. Replace your old Python files with the new modular structure")
    print("2. Test the bot with: python run.py")
    print("3. Remove old .py files from root directory")
    print("\nYour database and settings have been preserved.")


if __name__ == "__main__":
    migrate_project()
