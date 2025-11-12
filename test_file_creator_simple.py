#!/usr/bin/env python3
"""
Simple test for FileCreator - tests syntax and basic structure.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test imports
try:
    from codegenie.core.file_creator import (
        FileCreator,
        ContentGenerator,
        DiffPreview,
        FileOperation,
        OperationType,
        OperationStatus,
        Diff,
        Change
    )
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test class instantiation
try:
    file_creator = FileCreator(preview_by_default=False)
    print("✓ FileCreator instantiated")
    
    content_gen = ContentGenerator()
    print("✓ ContentGenerator instantiated")
    
    diff_preview = DiffPreview()
    print("✓ DiffPreview instantiated")
except Exception as e:
    print(f"✗ Instantiation error: {e}")
    sys.exit(1)

# Test content generation
try:
    content = content_gen.generate_content(
        'python',
        context={
            'module_name': 'test',
            'description': 'Test module',
            'functions': [
                {'name': 'test_func', 'parameters': [], 'description': 'Test function'}
            ]
        }
    )
    print("✓ Content generation works")
    print(f"  Generated {len(content)} characters")
except Exception as e:
    print(f"✗ Content generation error: {e}")
    sys.exit(1)

# Test diff generation
try:
    original = "line 1\nline 2\nline 3\n"
    modified = "line 1\nline 2 modified\nline 3\nline 4\n"
    diff = file_creator.generate_diff(original, modified, "test.txt")
    print("✓ Diff generation works")
    print(f"  Additions: {diff.additions}, Deletions: {diff.deletions}")
except Exception as e:
    print(f"✗ Diff generation error: {e}")
    sys.exit(1)

# Test template listing
try:
    templates = content_gen.list_templates()
    print("✓ Template listing works")
    print(f"  Available templates: {len(templates)}")
    for template in templates:
        print(f"    - {template}")
except Exception as e:
    print(f"✗ Template listing error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All tests passed! FileCreator implementation is working.")
print("=" * 60)
