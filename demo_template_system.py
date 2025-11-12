"""
Demo script for Template System.

This script demonstrates:
- Loading and listing templates
- Creating projects from templates
- Variable substitution
- Template validation
- Custom template creation
- Template import/export
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from codegenie.core.template_manager import TemplateManager, TemplateType
from codegenie.core.builtin_templates import initialize_builtin_templates


def demo_template_system():
    """Demonstrate template system functionality."""
    print("=" * 60)
    print("Template System Demo")
    print("=" * 60)
    
    # Initialize template manager
    print("\n1. Initializing Template Manager...")
    template_manager = TemplateManager()
    print(f"   Templates directory: {template_manager.templates_dir}")
    
    # Initialize built-in templates
    print("\n2. Initializing Built-in Templates...")
    count = initialize_builtin_templates(template_manager)
    print(f"   Initialized {count} built-in templates")
    
    # List all templates
    print("\n3. Listing Available Templates...")
    templates = template_manager.list_templates()
    print(f"   Found {len(templates)} templates:")
    for template in templates:
        print(f"   - {template.name} (v{template.version}) - {template.description}")
    
    # Load a specific template
    print("\n4. Loading FastAPI Template...")
    fastapi_template = template_manager.load_template("python-fastapi", TemplateType.BUILTIN)
    if fastapi_template:
        print(f"   Template: {fastapi_template.metadata.name}")
        print(f"   Version: {fastapi_template.metadata.version}")
        print(f"   Directories: {len(fastapi_template.directories)}")
        print(f"   Files: {len(fastapi_template.files)}")
        print(f"   Variables: {list(fastapi_template.variables.keys())}")
    
    # Validate template
    print("\n5. Validating Template...")
    if fastapi_template:
        validation = template_manager.validate_template(fastapi_template)
        print(f"   Valid: {validation.is_valid}")
        if validation.errors:
            print(f"   Errors: {validation.errors}")
        if validation.warnings:
            print(f"   Warnings: {validation.warnings}")
    
    # Demonstrate variable substitution
    print("\n6. Variable Substitution Demo...")
    if fastapi_template:
        sample_content = "Welcome to ${project_name} version ${version}"
        variables = {
            "project_name": "My Awesome API",
            "version": "1.0.0"
        }
        substituted = template_manager.substitute_variables(sample_content, variables)
        print(f"   Original: {sample_content}")
        print(f"   Substituted: {substituted}")
    
    # Clone a template
    print("\n7. Cloning Template...")
    cloned = template_manager.clone_template(
        "python-fastapi",
        "my-custom-fastapi",
        TemplateType.CUSTOM
    )
    if cloned:
        print(f"   Cloned template: {cloned.metadata.name}")
        print(f"   Type: {cloned.metadata.template_type.value}")
    
    # Check for updates
    print("\n8. Checking for Updates...")
    update_info = template_manager.check_for_updates("python-fastapi", TemplateType.BUILTIN)
    if update_info:
        print(f"   Template: {update_info['name']}")
        print(f"   Current version: {update_info['current_version']}")
        print(f"   Latest version: {update_info['latest_version']}")
        print(f"   Has update: {update_info['has_update']}")
    
    # List templates by type
    print("\n9. Listing Templates by Type...")
    for template_type in [TemplateType.BUILTIN, TemplateType.CUSTOM]:
        templates = template_manager.list_templates(template_type)
        print(f"   {template_type.value}: {len(templates)} templates")
        for template in templates:
            print(f"     - {template.name}")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        demo_template_system()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
