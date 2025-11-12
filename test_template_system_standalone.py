"""
Standalone test for Template System.

Tests the template system without requiring full dependencies.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import only what we need
from codegenie.core.template_manager import (
    Template,
    TemplateMetadata,
    TemplateFile,
    TemplateType,
    TemplateManager,
)
from codegenie.core.builtin_templates import (
    get_fastapi_template,
    get_react_template,
    BUILTIN_TEMPLATES,
)


def test_template_creation():
    """Test creating a template."""
    print("Test 1: Template Creation")
    
    template = get_fastapi_template()
    
    assert template.metadata.name == "python-fastapi"
    assert template.metadata.version == "1.0.0"
    assert len(template.directories) > 0
    assert len(template.files) > 0
    assert "project_name" in template.variables
    
    print("  ✓ Template created successfully")
    print(f"    - Name: {template.metadata.name}")
    print(f"    - Directories: {len(template.directories)}")
    print(f"    - Files: {len(template.files)}")
    print(f"    - Variables: {list(template.variables.keys())}")


def test_template_manager():
    """Test template manager functionality."""
    print("\nTest 2: Template Manager")
    
    # Create temp directory for testing
    temp_dir = Path("/tmp/codegenie_test_templates")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    manager = TemplateManager(templates_dir=temp_dir)
    
    assert manager.templates_dir == temp_dir
    assert manager.builtin_dir.exists()
    assert manager.custom_dir.exists()
    
    print("  ✓ Template manager initialized")
    print(f"    - Templates dir: {manager.templates_dir}")


def test_save_and_load():
    """Test saving and loading templates."""
    print("\nTest 3: Save and Load Template")
    
    temp_dir = Path("/tmp/codegenie_test_templates")
    manager = TemplateManager(templates_dir=temp_dir)
    
    # Create and save a template
    template = get_fastapi_template()
    success = manager.save_template(template, TemplateType.BUILTIN)
    
    assert success, "Failed to save template"
    print("  ✓ Template saved successfully")
    
    # Load the template
    loaded = manager.load_template("python-fastapi", TemplateType.BUILTIN)
    
    assert loaded is not None, "Failed to load template"
    assert loaded.metadata.name == template.metadata.name
    assert loaded.metadata.version == template.metadata.version
    
    print("  ✓ Template loaded successfully")
    print(f"    - Name: {loaded.metadata.name}")
    print(f"    - Version: {loaded.metadata.version}")


def test_variable_substitution():
    """Test variable substitution."""
    print("\nTest 4: Variable Substitution")
    
    manager = TemplateManager()
    
    # Test ${var} syntax
    content1 = "Project: ${project_name}, Version: ${version}"
    variables = {"project_name": "MyApp", "version": "1.0.0"}
    result1 = manager.substitute_variables(content1, variables)
    
    assert "MyApp" in result1
    assert "1.0.0" in result1
    print("  ✓ ${var} syntax works")
    print(f"    - Input: {content1}")
    print(f"    - Output: {result1}")
    
    # Test {{var}} syntax
    content2 = "Project: {{project_name}}, Version: {{version}}"
    result2 = manager.substitute_variables(content2, variables)
    
    assert "MyApp" in result2
    assert "1.0.0" in result2
    print("  ✓ {{var}} syntax works")
    print(f"    - Input: {content2}")
    print(f"    - Output: {result2}")


def test_template_validation():
    """Test template validation."""
    print("\nTest 5: Template Validation")
    
    manager = TemplateManager()
    template = get_fastapi_template()
    
    validation = manager.validate_template(template)
    
    assert validation.is_valid, f"Validation failed: {validation.errors}"
    print("  ✓ Template validation passed")
    print(f"    - Errors: {len(validation.errors)}")
    print(f"    - Warnings: {len(validation.warnings)}")
    
    if validation.warnings:
        for warning in validation.warnings:
            print(f"      - {warning}")


def test_list_templates():
    """Test listing templates."""
    print("\nTest 6: List Templates")
    
    temp_dir = Path("/tmp/codegenie_test_templates")
    manager = TemplateManager(templates_dir=temp_dir)
    
    # Save a few templates
    for name, template_func in list(BUILTIN_TEMPLATES.items())[:3]:
        template = template_func()
        manager.save_template(template, TemplateType.BUILTIN)
    
    # List templates
    templates = manager.list_templates(TemplateType.BUILTIN)
    
    assert len(templates) >= 3, f"Expected at least 3 templates, got {len(templates)}"
    print(f"  ✓ Found {len(templates)} templates")
    
    for template in templates:
        print(f"    - {template.name} (v{template.version})")


def test_clone_template():
    """Test cloning a template."""
    print("\nTest 7: Clone Template")
    
    temp_dir = Path("/tmp/codegenie_test_templates")
    manager = TemplateManager(templates_dir=temp_dir)
    
    # Save original template
    original = get_fastapi_template()
    manager.save_template(original, TemplateType.BUILTIN)
    
    # Clone it
    cloned = manager.clone_template(
        "python-fastapi",
        "my-custom-fastapi",
        TemplateType.CUSTOM
    )
    
    assert cloned is not None, "Failed to clone template"
    assert cloned.metadata.name == "my-custom-fastapi"
    assert cloned.metadata.template_type == TemplateType.CUSTOM
    
    print("  ✓ Template cloned successfully")
    print(f"    - Original: {original.metadata.name}")
    print(f"    - Clone: {cloned.metadata.name}")


def test_version_comparison():
    """Test version comparison."""
    print("\nTest 8: Version Comparison")
    
    manager = TemplateManager()
    
    # Test various version comparisons
    tests = [
        ("1.0.0", "1.0.0", 0),
        ("1.0.0", "1.0.1", -1),
        ("1.1.0", "1.0.0", 1),
        ("2.0.0", "1.9.9", 1),
    ]
    
    for v1, v2, expected in tests:
        result = manager.compare_versions(v1, v2)
        assert result == expected, f"Expected {v1} vs {v2} = {expected}, got {result}"
        
        if result == -1:
            comparison = "<"
        elif result == 0:
            comparison = "=="
        else:
            comparison = ">"
        
        print(f"  ✓ {v1} {comparison} {v2}")


def test_builtin_templates():
    """Test all built-in templates."""
    print("\nTest 9: Built-in Templates")
    
    print(f"  Found {len(BUILTIN_TEMPLATES)} built-in templates:")
    
    for name, template_func in BUILTIN_TEMPLATES.items():
        template = template_func()
        assert template.metadata.name == name
        assert template.metadata.version
        assert len(template.files) > 0
        print(f"    ✓ {name} (v{template.metadata.version})")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Template System Tests")
    print("=" * 60)
    
    tests = [
        test_template_creation,
        test_template_manager,
        test_save_and_load,
        test_variable_substitution,
        test_template_validation,
        test_list_templates,
        test_clone_template,
        test_version_comparison,
        test_builtin_templates,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
