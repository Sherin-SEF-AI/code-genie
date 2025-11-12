"""
Convention Enforcement System.

This module provides:
- PatternAnalyzer for learning project conventions
- Violation detection for coding standards
- Automatic fix suggestions for violations
- Configurable rule system for team standards
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from enum import Enum


class ConventionType(Enum):
    """Types of conventions that can be enforced."""
    NAMING = "naming"
    FORMATTING = "formatting"
    STRUCTURE = "structure"
    DOCUMENTATION = "documentation"
    IMPORTS = "imports"
    ERROR_HANDLING = "error_handling"


class ViolationSeverity(Enum):
    """Severity levels for convention violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Convention:
    """Represents a project convention."""
    name: str
    type: ConventionType
    description: str
    pattern: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class Violation:
    """Represents a convention violation."""
    convention: Convention
    file_path: Path
    line_number: Optional[int]
    severity: ViolationSeverity
    description: str
    current_code: str
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False



@dataclass
class TeamStandard:
    """Represents a team coding standard."""
    name: str
    rules: List[Dict[str, Any]]
    enabled: bool = True
    priority: int = 1


class PatternAnalyzer:
    """Analyzes codebase to learn project conventions."""
    
    def __init__(self, project_root: Path):
        """
        Initialize pattern analyzer.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.learned_conventions: List[Convention] = []
        self.naming_patterns: Dict[str, Counter] = {
            'functions': Counter(),
            'classes': Counter(),
            'variables': Counter(),
            'constants': Counter()
        }
        self.import_patterns: Counter = Counter()
        self.docstring_patterns: Counter = Counter()
    
    async def analyze_codebase(self) -> List[Convention]:
        """
        Analyze entire codebase to learn conventions.
        
        Returns:
            List of learned conventions
        """
        python_files = self._find_python_files()
        
        for file_path in python_files:
            await self._analyze_file(file_path)
        
        # Extract conventions from patterns
        self.learned_conventions = self._extract_conventions()
        
        return self.learned_conventions
    
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
    
    async def _analyze_file(self, file_path: Path) -> None:
        """
        Analyze a single file for patterns.
        
        Args:
            file_path: Path to file to analyze
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Analyze naming patterns
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    naming_style = self._detect_naming_style(node.name)
                    self.naming_patterns['functions'][naming_style] += 1
                    
                    # Check for docstring
                    if ast.get_docstring(node):
                        self.docstring_patterns['has_docstring'] += 1
                    else:
                        self.docstring_patterns['no_docstring'] += 1
                
                elif isinstance(node, ast.ClassDef):
                    naming_style = self._detect_naming_style(node.name)
                    self.naming_patterns['classes'][naming_style] += 1
                
                elif isinstance(node, ast.Name):
                    if node.id.isupper():
                        self.naming_patterns['constants']['UPPER_CASE'] += 1
                    else:
                        naming_style = self._detect_naming_style(node.id)
                        self.naming_patterns['variables'][naming_style] += 1
                
                # Analyze import patterns
                elif isinstance(node, ast.Import):
                    self.import_patterns['import'] += 1
                
                elif isinstance(node, ast.ImportFrom):
                    self.import_patterns['from_import'] += 1
                    if node.level > 0:
                        self.import_patterns['relative_import'] += 1
                    else:
                        self.import_patterns['absolute_import'] += 1
        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _detect_naming_style(self, name: str) -> str:
        """
        Detect naming style of an identifier.
        
        Args:
            name: Identifier name
            
        Returns:
            Naming style (snake_case, camelCase, PascalCase, etc.)
        """
        if '_' in name:
            return 'snake_case'
        elif name[0].isupper():
            return 'PascalCase'
        elif any(c.isupper() for c in name[1:]):
            return 'camelCase'
        else:
            return 'lowercase'
    
    def _extract_conventions(self) -> List[Convention]:
        """
        Extract conventions from analyzed patterns.
        
        Returns:
            List of conventions
        """
        conventions = []
        
        # Function naming convention
        if self.naming_patterns['functions']:
            most_common = self.naming_patterns['functions'].most_common(1)[0]
            style, count = most_common
            total = sum(self.naming_patterns['functions'].values())
            confidence = count / total if total > 0 else 0
            
            if confidence > 0.7:  # Strong convention
                conventions.append(Convention(
                    name='function_naming',
                    type=ConventionType.NAMING,
                    description=f"Functions should use {style}",
                    pattern=style,
                    examples=[],
                    confidence=confidence
                ))
        
        # Class naming convention
        if self.naming_patterns['classes']:
            most_common = self.naming_patterns['classes'].most_common(1)[0]
            style, count = most_common
            total = sum(self.naming_patterns['classes'].values())
            confidence = count / total if total > 0 else 0
            
            if confidence > 0.7:
                conventions.append(Convention(
                    name='class_naming',
                    type=ConventionType.NAMING,
                    description=f"Classes should use {style}",
                    pattern=style,
                    examples=[],
                    confidence=confidence
                ))
        
        # Docstring convention
        total_funcs = sum(self.docstring_patterns.values())
        if total_funcs > 0:
            has_doc = self.docstring_patterns['has_docstring']
            confidence = has_doc / total_funcs
            
            if confidence > 0.6:
                conventions.append(Convention(
                    name='docstring_required',
                    type=ConventionType.DOCUMENTATION,
                    description="Functions should have docstrings",
                    confidence=confidence
                ))
        
        # Import convention
        if self.import_patterns:
            total_imports = sum(self.import_patterns.values())
            absolute = self.import_patterns['absolute_import']
            relative = self.import_patterns['relative_import']
            
            if absolute > relative and total_imports > 0:
                confidence = absolute / total_imports
                if confidence > 0.7:
                    conventions.append(Convention(
                        name='absolute_imports',
                        type=ConventionType.IMPORTS,
                        description="Prefer absolute imports over relative imports",
                        confidence=confidence
                    ))
        
        return conventions
    
    def get_convention_summary(self) -> Dict[str, Any]:
        """
        Get summary of learned conventions.
        
        Returns:
            Dictionary with convention summary
        """
        return {
            'total_conventions': len(self.learned_conventions),
            'naming_patterns': {
                'functions': dict(self.naming_patterns['functions']),
                'classes': dict(self.naming_patterns['classes'])
            },
            'import_patterns': dict(self.import_patterns),
            'docstring_coverage': {
                'with_docstring': self.docstring_patterns['has_docstring'],
                'without_docstring': self.docstring_patterns['no_docstring']
            },
            'conventions': [
                {
                    'name': c.name,
                    'type': c.type.value,
                    'description': c.description,
                    'confidence': c.confidence
                }
                for c in self.learned_conventions
            ]
        }


