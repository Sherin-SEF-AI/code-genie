"""
Related Code Identification System.

This module provides:
- Algorithms to find related code when working on features
- Dependency analysis for identifying affected areas
- Test suggestion system based on code changes
- Documentation update detection
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class RelatedCode:
    """Represents related code that may need updates."""
    file_path: Path
    reason: str
    relationship_type: str  # dependency, similar, test, documentation
    confidence: float
    line_numbers: Optional[List[int]] = None
    suggested_action: Optional[str] = None


@dataclass
class DependencyInfo:
    """Information about code dependencies."""
    file_path: Path
    imports: List[str]
    imported_by: List[Path]
    depends_on: List[Path]
    symbols_used: List[str]
    symbols_defined: List[str]


@dataclass
class TestSuggestion:
    """Suggestion for tests to add or update."""
    test_file: Path
    test_type: str  # unit, integration, e2e
    reason: str
    suggested_tests: List[str]
    priority: int  # 1-5
    confidence: float


@dataclass
class DocumentationUpdate:
    """Suggestion for documentation updates."""
    doc_file: Path
    update_type: str  # api_doc, readme, comment
    reason: str
    affected_symbols: List[str]
    priority: int



class DependencyAnalyzer:
    """Analyzes code dependencies to identify affected areas."""
    
    def __init__(self, project_root: Path):
        """
        Initialize dependency analyzer.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.dependency_graph: Dict[Path, DependencyInfo] = {}
        self.reverse_dependencies: Dict[Path, Set[Path]] = defaultdict(set)
    
    async def build_dependency_graph(self) -> Dict[Path, DependencyInfo]:
        """
        Build dependency graph for the entire project.
        
        Returns:
            Dictionary mapping files to their dependency information
        """
        python_files = self._find_python_files()
        
        # First pass: collect all imports and symbols
        for file_path in python_files:
            dep_info = await self._analyze_file_dependencies(file_path)
            if dep_info:
                self.dependency_graph[file_path] = dep_info
        
        # Second pass: build reverse dependencies
        for file_path, dep_info in self.dependency_graph.items():
            for imported_module in dep_info.imports:
                # Try to resolve import to file path
                resolved_path = self._resolve_import(imported_module)
                if resolved_path and resolved_path in self.dependency_graph:
                    self.reverse_dependencies[resolved_path].add(file_path)
                    dep_info.depends_on.append(resolved_path)
        
        # Update imported_by information
        for file_path, importers in self.reverse_dependencies.items():
            if file_path in self.dependency_graph:
                self.dependency_graph[file_path].imported_by = list(importers)
        
        return self.dependency_graph
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in project."""
        ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.pytest_cache', '.mypy_cache'
        ]
        
        python_files = []
        for path in self.project_root.rglob('*.py'):
            if any(ignore in str(path) for ignore in ignore_patterns):
                continue
            python_files.append(path)
        
        return python_files
    
    async def _analyze_file_dependencies(self, file_path: Path) -> Optional[DependencyInfo]:
        """
        Analyze dependencies for a single file.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            DependencyInfo or None if analysis fails
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            imports = []
            symbols_defined = []
            symbols_used = []
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                
                # Extract defined symbols
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    symbols_defined.append(node.name)
                
                # Extract used symbols (function calls, attribute access)
                elif isinstance(node, ast.Name):
                    symbols_used.append(node.id)
            
            return DependencyInfo(
                file_path=file_path,
                imports=imports,
                imported_by=[],
                depends_on=[],
                symbols_used=list(set(symbols_used)),
                symbols_defined=symbols_defined
            )
            
        except Exception as e:
            print(f"Error analyzing dependencies for {file_path}: {e}")
            return None
    
    def _resolve_import(self, import_name: str) -> Optional[Path]:
        """
        Resolve an import name to a file path.
        
        Args:
            import_name: Import name (e.g., 'codegenie.core.agent')
            
        Returns:
            Resolved file path or None
        """
        # Convert import name to file path
        parts = import_name.split('.')
        
        # Try to find the file
        possible_paths = [
            self.project_root / 'src' / '/'.join(parts) / '__init__.py',
            self.project_root / 'src' / f"{'/'.join(parts)}.py",
            self.project_root / '/'.join(parts) / '__init__.py',
            self.project_root / f"{'/'.join(parts)}.py",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def get_affected_files(self, changed_file: Path) -> List[Path]:
        """
        Get files that may be affected by changes to a file.
        
        Args:
            changed_file: File that was changed
            
        Returns:
            List of potentially affected files
        """
        affected = set()
        
        if changed_file in self.dependency_graph:
            # Files that import this file
            affected.update(self.dependency_graph[changed_file].imported_by)
            
            # Files that this file depends on (might need to check compatibility)
            affected.update(self.dependency_graph[changed_file].depends_on)
        
        return list(affected)
    
    def get_dependency_chain(self, file_path: Path, max_depth: int = 3) -> List[List[Path]]:
        """
        Get dependency chains starting from a file.
        
        Args:
            file_path: Starting file
            max_depth: Maximum depth to traverse
            
        Returns:
            List of dependency chains
        """
        chains = []
        visited = set()
        
        def traverse(current: Path, chain: List[Path], depth: int):
            if depth > max_depth or current in visited:
                return
            
            visited.add(current)
            chain.append(current)
            
            if current in self.dependency_graph:
                importers = self.dependency_graph[current].imported_by
                if not importers:
                    chains.append(chain.copy())
                else:
                    for importer in importers:
                        traverse(importer, chain.copy(), depth + 1)
            
            visited.remove(current)
        
        traverse(file_path, [], 0)
        return chains



class TestSuggestionEngine:
    """Suggests tests based on code changes."""
    
    def __init__(self, project_root: Path):
        """
        Initialize test suggestion engine.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.test_patterns = {
            'unit': 'test_{module}.py',
            'integration': 'test_{module}_integration.py',
            'e2e': 'test_{module}_e2e.py'
        }
    
    async def suggest_tests(
        self,
        changed_file: Path,
        changes_description: Optional[str] = None
    ) -> List[TestSuggestion]:
        """
        Suggest tests for a changed file.
        
        Args:
            changed_file: File that was changed
            changes_description: Optional description of changes
            
        Returns:
            List of test suggestions
        """
        suggestions = []
        
        # Skip if already a test file
        if 'test' in str(changed_file):
            return suggestions
        
        # Analyze the file to understand what was changed
        try:
            content = changed_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
            
            # Suggest unit tests
            if functions or classes:
                test_file = self._get_test_file_path(changed_file, 'unit')
                suggested_tests = []
                
                for func in functions:
                    if not func.startswith('_'):  # Skip private functions
                        suggested_tests.append(f"test_{func}")
                
                for cls in classes:
                    suggested_tests.append(f"Test{cls}")
                
                if suggested_tests:
                    suggestion = TestSuggestion(
                        test_file=test_file,
                        test_type='unit',
                        reason=f"New or modified functions/classes in {changed_file.name}",
                        suggested_tests=suggested_tests,
                        priority=4,
                        confidence=0.8
                    )
                    suggestions.append(suggestion)
            
            # Suggest integration tests if file has external dependencies
            if any('import' in line for line in content.split('\n')):
                test_file = self._get_test_file_path(changed_file, 'integration')
                suggestion = TestSuggestion(
                    test_file=test_file,
                    test_type='integration',
                    reason=f"File has external dependencies that should be tested",
                    suggested_tests=[f"test_{changed_file.stem}_integration"],
                    priority=3,
                    confidence=0.6
                )
                suggestions.append(suggestion)
            
        except Exception as e:
            print(f"Error suggesting tests for {changed_file}: {e}")
        
        return suggestions
    
    def _get_test_file_path(self, source_file: Path, test_type: str) -> Path:
        """
        Get the path where test file should be located.
        
        Args:
            source_file: Source file being tested
            test_type: Type of test (unit, integration, e2e)
            
        Returns:
            Path to test file
        """
        # Convert src/module/file.py to tests/test_file.py
        relative_path = source_file.relative_to(self.project_root)
        
        # Remove 'src' prefix if present
        parts = list(relative_path.parts)
        if parts[0] == 'src':
            parts = parts[1:]
        
        # Create test file name
        file_name = parts[-1]
        module_name = file_name.replace('.py', '')
        
        if test_type == 'unit':
            test_name = f"test_{module_name}.py"
            test_dir = self.project_root / 'tests' / 'unit'
        elif test_type == 'integration':
            test_name = f"test_{module_name}_integration.py"
            test_dir = self.project_root / 'tests' / 'integration'
        else:  # e2e
            test_name = f"test_{module_name}_e2e.py"
            test_dir = self.project_root / 'tests' / 'e2e'
        
        return test_dir / test_name
    
    def check_test_coverage(self, source_file: Path) -> Dict[str, Any]:
        """
        Check if a source file has corresponding tests.
        
        Args:
            source_file: Source file to check
            
        Returns:
            Dictionary with coverage information
        """
        coverage = {
            'has_unit_tests': False,
            'has_integration_tests': False,
            'has_e2e_tests': False,
            'test_files': []
        }
        
        for test_type in ['unit', 'integration', 'e2e']:
            test_file = self._get_test_file_path(source_file, test_type)
            if test_file.exists():
                coverage[f'has_{test_type}_tests'] = True
                coverage['test_files'].append(test_file)
        
        return coverage



class DocumentationDetector:
    """Detects when documentation needs to be updated."""
    
    def __init__(self, project_root: Path):
        """
        Initialize documentation detector.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
    
    async def detect_documentation_updates(
        self,
        changed_file: Path,
        changed_symbols: Optional[List[str]] = None
    ) -> List[DocumentationUpdate]:
        """
        Detect documentation that needs updating based on code changes.
        
        Args:
            changed_file: File that was changed
            changed_symbols: Optional list of symbols that changed
            
        Returns:
            List of documentation update suggestions
        """
        updates = []
        
        try:
            # Check if README needs updating
            readme_update = await self._check_readme_update(changed_file, changed_symbols)
            if readme_update:
                updates.append(readme_update)
            
            # Check if API documentation needs updating
            api_doc_update = await self._check_api_doc_update(changed_file, changed_symbols)
            if api_doc_update:
                updates.append(api_doc_update)
            
            # Check if inline comments need updating
            comment_update = await self._check_comment_update(changed_file)
            if comment_update:
                updates.append(comment_update)
            
        except Exception as e:
            print(f"Error detecting documentation updates for {changed_file}: {e}")
        
        return updates
    
    async def _check_readme_update(
        self,
        changed_file: Path,
        changed_symbols: Optional[List[str]]
    ) -> Optional[DocumentationUpdate]:
        """Check if README needs updating."""
        readme_path = self.project_root / 'README.md'
        
        if not readme_path.exists():
            return None
        
        # If it's a new public API or major component, suggest README update
        if 'api' in str(changed_file).lower() or 'core' in str(changed_file).lower():
            return DocumentationUpdate(
                doc_file=readme_path,
                update_type='readme',
                reason=f"Core component {changed_file.name} was modified",
                affected_symbols=changed_symbols or [],
                priority=3
            )
        
        return None
    
    async def _check_api_doc_update(
        self,
        changed_file: Path,
        changed_symbols: Optional[List[str]]
    ) -> Optional[DocumentationUpdate]:
        """Check if API documentation needs updating."""
        # Look for API documentation files
        api_doc_paths = [
            self.project_root / 'docs' / 'API_REFERENCE.md',
            self.project_root / 'docs' / 'api.md',
            self.project_root / 'API.md'
        ]
        
        for doc_path in api_doc_paths:
            if doc_path.exists():
                # Check if file defines public API
                try:
                    content = changed_file.read_text(encoding='utf-8')
                    tree = ast.parse(content)
                    
                    public_symbols = []
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                            if not node.name.startswith('_'):
                                public_symbols.append(node.name)
                    
                    if public_symbols:
                        return DocumentationUpdate(
                            doc_file=doc_path,
                            update_type='api_doc',
                            reason=f"Public API in {changed_file.name} was modified",
                            affected_symbols=public_symbols,
                            priority=4
                        )
                except:
                    pass
        
        return None
    
    async def _check_comment_update(self, changed_file: Path) -> Optional[DocumentationUpdate]:
        """Check if inline comments need updating."""
        try:
            content = changed_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Check for functions/classes without docstrings
            missing_docs = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node) and not node.name.startswith('_'):
                        missing_docs.append(node.name)
            
            if missing_docs:
                return DocumentationUpdate(
                    doc_file=changed_file,
                    update_type='comment',
                    reason=f"Missing docstrings in {changed_file.name}",
                    affected_symbols=missing_docs,
                    priority=2
                )
        except:
            pass
        
        return None



