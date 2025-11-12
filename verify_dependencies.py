#!/usr/bin/env python3
"""
Verify all required dependencies are installed and working.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_core_dependencies():
    """Test core application dependencies."""
    print("=" * 80)
    print("  DEPENDENCY VERIFICATION")
    print("=" * 80)
    print()
    
    dependencies = [
        # Core
        ('ollama', 'Ollama AI client'),
        ('rich', 'Rich terminal output'),
        ('typer', 'CLI framework'),
        ('pydantic', 'Data validation'),
        ('yaml', 'YAML configuration'),
        
        # Async and Web
        ('aiohttp', 'Async HTTP framework'),
        ('aiohttp_session', 'Session management'),
        ('aiohttp_cors', 'CORS support'),
        ('websockets', 'WebSocket support'),
        
        # Security
        ('cryptography', 'Encryption library'),
        ('jwt', 'JWT tokens'),
        
        # Data Processing
        ('pandas', 'Data analysis'),
        ('numpy', 'Numerical computing'),
        ('networkx', 'Graph algorithms'),
        
        # System
        ('psutil', 'System monitoring'),
        ('git', 'Git integration'),
        
        # Utilities
        ('dotenv', 'Environment variables'),
        ('requests', 'HTTP requests'),
        ('jinja2', 'Template engine'),
        ('watchdog', 'File monitoring'),
        ('tabulate', 'Table formatting'),
        
        # Testing
        ('pytest', 'Testing framework'),
    ]
    
    print("Testing dependencies:")
    print("-" * 80)
    
    passed = 0
    failed = 0
    missing = []
    
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✅ {module:25} - {description}")
            passed += 1
        except ImportError as e:
            print(f"❌ {module:25} - {description}")
            failed += 1
            missing.append(module)
    
    print("-" * 80)
    print()
    
    # Test CodeGenie modules
    print("Testing CodeGenie modules:")
    print("-" * 80)
    
    codegenie_modules = [
        'codegenie.core.config',
        'codegenie.core.agent',
        'codegenie.core.session',
        'codegenie.core.memory',
        'codegenie.cli',
    ]
    
    for module in codegenie_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
            passed += 1
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed += 1
    
    print("-" * 80)
    print()
    
    # Summary
    total = passed + failed
    print(f"Results: {passed}/{total} passed")
    
    if failed > 0:
        print()
        print("❌ FAILED - Missing dependencies:")
        for module in missing:
            print(f"  • {module}")
        print()
        print("To install missing dependencies:")
        print("  pip install -r requirements.txt")
        return 1
    else:
        print()
        print("🎉 SUCCESS - All dependencies are installed and working!")
        print()
        print("You can now run:")
        print("  • python -m src.codegenie.cli start")
        print("  • python codegenie_interactive.py")
        print("  • python demo_full_application.py")
        return 0


if __name__ == "__main__":
    sys.exit(test_core_dependencies())
