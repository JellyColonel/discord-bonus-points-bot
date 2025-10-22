#!/usr/bin/env python3
"""Test script to verify the new structure works correctly."""

import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent / 'bot'))

def test_imports():
    """Test that all imports work correctly."""
    
    print("🧪 Testing imports...")
    
    try:
        # Test core imports
        print("  Testing core modules...")
        from core import Config, Database, BonusPointsBot
        print("    ✅ Core modules imported successfully")
        
        # Test data imports
        print("  Testing data modules...")
        from data import ACTIVITIES, get_all_activities, get_activity_by_id
        print("    ✅ Data modules imported successfully")
        
        # Test utils imports
        print("  Testing utils modules...")
        from utils import create_activities_embed, calculate_bp, is_event_active
        print("    ✅ Utils modules imported successfully")
        
        # Test commands imports
        print("  Testing commands modules...")
        from commands import setup_all_commands
        print("    ✅ Commands modules imported successfully")
        
        # Test main import
        print("  Testing main module...")
        from bot.main import main
        print("    ✅ Main module imported successfully")
        
        print("\n✅ All imports successful! The structure is working correctly.")
        
        # Test data integrity
        print("\n📊 Testing data integrity...")
        activities = get_all_activities()
        print(f"  Found {len(activities)} activities")
        
        if activities:
            first_activity = activities[0]
            print(f"  Sample activity: {first_activity['name']}")
            print(f"    - Base BP: {first_activity['bp']}")
            print(f"    - VIP BP: {first_activity['bp_vip']}")
        
        print("\n✅ Structure verification complete!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Please ensure all files are in place.")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
