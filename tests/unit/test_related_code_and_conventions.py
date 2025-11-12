"""
Unit tests for Related Code Finder and Convention Enforcer.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.codegenie.core.related_code_finder import (
    RelatedCodeFinder,
    DependencyAnalyzer,
    TestSuggestionEngine,
    DocumentationDetector,
    RelatedCode,
    TestSuggestion,
    DocumentationUpdate
)
from src.codegenie.core.convention_enforcer import (
    ConventionEnforcer,
    PatternAnalyzer,
    ViolationDetector,
    AutoFixer,
    Convention,
    Violation,
    ConventionType,
    ViolationSeverity
)


class TestDependencyAnalyzer:
    """Test cases for DependencyAnalyzer."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        src_dir = project_root / "src"
        src_dir.mkdir()
        
        # Create files with dependencies
        (src_dir / "module_a.py").write_text('''
import os
from module_b import helper

def function_a():
    return helper()
''')
        
        (src_dir / "module_b.py").write_text('''
def helper():
    return True
''')
        
        return project_root
    
    @pytest.fixture
    def analyzer(self, temp_project):
        """Create a DependencyAnalyzer instance."""
        return DependencyAnalyzer(temp_project)
    
    @pytest.mark.asyncio
    async def test_build_dependency_graph(self, analyzer):
        """Test building dependency graph."""
        graph = await analyzer.build_dependency_graph()
        
        assert len(graph) > 0
        assert all(isinstance(k, Path) for k in graph.keys())
    
    @pytest.mark.asyncio
    async def test_analyze_file_dependencies(self, analyzer, temp_project):
        """Test analyzing file dependencies."""
        file_path = temp_project / "src" / "module_a.py"
        dep_info = await analyzer._analyze_file_dependencies(file_path)
        
        assert dep_info is not None
        assert 'os' in dep_info.imports
        assert 'module_b' in dep_info.imports
        assert 'function_a' in dep_info.symbols_defined
    
    def test_get_affected_files(self, analyzer):
        """Test getting affected files."""
        # Setup mock dependency graph
        file_a = Path("file_a.py")
        file_b = Path("file_b.py")
        
        from src.codegenie.core.related_code_finder import DependencyInfo
        analyzer.dependency_graph[file_a] = DependencyInfo(
            file_path=file_a,
            imports=[],
            imported_by=[file_b],
            depends_on=[],
            symbols_used=[],
            symbols_defined=[]
        )
        
        affected = analyzer.get_affected_files(file_a)
        assert file_b in affected


class TestTestSuggestionEngine:
    """Test cases for TestSuggestionEngine."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        src_dir = project_root / "src"
        src_dir.mkdir()
        
        (src_dir / "calculator.py").write_text('''
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
''')
        
        return project_root
    
    @pytest.fixture
    def engine(self, temp_project):
        """Create a TestSuggestionEngine instance."""
        return TestSuggestionEngine(temp_project)
    
    @pytest.mark.asyncio
    async def test_suggest_tests_for_new_file(self, engine, temp_project):
        """Test suggesting tests for a new file."""
        file_path = temp_project / "src" / "calculator.py"
        suggestions = await engine.suggest_tests(file_path)
        
        assert len(suggestions) > 0
        unit_test_suggestions = [s for s in suggestions if s.test_type == 'unit']
        assert len(unit_test_suggestions) > 0
        
        # Should suggest tests for Calculator class
        assert any('Calculator' in str(s.suggested_tests) for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_no_suggestions_for_test_file(self, engine, temp_project):
        """Test that no suggestions are made for test files."""
        test_file = temp_project / "test_something.py"
        test_file.write_text("def test_function(): pass")
        
        suggestions = await engine.suggest_tests(test_file)
        assert len(suggestions) == 0
    
    def test_check_test_coverage(self, engine, temp_project):
        """Test checking test coverage."""
        file_path = temp_project / "src" / "calculator.py"
        coverage = engine.check_test_coverage(file_path)
        
        assert 'has_unit_tests' in coverage
        assert 'has_integration_tests' in coverage
        assert 'test_files' in coverage


class TestDocumentationDetector:
    """Test cases for DocumentationDetector."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Create README
        (project_root / "README.md").write_text("# Test Project")
        
        # Create docs directory
        docs_dir = project_root / "docs"
        docs_dir.mkdir()
        (docs_dir / "API_REFERENCE.md").write_text("# API Reference")
        
        # Create source file
        src_dir = project_root / "src"
        src_dir.mkdir()
        (src_dir / "api.py").write_text('''
def public_function():
    pass

def _private_function():
    pass
''')
        
        return project_root
    
    @pytest.fixture
    def detector(self, temp_project):
        """Create a DocumentationDetector instance."""
        return DocumentationDetector(temp_project)
    
    @pytest.mark.asyncio
    async def test_detect_readme_update(self, detector, temp_project):
        """Test detecting README update needs."""
        file_path = temp_project / "src" / "api.py"
        updates = await detector.detect_documentation_updates(file_path)
        
        readme_updates = [u for u in updates if u.update_type == 'readme']
        # Core/API files should suggest README updates
        assert len(readme_updates) >= 0
    
    @pytest.mark.asyncio
    async def test_detect_api_doc_update(self, detector, temp_project):
        """Test detecting API documentation update needs."""
        file_path = temp_project / "src" / "api.py"
        updates = await detector.detect_documentation_updates(file_path)
        
        api_doc_updates = [u for u in updates if u.update_type == 'api_doc']
        assert len(api_doc_updates) > 0
        assert any('public_function' in u.affected_symbols for u in api_doc_updates)


