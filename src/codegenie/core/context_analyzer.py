"""
Context Analyzer for understanding project structure and conventions.

This module provides intelligent analysis of project context including:
- Language and framework detection
- Project structure analysis
- Coding convention extraction
- Import pattern recognition
- Architecture pattern detection
- Dependency graph construction
"""

import ast
import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Language:
    """Represents a programming language."""
    name: str
    version: Optional[str] = None
    file_extensions: List[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class Framework:
    """Represents a framework or library."""
    name: str
    version: Optional[str] = None
    category: str = "general"  # web, testing, cli, etc.
    confidence: float = 1.0


@dataclass
class CodingConventions:
    """Represents coding conventions detected in a project."""
    indentation: str = "    "  # 4 spaces default
    quote_style: str = "double"  # single or double
    line_length: int = 88
    naming_conventions: Dict[str, str] = field(default_factory=dict)
    import_style: str = "standard"
    docstring_style: Optional[str] = None
    formatting_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dependency:
    """Represents a project dependency."""
    name: str
    version: Optional[str] = None
    source: str = "unknown"  # requirements.txt, package.json, etc.
    is_dev: bool = False


@dataclass
class DirectoryTree:
    """Represents project directory structure."""
    root: Path
    directories: List[Path] = field(default_factory=list)
    files: Dict[str, List[Path]] = field(default_factory=dict)  # extension -> files
    total_files: int = 0
    total_size: int = 0


@dataclass
class GitInfo:
    """Represents Git repository information."""
    is_repo: bool = False
    branch: Optional[str] = None
    remote: Optional[str] = None
    has_uncommitted: bool = False


@dataclass
class CodeMatch:
    """Represents a similar code match."""
    file_path: Path
    line_number: int
    similarity_score: float
    code_snippet: str


@dataclass
class ProjectContext:
    """Complete project context information."""
    project_path: Path
    language: Optional[Language] = None
    frameworks: List[Framework] = field(default_factory=list)
    conventions: Optional[CodingConventions] = None
    dependencies: List[Dependency] = field(default_factory=list)
    file_structure: Optional[DirectoryTree] = None
    git_info: Optional[GitInfo] = None
    architecture_patterns: List[str] = field(default_factory=list)
    entry_points: List[Path] = field(default_factory=list)


class ContextAnalyzer:
    """
    Analyzes project context to understand structure, conventions, and patterns.
    
    This class provides comprehensive project analysis including:
    - Language and framework detection
    - Coding convention extraction
    - Project structure analysis
    - Architecture pattern detection
    """
    
    # Language detection patterns
    LANGUAGE_INDICATORS = {
        'python': {
            'files': ['setup.py', 'pyproject.toml', 'requirements.txt', 'Pipfile'],
            'extensions': ['.py', '.pyw'],
            'patterns': [r'#!/usr/bin/env python', r'# -*- coding: utf-8 -*-']
        },
        'javascript': {
            'files': ['package.json', 'package-lock.json', 'yarn.lock'],
            'extensions': ['.js', '.mjs', '.cjs'],
            'patterns': [r'#!/usr/bin/env node', r'module\.exports', r'require\(']
        },
        'typescript': {
            'files': ['tsconfig.json', 'package.json'],
            'extensions': ['.ts', '.tsx'],
            'patterns': [r'interface\s+\w+', r'type\s+\w+\s*=', r'import.*from']
        },
        'go': {
            'files': ['go.mod', 'go.sum'],
            'extensions': ['.go'],
            'patterns': [r'package\s+\w+', r'import\s+\(', r'func\s+\w+']
        },
        'rust': {
            'files': ['Cargo.toml', 'Cargo.lock'],
            'extensions': ['.rs'],
            'patterns': [r'fn\s+\w+', r'use\s+\w+', r'pub\s+']
        },
        'java': {
            'files': ['pom.xml', 'build.gradle', 'settings.gradle'],
            'extensions': ['.java'],
            'patterns': [r'public\s+class', r'import\s+java\.', r'package\s+']
        },
        'cpp': {
            'files': ['CMakeLists.txt', 'Makefile'],
            'extensions': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'patterns': [r'#include\s*<', r'namespace\s+\w+', r'class\s+\w+']
        }
    }
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'python': {
            'django': ['django', 'manage.py', 'settings.py', 'urls.py'],
            'flask': ['flask', 'app.py', 'application.py'],
            'fastapi': ['fastapi', 'main.py'],
            'pytest': ['pytest', 'conftest.py', 'test_*.py'],
            'numpy': ['numpy', 'np.'],
            'pandas': ['pandas', 'pd.'],
            'tensorflow': ['tensorflow', 'tf.'],
            'pytorch': ['torch', 'nn.Module'],
        },
        'javascript': {
            'react': ['react', 'jsx', 'useState', 'useEffect'],
            'vue': ['vue', '.vue', 'createApp'],
            'angular': ['angular', '@angular/', 'ng'],
            'express': ['express', 'app.listen', 'app.get'],
            'next': ['next', 'next.config'],
            'jest': ['jest', 'describe(', 'test('],
        },
        'typescript': {
            'react': ['react', 'tsx', 'useState', 'useEffect'],
            'angular': ['@angular/', 'ng', 'Component'],
            'nest': ['@nestjs/', 'nest'],
        }
    }
    
    def __init__(self):
        """Initialize the Context Analyzer."""
        self._cache: Dict[str, Any] = {}
    
    def analyze_project(self, project_path: Path) -> ProjectContext:
        """
        Analyze a complete project and return comprehensive context.
        
        Args:
            project_path: Path to the project root directory
            
        Returns:
            ProjectContext with all analyzed information
        """
        if not project_path.exists() or not project_path.is_dir():
            raise ValueError(f"Invalid project path: {project_path}")
        
        logger.info(f"Analyzing project at: {project_path}")
        
        context = ProjectContext(project_path=project_path)
        
        # Analyze file structure first
        context.file_structure = self._analyze_file_structure(project_path)
        
        # Detect primary language
        context.language = self.detect_language(project_path)
        
        # Detect frameworks
        if context.language:
            context.frameworks = self.detect_framework(project_path, context.language.name)
        
        # Extract coding conventions
        context.conventions = self.extract_conventions(project_path)
        
        # Analyze dependencies
        context.dependencies = self._analyze_dependencies(project_path)
        
        # Detect architecture patterns
        context.architecture_patterns = self._detect_architecture_patterns(project_path)
        
        # Find entry points
        context.entry_points = self._find_entry_points(project_path)
        
        # Get Git information
        context.git_info = self._analyze_git_info(project_path)
        
        logger.info(f"Project analysis complete: {context.language.name if context.language else 'unknown'}")
        
        return context
    
    def detect_language(self, path: Path) -> Optional[Language]:
        """
        Detect the primary programming language of a file or project.
        
        Args:
            path: Path to file or directory
            
        Returns:
            Language object with detected language information
        """
        if path.is_file():
            return self._detect_language_from_file(path)
        
        # For directories, analyze all files
        language_scores: Dict[str, float] = defaultdict(float)
        file_counts: Dict[str, int] = defaultdict(int)
        
        # Check for language-specific files
        for lang, indicators in self.LANGUAGE_INDICATORS.items():
            for indicator_file in indicators['files']:
                if (path / indicator_file).exists():
                    language_scores[lang] += 10.0
        
        # Count files by extension
        for file_path in path.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                for lang, indicators in self.LANGUAGE_INDICATORS.items():
                    if ext in indicators['extensions']:
                        file_counts[lang] += 1
                        language_scores[lang] += 1.0
        
        if not language_scores:
            return None
        
        # Get language with highest score
        primary_lang = max(language_scores.items(), key=lambda x: x[1])
        
        return Language(
            name=primary_lang[0],
            file_extensions=self.LANGUAGE_INDICATORS[primary_lang[0]]['extensions'],
            confidence=min(1.0, primary_lang[1] / 20.0)
        )
    
    def _detect_language_from_file(self, file_path: Path) -> Optional[Language]:
        """Detect language from a single file."""
        ext = file_path.suffix.lower()
        
        for lang, indicators in self.LANGUAGE_INDICATORS.items():
            if ext in indicators['extensions']:
                return Language(
                    name=lang,
                    file_extensions=[ext],
                    confidence=1.0
                )
        
        return None
    
    def detect_framework(self, project_path: Path, language: str = None) -> List[Framework]:
        """
        Detect frameworks and libraries used in the project.
        
        Args:
            project_path: Path to project root
            language: Optional language hint
            
        Returns:
            List of detected frameworks
        """
        if not language:
            lang_obj = self.detect_language(project_path)
            language = lang_obj.name if lang_obj else None
        
        if not language or language not in self.FRAMEWORK_PATTERNS:
            return []
        
        frameworks: List[Framework] = []
        framework_scores: Dict[str, float] = defaultdict(float)
        
        patterns = self.FRAMEWORK_PATTERNS[language]
        
        # Check dependency files
        dep_files = self._get_dependency_files(project_path, language)
        for dep_file in dep_files:
            if dep_file.exists():
                content = dep_file.read_text(errors='ignore')
                for framework_name, indicators in patterns.items():
                    for indicator in indicators:
                        if indicator in content.lower():
                            framework_scores[framework_name] += 2.0
        
        # Check source files
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.go', '.rs']:
                try:
                    content = file_path.read_text(errors='ignore')
                    for framework_name, indicators in patterns.items():
                        for indicator in indicators:
                            if indicator in content:
                                framework_scores[framework_name] += 0.5
                except Exception:
                    continue
        
        # Convert scores to frameworks
        for framework_name, score in framework_scores.items():
            if score >= 1.0:
                category = self._categorize_framework(framework_name)
                frameworks.append(Framework(
                    name=framework_name,
                    category=category,
                    confidence=min(1.0, score / 10.0)
                ))
        
        return frameworks
    
    def extract_conventions(self, project_path: Path) -> CodingConventions:
        """
        Extract coding conventions from existing code.
        
        Args:
            project_path: Path to project root
            
        Returns:
            CodingConventions object with detected conventions
        """
        conventions = CodingConventions()
        
        # Analyze Python files for conventions
        python_files = list(project_path.rglob('*.py'))
        if python_files:
            conventions = self._extract_python_conventions(python_files)
        
        # Analyze JavaScript/TypeScript files
        js_files = list(project_path.rglob('*.js')) + list(project_path.rglob('*.ts'))
        if js_files and not python_files:
            conventions = self._extract_js_conventions(js_files)
        
        return conventions
    
    def _extract_python_conventions(self, files: List[Path]) -> CodingConventions:
        """Extract conventions from Python files."""
        conventions = CodingConventions()
        
        indentation_counts = Counter()
        quote_counts = Counter()
        line_lengths = []
        
        for file_path in files[:20]:  # Sample first 20 files
            try:
                content = file_path.read_text()
                lines = content.splitlines()
                
                # Analyze indentation
                for line in lines:
                    if line and line[0] in ' \t':
                        indent = len(line) - len(line.lstrip())
                        if indent > 0:
                            indentation_counts[indent] += 1
                
                # Analyze quote style
                single_quotes = content.count("'")
                double_quotes = content.count('"')
                quote_counts['single'] += single_quotes
                quote_counts['double'] += double_quotes
                
                # Analyze line lengths
                for line in lines:
                    if line.strip():
                        line_lengths.append(len(line))
                
            except Exception as e:
                logger.debug(f"Error analyzing {file_path}: {e}")
                continue
        
        # Determine indentation
        if indentation_counts:
            most_common_indent = indentation_counts.most_common(1)[0][0]
            conventions.indentation = ' ' * most_common_indent
        
        # Determine quote style
        if quote_counts:
            conventions.quote_style = 'single' if quote_counts['single'] > quote_counts['double'] else 'double'
        
        # Determine line length
        if line_lengths:
            conventions.line_length = int(sum(line_lengths) / len(line_lengths) * 1.2)
        
        # Detect naming conventions
        conventions.naming_conventions = {
            'function': 'snake_case',
            'class': 'PascalCase',
            'constant': 'UPPER_CASE',
            'variable': 'snake_case'
        }
        
        return conventions
    
    def _extract_js_conventions(self, files: List[Path]) -> CodingConventions:
        """Extract conventions from JavaScript/TypeScript files."""
        conventions = CodingConventions()
        
        indentation_counts = Counter()
        quote_counts = Counter()
        
        for file_path in files[:20]:
            try:
                content = file_path.read_text()
                lines = content.splitlines()
                
                for line in lines:
                    if line and line[0] in ' \t':
                        indent = len(line) - len(line.lstrip())
                        if indent > 0:
                            indentation_counts[indent] += 1
                
                single_quotes = content.count("'")
                double_quotes = content.count('"')
                quote_counts['single'] += single_quotes
                quote_counts['double'] += double_quotes
                
            except Exception:
                continue
        
        if indentation_counts:
            most_common_indent = indentation_counts.most_common(1)[0][0]
            conventions.indentation = ' ' * most_common_indent
        
        if quote_counts:
            conventions.quote_style = 'single' if quote_counts['single'] > quote_counts['double'] else 'double'
        
        conventions.naming_conventions = {
            'function': 'camelCase',
            'class': 'PascalCase',
            'constant': 'UPPER_CASE',
            'variable': 'camelCase'
        }
        
        return conventions
    
    def _analyze_file_structure(self, project_path: Path) -> DirectoryTree:
        """Analyze project directory structure."""
        tree = DirectoryTree(root=project_path)
        
        for item in project_path.rglob('*'):
            # Skip hidden and common ignore directories
            if any(part.startswith('.') for part in item.parts):
                continue
            if any(part in ['node_modules', '__pycache__', 'venv', 'env', 'dist', 'build'] for part in item.parts):
                continue
            
            if item.is_dir():
                tree.directories.append(item)
            elif item.is_file():
                ext = item.suffix.lower()
                if ext not in tree.files:
                    tree.files[ext] = []
                tree.files[ext].append(item)
                tree.total_files += 1
                try:
                    tree.total_size += item.stat().st_size
                except Exception:
                    pass
        
        return tree
    
    def _analyze_dependencies(self, project_path: Path) -> List[Dependency]:
        """Analyze project dependencies."""
        dependencies = []
        
        # Python dependencies
        req_file = project_path / 'requirements.txt'
        if req_file.exists():
            dependencies.extend(self._parse_requirements_txt(req_file))
        
        # Node dependencies
        package_json = project_path / 'package.json'
        if package_json.exists():
            dependencies.extend(self._parse_package_json(package_json))
        
        # Go dependencies
        go_mod = project_path / 'go.mod'
        if go_mod.exists():
            dependencies.extend(self._parse_go_mod(go_mod))
        
        # Rust dependencies
        cargo_toml = project_path / 'Cargo.toml'
        if cargo_toml.exists():
            dependencies.extend(self._parse_cargo_toml(cargo_toml))
        
        return dependencies
    
    def _parse_requirements_txt(self, file_path: Path) -> List[Dependency]:
        """Parse Python requirements.txt file."""
        dependencies = []
        content = file_path.read_text()
        
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                # Parse package==version or package>=version
                match = re.match(r'([a-zA-Z0-9_-]+)([>=<~!]=?)?([\d.]+)?', line)
                if match:
                    name = match.group(1)
                    version = match.group(3) if match.group(3) else None
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        source='requirements.txt'
                    ))
        
        return dependencies
    
    def _parse_package_json(self, file_path: Path) -> List[Dependency]:
        """Parse Node package.json file."""
        dependencies = []
        
        try:
            data = json.loads(file_path.read_text())
            
            for dep_name, version in data.get('dependencies', {}).items():
                dependencies.append(Dependency(
                    name=dep_name,
                    version=version.lstrip('^~'),
                    source='package.json',
                    is_dev=False
                ))
            
            for dep_name, version in data.get('devDependencies', {}).items():
                dependencies.append(Dependency(
                    name=dep_name,
                    version=version.lstrip('^~'),
                    source='package.json',
                    is_dev=True
                ))
        except Exception as e:
            logger.debug(f"Error parsing package.json: {e}")
        
        return dependencies
    
    def _parse_go_mod(self, file_path: Path) -> List[Dependency]:
        """Parse Go go.mod file."""
        dependencies = []
        content = file_path.read_text()
        
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('//'):
                match = re.match(r'([a-zA-Z0-9._/-]+)\s+v([\d.]+)', line)
                if match:
                    dependencies.append(Dependency(
                        name=match.group(1),
                        version=match.group(2),
                        source='go.mod'
                    ))
        
        return dependencies
    
    def _parse_cargo_toml(self, file_path: Path) -> List[Dependency]:
        """Parse Rust Cargo.toml file."""
        dependencies = []
        content = file_path.read_text()
        
        in_dependencies = False
        for line in content.splitlines():
            line = line.strip()
            
            if line == '[dependencies]':
                in_dependencies = True
                continue
            elif line.startswith('[') and in_dependencies:
                break
            
            if in_dependencies and '=' in line:
                parts = line.split('=')
                name = parts[0].strip()
                version = parts[1].strip().strip('"\'')
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    source='Cargo.toml'
                ))
        
        return dependencies
    
    def _detect_architecture_patterns(self, project_path: Path) -> List[str]:
        """Detect common architecture patterns."""
        patterns = []
        
        # Check for MVC pattern
        if (project_path / 'models').exists() and \
           (project_path / 'views').exists() and \
           (project_path / 'controllers').exists():
            patterns.append('MVC')
        
        # Check for microservices
        if (project_path / 'services').exists() or \
           len(list(project_path.glob('*-service'))) > 0:
            patterns.append('Microservices')
        
        # Check for layered architecture
        if (project_path / 'domain').exists() and \
           (project_path / 'application').exists() and \
           (project_path / 'infrastructure').exists():
            patterns.append('Clean Architecture')
        
        # Check for monorepo
        if len(list(project_path.glob('packages/*'))) > 1 or \
           len(list(project_path.glob('apps/*'))) > 1:
            patterns.append('Monorepo')
        
        return patterns
    
    def _find_entry_points(self, project_path: Path) -> List[Path]:
        """Find application entry points."""
        entry_points = []
        
        common_entry_files = [
            'main.py', 'app.py', '__main__.py',
            'index.js', 'main.js', 'app.js',
            'main.go', 'main.rs', 'Main.java'
        ]
        
        for entry_file in common_entry_files:
            matches = list(project_path.rglob(entry_file))
            entry_points.extend(matches)
        
        return entry_points
    
    def _analyze_git_info(self, project_path: Path) -> GitInfo:
        """Analyze Git repository information."""
        git_dir = project_path / '.git'
        
        if not git_dir.exists():
            return GitInfo(is_repo=False)
        
        git_info = GitInfo(is_repo=True)
        
        # Try to read current branch
        head_file = git_dir / 'HEAD'
        if head_file.exists():
            try:
                content = head_file.read_text().strip()
                if content.startswith('ref: refs/heads/'):
                    git_info.branch = content.replace('ref: refs/heads/', '')
            except Exception:
                pass
        
        return git_info
    
    def _get_dependency_files(self, project_path: Path, language: str) -> List[Path]:
        """Get dependency files for a language."""
        dep_files = {
            'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
            'javascript': ['package.json'],
            'typescript': ['package.json'],
            'go': ['go.mod'],
            'rust': ['Cargo.toml'],
            'java': ['pom.xml', 'build.gradle']
        }
        
        files = []
        for filename in dep_files.get(language, []):
            file_path = project_path / filename
            if file_path.exists():
                files.append(file_path)
        
        return files
    
    def _categorize_framework(self, framework_name: str) -> str:
        """Categorize a framework by type."""
        categories = {
            'web': ['django', 'flask', 'fastapi', 'express', 'react', 'vue', 'angular', 'next', 'nest'],
            'testing': ['pytest', 'jest', 'mocha', 'jasmine', 'junit'],
            'data': ['numpy', 'pandas', 'tensorflow', 'pytorch'],
            'cli': ['click', 'argparse', 'commander']
        }
        
        for category, frameworks in categories.items():
            if framework_name in frameworks:
                return category
        
        return 'general'

    def analyze_import_patterns(self, project_path: Path) -> Dict[str, Any]:
        """
        Analyze import patterns in the project.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Dictionary with import pattern analysis
        """
        patterns = {
            'import_styles': Counter(),
            'common_imports': Counter(),
            'import_order': [],
            'relative_imports': 0,
            'absolute_imports': 0,
            'grouped_imports': False
        }
        
        # Analyze Python imports
        python_files = list(project_path.rglob('*.py'))
        if python_files:
            patterns.update(self._analyze_python_imports(python_files))
        
        # Analyze JavaScript/TypeScript imports
        js_files = list(project_path.rglob('*.js')) + list(project_path.rglob('*.ts'))
        if js_files:
            patterns.update(self._analyze_js_imports(js_files))
        
        return patterns
    
    def _analyze_python_imports(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze Python import patterns."""
        patterns = {
            'import_styles': Counter(),
            'common_imports': Counter(),
            'relative_imports': 0,
            'absolute_imports': 0,
            'grouped_imports': False
        }
        
        for file_path in files[:30]:  # Sample files
            try:
                content = file_path.read_text()
                tree = ast.parse(content)
                
                import_groups = []
                current_group = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        patterns['absolute_imports'] += 1
                        for alias in node.names:
                            patterns['common_imports'][alias.name] += 1
                            patterns['import_styles']['import'] += 1
                            current_group.append(('import', alias.name))
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.level > 0:
                            patterns['relative_imports'] += 1
                        else:
                            patterns['absolute_imports'] += 1
                        
                        module = node.module or ""
                        patterns['common_imports'][module] += 1
                        patterns['import_styles']['from_import'] += 1
                        current_group.append(('from', module))
                
                if current_group:
                    import_groups.append(current_group)
                
                # Check if imports are grouped
                if len(import_groups) > 1:
                    patterns['grouped_imports'] = True
                
            except Exception as e:
                logger.debug(f"Error analyzing imports in {file_path}: {e}")
                continue
        
        return patterns
    
    def _analyze_js_imports(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript import patterns."""
        patterns = {
            'import_styles': Counter(),
            'common_imports': Counter(),
            'relative_imports': 0,
            'absolute_imports': 0
        }
        
        for file_path in files[:30]:
            try:
                content = file_path.read_text()
                lines = content.splitlines()
                
                for line in lines:
                    line = line.strip()
                    
                    # ES6 imports
                    if line.startswith('import '):
                        patterns['import_styles']['es6'] += 1
                        match = re.search(r'from\s+[\'"]([^\'"]+)[\'"]', line)
                        if match:
                            module = match.group(1)
                            patterns['common_imports'][module] += 1
                            if module.startswith('.'):
                                patterns['relative_imports'] += 1
                            else:
                                patterns['absolute_imports'] += 1
                    
                    # CommonJS require
                    elif 'require(' in line:
                        patterns['import_styles']['commonjs'] += 1
                        match = re.search(r'require\([\'"]([^\'"]+)[\'"]\)', line)
                        if match:
                            module = match.group(1)
                            patterns['common_imports'][module] += 1
                            if module.startswith('.'):
                                patterns['relative_imports'] += 1
                            else:
                                patterns['absolute_imports'] += 1
            
            except Exception:
                continue
        
        return patterns
    
    def detect_naming_conventions(self, project_path: Path) -> Dict[str, str]:
        """
        Detect naming conventions used in the project.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Dictionary mapping entity types to naming conventions
        """
        conventions = {
            'function': 'unknown',
            'class': 'unknown',
            'constant': 'unknown',
            'variable': 'unknown',
            'file': 'unknown'
        }
        
        # Analyze Python files
        python_files = list(project_path.rglob('*.py'))
        if python_files:
            py_conventions = self._detect_python_naming(python_files)
            conventions.update(py_conventions)
        
        # Analyze JavaScript/TypeScript files
        js_files = list(project_path.rglob('*.js')) + list(project_path.rglob('*.ts'))
        if js_files:
            js_conventions = self._detect_js_naming(js_files)
            conventions.update(js_conventions)
        
        # Analyze file naming
        all_files = list(project_path.rglob('*'))
        conventions['file'] = self._detect_file_naming(all_files)
        
        return conventions
    
    def _detect_python_naming(self, files: List[Path]) -> Dict[str, str]:
        """Detect Python naming conventions."""
        function_patterns = Counter()
        class_patterns = Counter()
        constant_patterns = Counter()
        variable_patterns = Counter()
        
        for file_path in files[:20]:
            try:
                content = file_path.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        name = node.name
                        if name.startswith('_'):
                            continue
                        function_patterns[self._classify_naming_style(name)] += 1
                    
                    elif isinstance(node, ast.ClassDef):
                        name = node.name
                        class_patterns[self._classify_naming_style(name)] += 1
                    
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                name = target.id
                                if name.isupper():
                                    constant_patterns[self._classify_naming_style(name)] += 1
                                else:
                                    variable_patterns[self._classify_naming_style(name)] += 1
            
            except Exception:
                continue
        
        return {
            'function': function_patterns.most_common(1)[0][0] if function_patterns else 'snake_case',
            'class': class_patterns.most_common(1)[0][0] if class_patterns else 'PascalCase',
            'constant': constant_patterns.most_common(1)[0][0] if constant_patterns else 'UPPER_CASE',
            'variable': variable_patterns.most_common(1)[0][0] if variable_patterns else 'snake_case'
        }
    
    def _detect_js_naming(self, files: List[Path]) -> Dict[str, str]:
        """Detect JavaScript/TypeScript naming conventions."""
        function_patterns = Counter()
        class_patterns = Counter()
        constant_patterns = Counter()
        
        for file_path in files[:20]:
            try:
                content = file_path.read_text()
                lines = content.splitlines()
                
                for line in lines:
                    line = line.strip()
                    
                    # Function declarations
                    func_match = re.match(r'(?:function|const|let|var)\s+(\w+)', line)
                    if func_match:
                        name = func_match.group(1)
                        function_patterns[self._classify_naming_style(name)] += 1
                    
                    # Class declarations
                    class_match = re.match(r'class\s+(\w+)', line)
                    if class_match:
                        name = class_match.group(1)
                        class_patterns[self._classify_naming_style(name)] += 1
                    
                    # Constants
                    const_match = re.match(r'const\s+([A-Z_]+)\s*=', line)
                    if const_match:
                        name = const_match.group(1)
                        constant_patterns[self._classify_naming_style(name)] += 1
            
            except Exception:
                continue
        
        return {
            'function': function_patterns.most_common(1)[0][0] if function_patterns else 'camelCase',
            'class': class_patterns.most_common(1)[0][0] if class_patterns else 'PascalCase',
            'constant': constant_patterns.most_common(1)[0][0] if constant_patterns else 'UPPER_CASE'
        }
    
    def _detect_file_naming(self, files: List[Path]) -> str:
        """Detect file naming convention."""
        naming_styles = Counter()
        
        for file_path in files:
            if file_path.is_file():
                name = file_path.stem
                if name and not name.startswith('.'):
                    style = self._classify_naming_style(name)
                    naming_styles[style] += 1
        
        if naming_styles:
            return naming_styles.most_common(1)[0][0]
        
        return 'snake_case'
    
    def _classify_naming_style(self, name: str) -> str:
        """Classify a name into a naming convention style."""
        if not name:
            return 'unknown'
        
        # Check for UPPER_CASE
        if name.isupper() and '_' in name:
            return 'UPPER_CASE'
        
        # Check for snake_case
        if '_' in name and name.islower():
            return 'snake_case'
        
        # Check for kebab-case
        if '-' in name and name.islower():
            return 'kebab-case'
        
        # Check for PascalCase
        if name[0].isupper() and not '_' in name and not '-' in name:
            return 'PascalCase'
        
        # Check for camelCase
        if name[0].islower() and not '_' in name and not '-' in name:
            has_upper = any(c.isupper() for c in name[1:])
            if has_upper:
                return 'camelCase'
        
        return 'mixed'
    
    def analyze_coding_style(self, project_path: Path) -> Dict[str, Any]:
        """
        Comprehensive coding style analysis.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Dictionary with detailed coding style information
        """
        style = {
            'indentation': self.extract_conventions(project_path).indentation,
            'quote_style': self.extract_conventions(project_path).quote_style,
            'line_length': self.extract_conventions(project_path).line_length,
            'naming_conventions': self.detect_naming_conventions(project_path),
            'import_patterns': self.analyze_import_patterns(project_path),
            'formatting_rules': {}
        }
        
        # Check for formatter config files
        if (project_path / '.prettierrc').exists() or (project_path / '.prettierrc.json').exists():
            style['formatting_rules']['prettier'] = True
        
        if (project_path / '.eslintrc').exists() or (project_path / '.eslintrc.json').exists():
            style['formatting_rules']['eslint'] = True
        
        if (project_path / 'pyproject.toml').exists():
            content = (project_path / 'pyproject.toml').read_text()
            if 'black' in content:
                style['formatting_rules']['black'] = True
            if 'flake8' in content or 'pylint' in content:
                style['formatting_rules']['linter'] = True
        
        return style

    def build_dependency_graph(self, project_path: Path) -> Dict[str, List[str]]:
        """
        Build a dependency graph showing relationships between modules.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Dictionary mapping modules to their dependencies
        """
        graph = defaultdict(list)
        
        # Analyze Python files
        python_files = list(project_path.rglob('*.py'))
        for file_path in python_files:
            try:
                content = file_path.read_text()
                tree = ast.parse(content)
                
                module_name = self._get_module_name(file_path, project_path)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            graph[module_name].append(alias.name)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            graph[module_name].append(node.module)
            
            except Exception:
                continue
        
        # Analyze JavaScript/TypeScript files
        js_files = list(project_path.rglob('*.js')) + list(project_path.rglob('*.ts'))
        for file_path in js_files:
            try:
                content = file_path.read_text()
                module_name = self._get_module_name(file_path, project_path)
                
                # Find imports
                for match in re.finditer(r'from\s+[\'"]([^\'"]+)[\'"]', content):
                    imported = match.group(1)
                    graph[module_name].append(imported)
                
                for match in re.finditer(r'require\([\'"]([^\'"]+)[\'"]\)', content):
                    imported = match.group(1)
                    graph[module_name].append(imported)
            
            except Exception:
                continue
        
        return dict(graph)
    
    def _get_module_name(self, file_path: Path, project_path: Path) -> str:
        """Get module name from file path."""
        try:
            relative = file_path.relative_to(project_path)
            return str(relative.with_suffix('')).replace('/', '.')
        except ValueError:
            return file_path.stem
    
    def detect_architecture_patterns(self, project_path: Path) -> List[Dict[str, Any]]:
        """
        Detect architecture patterns in the project.
        
        Args:
            project_path: Path to project root
            
        Returns:
            List of detected patterns with confidence scores
        """
        patterns = []
        
        # Check for MVC pattern
        mvc_score = self._check_mvc_pattern(project_path)
        if mvc_score > 0.5:
            patterns.append({
                'name': 'MVC',
                'confidence': mvc_score,
                'description': 'Model-View-Controller architecture'
            })
        
        # Check for layered architecture
        layered_score = self._check_layered_architecture(project_path)
        if layered_score > 0.5:
            patterns.append({
                'name': 'Layered Architecture',
                'confidence': layered_score,
                'description': 'Separation into presentation, business, and data layers'
            })
        
        # Check for microservices
        microservices_score = self._check_microservices(project_path)
        if microservices_score > 0.5:
            patterns.append({
                'name': 'Microservices',
                'confidence': microservices_score,
                'description': 'Distributed services architecture'
            })
        
        # Check for clean architecture
        clean_score = self._check_clean_architecture(project_path)
        if clean_score > 0.5:
            patterns.append({
                'name': 'Clean Architecture',
                'confidence': clean_score,
                'description': 'Domain-centric layered architecture'
            })
        
        # Check for monorepo
        monorepo_score = self._check_monorepo(project_path)
        if monorepo_score > 0.5:
            patterns.append({
                'name': 'Monorepo',
                'confidence': monorepo_score,
                'description': 'Multiple projects in single repository'
            })
        
        # Check for hexagonal architecture
        hexagonal_score = self._check_hexagonal_architecture(project_path)
        if hexagonal_score > 0.5:
            patterns.append({
                'name': 'Hexagonal Architecture',
                'confidence': hexagonal_score,
                'description': 'Ports and adapters architecture'
            })
        
        return patterns
    
    def _check_mvc_pattern(self, project_path: Path) -> float:
        """Check for MVC pattern."""
        score = 0.0
        
        if (project_path / 'models').exists():
            score += 0.33
        if (project_path / 'views').exists():
            score += 0.33
        if (project_path / 'controllers').exists():
            score += 0.34
        
        # Check for variations
        if score == 0:
            if (project_path / 'model').exists():
                score += 0.33
            if (project_path / 'view').exists():
                score += 0.33
            if (project_path / 'controller').exists():
                score += 0.34
        
        return score
    
    def _check_layered_architecture(self, project_path: Path) -> float:
        """Check for layered architecture."""
        score = 0.0
        layers = 0
        
        common_layers = [
            'presentation', 'ui', 'web',
            'business', 'service', 'application',
            'data', 'persistence', 'repository', 'dal'
        ]
        
        for layer in common_layers:
            if (project_path / layer).exists():
                layers += 1
        
        if layers >= 3:
            score = min(1.0, layers / 4.0)
        
        return score
    
    def _check_microservices(self, project_path: Path) -> float:
        """Check for microservices architecture."""
        score = 0.0
        
        # Check for services directory
        if (project_path / 'services').exists():
            service_count = len(list((project_path / 'services').iterdir()))
            if service_count > 1:
                score += 0.4
        
        # Check for service-named directories
        service_dirs = list(project_path.glob('*-service'))
        if len(service_dirs) > 1:
            score += 0.3
        
        # Check for docker-compose (common in microservices)
        if (project_path / 'docker-compose.yml').exists():
            score += 0.3
        
        return min(1.0, score)
    
    def _check_clean_architecture(self, project_path: Path) -> float:
        """Check for clean architecture."""
        score = 0.0
        
        clean_dirs = ['domain', 'application', 'infrastructure', 'interfaces']
        found = sum(1 for d in clean_dirs if (project_path / d).exists())
        
        if found >= 3:
            score = found / len(clean_dirs)
        
        return score
    
    def _check_monorepo(self, project_path: Path) -> float:
        """Check for monorepo structure."""
        score = 0.0
        
        # Check for packages directory
        packages_dir = project_path / 'packages'
        if packages_dir.exists():
            package_count = len(list(packages_dir.iterdir()))
            if package_count > 1:
                score += 0.5
        
        # Check for apps directory
        apps_dir = project_path / 'apps'
        if apps_dir.exists():
            app_count = len(list(apps_dir.iterdir()))
            if app_count > 1:
                score += 0.5
        
        return min(1.0, score)
    
    def _check_hexagonal_architecture(self, project_path: Path) -> float:
        """Check for hexagonal architecture."""
        score = 0.0
        
        hexagonal_indicators = ['ports', 'adapters', 'core', 'domain']
        found = sum(1 for d in hexagonal_indicators if (project_path / d).exists())
        
        if found >= 2:
            score = found / len(hexagonal_indicators)
        
        return score
    
    def find_similar_code(self, code_snippet: str, project_path: Path, 
                         threshold: float = 0.7) -> List[CodeMatch]:
        """
        Find similar code snippets in the project.
        
        Args:
            code_snippet: Code to search for
            project_path: Path to project root
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of similar code matches
        """
        matches = []
        
        # Normalize the search snippet
        normalized_snippet = self._normalize_code(code_snippet)
        snippet_tokens = set(normalized_snippet.split())
        
        # Search through project files
        for file_path in project_path.rglob('*.py'):
            try:
                content = file_path.read_text()
                lines = content.splitlines()
                
                # Check each window of lines
                window_size = len(code_snippet.splitlines())
                for i in range(len(lines) - window_size + 1):
                    window = '\n'.join(lines[i:i + window_size])
                    normalized_window = self._normalize_code(window)
                    window_tokens = set(normalized_window.split())
                    
                    # Calculate similarity using Jaccard index
                    if snippet_tokens and window_tokens:
                        intersection = len(snippet_tokens & window_tokens)
                        union = len(snippet_tokens | window_tokens)
                        similarity = intersection / union if union > 0 else 0.0
                        
                        if similarity >= threshold:
                            matches.append(CodeMatch(
                                file_path=file_path,
                                line_number=i + 1,
                                similarity_score=similarity,
                                code_snippet=window
                            ))
            
            except Exception:
                continue
        
        # Sort by similarity score
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return matches[:10]  # Return top 10 matches
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison."""
        # Remove comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # Remove extra whitespace
        code = re.sub(r'\s+', ' ', code)
        
        # Convert to lowercase
        code = code.lower()
        
        return code.strip()
    
    def analyze_module_complexity(self, project_path: Path) -> Dict[str, Any]:
        """
        Analyze complexity of modules in the project.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Dictionary with complexity metrics
        """
        complexity = {
            'modules': {},
            'average_complexity': 0.0,
            'max_complexity': 0,
            'total_modules': 0
        }
        
        total_complexity = 0
        
        # Analyze Python files
        for file_path in project_path.rglob('*.py'):
            try:
                content = file_path.read_text()
                tree = ast.parse(content)
                
                module_complexity = 0
                
                # Count functions and classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        module_complexity += 1
                        # Add complexity for control structures
                        for child in ast.walk(node):
                            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                                module_complexity += 1
                    
                    elif isinstance(node, ast.ClassDef):
                        module_complexity += 2
                
                module_name = self._get_module_name(file_path, project_path)
                complexity['modules'][module_name] = module_complexity
                total_complexity += module_complexity
                complexity['total_modules'] += 1
                complexity['max_complexity'] = max(complexity['max_complexity'], module_complexity)
            
            except Exception:
                continue
        
        if complexity['total_modules'] > 0:
            complexity['average_complexity'] = total_complexity / complexity['total_modules']
        
        return complexity
    
    def get_project_statistics(self, project_path: Path) -> Dict[str, Any]:
        """
        Get comprehensive project statistics.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Dictionary with project statistics
        """
        stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_size': 0,
            'languages': {},
            'file_types': Counter(),
            'largest_files': [],
            'most_complex_modules': []
        }
        
        file_sizes = []
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                # Skip common ignore patterns
                if any(part in str(file_path) for part in ['.git', '__pycache__', 'node_modules', 'venv']):
                    continue
                
                stats['total_files'] += 1
                ext = file_path.suffix.lower()
                stats['file_types'][ext] += 1
                
                try:
                    size = file_path.stat().st_size
                    stats['total_size'] += size
                    file_sizes.append((file_path, size))
                    
                    # Count lines for text files
                    if ext in ['.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c', '.h']:
                        content = file_path.read_text(errors='ignore')
                        lines = len(content.splitlines())
                        stats['total_lines'] += lines
                        
                        # Track by language
                        lang = self._get_language_from_extension(ext)
                        if lang not in stats['languages']:
                            stats['languages'][lang] = {'files': 0, 'lines': 0}
                        stats['languages'][lang]['files'] += 1
                        stats['languages'][lang]['lines'] += lines
                
                except Exception:
                    continue
        
        # Get largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        stats['largest_files'] = [
            {'path': str(f[0]), 'size': f[1]} 
            for f in file_sizes[:10]
        ]
        
        # Get most complex modules
        complexity = self.analyze_module_complexity(project_path)
        sorted_modules = sorted(
            complexity['modules'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        stats['most_complex_modules'] = [
            {'module': m[0], 'complexity': m[1]}
            for m in sorted_modules[:10]
        ]
        
        return stats
    
    def _get_language_from_extension(self, ext: str) -> str:
        """Get language name from extension."""
        mapping = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++',
            '.rb': 'Ruby',
            '.php': 'PHP'
        }
        return mapping.get(ext, 'Unknown')
