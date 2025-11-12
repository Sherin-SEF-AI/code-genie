#!/usr/bin/env python3
"""
Simple test for ProjectScaffolder without full dependencies.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from codegenie.core.project_scaffolder import (
    ProjectScaffolder,
    ProjectType,
    PackageManager,
    DirectoryStructure,
    ProjectConfig,
)


def test_project_type_detection():
    """Test project type detection."""
    print("Testing project type detection...")
    
    scaffolder = ProjectScaffolder()
    
    # Test FastAPI detection
    result = scaffolder.detect_project_type("Create a FastAPI REST API")
    assert result == ProjectType.PYTHON_FASTAPI, f"Expected PYTHON_FASTAPI, got {result}"
    print("  ✓ FastAPI detection works")
    
    # Test React detection
    result = scaffolder.detect_project_type("Build a React frontend application")
    assert result == ProjectType.JAVASCRIPT_REACT, f"Expected JAVASCRIPT_REACT, got {result}"
    print("  ✓ React detection works")
    
    # Test Django detection
    result = scaffolder.detect_project_type("Django web application")
    assert result == ProjectType.PYTHON_DJANGO, f"Expected PYTHON_DJANGO, got {result}"
    print("  ✓ Django detection works")
    
    # Test Go detection
    result = scaffolder.detect_project_type("Go CLI tool")
    assert result == ProjectType.GO_CLI, f"Expected GO_CLI, got {result}"
    print("  ✓ Go CLI detection works")
    
    print("✓ All project type detection tests passed\n")


def test_structure_generation():
    """Test directory structure generation."""
    print("Testing structure generation...")
    
    scaffolder = ProjectScaffolder()
    
    # Test FastAPI structure
    structure = scaffolder.generate_structure(ProjectType.PYTHON_FASTAPI, "test-api")
    assert len(structure.directories) > 0, "Should have directories"
    assert len(structure.files) > 0, "Should have files"
    print(f"  ✓ FastAPI structure: {len(structure.directories)} dirs, {len(structure.files)} files")
    
    # Test React structure
    structure = scaffolder.generate_structure(ProjectType.JAVASCRIPT_REACT, "test-app")
    assert len(structure.directories) > 0, "Should have directories"
    assert len(structure.files) > 0, "Should have files"
    print(f"  ✓ React structure: {len(structure.directories)} dirs, {len(structure.files)} files")
    
    print("✓ All structure generation tests passed\n")


def test_config_file_generation():
    """Test configuration file generation."""
    print("Testing config file generation...")
    
    scaffolder = ProjectScaffolder()
    
    # Test requirements.txt generation
    template = {'dependencies': ['fastapi', 'uvicorn'], 'dev_dependencies': ['pytest']}
    content = scaffolder._generate_requirements_txt(template)
    assert 'fastapi' in content, "Should contain fastapi"
    assert 'pytest' in content, "Should contain pytest"
    print("  ✓ requirements.txt generation works")
    
    # Test package.json generation
    content = scaffolder._generate_package_json(
        "test-app",
        ProjectType.JAVASCRIPT_REACT,
        {'dependencies': ['react'], 'dev_dependencies': ['vite']}
    )
    assert 'react' in content, "Should contain react"
    assert 'vite' in content, "Should contain vite"
    print("  ✓ package.json generation works")
    
    # Test README generation
    content = scaffolder._generate_readme("test-project", ProjectType.PYTHON_FASTAPI)
    assert 'test-project' in content, "Should contain project name"
    assert 'Installation' in content, "Should have Installation section"
    print("  ✓ README generation works")
    
    print("✓ All config file generation tests passed\n")


def test_package_manager_detection():
    """Test package manager detection."""
    print("Testing package manager detection...")
    
    scaffolder = ProjectScaffolder()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test Python detection
        pm = scaffolder.detect_package_manager(temp_path, ProjectType.PYTHON_FASTAPI)
        assert pm == PackageManager.PIP, f"Expected PIP, got {pm}"
        print("  ✓ Python package manager detection works")
        
        # Test JavaScript detection
        pm = scaffolder.detect_package_manager(temp_path, ProjectType.JAVASCRIPT_REACT)
        assert pm == PackageManager.NPM, f"Expected NPM, got {pm}"
        print("  ✓ JavaScript package manager detection works")
        
        # Test Go detection
        pm = scaffolder.detect_package_manager(temp_path, ProjectType.GO_WEB)
        assert pm == PackageManager.GO_MOD, f"Expected GO_MOD, got {pm}"
        print("  ✓ Go package manager detection works")
        
        # Test Rust detection
        pm = scaffolder.detect_package_manager(temp_path, ProjectType.RUST_CLI)
        assert pm == PackageManager.CARGO, f"Expected CARGO, got {pm}"
        print("  ✓ Rust package manager detection works")
    
    print("✓ All package manager detection tests passed\n")


def test_template_content():
    """Test template content generation."""
    print("Testing template content generation...")
    
    scaffolder = ProjectScaffolder()
    
    # Test FastAPI main.py
    content = scaffolder._generate_fastapi_main()
    assert 'FastAPI' in content, "Should contain FastAPI"
    assert '@app.get' in content, "Should have route decorators"
    print("  ✓ FastAPI main.py generation works")
    
    # Test Flask init
    content = scaffolder._generate_flask_init()
    assert 'Flask' in content, "Should contain Flask"
    assert 'create_app' in content, "Should have create_app function"
    print("  ✓ Flask __init__.py generation works")
    
    # Test React App
    content = scaffolder._generate_react_app()
    assert 'React' in content, "Should contain React"
    assert 'function App' in content, "Should have App function"
    print("  ✓ React App.jsx generation works")
    
    # Test Express main
    content = scaffolder._generate_express_main()
    assert 'express' in content, "Should contain express"
    assert 'app.listen' in content, "Should have app.listen"
    print("  ✓ Express index.js generation works")
    
    print("✓ All template content tests passed\n")


def test_gitignore_generation():
    """Test .gitignore generation."""
    print("Testing .gitignore generation...")
    
    scaffolder = ProjectScaffolder()
    
    # Test Python .gitignore
    content = scaffolder._generate_gitignore(ProjectType.PYTHON_FASTAPI)
    assert '__pycache__' in content, "Should ignore __pycache__"
    assert '.env' in content, "Should ignore .env"
    print("  ✓ Python .gitignore generation works")
    
    # Test JavaScript .gitignore
    content = scaffolder._generate_gitignore(ProjectType.JAVASCRIPT_REACT)
    assert 'node_modules' in content, "Should ignore node_modules"
    assert 'dist/' in content, "Should ignore dist"
    print("  ✓ JavaScript .gitignore generation works")
    
    print("✓ All .gitignore generation tests passed\n")


def main():
    """Run all tests."""
    print("="*60)
    print("PROJECT SCAFFOLDER TESTS")
    print("="*60)
    print()
    
    try:
        test_project_type_detection()
        test_structure_generation()
        test_config_file_generation()
        test_package_manager_detection()
        test_template_content()
        test_gitignore_generation()
        
        print("="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