class RelatedCodeFinder:
    """
    Main class for finding related code that may need updates.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize related code finder.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.dependency_analyzer = DependencyAnalyzer(project_root)
        self.test_suggester = TestSuggestionEngine(project_root)
        self.doc_detector = DocumentationDetector(project_root)
        self.dependency_graph_built = False
    
    async def initialize(self) -> None:
        """Initialize by building dependency graph."""
        if not self.dependency_graph_built:
            await self.dependency_analyzer.build_dependency_graph()
            self.dependency_graph_built = True
    
    async def find_related_code(
        self,
        changed_file: Path,
        change_description: Optional[str] = None
    ) -> List[RelatedCode]:
        """
        Find all code related to a changed file.
        
        Args:
            changed_file: File that was changed
            change_description: Optional description of changes
            
        Returns:
            List of related code that may need updates
        """
        if not self.dependency_graph_built:
            await self.initialize()
        
        related = []
        
        # Find files with direct dependencies
        affected_files = self.dependency_analyzer.get_affected_files(changed_file)
        for file_path in affected_files:
            related.append(RelatedCode(
                file_path=file_path,
                reason="Has dependency relationship with changed file",
                relationship_type='dependency',
                confidence=0.9,
                suggested_action="Review for compatibility with changes"
            ))
        
        # Find test files that should be updated
        test_suggestions = await self.test_suggester.suggest_tests(changed_file, change_description)
        for suggestion in test_suggestions:
            related.append(RelatedCode(
                file_path=suggestion.test_file,
                reason=suggestion.reason,
                relationship_type='test',
                confidence=suggestion.confidence,
                suggested_action=f"Add or update {suggestion.test_type} tests"
            ))
        
        # Find documentation that needs updating
        doc_updates = await self.doc_detector.detect_documentation_updates(changed_file)
        for update in doc_updates:
            related.append(RelatedCode(
                file_path=update.doc_file,
                reason=update.reason,
                relationship_type='documentation',
                confidence=0.8,
                suggested_action=f"Update {update.update_type}"
            ))
        
        return related
    
    async def analyze_change_impact(
        self,
        changed_files: List[Path]
    ) -> Dict[str, Any]:
        """
        Analyze the impact of changes to multiple files.
        
        Args:
            changed_files: List of files that were changed
            
        Returns:
            Dictionary with impact analysis
        """
        if not self.dependency_graph_built:
            await self.initialize()
        
        all_affected = set()
        all_tests_needed = []
        all_docs_needed = []
        
        for file_path in changed_files:
            # Get affected files
            affected = self.dependency_analyzer.get_affected_files(file_path)
            all_affected.update(affected)
            
            # Get test suggestions
            tests = await self.test_suggester.suggest_tests(file_path)
            all_tests_needed.extend(tests)
            
            # Get documentation updates
            docs = await self.doc_detector.detect_documentation_updates(file_path)
            all_docs_needed.extend(docs)
        
        return {
            'changed_files': len(changed_files),
            'affected_files': list(all_affected),
            'total_affected': len(all_affected),
            'tests_needed': all_tests_needed,
            'documentation_updates': all_docs_needed,
            'impact_score': self._calculate_impact_score(len(changed_files), len(all_affected))
        }
    
    def _calculate_impact_score(self, changed: int, affected: int) -> float:
        """
        Calculate impact score (0.0 to 1.0).
        
        Args:
            changed: Number of changed files
            affected: Number of affected files
            
        Returns:
            Impact score
        """
        if changed == 0:
            return 0.0
        
        ratio = affected / changed
        # Normalize to 0-1 scale (assuming max ratio of 10)
        return min(1.0, ratio / 10)
    
    def get_test_coverage_report(self) -> Dict[str, Any]:
        """
        Get test coverage report for the project.
        
        Returns:
            Dictionary with coverage information
        """
        python_files = self.dependency_analyzer._find_python_files()
        
        total_files = 0
        files_with_tests = 0
        coverage_details = []
        
        for file_path in python_files:
            if 'test' not in str(file_path):  # Skip test files themselves
                total_files += 1
                coverage = self.test_suggester.check_test_coverage(file_path)
                
                has_any_test = any([
                    coverage['has_unit_tests'],
                    coverage['has_integration_tests'],
                    coverage['has_e2e_tests']
                ])
                
                if has_any_test:
                    files_with_tests += 1
                
                coverage_details.append({
                    'file': file_path,
                    'coverage': coverage
                })
        
        coverage_percentage = (files_with_tests / total_files * 100) if total_files > 0 else 0
        
        return {
            'total_files': total_files,
            'files_with_tests': files_with_tests,
            'coverage_percentage': coverage_percentage,
            'details': coverage_details
        }
