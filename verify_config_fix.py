#!/usr/bin/env python3
"""
Verification script to confirm the configuration fix is working.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_config_fields():
    """Test that all required config fields exist."""
    from codegenie.core.config import Config
    
    print("=" * 80)
    print("  CONFIGURATION FIX VERIFICATION")
    print("=" * 80)
    print()
    
    # Create default config
    config = Config.create_default()
    
    # Test required fields
    required_fields = [
        'autonomous_workflows',
        'multi_agent_coordination',
        'adaptive_learning'
    ]
    
    print("Testing required fields:")
    print("-" * 80)
    
    all_passed = True
    for field in required_fields:
        if hasattr(config, field):
            value = getattr(config, field)
            status = "✅ PASS"
            print(f"{status} - {field}: {value}")
        else:
            status = "❌ FAIL"
            print(f"{status} - {field}: MISSING")
            all_passed = False
    
    print("-" * 80)
    print()
    
    # Test config sections
    print("Testing config sections:")
    print("-" * 80)
    
    sections = ['models', 'ui', 'execution', 'learning', 'security']
    for section in sections:
        if hasattr(config, section):
            print(f"✅ PASS - {section} section exists")
        else:
            print(f"❌ FAIL - {section} section missing")
            all_passed = False
    
    print("-" * 80)
    print()
    
    # Final result
    if all_passed:
        print("🎉 SUCCESS! All configuration fields are present and working.")
        print()
        print("The application is ready to use:")
        print("  • python demo_full_application.py")
        print("  • python codegenie_interactive.py")
        print("  • python -m src.codegenie.cli")
        return 0
    else:
        print("❌ FAILURE! Some configuration fields are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(test_config_fields())
