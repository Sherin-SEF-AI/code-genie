"""
Dependency Manager for CodeGenie.

Handles automatic dependency detection, version resolution, and package management
across multiple programming languages and package managers.
"""

import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PackageManager(Enum):
    """Supported package managers."""
    NPM = "npm"
    YARN = "yarn"
    PIP = "pip"
    POETRY = "poetry"
    CARGO = "cargo"
    GO_MODULES = "go"
    UNKNOWN = "unknown"


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    GO = "go"
    UNKNOWN = "unknown"


@dataclass
class Dependency:
    """Represents a package dependency."""
    name: str
    version: Optional[str] = None
    language: Language = Language.UNKNOWN
    package_manager: PackageManager = PackageManager.UNKNOWN
    is_dev: bool = False
    source: str = ""  # Where it was detected (import, require, etc.)


@dataclass
class DependencyConflict:
    """Represents a dependency version conflict."""
    package_name: str
    required_versions: List[str]
    sources: List[str]
    suggested_resolution: Optional[str] = None


@dataclass
class PackageFile:
    """Represents a package configuration file."""
    path: Path
    package_manager: PackageManager
    language: Language
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)


class DependencyManager:
    """
    Manages dependencies across multiple languages and package managers.
    
    Features:
    - Detects missing dependencies from import statements
    - Resolves package versions
    - Detects and resolves conflicts
    - Updates package files automatically
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize the DependencyManager.
        
        Args:
            project_path: Root path of the project
        """
        self.project_path = Path(project_path)
        self.package_files: Dict[PackageManager, PackageFile] = {}
        self._discover_package_files()
        
        # Common package name mappings (import name -> package name)
        self.package_mappings = {
            Language.PYTHON: {
                'PIL': 'Pillow',
                'cv2': 'opencv-python',
                'sklearn': 'scikit-learn',
                'yaml': 'PyYAML',
                'bs4': 'beautifulsoup4',
                'dotenv': 'python-dotenv',
            },
            Language.JAVASCRIPT: {
                '@types/node': '@types/node',
                '@types/react': '@types/react',
            }
        }
    
    def _discover_package_files(self) -> None:
        """Discover package configuration files in the project."""
        package_file_patterns = {
            'package.json': (PackageManager.NPM, Language.JAVASCRIPT),
            'requirements.txt': (PackageManager.PIP, Language.PYTHON),
            'pyproject.toml': (PackageManager.POETRY, Language.PYTHON),
            'Cargo.toml': (PackageManager.CARGO, Language.RUST),
            'go.mod': (PackageManager.GO_MODULES, Language.GO),
        }
        
        for filename, (pm, lang) in package_file_patterns.items():
            file_path = self.project_path / filename
            if file_path.exists():
                package_file = PackageFile(
                    path=file_path,
                    package_manager=pm,
                    language=lang
                )
                self._load_package_file(package_file)
                self.package_files[pm] = package_file
                logger.info(f"Discovered {filename} for {pm.value}")
    
    def _load_package_file(self, package_file: PackageFile) -> None:
        """Load dependencies from a package file."""
        try:
            if package_file.package_manager in [PackageManager.NPM, PackageManager.YARN]:
                self._load_package_json(package_file)
            elif package_file.package_manager == PackageManager.PIP:
                self._load_requirements_txt(package_file)
            elif package_file.package_manager == PackageManager.POETRY:
                self._load_pyproject_toml(package_file)
            elif package_file.package_manager == PackageManager.CARGO:
                self._load_cargo_toml(package_file)
            elif package_file.package_manager == PackageManager.GO_MODULES:
                self._load_go_mod(package_file)
        except Exception as e:
            logger.error(f"Error loading {package_file.path}: {e}")

    
    def _load_package_json(self, package_file: PackageFile) -> None:
        """Load dependencies from package.json."""
        with open(package_file.path, 'r') as f:
            data = json.load(f)
            package_file.dependencies = data.get('dependencies', {})
            package_file.dev_dependencies = data.get('devDependencies', {})
    
    def _load_requirements_txt(self, package_file: PackageFile) -> None:
        """Load dependencies from requirements.txt."""
        with open(package_file.path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package==version or package>=version
                    match = re.match(r'^([a-zA-Z0-9_\-\.]+)([>=<~!]+)?(.+)?$', line)
                    if match:
                        name = match.group(1)
                        version = match.group(3) if match.group(3) else ""
                        package_file.dependencies[name] = version
    
    def _load_pyproject_toml(self, package_file: PackageFile) -> None:
        """Load dependencies from pyproject.toml."""
        try:
            import tomli
        except ImportError:
            try:
                import tomllib as tomli
            except ImportError:
                logger.warning("tomli/tomllib not available, skipping pyproject.toml")
                return
        
        with open(package_file.path, 'rb') as f:
            data = tomli.load(f)
            deps = data.get('tool', {}).get('poetry', {}).get('dependencies', {})
            dev_deps = data.get('tool', {}).get('poetry', {}).get('dev-dependencies', {})
            
            package_file.dependencies = {k: str(v) for k, v in deps.items() if k != 'python'}
            package_file.dev_dependencies = {k: str(v) for k, v in dev_deps.items()}
    
    def _load_cargo_toml(self, package_file: PackageFile) -> None:
        """Load dependencies from Cargo.toml."""
        try:
            import tomli
        except ImportError:
            try:
                import tomllib as tomli
            except ImportError:
                logger.warning("tomli/tomllib not available, skipping Cargo.toml")
                return
        
        with open(package_file.path, 'rb') as f:
            data = tomli.load(f)
            deps = data.get('dependencies', {})
            dev_deps = data.get('dev-dependencies', {})
            
            package_file.dependencies = {k: str(v) for k, v in deps.items()}
            package_file.dev_dependencies = {k: str(v) for k, v in dev_deps.items()}
    
    def _load_go_mod(self, package_file: PackageFile) -> None:
        """Load dependencies from go.mod."""
        with open(package_file.path, 'r') as f:
            in_require = False
            for line in f:
                line = line.strip()
                if line.startswith('require ('):
                    in_require = True
                    continue
                elif line == ')':
                    in_require = False
                    continue
                
                if in_require or line.startswith('require '):
                    # Parse: require github.com/pkg/name v1.2.3
                    match = re.match(r'require\s+([^\s]+)\s+([^\s]+)', line)
                    if match:
                        name = match.group(1)
                        version = match.group(2)
                        package_file.dependencies[name] = version
    
    def detect_missing_dependencies(self, file_path: Optional[Path] = None) -> List[Dependency]:
        """
        Detect missing dependencies by analyzing import statements.
        
        Args:
            file_path: Specific file to analyze, or None to analyze all files
            
        Returns:
            List of missing dependencies
        """
        missing_deps: List[Dependency] = []
        
        if file_path:
            files_to_analyze = [file_path]
        else:
            files_to_analyze = self._get_source_files()
        
        for file in files_to_analyze:
            language = self._detect_language(file)
            imports = self._extract_imports(file, language)
            
            for import_name in imports:
                if not self._is_dependency_installed(import_name, language):
                    dep = Dependency(
                        name=self._map_import_to_package(import_name, language),
                        language=language,
                        package_manager=self._get_package_manager_for_language(language),
                        source=str(file)
                    )
                    missing_deps.append(dep)
        
        return missing_deps
    
    def _get_source_files(self) -> List[Path]:
        """Get all source files in the project."""
        extensions = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.jsx': Language.JAVASCRIPT,
            '.tsx': Language.TYPESCRIPT,
            '.rs': Language.RUST,
            '.go': Language.GO,
        }
        
        source_files = []
        for ext in extensions.keys():
            source_files.extend(self.project_path.rglob(f'*{ext}'))
        
        # Filter out common directories to ignore
        ignore_dirs = {'node_modules', 'venv', '.venv', 'target', 'dist', 'build', '__pycache__'}
        return [f for f in source_files if not any(d in f.parts for d in ignore_dirs)]
    
    def _detect_language(self, file_path: Path) -> Language:
        """Detect programming language from file extension."""
        ext = file_path.suffix.lower()
        mapping = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.jsx': Language.JAVASCRIPT,
            '.tsx': Language.TYPESCRIPT,
            '.rs': Language.RUST,
            '.go': Language.GO,
        }
        return mapping.get(ext, Language.UNKNOWN)
    
    def _extract_imports(self, file_path: Path, language: Language) -> Set[str]:
        """Extract import statements from a source file."""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if language == Language.PYTHON:
                    imports.update(self._extract_python_imports(content))
                elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
                    imports.update(self._extract_js_imports(content))
                elif language == Language.RUST:
                    imports.update(self._extract_rust_imports(content))
                elif language == Language.GO:
                    imports.update(self._extract_go_imports(content))
        except Exception as e:
            logger.error(f"Error extracting imports from {file_path}: {e}")
        
        return imports

    
    def _extract_python_imports(self, content: str) -> Set[str]:
        """Extract Python import statements."""
        imports = set()
        
        # Match: import package, from package import ...
        import_patterns = [
            r'^\s*import\s+([a-zA-Z0-9_\.]+)',
            r'^\s*from\s+([a-zA-Z0-9_\.]+)\s+import',
        ]
        
        for line in content.split('\n'):
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1).split('.')[0]
                    imports.add(module)
        
        return imports
    
    def _extract_js_imports(self, content: str) -> Set[str]:
        """Extract JavaScript/TypeScript import statements."""
        imports = set()
        
        # Match: import ... from 'package', require('package')
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'".][^\'"]*)[\'"',
            r'require\s*\(\s*[\'"]([^\'".][^\'"]*)[\'"]\s*\)',
        ]
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                package = match.group(1)
                # Extract package name (handle scoped packages like @types/node)
                if package.startswith('@'):
                    parts = package.split('/')[:2]
                    imports.add('/'.join(parts))
                else:
                    imports.add(package.split('/')[0])
        
        return imports
    
    def _extract_rust_imports(self, content: str) -> Set[str]:
        """Extract Rust use statements."""
        imports = set()
        
        # Match: use package::...
        pattern = r'use\s+([a-zA-Z0-9_]+)::'
        matches = re.finditer(pattern, content)
        for match in matches:
            imports.add(match.group(1))
        
        return imports
    
    def _extract_go_imports(self, content: str) -> Set[str]:
        """Extract Go import statements."""
        imports = set()
        
        # Match: import "package" or import ( "package1" "package2" )
        in_import_block = False
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('import ('):
                in_import_block = True
                continue
            elif line == ')':
                in_import_block = False
                continue
            
            if in_import_block:
                match = re.match(r'[\'"]([^\'"]+)[\'"]', line)
                if match:
                    imports.add(match.group(1))
            elif line.startswith('import '):
                match = re.match(r'import\s+[\'"]([^\'"]+)[\'"]', line)
                if match:
                    imports.add(match.group(1))
        
        return imports
    
    def _is_dependency_installed(self, import_name: str, language: Language) -> bool:
        """Check if a dependency is already installed/declared."""
        # Check if it's a standard library module
        if self._is_standard_library(import_name, language):
            return True
        
        # Check if it's in package files
        package_name = self._map_import_to_package(import_name, language)
        pm = self._get_package_manager_for_language(language)
        
        if pm in self.package_files:
            package_file = self.package_files[pm]
            if package_name in package_file.dependencies or package_name in package_file.dev_dependencies:
                return True
        
        return False
    
    def _is_standard_library(self, module_name: str, language: Language) -> bool:
        """Check if a module is part of the standard library."""
        stdlib_modules = {
            Language.PYTHON: {
                'os', 'sys', 'json', 're', 'math', 'datetime', 'time', 'random',
                'collections', 'itertools', 'functools', 'pathlib', 'typing',
                'asyncio', 'threading', 'multiprocessing', 'subprocess', 'logging',
                'unittest', 'io', 'csv', 'xml', 'html', 'http', 'urllib', 'email',
                'base64', 'hashlib', 'hmac', 'secrets', 'uuid', 'copy', 'pickle',
            },
            Language.JAVASCRIPT: {
                'fs', 'path', 'http', 'https', 'url', 'util', 'events', 'stream',
                'crypto', 'os', 'process', 'buffer', 'child_process', 'cluster',
            },
            Language.GO: {
                'fmt', 'os', 'io', 'time', 'strings', 'strconv', 'math', 'sort',
                'encoding/json', 'net/http', 'context', 'sync', 'errors',
            },
        }
        
        return module_name in stdlib_modules.get(language, set())

    
    def _map_import_to_package(self, import_name: str, language: Language) -> str:
        """Map import name to package name."""
        mappings = self.package_mappings.get(language, {})
        return mappings.get(import_name, import_name)
    
    def _get_package_manager_for_language(self, language: Language) -> PackageManager:
        """Get the default package manager for a language."""
        mapping = {
            Language.PYTHON: PackageManager.PIP,
            Language.JAVASCRIPT: PackageManager.NPM,
            Language.TYPESCRIPT: PackageManager.NPM,
            Language.RUST: PackageManager.CARGO,
            Language.GO: PackageManager.GO_MODULES,
        }
        
        # Check if we have a specific package manager configured
        if language == Language.PYTHON and PackageManager.POETRY in self.package_files:
            return PackageManager.POETRY
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            if PackageManager.YARN in self.package_files:
                return PackageManager.YARN
        
        return mapping.get(language, PackageManager.UNKNOWN)
    
    def resolve_version(self, package_name: str, language: Language) -> Optional[str]:
        """
        Resolve the best version for a package.
        
        Args:
            package_name: Name of the package
            language: Programming language
            
        Returns:
            Recommended version string or None
        """
        pm = self._get_package_manager_for_language(language)
        
        try:
            if pm == PackageManager.PIP:
                return self._resolve_pip_version(package_name)
            elif pm in [PackageManager.NPM, PackageManager.YARN]:
                return self._resolve_npm_version(package_name)
            elif pm == PackageManager.CARGO:
                return self._resolve_cargo_version(package_name)
            elif pm == PackageManager.GO_MODULES:
                return self._resolve_go_version(package_name)
        except Exception as e:
            logger.error(f"Error resolving version for {package_name}: {e}")
        
        return None
    
    def _resolve_pip_version(self, package_name: str) -> Optional[str]:
        """Resolve latest version from PyPI."""
        try:
            result = subprocess.run(
                ['pip', 'index', 'versions', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Parse output to get latest version
                match = re.search(r'Available versions: ([^\s,]+)', result.stdout)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.debug(f"Could not resolve pip version: {e}")
        
        return None

    
    def _resolve_npm_version(self, package_name: str) -> Optional[str]:
        """Resolve latest version from npm registry."""
        try:
            result = subprocess.run(
                ['npm', 'view', package_name, 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"Could not resolve npm version: {e}")
        
        return None
    
    def _resolve_cargo_version(self, package_name: str) -> Optional[str]:
        """Resolve latest version from crates.io."""
        try:
            result = subprocess.run(
                ['cargo', 'search', package_name, '--limit', '1'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Parse: package_name = "version" # description
                match = re.search(rf'{package_name}\s*=\s*"([^"]+)"', result.stdout)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.debug(f"Could not resolve cargo version: {e}")
        
        return None
    
    def _resolve_go_version(self, package_name: str) -> Optional[str]:
        """Resolve latest version for Go module."""
        try:
            result = subprocess.run(
                ['go', 'list', '-m', '-versions', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                versions = result.stdout.strip().split()
                if len(versions) > 1:
                    return versions[-1]  # Last version is usually the latest
        except Exception as e:
            logger.debug(f"Could not resolve go version: {e}")
        
        return None
    
    def detect_conflicts(self) -> List[DependencyConflict]:
        """
        Detect version conflicts in dependencies.
        
        Returns:
            List of detected conflicts
        """
        conflicts: List[DependencyConflict] = []
        
        # Collect all dependencies with their sources
        dep_versions: Dict[str, List[Tuple[str, str]]] = {}  # package -> [(version, source)]
        
        for pm, package_file in self.package_files.items():
            all_deps = {**package_file.dependencies, **package_file.dev_dependencies}
            
            for name, version in all_deps.items():
                if name not in dep_versions:
                    dep_versions[name] = []
                dep_versions[name].append((version, str(package_file.path)))
        
        # Check for conflicts (different versions of same package)
        for package_name, versions_sources in dep_versions.items():
            unique_versions = set(v for v, _ in versions_sources)
            
            if len(unique_versions) > 1:
                conflict = DependencyConflict(
                    package_name=package_name,
                    required_versions=list(unique_versions),
                    sources=[s for _, s in versions_sources],
                    suggested_resolution=self._suggest_conflict_resolution(unique_versions)
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _suggest_conflict_resolution(self, versions: Set[str]) -> Optional[str]:
        """Suggest a resolution for conflicting versions."""
        # Simple strategy: suggest the highest version
        version_list = list(versions)
        
        # Try to parse semantic versions
        try:
            parsed_versions = []
            for v in version_list:
                # Extract version numbers (e.g., "^1.2.3" -> "1.2.3")
                clean_v = re.sub(r'[^\d.]', '', v)
                parts = [int(x) for x in clean_v.split('.') if x.isdigit()]
                parsed_versions.append((parts, v))
            
            # Sort and return highest
            parsed_versions.sort(reverse=True)
            return parsed_versions[0][1]
        except Exception:
            # If parsing fails, just return the first one
            return version_list[0]
    
    def get_dependency_info(self, package_name: str, language: Language) -> Dict[str, Any]:
        """
        Get detailed information about a dependency.
        
        Args:
            package_name: Name of the package
            language: Programming language
            
        Returns:
            Dictionary with dependency information
        """
        info = {
            'name': package_name,
            'language': language.value,
            'installed': False,
            'version': None,
            'latest_version': None,
        }
        
        pm = self._get_package_manager_for_language(language)
        
        # Check if installed
        if pm in self.package_files:
            package_file = self.package_files[pm]
            if package_name in package_file.dependencies:
                info['installed'] = True
                info['version'] = package_file.dependencies[package_name]
            elif package_name in package_file.dev_dependencies:
                info['installed'] = True
                info['version'] = package_file.dev_dependencies[package_name]
        
        # Get latest version
        info['latest_version'] = self.resolve_version(package_name, language)
        
        return info

    
    def add_dependency(
        self,
        package_name: str,
        version: Optional[str] = None,
        language: Optional[Language] = None,
        is_dev: bool = False
    ) -> bool:
        """
        Add a dependency to the appropriate package file.
        
        Args:
            package_name: Name of the package to add
            version: Version string (None for latest)
            language: Programming language (auto-detected if None)
            is_dev: Whether this is a dev dependency
            
        Returns:
            True if successful, False otherwise
        """
        if language is None:
            # Try to detect language from existing package files
            if self.package_files:
                language = list(self.package_files.values())[0].language
            else:
                logger.error("Cannot determine language for dependency")
                return False
        
        pm = self._get_package_manager_for_language(language)
        
        if pm not in self.package_files:
            logger.error(f"No package file found for {pm.value}")
            return False
        
        # Resolve version if not provided
        if version is None:
            version = self.resolve_version(package_name, language)
            if version is None:
                version = "*"  # Use wildcard if resolution fails
        
        package_file = self.package_files[pm]
        
        # Add to appropriate dependency dict
        if is_dev:
            package_file.dev_dependencies[package_name] = version
        else:
            package_file.dependencies[package_name] = version
        
        # Update the file
        return self._update_package_file(package_file)
    
    def remove_dependency(self, package_name: str, language: Optional[Language] = None) -> bool:
        """
        Remove a dependency from the package file.
        
        Args:
            package_name: Name of the package to remove
            language: Programming language (auto-detected if None)
            
        Returns:
            True if successful, False otherwise
        """
        if language is None:
            if self.package_files:
                language = list(self.package_files.values())[0].language
            else:
                return False
        
        pm = self._get_package_manager_for_language(language)
        
        if pm not in self.package_files:
            return False
        
        package_file = self.package_files[pm]
        
        # Remove from both dicts
        removed = False
        if package_name in package_file.dependencies:
            del package_file.dependencies[package_name]
            removed = True
        if package_name in package_file.dev_dependencies:
            del package_file.dev_dependencies[package_name]
            removed = True
        
        if removed:
            return self._update_package_file(package_file)
        
        return False

    
    def update_dependency(
        self,
        package_name: str,
        new_version: str,
        language: Optional[Language] = None
    ) -> bool:
        """
        Update a dependency version.
        
        Args:
            package_name: Name of the package
            new_version: New version string
            language: Programming language (auto-detected if None)
            
        Returns:
            True if successful, False otherwise
        """
        if language is None:
            if self.package_files:
                language = list(self.package_files.values())[0].language
            else:
                return False
        
        pm = self._get_package_manager_for_language(language)
        
        if pm not in self.package_files:
            return False
        
        package_file = self.package_files[pm]
        
        # Update in appropriate dict
        if package_name in package_file.dependencies:
            package_file.dependencies[package_name] = new_version
        elif package_name in package_file.dev_dependencies:
            package_file.dev_dependencies[package_name] = new_version
        else:
            return False
        
        return self._update_package_file(package_file)
    
    def _update_package_file(self, package_file: PackageFile) -> bool:
        """Update a package file on disk."""
        try:
            if package_file.package_manager in [PackageManager.NPM, PackageManager.YARN]:
                return self._update_package_json(package_file)
            elif package_file.package_manager == PackageManager.PIP:
                return self._update_requirements_txt(package_file)
            elif package_file.package_manager == PackageManager.POETRY:
                return self._update_pyproject_toml(package_file)
            elif package_file.package_manager == PackageManager.CARGO:
                return self._update_cargo_toml(package_file)
            elif package_file.package_manager == PackageManager.GO_MODULES:
                return self._update_go_mod(package_file)
        except Exception as e:
            logger.error(f"Error updating {package_file.path}: {e}")
            return False
        
        return False
    
    def _update_package_json(self, package_file: PackageFile) -> bool:
        """Update package.json file."""
        try:
            with open(package_file.path, 'r') as f:
                data = json.load(f)
            
            data['dependencies'] = package_file.dependencies
            data['devDependencies'] = package_file.dev_dependencies
            
            with open(package_file.path, 'w') as f:
                json.dump(data, f, indent=2)
                f.write('\n')  # Add trailing newline
            
            logger.info(f"Updated {package_file.path}")
            return True
        except Exception as e:
            logger.error(f"Error updating package.json: {e}")
            return False

    
    def _update_requirements_txt(self, package_file: PackageFile) -> bool:
        """Update requirements.txt file."""
        try:
            lines = []
            for name, version in sorted(package_file.dependencies.items()):
                if version:
                    lines.append(f"{name}=={version}")
                else:
                    lines.append(name)
            
            with open(package_file.path, 'w') as f:
                f.write('\n'.join(lines))
                if lines:
                    f.write('\n')
            
            logger.info(f"Updated {package_file.path}")
            return True
        except Exception as e:
            logger.error(f"Error updating requirements.txt: {e}")
            return False
    
    def _update_pyproject_toml(self, package_file: PackageFile) -> bool:
        """Update pyproject.toml file."""
        try:
            import tomli
            import tomli_w
        except ImportError:
            logger.error("tomli/tomli_w not available for updating pyproject.toml")
            return False
        
        try:
            with open(package_file.path, 'rb') as f:
                data = tomli.load(f)
            
            if 'tool' not in data:
                data['tool'] = {}
            if 'poetry' not in data['tool']:
                data['tool']['poetry'] = {}
            
            data['tool']['poetry']['dependencies'] = package_file.dependencies
            data['tool']['poetry']['dev-dependencies'] = package_file.dev_dependencies
            
            with open(package_file.path, 'wb') as f:
                tomli_w.dump(data, f)
            
            logger.info(f"Updated {package_file.path}")
            return True
        except Exception as e:
            logger.error(f"Error updating pyproject.toml: {e}")
            return False
    
    def _update_cargo_toml(self, package_file: PackageFile) -> bool:
        """Update Cargo.toml file."""
        try:
            import tomli
            import tomli_w
        except ImportError:
            logger.error("tomli/tomli_w not available for updating Cargo.toml")
            return False
        
        try:
            with open(package_file.path, 'rb') as f:
                data = tomli.load(f)
            
            data['dependencies'] = package_file.dependencies
            if package_file.dev_dependencies:
                data['dev-dependencies'] = package_file.dev_dependencies
            
            with open(package_file.path, 'wb') as f:
                tomli_w.dump(data, f)
            
            logger.info(f"Updated {package_file.path}")
            return True
        except Exception as e:
            logger.error(f"Error updating Cargo.toml: {e}")
            return False

    
    def _update_go_mod(self, package_file: PackageFile) -> bool:
        """Update go.mod file."""
        try:
            # Read existing content
            with open(package_file.path, 'r') as f:
                lines = f.readlines()
            
            # Find and update require block
            new_lines = []
            in_require = False
            require_written = False
            
            for line in lines:
                if line.strip().startswith('require ('):
                    in_require = True
                    new_lines.append(line)
                    # Write all dependencies
                    for name, version in sorted(package_file.dependencies.items()):
                        new_lines.append(f'\t{name} {version}\n')
                    require_written = True
                elif in_require and line.strip() == ')':
                    in_require = False
                    new_lines.append(line)
                elif not in_require:
                    # Skip old require lines
                    if not line.strip().startswith('require ') or require_written:
                        new_lines.append(line)
            
            # If no require block existed, add one
            if not require_written and package_file.dependencies:
                new_lines.append('\nrequire (\n')
                for name, version in sorted(package_file.dependencies.items()):
                    new_lines.append(f'\t{name} {version}\n')
                new_lines.append(')\n')
            
            with open(package_file.path, 'w') as f:
                f.writelines(new_lines)
            
            logger.info(f"Updated {package_file.path}")
            return True
        except Exception as e:
            logger.error(f"Error updating go.mod: {e}")
            return False

    
    def install_dependency(
        self,
        package_name: str,
        version: Optional[str] = None,
        language: Optional[Language] = None,
        is_dev: bool = False
    ) -> bool:
        """
        Install a dependency using the appropriate package manager.
        
        Args:
            package_name: Name of the package to install
            version: Version string (None for latest)
            language: Programming language (auto-detected if None)
            is_dev: Whether this is a dev dependency
            
        Returns:
            True if successful, False otherwise
        """
        if language is None:
            if self.package_files:
                language = list(self.package_files.values())[0].language
            else:
                logger.error("Cannot determine language for dependency")
                return False
        
        pm = self._get_package_manager_for_language(language)
        
        # First add to package file
        if not self.add_dependency(package_name, version, language, is_dev):
            logger.error(f"Failed to add {package_name} to package file")
            return False
        
        # Then install using package manager
        try:
            if pm == PackageManager.NPM:
                return self._install_npm(package_name, version, is_dev)
            elif pm == PackageManager.YARN:
                return self._install_yarn(package_name, version, is_dev)
            elif pm == PackageManager.PIP:
                return self._install_pip(package_name, version)
            elif pm == PackageManager.POETRY:
                return self._install_poetry(package_name, version, is_dev)
            elif pm == PackageManager.CARGO:
                return self._install_cargo(package_name, version)
            elif pm == PackageManager.GO_MODULES:
                return self._install_go(package_name, version)
        except Exception as e:
            logger.error(f"Error installing {package_name}: {e}")
            return False
        
        return False
    
    def _install_npm(self, package_name: str, version: Optional[str], is_dev: bool) -> bool:
        """Install package using npm."""
        package_spec = f"{package_name}@{version}" if version else package_name
        cmd = ['npm', 'install']
        if is_dev:
            cmd.append('--save-dev')
        cmd.append(package_spec)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info(f"Successfully installed {package_name} with npm")
                return True
            else:
                logger.error(f"npm install failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running npm install: {e}")
            return False

    
    def _install_yarn(self, package_name: str, version: Optional[str], is_dev: bool) -> bool:
        """Install package using yarn."""
        package_spec = f"{package_name}@{version}" if version else package_name
        cmd = ['yarn', 'add']
        if is_dev:
            cmd.append('--dev')
        cmd.append(package_spec)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info(f"Successfully installed {package_name} with yarn")
                return True
            else:
                logger.error(f"yarn add failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running yarn add: {e}")
            return False
    
    def _install_pip(self, package_name: str, version: Optional[str]) -> bool:
        """Install package using pip."""
        package_spec = f"{package_name}=={version}" if version else package_name
        cmd = ['pip', 'install', package_spec]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info(f"Successfully installed {package_name} with pip")
                return True
            else:
                logger.error(f"pip install failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running pip install: {e}")
            return False
    
    def _install_poetry(self, package_name: str, version: Optional[str], is_dev: bool) -> bool:
        """Install package using poetry."""
        package_spec = f"{package_name}@{version}" if version else package_name
        cmd = ['poetry', 'add']
        if is_dev:
            cmd.append('--group=dev')
        cmd.append(package_spec)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info(f"Successfully installed {package_name} with poetry")
                return True
            else:
                logger.error(f"poetry add failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running poetry add: {e}")
            return False

    
    def _install_cargo(self, package_name: str, version: Optional[str]) -> bool:
        """Install package using cargo."""
        # Cargo doesn't have a direct install command for dependencies
        # Dependencies are managed through Cargo.toml and installed with cargo build
        logger.info(f"Added {package_name} to Cargo.toml. Run 'cargo build' to install.")
        
        # Optionally run cargo fetch to download the dependency
        try:
            result = subprocess.run(
                ['cargo', 'fetch'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info(f"Successfully fetched {package_name} with cargo")
                return True
            else:
                logger.warning(f"cargo fetch failed: {result.stderr}")
                return True  # Still return True as dependency is in Cargo.toml
        except Exception as e:
            logger.error(f"Error running cargo fetch: {e}")
            return True  # Still return True as dependency is in Cargo.toml
    
    def _install_go(self, package_name: str, version: Optional[str]) -> bool:
        """Install package using go modules."""
        package_spec = f"{package_name}@{version}" if version else package_name
        cmd = ['go', 'get', package_spec]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info(f"Successfully installed {package_name} with go get")
                return True
            else:
                logger.error(f"go get failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running go get: {e}")
            return False
    
    def install_all_dependencies(self) -> bool:
        """
        Install all dependencies from package files.
        
        Returns:
            True if successful, False otherwise
        """
        success = True
        
        for pm, package_file in self.package_files.items():
            try:
                if pm == PackageManager.NPM:
                    result = subprocess.run(
                        ['npm', 'install'],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    success = success and (result.returncode == 0)
                
                elif pm == PackageManager.YARN:
                    result = subprocess.run(
                        ['yarn', 'install'],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    success = success and (result.returncode == 0)
                
                elif pm == PackageManager.PIP:
                    result = subprocess.run(
                        ['pip', 'install', '-r', str(package_file.path)],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    success = success and (result.returncode == 0)
                
                elif pm == PackageManager.POETRY:
                    result = subprocess.run(
                        ['poetry', 'install'],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    success = success and (result.returncode == 0)
                
                elif pm == PackageManager.CARGO:
                    result = subprocess.run(
                        ['cargo', 'build'],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    success = success and (result.returncode == 0)
                
                elif pm == PackageManager.GO_MODULES:
                    result = subprocess.run(
                        ['go', 'mod', 'download'],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    success = success and (result.returncode == 0)
                
                if success:
                    logger.info(f"Successfully installed dependencies with {pm.value}")
                else:
                    logger.error(f"Failed to install dependencies with {pm.value}")
                    
            except Exception as e:
                logger.error(f"Error installing dependencies with {pm.value}: {e}")
                success = False
        
        return success
    
    def get_package_manager_info(self, pm: PackageManager) -> Dict[str, Any]:
        """
        Get information about a package manager.
        
        Args:
            pm: Package manager
            
        Returns:
            Dictionary with package manager information
        """
        info = {
            'name': pm.value,
            'available': self._is_package_manager_available(pm),
            'version': self._get_package_manager_version(pm),
            'package_file': None,
        }
        
        if pm in self.package_files:
            info['package_file'] = str(self.package_files[pm].path)
        
        return info
    
    def _is_package_manager_available(self, pm: PackageManager) -> bool:
        """Check if a package manager is available on the system."""
        commands = {
            PackageManager.NPM: 'npm',
            PackageManager.YARN: 'yarn',
            PackageManager.PIP: 'pip',
            PackageManager.POETRY: 'poetry',
            PackageManager.CARGO: 'cargo',
            PackageManager.GO_MODULES: 'go',
        }
        
        cmd = commands.get(pm)
        if not cmd:
            return False
        
        try:
            result = subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    
    def _get_package_manager_version(self, pm: PackageManager) -> Optional[str]:
        """Get the version of a package manager."""
        commands = {
            PackageManager.NPM: 'npm',
            PackageManager.YARN: 'yarn',
            PackageManager.PIP: 'pip',
            PackageManager.POETRY: 'poetry',
            PackageManager.CARGO: 'cargo',
            PackageManager.GO_MODULES: 'go',
        }
        
        cmd = commands.get(pm)
        if not cmd:
            return None
        
        try:
            result = subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return None
    
    def get_all_dependencies(self) -> List[Dependency]:
        """
        Get all dependencies from all package files.
        
        Returns:
            List of all dependencies
        """
        all_deps = []
        
        for pm, package_file in self.package_files.items():
            for name, version in package_file.dependencies.items():
                dep = Dependency(
                    name=name,
                    version=version,
                    language=package_file.language,
                    package_manager=pm,
                    is_dev=False,
                    source=str(package_file.path)
                )
                all_deps.append(dep)
            
            for name, version in package_file.dev_dependencies.items():
                dep = Dependency(
                    name=name,
                    version=version,
                    language=package_file.language,
                    package_manager=pm,
                    is_dev=True,
                    source=str(package_file.path)
                )
                all_deps.append(dep)
        
        return all_deps
    
    def create_package_file(self, language: Language, package_manager: Optional[PackageManager] = None) -> bool:
        """
        Create a new package file for a language.
        
        Args:
            language: Programming language
            package_manager: Specific package manager (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if package_manager is None:
            package_manager = self._get_package_manager_for_language(language)
        
        file_templates = {
            PackageManager.NPM: ('package.json', {
                "name": self.project_path.name,
                "version": "1.0.0",
                "description": "",
                "main": "index.js",
                "scripts": {},
                "dependencies": {},
                "devDependencies": {}
            }),
            PackageManager.PIP: ('requirements.txt', ''),
            PackageManager.CARGO: ('Cargo.toml', '''[package]
name = "{}"
version = "0.1.0"
edition = "2021"

[dependencies]
'''.format(self.project_path.name)),
            PackageManager.GO_MODULES: ('go.mod', f'module {self.project_path.name}\n\ngo 1.21\n'),
        }
        
        if package_manager not in file_templates:
            logger.error(f"No template for {package_manager.value}")
            return False
        
        filename, content = file_templates[package_manager]
        file_path = self.project_path / filename
        
        if file_path.exists():
            logger.warning(f"{filename} already exists")
            return False
        
        try:
            if isinstance(content, dict):
                with open(file_path, 'w') as f:
                    json.dump(content, f, indent=2)
                    f.write('\n')
            else:
                with open(file_path, 'w') as f:
                    f.write(content)
            
            logger.info(f"Created {filename}")
            
            # Reload package files
            self._discover_package_files()
            return True
        except Exception as e:
            logger.error(f"Error creating {filename}: {e}")
            return False
