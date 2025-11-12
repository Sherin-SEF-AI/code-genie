"""
Template Manager for project scaffolding.

This module provides template management with:
- Template loading from files and directories
- Template variable substitution
- Template validation
- Custom template support
- Template versioning and updates
"""

import json
import logging
import re
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from string import Template as StringTemplate

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Types of templates."""
    BUILTIN = "builtin"
    CUSTOM = "custom"
    IMPORTED = "imported"


@dataclass
class TemplateMetadata:
    """Metadata for a template."""
    name: str
    version: str
    description: str
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    template_type: TemplateType = TemplateType.CUSTOM
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['template_type'] = self.template_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateMetadata':
        """Create from dictionary."""
        if 'template_type' in data and isinstance(data['template_type'], str):
            data['template_type'] = TemplateType(data['template_type'])
        return cls(**data)


@dataclass
class TemplateFile:
    """Represents a file in a template."""
    path: str  # Relative path within project
    content: str  # File content with variables
    is_template: bool = True  # Whether to perform variable substitution
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateFile':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Template:
    """Represents a project template."""
    metadata: TemplateMetadata
    directories: List[str]  # Directory paths to create
    files: List[TemplateFile]  # Files to create
    variables: Dict[str, Any] = field(default_factory=dict)  # Default variable values
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    post_create_commands: List[str] = field(default_factory=list)  # Commands to run after creation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'metadata': self.metadata.to_dict(),
            'directories': self.directories,
            'files': [f.to_dict() for f in self.files],
            'variables': self.variables,
            'dependencies': self.dependencies,
            'dev_dependencies': self.dev_dependencies,
            'post_create_commands': self.post_create_commands,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """Create from dictionary."""
        return cls(
            metadata=TemplateMetadata.from_dict(data['metadata']),
            directories=data.get('directories', []),
            files=[TemplateFile.from_dict(f) for f in data.get('files', [])],
            variables=data.get('variables', {}),
            dependencies=data.get('dependencies', []),
            dev_dependencies=data.get('dev_dependencies', []),
            post_create_commands=data.get('post_create_commands', []),
        )


@dataclass
class ValidationResult:
    """Result of template validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class TemplateManager:
    """
    Template management system for project scaffolding.
    
    Provides:
    - Template loading from files and directories
    - Variable substitution in templates
    - Template validation
    - Custom template support
    - Template versioning
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template manager.
        
        Args:
            templates_dir: Directory containing templates (defaults to ~/.codegenie/templates)
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path.home() / '.codegenie' / 'templates'
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Separate directories for different template types
        self.builtin_dir = self.templates_dir / 'builtin'
        self.custom_dir = self.templates_dir / 'custom'
        self.imported_dir = self.templates_dir / 'imported'
        
        for dir_path in [self.builtin_dir, self.custom_dir, self.imported_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Cache of loaded templates
        self._template_cache: Dict[str, Template] = {}
        
        logger.info(f"Initialized TemplateManager with templates_dir: {self.templates_dir}")
    
    def load_template(self, name: str, template_type: Optional[TemplateType] = None) -> Optional[Template]:
        """
        Load a template by name.
        
        Args:
            name: Name of the template
            template_type: Type of template (searches all if None)
            
        Returns:
            Template object or None if not found
        """
        # Check cache first
        cache_key = f"{template_type.value if template_type else 'any'}:{name}"
        if cache_key in self._template_cache:
            logger.debug(f"Loaded template from cache: {name}")
            return self._template_cache[cache_key]
        
        # Determine search directories
        if template_type:
            search_dirs = [self._get_type_dir(template_type)]
        else:
            search_dirs = [self.builtin_dir, self.custom_dir, self.imported_dir]
        
        # Search for template
        for search_dir in search_dirs:
            template_path = search_dir / name / 'template.json'
            if template_path.exists():
                try:
                    template = self._load_template_from_file(template_path)
                    self._template_cache[cache_key] = template
                    logger.info(f"Loaded template: {name} from {search_dir}")
                    return template
                except Exception as e:
                    logger.error(f"Error loading template {name}: {e}")
                    return None
        
        logger.warning(f"Template not found: {name}")
        return None
    
    def _load_template_from_file(self, template_path: Path) -> Template:
        """Load template from JSON file."""
        with open(template_path, 'r') as f:
            data = json.load(f)
        
        template = Template.from_dict(data)
        
        # Load file contents from separate files if they exist
        template_dir = template_path.parent
        for template_file in template.files:
            file_path = template_dir / 'files' / template_file.path
            if file_path.exists():
                with open(file_path, 'r') as f:
                    template_file.content = f.read()
        
        return template
    
    def save_template(self, template: Template, template_type: TemplateType = TemplateType.CUSTOM) -> bool:
        """
        Save a template to disk.
        
        Args:
            template: Template to save
            template_type: Type of template
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update metadata
            template.metadata.template_type = template_type
            template.metadata.updated_at = datetime.now().isoformat()
            
            # Determine save directory
            save_dir = self._get_type_dir(template_type) / template.metadata.name
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Save template metadata and structure
            template_data = template.to_dict()
            
            # Save file contents separately
            files_dir = save_dir / 'files'
            files_dir.mkdir(parents=True, exist_ok=True)
            
            for template_file in template.files:
                file_path = files_dir / template_file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(template_file.content)
            
            # Save template.json without file contents (they're in separate files)
            template_data_copy = template_data.copy()
            template_data_copy['files'] = [
                {**f, 'content': ''} for f in template_data_copy['files']
            ]
            
            template_file_path = save_dir / 'template.json'
            with open(template_file_path, 'w') as f:
                json.dump(template_data_copy, f, indent=2)
            
            logger.info(f"Saved template: {template.metadata.name} to {save_dir}")
            
            # Update cache
            cache_key = f"{template_type.value}:{template.metadata.name}"
            self._template_cache[cache_key] = template
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            return False
    
    def list_templates(self, template_type: Optional[TemplateType] = None) -> List[TemplateMetadata]:
        """
        List available templates.
        
        Args:
            template_type: Filter by template type (None for all)
            
        Returns:
            List of template metadata
        """
        templates = []
        
        # Determine search directories
        if template_type:
            search_dirs = [(self._get_type_dir(template_type), template_type)]
        else:
            search_dirs = [
                (self.builtin_dir, TemplateType.BUILTIN),
                (self.custom_dir, TemplateType.CUSTOM),
                (self.imported_dir, TemplateType.IMPORTED),
            ]
        
        for search_dir, ttype in search_dirs:
            if not search_dir.exists():
                continue
            
            for template_dir in search_dir.iterdir():
                if not template_dir.is_dir():
                    continue
                
                template_file = template_dir / 'template.json'
                if template_file.exists():
                    try:
                        with open(template_file, 'r') as f:
                            data = json.load(f)
                        metadata = TemplateMetadata.from_dict(data['metadata'])
                        metadata.template_type = ttype
                        templates.append(metadata)
                    except Exception as e:
                        logger.error(f"Error reading template metadata from {template_dir}: {e}")
        
        return templates
    
    def substitute_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables in template content.
        
        Supports both ${var} and {{var}} syntax.
        
        Args:
            content: Template content with variables
            variables: Dictionary of variable values
            
        Returns:
            Content with variables substituted
        """
        # First handle ${var} syntax using string.Template
        try:
            template = StringTemplate(content)
            content = template.safe_substitute(variables)
        except Exception as e:
            logger.warning(f"Error in ${} variable substitution: {e}")
        
        # Then handle {{var}} syntax
        for var_name, var_value in variables.items():
            pattern = r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}'
            content = re.sub(pattern, str(var_value), content)
        
        return content
    
    def validate_template(self, template: Template) -> ValidationResult:
        """
        Validate a template.
        
        Checks:
        - Required metadata fields
        - File path validity
        - Variable references
        - Directory structure
        
        Args:
            template: Template to validate
            
        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []
        
        # Validate metadata
        if not template.metadata.name:
            errors.append("Template name is required")
        if not template.metadata.version:
            errors.append("Template version is required")
        if not template.metadata.description:
            warnings.append("Template description is missing")
        
        # Validate version format (should be semver-like)
        if template.metadata.version:
            if not re.match(r'^\d+\.\d+\.\d+', template.metadata.version):
                warnings.append(f"Version '{template.metadata.version}' doesn't follow semver format")
        
        # Validate file paths
        file_paths = set()
        for template_file in template.files:
            # Check for duplicate paths
            if template_file.path in file_paths:
                errors.append(f"Duplicate file path: {template_file.path}")
            file_paths.add(template_file.path)
            
            # Check for invalid characters
            if '..' in template_file.path:
                errors.append(f"Invalid file path (contains '..'): {template_file.path}")
            
            # Check for absolute paths
            if Path(template_file.path).is_absolute():
                errors.append(f"File path must be relative: {template_file.path}")
        
        # Validate variable references
        defined_vars = set(template.variables.keys())
        used_vars = self._extract_variables(template)
        
        undefined_vars = used_vars - defined_vars
        if undefined_vars:
            warnings.append(f"Variables used but not defined: {', '.join(undefined_vars)}")
        
        unused_vars = defined_vars - used_vars
        if unused_vars:
            warnings.append(f"Variables defined but not used: {', '.join(unused_vars)}")
        
        # Validate directory structure
        for directory in template.directories:
            if '..' in directory:
                errors.append(f"Invalid directory path (contains '..'): {directory}")
            if Path(directory).is_absolute():
                errors.append(f"Directory path must be relative: {directory}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Template validation passed: {template.metadata.name}")
        else:
            logger.warning(f"Template validation failed: {template.metadata.name} ({len(errors)} errors)")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def _extract_variables(self, template: Template) -> Set[str]:
        """Extract all variable references from template."""
        variables = set()
        
        # Extract from file contents
        for template_file in template.files:
            # Find ${var} syntax
            variables.update(re.findall(r'\$\{(\w+)\}', template_file.content))
            # Find {{var}} syntax
            variables.update(re.findall(r'\{\{\s*(\w+)\s*\}\}', template_file.content))
        
        # Extract from directories
        for directory in template.directories:
            variables.update(re.findall(r'\$\{(\w+)\}', directory))
            variables.update(re.findall(r'\{\{\s*(\w+)\s*\}\}', directory))
        
        # Extract from post-create commands
        for command in template.post_create_commands:
            variables.update(re.findall(r'\$\{(\w+)\}', command))
            variables.update(re.findall(r'\{\{\s*(\w+)\s*\}\}', command))
        
        return variables
    
    def delete_template(self, name: str, template_type: TemplateType) -> bool:
        """
        Delete a template.
        
        Args:
            name: Name of the template
            template_type: Type of template
            
        Returns:
            True if successful, False otherwise
        """
        try:
            template_dir = self._get_type_dir(template_type) / name
            
            if not template_dir.exists():
                logger.warning(f"Template not found: {name}")
                return False
            
            # Remove from cache
            cache_key = f"{template_type.value}:{name}"
            if cache_key in self._template_cache:
                del self._template_cache[cache_key]
            
            # Delete directory
            shutil.rmtree(template_dir)
            
            logger.info(f"Deleted template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False
    
    def _get_type_dir(self, template_type: TemplateType) -> Path:
        """Get directory for template type."""
        if template_type == TemplateType.BUILTIN:
            return self.builtin_dir
        elif template_type == TemplateType.CUSTOM:
            return self.custom_dir
        elif template_type == TemplateType.IMPORTED:
            return self.imported_dir
        else:
            raise ValueError(f"Unknown template type: {template_type}")
    
    def export_template(self, name: str, template_type: TemplateType, export_path: Path) -> bool:
        """
        Export a template to a file.
        
        Args:
            name: Name of the template
            template_type: Type of template
            export_path: Path to export to (should be a .tar.gz or .zip file)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            template_dir = self._get_type_dir(template_type) / name
            
            if not template_dir.exists():
                logger.error(f"Template not found: {name}")
                return False
            
            # Create archive
            export_path = Path(export_path)
            if export_path.suffix == '.zip':
                shutil.make_archive(
                    str(export_path.with_suffix('')),
                    'zip',
                    template_dir.parent,
                    template_dir.name
                )
            else:
                # Default to tar.gz
                shutil.make_archive(
                    str(export_path.with_suffix('').with_suffix('')),
                    'gztar',
                    template_dir.parent,
                    template_dir.name
                )
            
            logger.info(f"Exported template {name} to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting template: {e}")
            return False
    
    def import_template(self, import_path: Path, name: Optional[str] = None) -> Optional[Template]:
        """
        Import a template from a file.
        
        Args:
            import_path: Path to template archive (.tar.gz or .zip)
            name: Optional name for the imported template (uses original if None)
            
        Returns:
            Imported Template object or None if failed
        """
        try:
            import_path = Path(import_path)
            
            if not import_path.exists():
                logger.error(f"Import file not found: {import_path}")
                return None
            
            # Extract archive to temporary location
            temp_dir = self.templates_dir / 'temp_import'
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            if import_path.suffix == '.zip':
                shutil.unpack_archive(import_path, temp_dir, 'zip')
            else:
                shutil.unpack_archive(import_path, temp_dir, 'gztar')
            
            # Find template.json in extracted files
            template_json = None
            for root, dirs, files in temp_dir.walk():
                if 'template.json' in files:
                    template_json = root / 'template.json'
                    break
            
            if not template_json:
                logger.error("No template.json found in archive")
                shutil.rmtree(temp_dir)
                return None
            
            # Load template
            template = self._load_template_from_file(template_json)
            
            # Rename if requested
            if name:
                template.metadata.name = name
            
            # Save to imported directory
            success = self.save_template(template, TemplateType.IMPORTED)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            if success:
                logger.info(f"Imported template: {template.metadata.name}")
                return template
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error importing template: {e}")
            return None
    
    def create_template_from_project(
        self,
        project_path: Path,
        name: str,
        description: str = "",
        author: str = "",
        version: str = "1.0.0",
        exclude_patterns: Optional[List[str]] = None,
        variable_mappings: Optional[Dict[str, str]] = None,
    ) -> Optional[Template]:
        """
        Create a custom template from an existing project.
        
        Args:
            project_path: Path to the project directory
            name: Name for the template
            description: Description of the template
            author: Author name
            version: Template version
            exclude_patterns: Patterns to exclude (e.g., ['node_modules', '.git', '__pycache__'])
            variable_mappings: Map actual values to variable names (e.g., {'MyProject': 'project_name'})
            
        Returns:
            Created Template object or None if failed
        """
        try:
            project_path = Path(project_path)
            
            if not project_path.exists() or not project_path.is_dir():
                logger.error(f"Project path not found or not a directory: {project_path}")
                return None
            
            # Default exclude patterns
            if exclude_patterns is None:
                exclude_patterns = [
                    '.git', '.gitignore', '__pycache__', '*.pyc', 'node_modules',
                    'venv', '.venv', 'env', '.env', 'dist', 'build', '.DS_Store',
                    '*.egg-info', '.pytest_cache', '.coverage', 'coverage',
                ]
            
            # Default variable mappings
            if variable_mappings is None:
                variable_mappings = {}
            
            # Scan project structure
            directories = []
            files = []
            
            for item in project_path.rglob('*'):
                # Skip excluded patterns
                if self._should_exclude(item, project_path, exclude_patterns):
                    continue
                
                relative_path = item.relative_to(project_path)
                
                if item.is_dir():
                    directories.append(str(relative_path))
                elif item.is_file():
                    try:
                        # Read file content
                        with open(item, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Apply variable mappings
                        for actual_value, var_name in variable_mappings.items():
                            content = content.replace(actual_value, f'${{{var_name}}}')
                        
                        files.append(TemplateFile(
                            path=str(relative_path),
                            content=content,
                            is_template=True,
                        ))
                    except (UnicodeDecodeError, PermissionError) as e:
                        logger.warning(f"Skipping file {item}: {e}")
                        continue
            
            # Create template metadata
            metadata = TemplateMetadata(
                name=name,
                version=version,
                description=description or f"Custom template created from {project_path.name}",
                author=author,
                tags=["custom"],
                template_type=TemplateType.CUSTOM,
            )
            
            # Extract variables from mappings
            variables = {var_name: actual_value for actual_value, var_name in variable_mappings.items()}
            
            # Create template
            template = Template(
                metadata=metadata,
                directories=directories,
                files=files,
                variables=variables,
            )
            
            # Validate template
            validation = self.validate_template(template)
            if not validation.is_valid:
                logger.error(f"Template validation failed: {validation.errors}")
                return None
            
            # Save template
            if self.save_template(template, TemplateType.CUSTOM):
                logger.info(f"Created custom template: {name}")
                return template
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error creating template from project: {e}")
            return None
    
    def _should_exclude(self, path: Path, base_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if path should be excluded based on patterns."""
        relative_path = path.relative_to(base_path)
        path_str = str(relative_path)
        
        for pattern in exclude_patterns:
            # Handle glob patterns
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                    return True
            # Handle exact matches
            elif pattern in path_str or path.name == pattern:
                return True
        
        return False
    
    def share_template(self, name: str, template_type: TemplateType, share_url: str) -> bool:
        """
        Share a template to a remote location.
        
        This is a placeholder for future implementation of template sharing.
        Could integrate with GitHub, GitLab, or a custom template registry.
        
        Args:
            name: Name of the template
            template_type: Type of template
            share_url: URL to share to
            
        Returns:
            True if successful, False otherwise
        """
        logger.warning("Template sharing not yet implemented")
        return False
    
    def clone_template(self, source_name: str, new_name: str, template_type: TemplateType = TemplateType.CUSTOM) -> Optional[Template]:
        """
        Clone an existing template with a new name.
        
        Args:
            source_name: Name of the template to clone
            new_name: Name for the cloned template
            template_type: Type for the new template
            
        Returns:
            Cloned Template object or None if failed
        """
        try:
            # Load source template
            source_template = self.load_template(source_name)
            
            if not source_template:
                logger.error(f"Source template not found: {source_name}")
                return None
            
            # Create new template with updated metadata
            cloned_template = Template(
                metadata=TemplateMetadata(
                    name=new_name,
                    version=source_template.metadata.version,
                    description=f"Cloned from {source_name}: {source_template.metadata.description}",
                    author=source_template.metadata.author,
                    tags=source_template.metadata.tags.copy(),
                    template_type=template_type,
                ),
                directories=source_template.directories.copy(),
                files=[TemplateFile(**f.to_dict()) for f in source_template.files],
                variables=source_template.variables.copy(),
                dependencies=source_template.dependencies.copy(),
                dev_dependencies=source_template.dev_dependencies.copy(),
                post_create_commands=source_template.post_create_commands.copy(),
            )
            
            # Save cloned template
            if self.save_template(cloned_template, template_type):
                logger.info(f"Cloned template {source_name} to {new_name}")
                return cloned_template
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error cloning template: {e}")
            return None
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two semantic version strings.
        
        Args:
            version1: First version string (e.g., "1.2.3")
            version2: Second version string (e.g., "1.3.0")
            
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        def parse_version(version: str) -> tuple:
            """Parse version string into tuple of integers."""
            parts = version.split('.')
            return tuple(int(p) for p in parts if p.isdigit())
        
        try:
            v1 = parse_version(version1)
            v2 = parse_version(version2)
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0
        except Exception as e:
            logger.warning(f"Error comparing versions: {e}")
            return 0
    
    def check_for_updates(self, name: str, template_type: Optional[TemplateType] = None) -> Optional[Dict[str, Any]]:
        """
        Check if a template has updates available.
        
        For built-in templates, compares with the latest version in builtin_templates.py.
        For custom/imported templates, this is a placeholder for future remote update checking.
        
        Args:
            name: Name of the template
            template_type: Type of template
            
        Returns:
            Dictionary with update info or None if no updates
        """
        try:
            # Load current template
            current_template = self.load_template(name, template_type)
            
            if not current_template:
                logger.error(f"Template not found: {name}")
                return None
            
            # For built-in templates, check against the latest version
            if current_template.metadata.template_type == TemplateType.BUILTIN:
                from .builtin_templates import BUILTIN_TEMPLATES
                
                if name in BUILTIN_TEMPLATES:
                    latest_template = BUILTIN_TEMPLATES[name]()
                    
                    # Compare versions
                    comparison = self.compare_versions(
                        current_template.metadata.version,
                        latest_template.metadata.version
                    )
                    
                    if comparison < 0:
                        return {
                            'name': name,
                            'current_version': current_template.metadata.version,
                            'latest_version': latest_template.metadata.version,
                            'has_update': True,
                            'template': latest_template,
                        }
                    else:
                        return {
                            'name': name,
                            'current_version': current_template.metadata.version,
                            'latest_version': latest_template.metadata.version,
                            'has_update': False,
                        }
            
            # For custom/imported templates, no remote checking yet
            logger.info(f"Update checking not available for {current_template.metadata.template_type.value} templates")
            return None
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None
    
    def update_template(self, name: str, template_type: Optional[TemplateType] = None, auto_update: bool = False) -> bool:
        """
        Update a template to the latest version.
        
        Args:
            name: Name of the template
            template_type: Type of template
            auto_update: If True, update without confirmation
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Check for updates
            update_info = self.check_for_updates(name, template_type)
            
            if not update_info:
                logger.info(f"No update information available for template: {name}")
                return False
            
            if not update_info.get('has_update'):
                logger.info(f"Template {name} is already up to date (version {update_info['current_version']})")
                return True
            
            logger.info(
                f"Update available for {name}: "
                f"{update_info['current_version']} -> {update_info['latest_version']}"
            )
            
            if not auto_update:
                logger.warning("Auto-update is disabled. Set auto_update=True to proceed with update.")
                return False
            
            # Get the latest template
            latest_template = update_info.get('template')
            
            if not latest_template:
                logger.error("Latest template not available")
                return False
            
            # Save the updated template
            success = self.save_template(latest_template, latest_template.metadata.template_type)
            
            if success:
                logger.info(f"Successfully updated template {name} to version {latest_template.metadata.version}")
                # Clear cache
                cache_key = f"{latest_template.metadata.template_type.value}:{name}"
                if cache_key in self._template_cache:
                    del self._template_cache[cache_key]
                return True
            else:
                logger.error(f"Failed to update template {name}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return False
    
    def update_all_templates(self, template_type: Optional[TemplateType] = None, auto_update: bool = False) -> Dict[str, bool]:
        """
        Update all templates of a given type.
        
        Args:
            template_type: Type of templates to update (None for all)
            auto_update: If True, update without confirmation
            
        Returns:
            Dictionary mapping template names to update success status
        """
        results = {}
        
        # Get list of templates
        templates = self.list_templates(template_type)
        
        for template_metadata in templates:
            name = template_metadata.name
            ttype = template_metadata.template_type
            
            logger.info(f"Checking for updates: {name}")
            success = self.update_template(name, ttype, auto_update)
            results[name] = success
        
        # Summary
        updated_count = sum(1 for success in results.values() if success)
        logger.info(f"Update complete: {updated_count}/{len(results)} templates updated")
        
        return results
    
    def get_template_version_history(self, name: str, template_type: Optional[TemplateType] = None) -> List[Dict[str, Any]]:
        """
        Get version history for a template.
        
        This is a placeholder for future implementation of version history tracking.
        
        Args:
            name: Name of the template
            template_type: Type of template
            
        Returns:
            List of version history entries
        """
        # Load current template
        template = self.load_template(name, template_type)
        
        if not template:
            return []
        
        # For now, just return current version
        return [{
            'version': template.metadata.version,
            'created_at': template.metadata.created_at,
            'updated_at': template.metadata.updated_at,
            'description': template.metadata.description,
        }]
