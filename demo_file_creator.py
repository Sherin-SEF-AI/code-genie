#!/usr/bin/env python3
"""
Demo script for FileCreator functionality.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.file_creator import FileCreator, ContentGenerator


def demo_basic_operations():
    """Demonstrate basic file operations."""
    print("=" * 60)
    print("Demo: Basic File Operations")
    print("=" * 60)
    print()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Initialize FileCreator
        file_creator = FileCreator(preview_by_default=False)
        
        # 1. Create a file
        print("1. Creating a Python file...")
        test_file = temp_path / "test_module.py"
        operation = file_creator.create_file(
            test_file,
            '"""Test module."""\n\ndef hello():\n    print("Hello, World!")\n',
            preview=False
        )
        print(f"   Status: {operation.status.value}")
        print(f"   File: {operation.file_path}")
        print()
        
        # 2. Modify the file
        print("2. Modifying the file...")
        new_content = '"""Test module."""\n\ndef hello(name="World"):\n    print(f"Hello, {name}!")\n\ndef goodbye():\n    print("Goodbye!")\n'
        operation = file_creator.modify_file(
            test_file,
            new_content,
            preview=False
        )
        print(f"   Status: {operation.status.value}")
        if operation.diff:
            print(f"   Changes: +{operation.diff.additions} -{operation.diff.deletions}")
        print()
        
        # 3. Show diff
        print("3. Showing diff...")
        if operation.diff:
            print(file_creator.show_diff(operation.diff, colored=False))
        print()
        
        # 4. Delete the file
        print("4. Deleting the file...")
        operation = file_creator.delete_file(test_file, safe=True, preview=False)
        print(f"   Status: {operation.status.value}")
        print()


def demo_content_generation():
    """Demonstrate content generation."""
    print("=" * 60)
    print("Demo: Content Generation")
    print("=" * 60)
    print()
    
    content_gen = ContentGenerator()
    
    # 1. Generate Python module
    print("1. Generating Python module...")
    content = content_gen.generate_content(
        'python',
        context={
            'module_name': 'calculator',
            'description': 'Simple calculator module',
            'author': 'Demo User',
            'functions': [
                {'name': 'add', 'parameters': ['a', 'b'], 'description': 'Add two numbers'},
                {'name': 'subtract', 'parameters': ['a', 'b'], 'description': 'Subtract two numbers'},
            ],
            'include_main': True,
        }
    )
    print(content)
    print()
    
    # 2. Generate JavaScript module
    print("2. Generating JavaScript module...")
    content = content_gen.generate_content(
        'javascript',
        context={
            'description': 'Utility functions',
            'author': 'Demo User',
            'class_name': 'Utils',
            'functions': [
                {'name': 'formatDate', 'parameters': ['date'], 'description': 'Format a date'},
            ],
        }
    )
    print(content)
    print()
    
    # 3. Generate HTML file
    print("3. Generating HTML file...")
    content = content_gen.generate_content(
        'html',
        context={
            'title': 'Demo Page',
            'description': 'A demo HTML page',
        }
    )
    print(content)
    print()


def demo_directory_structure():
    """Demonstrate directory structure creation."""
    print("=" * 60)
    print("Demo: Directory Structure Creation")
    print("=" * 60)
    print()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        file_creator = FileCreator(preview_by_default=False)
        
        # Create a project structure
        structure = {
            'src': {
                '__init__.py': '',
                'main.py': '"""Main module."""\n\ndef main():\n    pass\n',
                'utils': {
                    '__init__.py': '',
                    'helpers.py': '"""Helper functions."""\n',
                }
            },
            'tests': {
                '__init__.py': '',
                'test_main.py': '"""Tests for main module."""\n',
            },
            'README.md': '# Demo Project\n\nA demo project.\n',
        }
        
        print("Creating project structure...")
        operations = file_creator.create_directory_structure(structure, temp_path)
        
        print(f"Created {len(operations)} files")
        for op in operations:
            print(f"  - {op.file_path.relative_to(temp_path)}")
        print()
        
        # List created structure
        print("Directory structure:")
        for item in sorted(temp_path.rglob('*')):
            if item.is_file():
                rel_path = item.relative_to(temp_path)
                print(f"  {rel_path}")
        print()


def demo_templates():
    """Demonstrate template usage."""
    print("=" * 60)
    print("Demo: Template Usage")
    print("=" * 60)
    print()
    
    content_gen = ContentGenerator()
    
    # List available templates
    print("Available templates:")
    for template_name in content_gen.list_templates():
        print(f"  - {template_name}")
    print()
    
    # Use a template
    print("Using 'readme' template...")
    content = content_gen.generate_content(
        'markdown',
        context={
            'title': 'My Project',
            'description': 'A sample project',
            'license': 'MIT',
        },
        template_name='readme'
    )
    print(content)
    print()
    
    # Add custom template
    print("Adding custom template...")
    content_gen.add_template(
        'custom_python',
        '''#!/usr/bin/env python3
"""
{description}
Author: {author}
"""

def main():
    """Main entry point."""
    print("{message}")

if __name__ == "__main__":
    main()
'''
    )
    
    content = content_gen.generate_content(
        'python',
        context={
            'description': 'Custom script',
            'author': 'Demo User',
            'message': 'Hello from custom template!',
        },
        template_name='custom_python'
    )
    print(content)
    print()


def demo_preview_and_approval():
    """Demonstrate preview and approval workflow."""
    print("=" * 60)
    print("Demo: Preview and Approval Workflow")
    print("=" * 60)
    print()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Initialize with preview enabled
        file_creator = FileCreator(preview_by_default=True)
        
        # Create some operations
        print("Creating operations with preview enabled...")
        
        op1 = file_creator.create_file(
            temp_path / "file1.py",
            '"""File 1."""\n\nprint("Hello")\n',
            preview=True
        )
        
        op2 = file_creator.create_file(
            temp_path / "file2.py",
            '"""File 2."""\n\nprint("World")\n',
            preview=True
        )
        
        print(f"Created {len(file_creator.get_pending_operations())} pending operations")
        print()
        
        # Show preview
        print("Preview of pending operations:")
        preview = file_creator.preview_pending_operations()
        print(preview)
        print()
        
        # Approve all (without interactive confirmation for demo)
        print("Approving all operations...")
        results = file_creator.approve_all_pending()
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print()


def main():
    """Run all demos."""
    demos = [
        ("Basic Operations", demo_basic_operations),
        ("Content Generation", demo_content_generation),
        ("Directory Structure", demo_directory_structure),
        ("Templates", demo_templates),
        ("Preview and Approval", demo_preview_and_approval),
    ]
    
    print("\n" + "=" * 60)
    print("FileCreator Demo")
    print("=" * 60)
    print()
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"Error in {name} demo: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