class ViolationDetector:
    """Detects violations of coding standards."""
    
    def __init__(self, conventions: List[Convention]):
        """
        Initialize violation detector.
        
        Args:
            conventions: List of conventions to enforce
        """
        self.conventions = conventions
        self.violations: List[Violation] = []
    
    async def detect_violations(self, file_path: Path) -> List[Violation]:
        """
        Detect violations in a file.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            List of violations
        """
        violations = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Check each convention
            for convention in self.conventions:
                if convention.type == ConventionType.NAMING:
                    violations.extend(
                        self._check_naming_convention(tree, file_path, content, convention)
                    )
                elif convention.type == ConventionType.DOCUMENTATION:
                    violations.extend(
                        self._check_documentation_convention(tree, file_path, content, convention)
                    )
                elif convention.type == ConventionType.IMPORTS:
                    violations.extend(
                        self._check_import_convention(tree, file_path, content, convention)
                    )
        
        except Exception as e:
            print(f"Error detecting violations in {file_path}: {e}")
        
        self.violations.extend(violations)
        return violations
    
    def _check_naming_convention(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str,
        convention: Convention
    ) -> List[Violation]:
        """Check naming convention violations."""
        violations = []
        
        for node in ast.walk(tree):
            if convention.name == 'function_naming' and isinstance(node, ast.FunctionDef):
                expected_style = convention.pattern
                actual_style = self._detect_naming_style(node.name)
                
                if actual_style != expected_style and not node.name.startswith('_'):
                    suggested_name = self._convert_naming_style(node.name, expected_style)
                    violations.append(Violation(
                        convention=convention,
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=ViolationSeverity.WARNING,
                        description=f"Function '{node.name}' uses {actual_style} but project uses {expected_style}",
                        current_code=node.name,
                        suggested_fix=f"Rename to '{suggested_name}'",
                        auto_fixable=True
                    ))
            
            elif convention.name == 'class_naming' and isinstance(node, ast.ClassDef):
                expected_style = convention.pattern
                actual_style = self._detect_naming_style(node.name)
                
                if actual_style != expected_style:
                    suggested_name = self._convert_naming_style(node.name, expected_style)
                    violations.append(Violation(
                        convention=convention,
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=ViolationSeverity.WARNING,
                        description=f"Class '{node.name}' uses {actual_style} but project uses {expected_style}",
                        current_code=node.name,
                        suggested_fix=f"Rename to '{suggested_name}'",
                        auto_fixable=True
                    ))
        
        return violations
    
    def _detect_naming_style(self, name: str) -> str:
        """Detect naming style."""
        if '_' in name:
            return 'snake_case'
        elif name[0].isupper():
            return 'PascalCase'
        elif any(c.isupper() for c in name[1:]):
            return 'camelCase'
        else:
            return 'lowercase'
    
    def _convert_naming_style(self, name: str, target_style: str) -> str:
        """
        Convert name to target naming style.
        
        Args:
            name: Original name
            target_style: Target naming style
            
        Returns:
            Converted name
        """
        # Split name into words
        if '_' in name:
            words = name.split('_')
        else:
            # Split camelCase or PascalCase
            words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', name)
        
        words = [w.lower() for w in words if w]
        
        if target_style == 'snake_case':
            return '_'.join(words)
        elif target_style == 'camelCase':
            return words[0] + ''.join(w.capitalize() for w in words[1:])
        elif target_style == 'PascalCase':
            return ''.join(w.capitalize() for w in words)
        else:
            return ''.join(words)
    
    def _check_documentation_convention(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str,
        convention: Convention
    ) -> List[Violation]:
        """Check documentation convention violations."""
        violations = []
        
        if convention.name == 'docstring_required':
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node) and not node.name.startswith('_'):
                        violations.append(Violation(
                            convention=convention,
                            file_path=file_path,
                            line_number=node.lineno,
                            severity=ViolationSeverity.WARNING,
                            description=f"{node.__class__.__name__} '{node.name}' is missing a docstring",
                            current_code=node.name,
                            suggested_fix="Add a docstring describing the purpose and parameters",
                            auto_fixable=False
                        ))
        
        return violations
    
    def _check_import_convention(
        self,
        tree: ast.AST,
        file_path: Path,
        content: str,
        convention: Convention
    ) -> List[Violation]:
        """Check import convention violations."""
        violations = []
        
        if convention.name == 'absolute_imports':
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level > 0:
                    violations.append(Violation(
                        convention=convention,
                        file_path=file_path,
                        line_number=node.lineno,
                        severity=ViolationSeverity.INFO,
                        description="Relative import used, project prefers absolute imports",
                        current_code=ast.get_source_segment(content, node) or '',
                        suggested_fix="Convert to absolute import",
                        auto_fixable=True
                    ))
        
        return violations
    
    def get_violations_by_severity(self, severity: ViolationSeverity) -> List[Violation]:
        """Get violations of a specific severity."""
        return [v for v in self.violations if v.severity == severity]
    
    def get_auto_fixable_violations(self) -> List[Violation]:
        """Get violations that can be automatically fixed."""
        return [v for v in self.violations if v.auto_fixable]


