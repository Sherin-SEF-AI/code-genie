# Template System Guide

## Overview

The Template System provides a powerful way to create, manage, and use project templates in CodeGenie. It supports built-in templates for common frameworks, custom template creation, and template sharing.

## Quick Start

### Using a Built-in Template

```python
from codegenie.core.template_manager import TemplateManager, TemplateType

# Initialize manager
manager = TemplateManager()

# Load a template
template = manager.load_template("python-fastapi", TemplateType.BUILTIN)

# Customize with variables
variables = {
    "project_name": "my-awesome-api",
    "description": "My awesome FastAPI project",
    "version": "1.0.0",
    "license": "MIT"
}

# Use template files with substitution
for template_file in template.files:
    content = manager.substitute_variables(template_file.content, variables)
    # Create file with content...
```

### Listing Available Templates

```python
# List all templates
all_templates = manager.list_templates()

# List by type
builtin = manager.list_templates(TemplateType.BUILTIN)
custom = manager.list_templates(TemplateType.CUSTOM)

# Display templates
for template in builtin:
    print(f"{template.name} v{template.version} - {template.description}")
```

## Built-in Templates

### Python Templates

#### python-fastapi
Modern FastAPI REST API with async support
- **Directories**: app, app/api, app/models, app/services, tests
- **Dependencies**: fastapi, uvicorn, pydantic, python-dotenv
- **Features**: CORS, health endpoint, API docs

#### python-django
Django web application with REST framework
- **Directories**: config, apps, static, media, templates
- **Dependencies**: django, djangorestframework, psycopg2-binary
- **Features**: Django project structure, manage.py

#### python-flask
Flask web application
- **Directories**: app, app/routes, app/models, app/templates, tests
- **Dependencies**: flask, flask-sqlalchemy, python-dotenv
- **Features**: Application factory pattern

### JavaScript Templates

#### javascript-react
React application with Vite
- **Directories**: src, src/components, src/hooks, public
- **Dependencies**: react, react-dom, vite
- **Features**: Modern React, Vite build

#### javascript-nextjs
Next.js application with App Router
- **Directories**: app, components, lib, public
- **Dependencies**: next, react, react-dom
- **Features**: Next.js 14, SSR

#### javascript-express
Express REST API server
- **Directories**: src, src/routes, src/controllers, tests
- **Dependencies**: express, dotenv, cors
- **Features**: REST API structure

### Go Templates

#### go-cli
Go command-line application
- **Directories**: cmd, internal, pkg
- **Features**: Standard Go layout

#### go-web
Go web server
- **Directories**: cmd, internal, pkg, api
- **Features**: HTTP server

### Rust Templates

#### rust-cli
Rust command-line application
- **Directories**: src
- **Dependencies**: clap
- **Features**: CLI with args

#### rust-web
Rust web server with Actix
- **Directories**: src, src/handlers, src/models
- **Dependencies**: actix-web, tokio, serde
- **Features**: Async web server

## Creating Custom Templates

### From an Existing Project

```python
# Create template from project directory
template = manager.create_template_from_project(
    project_path=Path("./my-project"),
    name="my-custom-template",
    description="My custom project template",
    author="Your Name",
    version="1.0.0",
    exclude_patterns=[
        '.git', 'node_modules', '__pycache__',
        '*.pyc', 'venv', '.env'
    ],
    variable_mappings={
        'MyProject': 'project_name',
        'John Doe': 'author',
        '1.0.0': 'version'
    }
)
```

### Cloning an Existing Template

```python
# Clone and customize
cloned = manager.clone_template(
    source_name="python-fastapi",
    new_name="my-fastapi-variant",
    template_type=TemplateType.CUSTOM
)

# Modify the cloned template as needed
# Then save it
manager.save_template(cloned, TemplateType.CUSTOM)
```

## Template Variables

### Variable Syntax

Templates support two variable syntaxes:

1. **Shell-style**: `${variable_name}`
2. **Jinja2-style**: `{{variable_name}}`

Example template content:
```python
# ${project_name}

Welcome to {{project_name}} version ${version}!

Author: ${author}
License: {{license}}
```

### Common Variables

- `project_name` - Name of the project
- `description` - Project description
- `version` - Project version (e.g., "1.0.0")
- `author` - Author name
- `license` - License type (e.g., "MIT")

### Variable Substitution

```python
content = "Project: ${project_name} v${version}"
variables = {
    "project_name": "MyApp",
    "version": "1.0.0"
}
result = manager.substitute_variables(content, variables)
# Result: "Project: MyApp v1.0.0"
```

## Template Validation

### Validating a Template

```python
validation = manager.validate_template(template)

if validation.is_valid:
    print("Template is valid!")
else:
    print("Validation errors:")
    for error in validation.errors:
        print(f"  - {error}")

if validation.warnings:
    print("Warnings:")
    for warning in validation.warnings:
        print(f"  - {warning}")
```

### Validation Checks

The validator checks:
- Required metadata fields (name, version, description)
- Semantic versioning format
- File path validity (no `..`, no absolute paths)
- Duplicate file paths
- Variable references (defined vs used)
- Directory structure validity

## Sharing Templates

### Exporting Templates

```python
# Export to archive
success = manager.export_template(
    name="my-custom-template",
    template_type=TemplateType.CUSTOM,
    export_path=Path("./my-template.tar.gz")
)
```

### Importing Templates

```python
# Import from archive
template = manager.import_template(
    import_path=Path("./shared-template.tar.gz"),
    name="imported-template"  # Optional: rename during import
)
```

## Template Updates

### Checking for Updates

```python
# Check single template
update_info = manager.check_for_updates(
    name="python-fastapi",
    template_type=TemplateType.BUILTIN
)

if update_info and update_info['has_update']:
    print(f"Update available: {update_info['current_version']} -> {update_info['latest_version']}")
```

