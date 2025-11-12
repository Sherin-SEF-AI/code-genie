#!/usr/bin/env python3
"""
Demo script for ProjectScaffolder functionality.

This demonstrates:
1. Project type detection from descriptions
2. Project structure generation
3. Git initialization
4. Dependency installation
"""

import asyncio
import tempfile
from pathlib import Path

from src.codegenie.core.project_scaffolder import (
    ProjectScaffolder,
    ProjectType,
    PackageManager
)


def demo_project_type_detection():
    """Demonstrate project type detection."""
    print("\n" + "="*60)
    print("DEMO 1: Project Type Detection")
    print("="*60)
    
    scaffolder = ProjectScaffolder()
    
    test_descriptions = [
        "Create a FastAPI REST API for user management",
        "Build a React frontend application with TypeScript",
        "Make a Django web application with PostgreSQL",
        "Create a Go CLI tool for file processing",
        "Build a Rust web server with Actix",
        "Simple Flask API for data processing",
        "Next.js application with server-side rendering",
        "Express.js backend API",
    ]
    
    print("\nDetecting project types from descriptions:")
    for desc in test_descriptions:
        project_type = scaffolder.detect_project_type(desc)
        print(f"  '{desc[:50]}...'")
        print(f"  → {project_type.value}\n")


def demo_structure_generation():
    """Demonstrate directory structure generation."""
    print("\n" + "="*60)
    print("DEMO 2: Directory Structure Generation")
    print("="*60)
    
    scaffolder = ProjectScaffolder()
    
    project_types = [
        ProjectType.PYTHON_FASTAPI,
        ProjectType.JAVASCRIPT_REACT,
        ProjectType.GO_WEB,
    ]
    
    for proj_type in project_types:
        print(f"\n{proj_type.value.upper()} Structure:")
        structure = scaffolder.generate_structure(proj_type, "my-project")
        
        print(f"  Directories ({len(structure.directories)}):")
        for directory in structure.directories:
            print(f"    📁 {directory}")
        
        print(f"  Files ({len(structure.files)}):")
        for file_path in sorted(structure.files.keys()):
            print(f"    📄 {file_path}")


def demo_project_creation():
    """Demonstrate complete project creation."""
    print("\n" + "="*60)
    print("DEMO 3: Complete Project Creation")
    print("="*60)
    
    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        scaffolder = ProjectScaffolder(base_path=temp_path)
        
        print("\nCreating a FastAPI project...")
        project = scaffolder.create_project(
            project_type=ProjectType.PYTHON_FASTAPI,
            name="demo-api",
            options={
                'description': 'Demo FastAPI project',
                'author': 'Demo User',
                'version': '0.1.0',
            }
        )
        
        print(f"\n✓ Project created at: {project.path}")
        print(f"  Type: {project.project_type.value}")
        print(f"  Dependencies: {len(project.config.dependencies)}")
        print(f"  Dev Dependencies: {len(project.config.dev_dependencies)}")
        
        # List created files
        print("\n  Created files:")
        for file_path in sorted(project.structure.files.keys()):
            full_path = temp_path / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                print(f"    ✓ {file_path} ({size} bytes)")


def demo_git_initialization():
    """Demonstrate git initialization."""
    print("\n" + "="*60)
    print("DEMO 4: Git Initialization")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        scaffolder = ProjectScaffolder(base_path=temp_path)
        
        print("\nCreating project with git...")
        project = scaffolder.create_project(
            project_type=ProjectType.PYTHON_CLI,
            name="demo-cli",
        )
        
        # Generate .gitignore
        print("\n  Generating .gitignore...")
        scaffolder.generate_gitignore(project.project_type, project.path)
        
        gitignore_path = project.path / '.gitignore'
        if gitignore_path.exists():
            print(f"  ✓ .gitignore created ({gitignore_path.stat().st_size} bytes)")
        
        # Initialize git
        print("\n  Initializing git repository...")
        git_success = scaffolder.initialize_git(project.path, create_initial_commit=True)
        
        if git_success:
            print("  ✓ Git repository initialized")
            print("  ✓ Initial commit created")
        else:
            print("  ✗ Git initialization failed (git may not be installed)")


def demo_package_manager_detection():
    """Demonstrate package manager detection."""
    print("\n" + "="*60)
    print("DEMO 5: Package Manager Detection")
    print("="*60)
    
    scaffolder = ProjectScaffolder()
    
    test_cases = [
        (ProjectType.PYTHON_FASTAPI, "Python FastAPI"),
        (ProjectType.JAVASCRIPT_REACT, "JavaScript React"),
        (ProjectType.TYPESCRIPT_EXPRESS, "TypeScript Express"),
        (ProjectType.GO_WEB, "Go Web"),
        (ProjectType.RUST_CLI, "Rust CLI"),
    ]
    
    print("\nDetected package managers:")
    for proj_type, name in test_cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            project_path = temp_path / "test-project"
            project_path.mkdir()
            
            pm = scaffolder.detect_package_manager(project_path, proj_type)
            print(f"  {name:25} → {pm.value}")


def demo_full_workflow():
    """Demonstrate complete workflow with all features."""
    print("\n" + "="*60)
    print("DEMO 6: Complete Workflow")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        scaffolder = ProjectScaffolder(base_path=temp_path)
        
        def progress_callback(message: str):
            print(f"  → {message}")
        
        print("\nCreating complete project with all features...")
        print("(Note: Dependency installation will be skipped in demo)")
        
        project = scaffolder.create_project_with_git_and_deps(
            project_type="python fastapi rest api",
            name="complete-api",
            options={
                'description': 'Complete API with all features',
                'author': 'Demo User',
            },
            initialize_git=True,
            install_deps=False,  # Skip actual installation in demo
            progress_callback=progress_callback
        )
        
        print(f"\n✓ Complete project created!")
        print(f"  Path: {project.path}")
        print(f"  Type: {project.project_type.value}")
        print(f"  Git initialized: {project.git_initialized}")
        print(f"  Dependencies installed: {project.dependencies_installed}")
        
        # Show project structure
        print("\n  Project structure:")
        for directory in sorted(project.structure.directories):
            print(f"    📁 {directory}")


def main():
    """Run all demos."""
    print("="*60)
    print("PROJECT SCAFFOLDER DEMO")
    print("="*60)
    
    try:
        demo_project_type_detection()
        demo_structure_generation()
        demo_project_creation()
        demo_git_initialization()
        demo_package_manager_detection()
        demo_full_workflow()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