class AutoFixer:
    """Automatically fixes convention violations."""
    
    def __init__(self):
        """Initialize auto fixer."""
        self.fixes_applied: List[Tuple[Path, Violation]] = []
    
    async def apply_fixes(
        self,
        violations: List[Violation],
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Apply automatic fixes for violations.
        
        Args:
            violations: List of violations to fix
            dry_run: If True, don't actually modify files
            
        Returns:
            Dictionary with fix results
        """
        fixes_by_file = defaultdict(list)
        
        # Group violations by file
        for violation in violations:
            if violation.auto_fixable:
                fixes_by_file[violation.file_path].append(violation)
        
        results = {
            'total_violations': len(violations),
            'fixable_violations': sum(len(v) for v in fixes_by_file.values()),
            'files_modified': 0,
            'fixes_applied': [],
            'dry_run': dry_run
        }
        
        # Apply fixes to each file
        for file_path, file_violations in fixes_by_file.items():
            if not dry_run:
                success = await self._apply_file_fixes(file_path, file_violations)
                if success:
                    results['files_modified'] += 1
                    results['fixes_applied'].extend(file_violations)
            else:
                results['fixes_applied'].extend(file_violations)
        
        return results
    
    async def _apply_file_fixes(
        self,
        file_path: Path,
        violations: List[Violation]
    ) -> bool:
        """
        Apply fixes to a single file.
        
        Args:
            file_path: Path to file
            violations: Violations to fix
            
        Returns:
            True if successful
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Sort violations by line number (descending) to avoid offset issues
            sorted_violations = sorted(
                violations,
                key=lambda v: v.line_number or 0,
                reverse=True
            )
            
            for violation in sorted_violations:
                if violation.line_number and violation.suggested_fix:
                    # Simple replacement for naming violations
                    if violation.convention.type == ConventionType.NAMING:
                        line_idx = violation.line_number - 1
                        if 0 <= line_idx < len(lines):
                            lines[line_idx] = lines[line_idx].replace(
                                violation.current_code,
                                violation.suggested_fix.split("'")[1]  # Extract new name
                            )
            
            # Write back
            file_path.write_text('\n'.join(lines), encoding='utf-8')
            self.fixes_applied.extend([(file_path, v) for v in violations])
            return True
            
        except Exception as e:
            print(f"Error applying fixes to {file_path}: {e}")
            return False


class ConventionEnforcer:
    """
    Main class for enforcing coding conventions.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize convention enforcer.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.pattern_analyzer = PatternAnalyzer(project_root)
        self.violation_detector: Optional[ViolationDetector] = None
        self.auto_fixer = AutoFixer()
        self.team_standards: List[TeamStandard] = []
        self.conventions_learned = False
    
    async def learn_conventions(self) -> List[Convention]:
        """
        Learn conventions from the codebase.
        
        Returns:
            List of learned conventions
        """
        conventions = await self.pattern_analyzer.analyze_codebase()
        self.violation_detector = ViolationDetector(conventions)
        self.conventions_learned = True
        return conventions
    
    async def check_file(self, file_path: Path) -> List[Violation]:
        """
        Check a file for convention violations.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            List of violations
        """
        if not self.conventions_learned:
            await self.learn_conventions()
        
        if self.violation_detector:
            return await self.violation_detector.detect_violations(file_path)
        
        return []
    
    async def check_codebase(self) -> Dict[str, Any]:
        """
        Check entire codebase for violations.
        
        Returns:
            Dictionary with violation report
        """
        if not self.conventions_learned:
            await self.learn_conventions()
        
        all_violations = []
        python_files = self.pattern_analyzer._find_python_files()
        
        for file_path in python_files:
            violations = await self.check_file(file_path)
            all_violations.extend(violations)
        
        # Generate report
        violations_by_severity = defaultdict(list)
        violations_by_type = defaultdict(list)
        violations_by_file = defaultdict(list)
        
        for violation in all_violations:
            violations_by_severity[violation.severity].append(violation)
            violations_by_type[violation.convention.type].append(violation)
            violations_by_file[violation.file_path].append(violation)
        
        return {
            'total_violations': len(all_violations),
            'files_checked': len(python_files),
            'files_with_violations': len(violations_by_file),
            'by_severity': {
                severity.value: len(viols)
                for severity, viols in violations_by_severity.items()
            },
            'by_type': {
                conv_type.value: len(viols)
                for conv_type, viols in violations_by_type.items()
            },
            'auto_fixable': len([v for v in all_violations if v.auto_fixable]),
            'violations': all_violations
        }
    
    async def fix_violations(
        self,
        violations: Optional[List[Violation]] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Fix violations automatically.
        
        Args:
            violations: Violations to fix (if None, fix all auto-fixable)
            dry_run: If True, don't actually modify files
            
        Returns:
            Dictionary with fix results
        """
        if violations is None:
            if self.violation_detector:
                violations = self.violation_detector.get_auto_fixable_violations()
            else:
                violations = []
        
        return await self.auto_fixer.apply_fixes(violations, dry_run)
    
    def add_team_standard(self, standard: TeamStandard) -> None:
        """
        Add a team coding standard.
        
        Args:
            standard: Team standard to add
        """
        self.team_standards.append(standard)
    
    def get_convention_summary(self) -> Dict[str, Any]:
        """
        Get summary of conventions and standards.
        
        Returns:
            Dictionary with summary
        """
        summary = self.pattern_analyzer.get_convention_summary()
        summary['team_standards'] = [
            {
                'name': std.name,
                'enabled': std.enabled,
                'rules_count': len(std.rules)
            }
            for std in self.team_standards
        ]
        return summary
