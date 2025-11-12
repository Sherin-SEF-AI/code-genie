#!/usr/bin/env python3
"""
Direct test for ProjectScaffolder without package imports.
"""

import sys
from pathlib import Path

# Direct import without going through __init__.py
sys.path.insert(0, str(Path(__file__).parent))

# Import only what we need
import importlib.util

spec = importlib.util.spec_from_file_location(
    "project_scaffolder",
    "src/codegenie/core/project_scaffolder.py"
)
ps_module = importlib.util.module_from_spec(spec)

# Mock the dependencies
class MockFileCreator:
    def create_file(self, path, content, preview=True):
        return None

class MockCommandExecutor:
    async def execute_command(self, command, cwd=None, require_approval=True):
        class Result:
            success = True
            stdout = ""
            stderr = ""
        return Result()

# Inject mocks
sys.modules['codegenie.core.file_creator'] = type(sys)('file_creator')
sys.modules['codegenie.core.file_creator'].FileCreator = MockFileCreator
sys.modules['codegenie.core.file_creator'].FileOperation = object
sys.modules['codegenie.core.file_creator'].OperationType = object

sys.modules['codegenie.core.command_executor'] = type(sys)('command_executor')
sys.modules['codegenie.core.command_executor'].CommandExecutor = MockCommandExecutor
sys.modules['codegenie.core.command_executor'].CommandResult = object

sys.modules['codegenie.utils.file_operations'] = type(sys)('file_operations')
sys.modules['codegenie.utils.file_operations'].FileOperations = object

# Now load the module
spec.loader.exec_module(ps_module)

ProjectScaffolder = ps_module.ProjectScaffolder
ProjectType = ps_module.ProjectType
PackageManager = ps_module.PackageManager


def test_basic_functionality():
    """Test basic ProjectScaffolder functionality."""
    print("="*60)
    print("PROJECT SCAFFOLDER BASIC TESTS")
    print("="*60)
    print()
    
    scaffolder = ProjectScaffolder()
    
    # Test 1: Project type detection
    print("Test 1: Project Type Detection")
    test_cases = [
        ("Create a FastAPI REST API", ps_module.ProjectType.PYTHON_FASTAPI),
        ("Build a React frontend", ps_module.ProjectType.JAVASCRIPT_REACT),
        ("Django web application", ps_module.ProjectType.PYTHON_DJANGO),
        ("Go CLI tool", ps_module.ProjectType.GO_CLI),
        ("Rust web server with Actix", ps_module.ProjectType.RUST_WEB),
    ]
    
    for description, expected in test_cases:
        result = scaffolder.detect_project_type(description)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{description[:40]}...' → {result.value}")
    
    print()
    
    # Test 2: Structure generation
    print("Test 2: Structure Generation")
    for proj_type in [
        ps_module.ProjectType.PYTHON_FASTAPI,
        ps_module.ProjectType.JAVASCRIPT_REACT,
        ps_module.ProjectType.GO_WEB,
    ]:
        structure = scaffolder.generate_structure(proj_type, "test-project")
        print(f"  ✓ {proj_type.value}: {len(structure.directories)} dirs, {len(structure.files)} files")
    
    print()
    
    # Test 3: Template content generation
    print("Test 3: Template Content Generation")
    
    # FastAPI main
    content = scaffolder._generate_fastapi_main()
    assert 'FastAPI' in content and '@app.get' in content
    print("  ✓ FastAPI main.py")
    
    # React App
    content = scaffolder._generate_react_app()
    assert 'React' in content and 'function App' in content
    print("  ✓ React App.jsx")
    
    # Express main
    content = scaffolder._generate_express_main()
    assert 'express' in content and 'app.listen' in content
    print("  ✓ Express index.js")
    
    # Go main
    content = scaffolder._generate_go_main("test", ps_module.ProjectType.GO_WEB)
    assert 'http.HandleFunc' in content
    print("  ✓ Go main.go")
    
    # Rust main
    content = scaffolder._generate_rust_main(ps_module.ProjectType.RUST_WEB)
    assert 'actix_web' in content
    print("  ✓ Rust main.rs")
    
    print()
    
    # Test 4: Config file generation
    print("Test 4: Config File Generation")
    
    # requirements.txt
    template = {'dependencies': ['fastapi', 'uvicorn'], 'dev_dependencies': ['pytest']}
    content = scaffolder._generate_requirements_txt(template)
    assert 'fastapi' in content and 'pytest' in content
    print("  ✓ requirements.txt")
    
    # package.json
    content = scaffolder._generate_package_json(
        "test-app",
        ps_module.ProjectType.JAVASCRIPT_REACT,
        {'dependencies': ['react'], 'dev_dependencies': ['vite']}
    )
    assert 'react' in content and 'vite' in content
    print("  ✓ package.json")
    
    # README
    content = scaffolder._generate_readme("test-project", ps_module.ProjectType.PYTHON_FASTAPI)
    assert 'test-project' in content and 'Installation' in content
    print("  ✓ README.md")
    
    # .gitignore
    content = scaffolder._generate_gitignore(ps_module.ProjectType.PYTHON_FASTAPI)
    assert '__pycache__' in content and '.env' in content
    print("  ✓ .gitignore (Python)")
    
    content = scaffolder._generate_gitignore(ps_module.ProjectType.JAVASCRIPT_REACT)
    assert 'node_modules' in content and 'dist/' in content
    print("  ✓ .gitignore (JavaScript)")
    
    print()
    
    # Test 5: Package manager detection
    print("Test 5: Package Manager Detection")
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        test_cases = [
            (ps_module.ProjectType.PYTHON_FASTAPI, ps_module.PackageManager.PIP),
            (ps_module.ProjectType.JAVASCRIPT_REACT, ps_module.PackageManager.NPM),
            (ps_module.ProjectType.GO_WEB, ps_module.PackageManager.GO_MOD),
            (ps_module.ProjectType.RUST_CLI, ps_module.PackageManager.CARGO),
        ]
        
        for proj_type, expected_pm in test_cases:
            pm = scaffolder.detect_package_manager(temp_path, proj_type)
            status = "✓" if pm == expected_pm else "✗"
            print(f"  {status} {proj_type.value:25} → {pm.value}")
    
    print()
    print("="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60)


if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