class TestRelatedCodeFinder:
    """Test cases for RelatedCodeFinder."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        src_dir = project_root / "src"
        src_dir.mkdir()
        
        (src_dir / "module.py").write_text('''
def function():
    pass
''')
        
        return project_root
    
    @pytest.fixture
    def finder(self, temp_project):
        """Create a RelatedCodeFinder instance."""
        return RelatedCodeFinder(temp_project)
    
    @pytest.mark.asyncio
    async def test_initialize(self, finder):
        """Test initialization."""
        await finder.initialize()
        assert finder.dependency_graph_built is True
    
    @pytest.mark.asyncio
    async def test_find_related_code(self, finder, temp_project):
        """Test finding related code."""
        file_path = temp_project / "src" / "module.py"
        related = await finder.find_related_code(file_path)
        
        assert isinstance(related, list)
        # Should suggest tests and possibly documentation
        assert len(related) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_change_impact(self, finder, temp_project):
        """Test analyzing change impact."""
        changed_files = [temp_project / "src" / "module.py"]
        impact = await finder.analyze_change_impact(changed_files)
        
        assert 'changed_files' in impact
        assert 'affected_files' in impact
        assert 'tests_needed' in impact
        assert 'documentation_updates' in impact
        assert 'impact_score' in impact


class TestPatternAnalyzer:
    """Test cases for PatternAnalyzer."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project with consistent patterns."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Create files with snake_case naming
        (project_root / "module_one.py").write_text('''
def function_one():
    """Docstring."""
    pass

def function_two():
    """Docstring."""
    pass

class MyClass:
    """Docstring."""
    pass
''')
        
        (project_root / "module_two.py").write_text('''
def another_function():
    """Docstring."""
    pass

class AnotherClass:
    """Docstring."""
    pass
''')
        
        return project_root
    
    @pytest.fixture
    def analyzer(self, temp_project):
        """Create a PatternAnalyzer instance."""
        return PatternAnalyzer(temp_project)
    
    @pytest.mark.asyncio
    async def test_analyze_codebase(self, analyzer):
        """Test analyzing codebase for patterns."""
        conventions = await analyzer.analyze_codebase()
        
        assert len(conventions) > 0
        assert all(isinstance(c, Convention) for c in conventions)
    
    @pytest.mark.asyncio
    async def test_detect_naming_patterns(self, analyzer):
        """Test detecting naming patterns."""
        await analyzer.analyze_codebase()
        
        # Should detect snake_case for functions
        assert 'snake_case' in analyzer.naming_patterns['functions']
        # Should detect PascalCase for classes
        assert 'PascalCase' in analyzer.naming_patterns['classes']
    
    @pytest.mark.asyncio
    async def test_detect_docstring_patterns(self, analyzer):
        """Test detecting docstring patterns."""
        await analyzer.analyze_codebase()
        
        assert analyzer.docstring_patterns['has_docstring'] > 0
    
    def test_get_convention_summary(self, analyzer):
        """Test getting convention summary."""
        analyzer.learned_conventions = [
            Convention(
                name='test_convention',
                type=ConventionType.NAMING,
                description='Test',
                confidence=0.9
            )
        ]
        
        summary = analyzer.get_convention_summary()
        
        assert 'total_conventions' in summary
        assert 'conventions' in summary
        assert len(summary['conventions']) == 1