### Updating Templates

```python
# Update single template
success = manager.update_template(
    name="python-fastapi",
    template_type=TemplateType.BUILTIN,
    auto_update=True
)

# Update all templates
results = manager.update_all_templates(
    template_type=TemplateType.BUILTIN,
    auto_update=True
)

for name, success in results.items():
    status = "✓" if success else "✗"
    print(f"{status} {name}")
```

### Version Comparison

```python
# Compare versions
result = manager.compare_versions("1.0.0", "1.1.0")
# Returns: -1 (first is older)

result = manager.compare_versions("2.0.0", "1.9.9")
# Returns: 1 (first is newer)

result = manager.compare_versions("1.0.0", "1.0.0")
# Returns: 0 (equal)
```

## Template Storage

Templates are stored in `~/.codegenie/templates/` with the following structure:

```
~/.codegenie/templates/
├── builtin/           # Built-in templates
│   ├── python-fastapi/
│   │   ├── template.json
│   │   └── files/
│   │       ├── app/main.py
│   │       ├── requirements.txt
│   │       └── README.md
│   └── javascript-react/
│       └── ...
├── custom/            # User-created templates
│   └── my-template/
│       └── ...
└── imported/          # Imported templates
    └── shared-template/
        └── ...
```

## Advanced Usage

### Creating a Template Programmatically

```python
from codegenie.core.template_manager import (
    Template,
    TemplateMetadata,
    TemplateFile,
    TemplateType
)

# Create template
template = Template(
    metadata=TemplateMetadata(
        name="my-template",
        version="1.0.0",
        description="My custom template",
        author="Your Name",
        tags=["custom", "python"],
        template_type=TemplateType.CUSTOM
    ),
    directories=["src", "tests", "docs"],
    files=[
        TemplateFile(
            path="src/main.py",
            content="# ${project_name}\nprint('Hello, ${project_name}!')",
            is_template=True
        ),
        TemplateFile(
            path="README.md",
            content="# ${project_name}\n\n${description}",
            is_template=True
        )
    ],
    variables={
        "project_name": "MyProject",
        "description": "A sample project"
    },
    dependencies=["requests", "click"],
    dev_dependencies=["pytest", "black"]
)

# Save template
manager.save_template(template, TemplateType.CUSTOM)
```

### Deleting Templates

```python
# Delete a template
success = manager.delete_template(
    name="old-template",
    template_type=TemplateType.CUSTOM
)
```

## Integration with ProjectScaffolder

The Template System integrates seamlessly with ProjectScaffolder:

```python
from codegenie.core.project_scaffolder import ProjectScaffolder
from codegenie.core.template_manager import TemplateManager

# Initialize
scaffolder = ProjectScaffolder()
template_manager = TemplateManager()

# Load template
template = template_manager.load_template("python-fastapi")

# Use template with scaffolder
# (Integration code would go here)
```

## Best Practices

1. **Use Semantic Versioning**: Always use semver format (e.g., "1.0.0")
2. **Validate Templates**: Always validate before saving
3. **Document Variables**: List all variables in template description
4. **Exclude Build Artifacts**: Use exclude_patterns when creating from projects
5. **Test Templates**: Create test projects to verify templates work
6. **Keep Templates Updated**: Regularly check for and apply updates
7. **Use Meaningful Names**: Choose clear, descriptive template names
8. **Add Tags**: Use tags for better template organization

## Troubleshooting

### Template Not Found
```python
template = manager.load_template("my-template")
if template is None:
    # Check if template exists
    templates = manager.list_templates()
    print("Available templates:", [t.name for t in templates])
```

### Variable Not Substituted
- Check variable name spelling
- Ensure variable is defined in template.variables
- Verify syntax: `${var}` or `{{var}}`

### Validation Errors
```python
validation = manager.validate_template(template)
if not validation.is_valid:
    for error in validation.errors:
        print(f"Error: {error}")
```

### Import Failed
- Verify archive format (.tar.gz or .zip)
- Check archive contains template.json
- Ensure archive structure is correct

## API Reference

### TemplateManager

#### Methods

- `load_template(name, template_type)` - Load template
- `save_template(template, template_type)` - Save template
- `list_templates(template_type)` - List templates
- `delete_template(name, template_type)` - Delete template
- `substitute_variables(content, variables)` - Replace variables
- `validate_template(template)` - Validate template
- `create_template_from_project(...)` - Create from project
- `export_template(name, template_type, export_path)` - Export
- `import_template(import_path, name)` - Import
- `clone_template(source_name, new_name, template_type)` - Clone
- `check_for_updates(name, template_type)` - Check updates
- `update_template(name, template_type, auto_update)` - Update
- `update_all_templates(template_type, auto_update)` - Update all
- `compare_versions(version1, version2)` - Compare versions

### Template

#### Attributes

- `metadata` - TemplateMetadata object
- `directories` - List of directory paths
- `files` - List of TemplateFile objects
- `variables` - Dictionary of variables
- `dependencies` - List of dependencies
- `dev_dependencies` - List of dev dependencies
- `post_create_commands` - Commands to run after creation

### TemplateMetadata

#### Attributes

- `name` - Template name
- `version` - Template version
- `description` - Template description
- `author` - Author name
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp
- `tags` - List of tags
- `template_type` - TemplateType enum

## Examples

See the following files for complete examples:
- `demo_template_system.py` - Full demonstration
- `test_template_system_standalone.py` - Unit tests
- `TASK_6_TEMPLATE_SYSTEM_SUMMARY.md` - Implementation details

## Support

For issues or questions:
1. Check this guide
2. Review example code
3. Check validation errors
4. Consult API reference