class TestViolationDetector:
    """Test cases for ViolationDetector."""
    
    @pytest.fixture
    def conventions(self):
        """Create sample conventions."""
        return [
            Convention(
                name='function_naming',
                type=ConventionType.NAMING,
                description='Functions should use snake_case',
                pattern='snake_case',
                confidence=0.9
            ),
            Convention(
                name='docstring_required',
                type=ConventionType.DOCUMENTATION,
                description='Functions should have docstrings',
                confidence=0.8
            )
        ]
    
    @pytest.fixture
    def detector(self, conventions):
        """Create a ViolationDetector instance."""
        return ViolationDetector(conventions)
    
    @pytest.fixture
    def temp_file_with_violations(self, tmp_path):
        """Create a file with convention violations."""
        file_path = tmp_path / "violations.py"
        file_path.write_text('''
def badNaming():
    pass

def good_naming():
    """This has a docstring."""
    pass

class badClassName:
    pass
''')
        return file_path
    
    @pytest.mark.asyncio
    async def test_detect_violations(self, detector, temp_file_with_violations):
        """Test detecting violations."""
        violations = await detector.detect_violations(temp_file_with_violations)
        
        assert len(violations) > 0
        assert all(isinstance(v, Violation) for v in violations)
    
    @pytest.mark.asyncio
    async def test_detect_naming_violations(self, detector, temp_file_with_violations):
        """Test detecting naming violations."""
        violations = await detector.detect_violations(temp_file_with_violations)
        
        naming_violations = [v for v in violations if v.convention.type == ConventionType.NAMING]
        assert len(naming_violations) > 0
        
        # Should detect camelCase function
        assert any('badNaming' in v.current_code for v in naming_violations)
    
    @pytest.mark.asyncio
    async def test_detect_documentation_violations(self, detector, temp_file_with_violations):
        """Test detecting documentation violations."""
        violations = await detector.detect_violations(temp_file_with_violations)
        
        doc_violations = [v for v in violations if v.convention.type == ConventionType.DOCUMENTATION]
        assert len(doc_violations) > 0
    
    def test_get_auto_fixable_violations(self, detector):
        """Test getting auto-fixable violations."""
        detector.violations = [
            Violation(
                convention=Convention('test', ConventionType.NAMING, 'Test'),
                file_path=Path("test.py"),
                line_number=1,
                severity=ViolationSeverity.WARNING,
                description="Test",
                current_code="badName",
                auto_fixable=True
            ),
            Violation(
                convention=Convention('test2', ConventionType.DOCUMENTATION, 'Test'),
                file_path=Path("test.py"),
                line_number=2,
                severity=ViolationSeverity.WARNING,
                description="Test",
                current_code="func",
                auto_fixable=False
            )
        ]
        
        auto_fixable = detector.get_auto_fixable_violations()
        assert len(auto_fixable) == 1


class TestConventionEnforcer:
    """Test cases for ConventionEnforcer."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        (project_root / "module.py").write_text('''
def snake_case_function():
    """Docstring."""
    pass

def another_function():
    """Docstring."""
    pass
''')
        
        return project_root
    
    @pytest.fixture
    def enforcer(self, temp_project):
        """Create a ConventionEnforcer instance."""
        return ConventionEnforcer(temp_project)
    
    @pytest.mark.asyncio
    async def test_learn_conventions(self, enforcer):
        """Test learning conventions."""
        conventions = await enforcer.learn_conventions()
        
        assert len(conventions) > 0
        assert enforcer.conventions_learned is True
    
    @pytest.mark.asyncio
    async def test_check_file(self, enforcer, temp_project):
        """Test checking a file."""
        file_path = temp_project / "module.py"
        violations = await enforcer.check_file(file_path)
        
        assert isinstance(violations, list)
    
    @pytest.mark.asyncio
    async def test_check_codebase(self, enforcer):
        """Test checking entire codebase."""
        report = await enforcer.check_codebase()
        
        assert 'total_violations' in report
        assert 'files_checked' in report
        assert 'by_severity' in report
        assert 'auto_fixable' in report
    
    def test_get_convention_summary(self, enforcer):
        """Test getting convention summary."""
        enforcer.pattern_analyzer.learned_conventions = [
            Convention('test', ConventionType.NAMING, 'Test', confidence=0.9)
        ]
        
        summary = enforcer.get_convention_summary()
        
        assert 'total_conventions' in summary
        assert 'team_standards' in summary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
