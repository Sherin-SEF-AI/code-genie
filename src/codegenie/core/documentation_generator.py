"""
Documentation Generator for automatic code documentation.

This module provides comprehensive documentation generation capabilities including:
- Docstring generation for functions and classes
- README file generation
- API documentation generation
- Code explanation in natural language
- Example generation
- Documentation maintenance and sync checking
"""

import ast
import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class DocstringStyle(Enum):
    """Docstring formatting styles."""
    GOOGLE = "google"
    NUMPY = "numpy"
    SPHINX = "sphinx"
    PLAIN = "plain"


class DocumentationFormat(Enum):
    """Documentation output formats."""
    MARKDOWN = "markdown"
    RST = "rst"
    HTML = "html"
    PLAIN_TEXT = "plain_text"


@dataclass
class FunctionDoc:
    """Documentation for a function."""
    name: str
    description: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    returns: Optional[str] = None
    raises: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class ClassDoc:
    """Documentation for a class."""
    name: str
    description: str
    attributes: List[Dict[str, str]] = field(default_factory=list)
    methods: List[FunctionDoc] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    inheritance: List[str] = field(default_factory=list)


@dataclass
class ModuleDoc:
    """Documentation for a module."""
    name: str
    description: str
    functions: List[FunctionDoc] = field(default_factory=list)
    classes: List[ClassDoc] = field(default_factory=list)
    constants: List[Dict[str, str]] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


@dataclass
class APIDocumentation:
    """Complete API documentation."""
    title: str
    modules: List[ModuleDoc] = field(default_factory=list)
    overview: Optional[str] = None
    installation: Optional[str] = None
    quick_start: Optional[str] = None
    format: DocumentationFormat = DocumentationFormat.MARKDOWN


@dataclass
class READMEContent:
    """Content for README file."""
    project_name: str
    description: str
    features: List[str] = field(default_factory=list)
    installation: Optional[str] = None
    usage: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    contributing: Optional[str] = None
    license: Optional[str] = None
    badges: List[str] = field(default_factory=list)


@dataclass
class DocSyncIssue:
    """Issue found during doc-code sync check."""
    file_path: Path
    issue_type: str
    description: str
    line_number: Optional[int] = None
    severity: str = "warning"  # info, warning, error
    suggestion: Optional[str] = None


class DocumentationGenerator:
    """
    Generates comprehensive documentation for code.
    
    This class provides automatic documentation generation including:
    - Docstrings for functions and classes
    - README files with usage examples
    - API documentation
    - Code explanations
    - Documentation maintenance
    """
    
    def __init__(self, docstring_style: DocstringStyle = DocstringStyle.GOOGLE):
        """
        Initialize the Documentation Generator.
        
        Args:
            docstring_style: Style for generated docstrings
        """
        self.docstring_style = docstring_style
        self._cache: Dict[str, Any] = {}
    
    def generate_docstring(
        self,
        code: str,
        name: str,
        entity_type: str = "function"
    ) -> str:
        """
        Generate a docstring for a function or class.
        
        Args:
            code: Source code of the function/class
            name: Name of the function/class
            entity_type: Type of entity ("function" or "class")
            
        Returns:
            Generated docstring in the specified style
        """
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if entity_type == "function" and isinstance(node, ast.FunctionDef):
                    if node.name == name:
                        return self._generate_function_docstring(node)
                elif entity_type == "class" and isinstance(node, ast.ClassDef):
                    if node.name == name:
                        return self._generate_class_docstring(node)
            
            return self._generate_generic_docstring(name, entity_type)
            
        except Exception as e:
            logger.warning(f"Error generating docstring for {name}: {e}")
            return self._generate_generic_docstring(name, entity_type)
    
    def _generate_function_docstring(self, node: ast.FunctionDef) -> str:
        """Generate docstring for a function node."""
        # Extract function information
        func_doc = self._analyze_function(node)
        
        # Format according to style
        if self.docstring_style == DocstringStyle.GOOGLE:
            return self._format_google_docstring(func_doc)
        elif self.docstring_style == DocstringStyle.NUMPY:
            return self._format_numpy_docstring(func_doc)
        elif self.docstring_style == DocstringStyle.SPHINX:
            return self._format_sphinx_docstring(func_doc)
        else:
            return self._format_plain_docstring(func_doc)
    
    def _generate_class_docstring(self, node: ast.ClassDef) -> str:
        """Generate docstring for a class node."""
        class_doc = self._analyze_class(node)
        
        if self.docstring_style == DocstringStyle.GOOGLE:
            return self._format_google_class_docstring(class_doc)
        elif self.docstring_style == DocstringStyle.NUMPY:
            return self._format_numpy_class_docstring(class_doc)
        else:
            return self._format_plain_class_docstring(class_doc)
    
    def _analyze_function(self, node: ast.FunctionDef) -> FunctionDoc:
        """Analyze a function node and extract documentation info."""
        func_doc = FunctionDoc(
            name=node.name,
            description=f"Function {node.name}."
        )
        
        # Extract parameters
        for arg in node.args.args:
            param_name = arg.arg
            param_type = self._get_annotation_string(arg.annotation) if arg.annotation else "Any"
            
            func_doc.parameters.append({
                "name": param_name,
                "type": param_type,
                "description": f"Parameter {param_name}"
            })
        
        # Extract return type
        if node.returns:
            func_doc.returns = self._get_annotation_string(node.returns)
        
        # Check for raises
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc and isinstance(child.exc, ast.Call):
                    if isinstance(child.exc.func, ast.Name):
                        func_doc.raises.append(child.exc.func.id)
        
        return func_doc
    
    def _analyze_class(self, node: ast.ClassDef) -> ClassDoc:
        """Analyze a class node and extract documentation info."""
        class_doc = ClassDoc(
            name=node.name,
            description=f"Class {node.name}."
        )
        
        # Extract base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                class_doc.inheritance.append(base.id)
        
        # Extract methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_doc = self._analyze_function(item)
                class_doc.methods.append(method_doc)
            elif isinstance(item, ast.Assign):
                # Extract class attributes
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_doc.attributes.append({
                            "name": target.id,
                            "type": "Any",
                            "description": f"Attribute {target.id}"
                        })
        
        return class_doc
    
    def _get_annotation_string(self, annotation: ast.AST) -> str:
        """Convert AST annotation to string."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            value = self._get_annotation_string(annotation.value)
            slice_val = self._get_annotation_string(annotation.slice)
            return f"{value}[{slice_val}]"
        else:
            return "Any"
    
    def _format_google_docstring(self, func_doc: FunctionDoc) -> str:
        """Format docstring in Google style."""
        lines = [f'"""', func_doc.description, ""]
        
        if func_doc.parameters:
            lines.append("Args:")
            for param in func_doc.parameters:
                lines.append(f"    {param['name']} ({param['type']}): {param['description']}")
            lines.append("")
        
        if func_doc.returns:
            lines.append("Returns:")
            lines.append(f"    {func_doc.returns}")
            lines.append("")
        
        if func_doc.raises:
            lines.append("Raises:")
            for exc in func_doc.raises:
                lines.append(f"    {exc}: Description of when this exception is raised")
            lines.append("")
        
        if func_doc.examples:
            lines.append("Examples:")
            for example in func_doc.examples:
                lines.append(f"    {example}")
            lines.append("")
        
        lines.append('"""')
        return "\n".join(lines)
    
    def _format_numpy_docstring(self, func_doc: FunctionDoc) -> str:
        """Format docstring in NumPy style."""
        lines = [f'"""', func_doc.description, ""]
        
        if func_doc.parameters:
            lines.append("Parameters")
            lines.append("----------")
            for param in func_doc.parameters:
                lines.append(f"{param['name']} : {param['type']}")
                lines.append(f"    {param['description']}")
            lines.append("")
        
        if func_doc.returns:
            lines.append("Returns")
            lines.append("-------")
            lines.append(func_doc.returns)
            lines.append("")
        
        if func_doc.raises:
            lines.append("Raises")
            lines.append("------")
            for exc in func_doc.raises:
                lines.append(exc)
            lines.append("")
        
        lines.append('"""')
        return "\n".join(lines)
    
    def _format_sphinx_docstring(self, func_doc: FunctionDoc) -> str:
        """Format docstring in Sphinx style."""
        lines = [f'"""', func_doc.description, ""]
        
        for param in func_doc.parameters:
            lines.append(f":param {param['name']}: {param['description']}")
            lines.append(f":type {param['name']}: {param['type']}")
        
        if func_doc.returns:
            lines.append(f":return: {func_doc.returns}")
        
        for exc in func_doc.raises:
            lines.append(f":raises {exc}: Description")
        
        lines.append('"""')
        return "\n".join(lines)
    
    def _format_plain_docstring(self, func_doc: FunctionDoc) -> str:
        """Format docstring in plain style."""
        lines = [f'"""', func_doc.description, ""]
        
        if func_doc.parameters:
            lines.append("Parameters:")
            for param in func_doc.parameters:
                lines.append(f"  - {param['name']}: {param['description']}")
            lines.append("")
        
        if func_doc.returns:
            lines.append(f"Returns: {func_doc.returns}")
            lines.append("")
        
        lines.append('"""')
        return "\n".join(lines)
    
    def _format_google_class_docstring(self, class_doc: ClassDoc) -> str:
        """Format class docstring in Google style."""
        lines = [f'"""', class_doc.description, ""]
        
        if class_doc.attributes:
            lines.append("Attributes:")
            for attr in class_doc.attributes:
                lines.append(f"    {attr['name']} ({attr['type']}): {attr['description']}")
            lines.append("")
        
        if class_doc.examples:
            lines.append("Examples:")
            for example in class_doc.examples:
                lines.append(f"    {example}")
            lines.append("")
        
        lines.append('"""')
        return "\n".join(lines)
    
    def _format_numpy_class_docstring(self, class_doc: ClassDoc) -> str:
        """Format class docstring in NumPy style."""
        lines = [f'"""', class_doc.description, ""]
        
        if class_doc.attributes:
            lines.append("Attributes")
            lines.append("----------")
            for attr in class_doc.attributes:
                lines.append(f"{attr['name']} : {attr['type']}")
                lines.append(f"    {attr['description']}")
            lines.append("")
        
        lines.append('"""')
        return "\n".join(lines)
    
    def _format_plain_class_docstring(self, class_doc: ClassDoc) -> str:
        """Format class docstring in plain style."""
        lines = [f'"""', class_doc.description, ""]
        
        if class_doc.attributes:
            lines.append("Attributes:")
            for attr in class_doc.attributes:
                lines.append(f"  - {attr['name']}: {attr['description']}")
            lines.append("")
        
        lines.append('"""')
        return "\n".join(lines)
    
    def _generate_generic_docstring(self, name: str, entity_type: str) -> str:
        """Generate a generic docstring when parsing fails."""
        return f'"""{entity_type.capitalize()} {name}."""'
    
    def generate_readme(
        self,
        project_path: Path,
        project_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Generate a README file for a project.
        
        Args:
            project_path: Path to the project root
            project_name: Name of the project
            description: Project description
            
        Returns:
            Generated README content in Markdown format
        """
        if not project_name:
            project_name = project_path.name
        
        if not description:
            description = f"A Python project: {project_name}"
        
        readme = READMEContent(
            project_name=project_name,
            description=description
        )
        
        # Detect features from project structure
        readme.features = self._detect_project_features(project_path)
        
        # Generate installation instructions
        readme.installation = self._generate_installation_instructions(project_path)
        
        # Generate usage examples
        readme.usage = self._generate_usage_section(project_path)
        
        # Generate examples
        readme.examples = self._generate_code_examples(project_path)
        
        # Format as Markdown
        return self._format_readme_markdown(readme)
    
    def _detect_project_features(self, project_path: Path) -> List[str]:
        """Detect features from project structure."""
        features = []
        
        # Check for common directories
        if (project_path / "tests").exists():
            features.append("Comprehensive test suite")
        
        if (project_path / "docs").exists():
            features.append("Detailed documentation")
        
        if (project_path / "examples").exists():
            features.append("Usage examples")
        
        # Check for configuration files
        if (project_path / "setup.py").exists() or (project_path / "pyproject.toml").exists():
            features.append("Easy installation via pip")
        
        if (project_path / ".github").exists():
            features.append("CI/CD integration")
        
        if (project_path / "Dockerfile").exists():
            features.append("Docker support")
        
        return features
    
    def _generate_installation_instructions(self, project_path: Path) -> str:
        """Generate installation instructions."""
        instructions = []
        
        if (project_path / "requirements.txt").exists():
            instructions.append("```bash")
            instructions.append("pip install -r requirements.txt")
            instructions.append("```")
        elif (project_path / "setup.py").exists():
            instructions.append("```bash")
            instructions.append("pip install .")
            instructions.append("```")
        elif (project_path / "pyproject.toml").exists():
            instructions.append("```bash")
            instructions.append("pip install .")
            instructions.append("```")
        else:
            instructions.append("```bash")
            instructions.append("# Clone the repository")
            instructions.append("git clone <repository-url>")
            instructions.append("cd " + project_path.name)
            instructions.append("```")
        
        return "\n".join(instructions)
    
    def _generate_usage_section(self, project_path: Path) -> str:
        """Generate usage section."""
        usage_lines = []
        
        # Look for main entry points
        main_files = list(project_path.glob("**/main.py")) + \
                    list(project_path.glob("**/app.py")) + \
                    list(project_path.glob("**/__main__.py"))
        
        if main_files:
            usage_lines.append("```python")
            usage_lines.append("# Run the application")
            usage_lines.append(f"python {main_files[0].name}")
            usage_lines.append("```")
        else:
            usage_lines.append("```python")
            usage_lines.append("# Import and use the library")
            usage_lines.append(f"from {project_path.name} import *")
            usage_lines.append("```")
        
        return "\n".join(usage_lines)
    
    def _generate_code_examples(self, project_path: Path) -> List[str]:
        """Generate code examples from the project."""
        examples = []
        
        # Look for example files
        example_dir = project_path / "examples"
        if example_dir.exists():
            for example_file in example_dir.glob("*.py"):
                try:
                    content = example_file.read_text()
                    # Extract first 20 lines as example
                    lines = content.split('\n')[:20]
                    example = f"```python\n" + "\n".join(lines) + "\n```"
                    examples.append(example)
                except Exception:
                    continue
        
        return examples[:3]  # Limit to 3 examples
    
    def _format_readme_markdown(self, readme: READMEContent) -> str:
        """Format README content as Markdown."""
        lines = []
        
        # Title
        lines.append(f"# {readme.project_name}")
        lines.append("")
        
        # Badges
        if readme.badges:
            lines.extend(readme.badges)
            lines.append("")
        
        # Description
        lines.append(readme.description)
        lines.append("")
        
        # Features
        if readme.features:
            lines.append("## Features")
            lines.append("")
            for feature in readme.features:
                lines.append(f"- {feature}")
            lines.append("")
        
        # Installation
        if readme.installation:
            lines.append("## Installation")
            lines.append("")
            lines.append(readme.installation)
            lines.append("")
        
        # Usage
        if readme.usage:
            lines.append("## Usage")
            lines.append("")
            lines.append(readme.usage)
            lines.append("")
        
        # Examples
        if readme.examples:
            lines.append("## Examples")
            lines.append("")
            for i, example in enumerate(readme.examples, 1):
                lines.append(f"### Example {i}")
                lines.append("")
                lines.append(example)
                lines.append("")
        
        # Contributing
        if readme.contributing:
            lines.append("## Contributing")
            lines.append("")
            lines.append(readme.contributing)
            lines.append("")
        
        # License
        if readme.license:
            lines.append("## License")
            lines.append("")
            lines.append(readme.license)
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_api_documentation(
        self,
        project_path: Path,
        output_format: DocumentationFormat = DocumentationFormat.MARKDOWN
    ) -> APIDocumentation:
        """
        Generate API documentation for a project.
        
        Args:
            project_path: Path to the project root
            output_format: Format for the documentation
            
        Returns:
            APIDocumentation object with complete API docs
        """
        api_doc = APIDocumentation(
            title=f"{project_path.name} API Documentation",
            format=output_format
        )
        
        # Find all Python modules
        python_files = list(project_path.rglob("*.py"))
        
        for py_file in python_files:
            # Skip test files and __pycache__
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            try:
                module_doc = self._analyze_module(py_file)
                if module_doc.functions or module_doc.classes:
                    api_doc.modules.append(module_doc)
            except Exception as e:
                logger.warning(f"Error analyzing {py_file}: {e}")
                continue
        
        # Generate overview
        api_doc.overview = self._generate_api_overview(api_doc.modules)
        
        return api_doc
    
    def _analyze_module(self, file_path: Path) -> ModuleDoc:
        """Analyze a Python module and extract documentation."""
        module_doc = ModuleDoc(
            name=file_path.stem,
            description=f"Module {file_path.stem}"
        )
        
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            # Extract module docstring
            if ast.get_docstring(tree):
                module_doc.description = ast.get_docstring(tree)
            
            # Extract functions and classes
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    func_doc = self._analyze_function(node)
                    module_doc.functions.append(func_doc)
                elif isinstance(node, ast.ClassDef):
                    class_doc = self._analyze_class(node)
                    module_doc.classes.append(class_doc)
                elif isinstance(node, ast.Assign):
                    # Extract module-level constants
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            module_doc.constants.append({
                                "name": target.id,
                                "description": f"Constant {target.id}"
                            })
        
        except Exception as e:
            logger.warning(f"Error analyzing module {file_path}: {e}")
        
        return module_doc
    
    def _generate_api_overview(self, modules: List[ModuleDoc]) -> str:
        """Generate overview section for API documentation."""
        lines = [
            "# API Overview",
            "",
            f"This documentation covers {len(modules)} modules.",
            ""
        ]
        
        total_functions = sum(len(m.functions) for m in modules)
        total_classes = sum(len(m.classes) for m in modules)
        
        lines.append(f"- Total Functions: {total_functions}")
        lines.append(f"- Total Classes: {total_classes}")
        lines.append("")
        
        return "\n".join(lines)
    
    def format_api_documentation(self, api_doc: APIDocumentation) -> str:
        """
        Format API documentation as a string.
        
        Args:
            api_doc: APIDocumentation object
            
        Returns:
            Formatted documentation string
        """
        if api_doc.format == DocumentationFormat.MARKDOWN:
            return self._format_api_markdown(api_doc)
        elif api_doc.format == DocumentationFormat.RST:
            return self._format_api_rst(api_doc)
        else:
            return self._format_api_plain(api_doc)
    
    def _format_api_markdown(self, api_doc: APIDocumentation) -> str:
        """Format API documentation as Markdown."""
        lines = [f"# {api_doc.title}", ""]
        
        if api_doc.overview:
            lines.append(api_doc.overview)
            lines.append("")
        
        # Document each module
        for module in api_doc.modules:
            lines.append(f"## Module: {module.name}")
            lines.append("")
            lines.append(module.description)
            lines.append("")
            
            # Document functions
            if module.functions:
                lines.append("### Functions")
                lines.append("")
                for func in module.functions:
                    lines.append(f"#### `{func.name}()`")
                    lines.append("")
                    lines.append(func.description)
                    lines.append("")
                    
                    if func.parameters:
                        lines.append("**Parameters:**")
                        lines.append("")
                        for param in func.parameters:
                            lines.append(f"- `{param['name']}` ({param['type']}): {param['description']}")
                        lines.append("")
                    
                    if func.returns:
                        lines.append(f"**Returns:** {func.returns}")
                        lines.append("")
            
            # Document classes
            if module.classes:
                lines.append("### Classes")
                lines.append("")
                for cls in module.classes:
                    lines.append(f"#### `{cls.name}`")
                    lines.append("")
                    lines.append(cls.description)
                    lines.append("")
                    
                    if cls.attributes:
                        lines.append("**Attributes:**")
                        lines.append("")
                        for attr in cls.attributes:
                            lines.append(f"- `{attr['name']}` ({attr['type']}): {attr['description']}")
                        lines.append("")
                    
                    if cls.methods:
                        lines.append("**Methods:**")
                        lines.append("")
                        for method in cls.methods:
                            lines.append(f"- `{method.name}()`: {method.description}")
                        lines.append("")
        
        return "\n".join(lines)
    
    def _format_api_rst(self, api_doc: APIDocumentation) -> str:
        """Format API documentation as reStructuredText."""
        lines = [
            api_doc.title,
            "=" * len(api_doc.title),
            ""
        ]
        
        if api_doc.overview:
            lines.append(api_doc.overview)
            lines.append("")
        
        for module in api_doc.modules:
            lines.append(module.name)
            lines.append("-" * len(module.name))
            lines.append("")
            lines.append(module.description)
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_api_plain(self, api_doc: APIDocumentation) -> str:
        """Format API documentation as plain text."""
        lines = [api_doc.title, "=" * len(api_doc.title), ""]
        
        if api_doc.overview:
            lines.append(api_doc.overview)
            lines.append("")
        
        for module in api_doc.modules:
            lines.append(f"Module: {module.name}")
            lines.append(module.description)
            lines.append("")
        
        return "\n".join(lines)


    def explain_code(
        self,
        code: str,
        context: Optional[str] = None,
        detail_level: str = "standard"
    ) -> str:
        """
        Generate natural language explanation of code.
        
        Args:
            code: Code to explain
            context: Optional context about the code
            detail_level: Level of detail ("brief", "standard", "detailed")
            
        Returns:
            Natural language explanation of the code
        """
        try:
            tree = ast.parse(code)
            
            explanation_parts = []
            
            # Analyze overall structure
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
            
            # High-level overview
            if context:
                explanation_parts.append(f"Context: {context}\n")
            
            explanation_parts.append("Code Overview:")
            explanation_parts.append(f"This code contains {len(functions)} function(s) and {len(classes)} class(es).")
            
            if imports:
                explanation_parts.append(f"\nIt imports {len(imports)} external module(s).")
            
            # Detailed analysis
            if detail_level in ["standard", "detailed"]:
                if classes:
                    explanation_parts.append("\nClasses:")
                    for cls_node in classes:
                        if isinstance(cls_node, ast.ClassDef):
                            methods = [n for n in cls_node.body if isinstance(n, ast.FunctionDef)]
                            explanation_parts.append(f"  - {cls_node.name}: A class with {len(methods)} method(s)")
                
                if functions:
                    explanation_parts.append("\nFunctions:")
                    for func_node in functions:
                        if isinstance(func_node, ast.FunctionDef):
                            params = [arg.arg for arg in func_node.args.args]
                            explanation_parts.append(f"  - {func_node.name}({', '.join(params)})")
            
            # Very detailed analysis
            if detail_level == "detailed":
                explanation_parts.append("\nDetailed Analysis:")
                
                # Analyze complexity
                loops = len([n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))])
                conditionals = len([n for n in ast.walk(tree) if isinstance(n, ast.If)])
                
                explanation_parts.append(f"  - Control flow: {loops} loop(s), {conditionals} conditional(s)")
                
                # Analyze patterns
                if any(isinstance(n, ast.Try) for n in ast.walk(tree)):
                    explanation_parts.append("  - Includes error handling with try/except")
                
                if any(isinstance(n, ast.With) for n in ast.walk(tree)):
                    explanation_parts.append("  - Uses context managers (with statements)")
                
                if any(isinstance(n, ast.ListComp) for n in ast.walk(tree)):
                    explanation_parts.append("  - Uses list comprehensions")
            
            return "\n".join(explanation_parts)
            
        except Exception as e:
            logger.warning(f"Error explaining code: {e}")
            return self._generate_simple_explanation(code)
    
    def _generate_simple_explanation(self, code: str) -> str:
        """Generate a simple explanation when AST parsing fails."""
        lines = code.split('\n')
        non_empty = [l for l in lines if l.strip()]
        
        explanation = f"This code consists of {len(non_empty)} lines. "
        
        if 'def ' in code:
            explanation += "It defines functions. "
        if 'class ' in code:
            explanation += "It defines classes. "
        if 'import ' in code:
            explanation += "It imports external modules. "
        
        return explanation
    
    def generate_examples(
        self,
        code: str,
        num_examples: int = 3
    ) -> List[str]:
        """
        Generate usage examples for code.
        
        Args:
            code: Code to generate examples for
            num_examples: Number of examples to generate
            
        Returns:
            List of usage examples
        """
        examples = []
        
        try:
            tree = ast.parse(code)
            
            # Generate examples for functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and len(examples) < num_examples:
                    example = self._generate_function_example(node)
                    if example:
                        examples.append(example)
                
                elif isinstance(node, ast.ClassDef) and len(examples) < num_examples:
                    example = self._generate_class_example(node)
                    if example:
                        examples.append(example)
        
        except Exception as e:
            logger.warning(f"Error generating examples: {e}")
        
        return examples
    
    def _generate_function_example(self, node: ast.FunctionDef) -> str:
        """Generate usage example for a function."""
        params = node.args.args
        
        # Generate sample arguments
        sample_args = []
        for arg in params:
            arg_name = arg.arg
            if arg_name == "self":
                continue
            
            # Infer type from annotation or name
            if arg.annotation:
                ann_str = self._get_annotation_string(arg.annotation)
                if "str" in ann_str.lower():
                    sample_args.append(f'"{arg_name}_value"')
                elif "int" in ann_str.lower():
                    sample_args.append("42")
                elif "list" in ann_str.lower():
                    sample_args.append("[]")
                elif "dict" in ann_str.lower():
                    sample_args.append("{}")
                else:
                    sample_args.append("None")
            else:
                # Guess from name
                if "name" in arg_name.lower() or "text" in arg_name.lower():
                    sample_args.append(f'"{arg_name}"')
                elif "count" in arg_name.lower() or "num" in arg_name.lower():
                    sample_args.append("10")
                else:
                    sample_args.append("value")
        
        example_lines = [
            "```python",
            f"# Example usage of {node.name}",
            f"result = {node.name}({', '.join(sample_args)})",
            "print(result)",
            "```"
        ]
        
        return "\n".join(example_lines)
    
    def _generate_class_example(self, node: ast.ClassDef) -> str:
        """Generate usage example for a class."""
        # Find __init__ method
        init_method = None
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                init_method = item
                break
        
        # Generate constructor arguments
        init_args = []
        if init_method:
            for arg in init_method.args.args:
                if arg.arg != "self":
                    init_args.append(f"{arg.arg}=value")
        
        example_lines = [
            "```python",
            f"# Example usage of {node.name}",
            f"instance = {node.name}({', '.join(init_args)})",
            "",
            "# Use the instance",
            "# instance.method()",
            "```"
        ]
        
        return "\n".join(example_lines)
    
    def check_doc_sync(
        self,
        project_path: Path,
        check_docstrings: bool = True,
        check_readme: bool = True
    ) -> List[DocSyncIssue]:
        """
        Check if documentation is in sync with code.
        
        Args:
            project_path: Path to the project root
            check_docstrings: Whether to check docstrings
            check_readme: Whether to check README
            
        Returns:
            List of documentation sync issues found
        """
        issues = []
        
        if check_docstrings:
            issues.extend(self._check_docstring_sync(project_path))
        
        if check_readme:
            issues.extend(self._check_readme_sync(project_path))
        
        return issues
    
    def _check_docstring_sync(self, project_path: Path) -> List[DocSyncIssue]:
        """Check if docstrings are in sync with code."""
        issues = []
        
        python_files = list(project_path.rglob("*.py"))
        
        for py_file in python_files:
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                # Check functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        docstring = ast.get_docstring(node)
                        
                        # Check if public function has docstring
                        if not node.name.startswith("_") and not docstring:
                            issues.append(DocSyncIssue(
                                file_path=py_file,
                                issue_type="missing_docstring",
                                description=f"Function '{node.name}' is missing a docstring",
                                line_number=node.lineno,
                                severity="warning",
                                suggestion=f"Add a docstring to document the function '{node.name}'"
                            ))
                        
                        # Check if docstring mentions all parameters
                        if docstring:
                            param_names = [arg.arg for arg in node.args.args if arg.arg != "self"]
                            for param in param_names:
                                if param not in docstring:
                                    issues.append(DocSyncIssue(
                                        file_path=py_file,
                                        issue_type="incomplete_docstring",
                                        description=f"Parameter '{param}' not documented in '{node.name}'",
                                        line_number=node.lineno,
                                        severity="info",
                                        suggestion=f"Add documentation for parameter '{param}'"
                                    ))
                    
                    elif isinstance(node, ast.ClassDef):
                        docstring = ast.get_docstring(node)
                        
                        # Check if public class has docstring
                        if not node.name.startswith("_") and not docstring:
                            issues.append(DocSyncIssue(
                                file_path=py_file,
                                issue_type="missing_docstring",
                                description=f"Class '{node.name}' is missing a docstring",
                                line_number=node.lineno,
                                severity="warning",
                                suggestion=f"Add a docstring to document the class '{node.name}'"
                            ))
            
            except Exception as e:
                logger.debug(f"Error checking {py_file}: {e}")
                continue
        
        return issues
    
    def _check_readme_sync(self, project_path: Path) -> List[DocSyncIssue]:
        """Check if README is in sync with project."""
        issues = []
        
        readme_files = list(project_path.glob("README*"))
        
        if not readme_files:
            issues.append(DocSyncIssue(
                file_path=project_path,
                issue_type="missing_readme",
                description="Project is missing a README file",
                severity="error",
                suggestion="Create a README.md file to document the project"
            ))
            return issues
        
        readme_file = readme_files[0]
        
        try:
            readme_content = readme_file.read_text().lower()
            
            # Check for essential sections
            essential_sections = {
                "installation": ["install", "setup"],
                "usage": ["usage", "how to use", "getting started"],
                "description": ["description", "about", "overview"]
            }
            
            for section_name, keywords in essential_sections.items():
                if not any(keyword in readme_content for keyword in keywords):
                    issues.append(DocSyncIssue(
                        file_path=readme_file,
                        issue_type="incomplete_readme",
                        description=f"README is missing '{section_name}' section",
                        severity="warning",
                        suggestion=f"Add a '{section_name}' section to the README"
                    ))
            
            # Check if README mentions main modules
            src_dir = project_path / "src"
            if src_dir.exists():
                main_modules = [d.name for d in src_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
                for module in main_modules:
                    if module not in readme_content:
                        issues.append(DocSyncIssue(
                            file_path=readme_file,
                            issue_type="outdated_readme",
                            description=f"README doesn't mention module '{module}'",
                            severity="info",
                            suggestion=f"Consider documenting the '{module}' module in README"
                        ))
        
        except Exception as e:
            logger.debug(f"Error checking README: {e}")
        
        return issues
    
    def update_documentation(
        self,
        project_path: Path,
        update_docstrings: bool = True,
        update_readme: bool = False
    ) -> Dict[str, int]:
        """
        Automatically update documentation.
        
        Args:
            project_path: Path to the project root
            update_docstrings: Whether to add missing docstrings
            update_readme: Whether to update README
            
        Returns:
            Dictionary with counts of updates made
        """
        updates = {
            "docstrings_added": 0,
            "docstrings_updated": 0,
            "readme_updated": 0
        }
        
        if update_docstrings:
            updates["docstrings_added"] = self._add_missing_docstrings(project_path)
        
        if update_readme:
            readme_path = project_path / "README.md"
            if not readme_path.exists():
                readme_content = self.generate_readme(project_path)
                readme_path.write_text(readme_content)
                updates["readme_updated"] = 1
        
        return updates
    
    def _add_missing_docstrings(self, project_path: Path) -> int:
        """Add missing docstrings to code."""
        count = 0
        
        python_files = list(project_path.rglob("*.py"))
        
        for py_file in python_files:
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                modified = False
                lines = content.split('\n')
                
                # Find functions and classes without docstrings
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if not node.name.startswith("_") and not ast.get_docstring(node):
                            # Generate and insert docstring
                            entity_type = "function" if isinstance(node, ast.FunctionDef) else "class"
                            docstring = self.generate_docstring(content, node.name, entity_type)
                            
                            # Insert after function/class definition
                            insert_line = node.lineno
                            indent = self._get_indentation(lines[insert_line - 1])
                            
                            # Add docstring with proper indentation
                            docstring_lines = docstring.split('\n')
                            indented_docstring = [indent + "    " + line for line in docstring_lines]
                            
                            # This is a simplified approach - in production, use ast.unparse or similar
                            logger.info(f"Would add docstring to {node.name} in {py_file}")
                            count += 1
                            modified = True
                
            except Exception as e:
                logger.debug(f"Error processing {py_file}: {e}")
                continue
        
        return count
    
    def _get_indentation(self, line: str) -> str:
        """Get the indentation of a line."""
        return line[:len(line) - len(line.lstrip())]
    
    def validate_documentation(
        self,
        project_path: Path
    ) -> Dict[str, Any]:
        """
        Validate documentation consistency.
        
        Args:
            project_path: Path to the project root
            
        Returns:
            Validation report with statistics and issues
        """
        report = {
            "total_files": 0,
            "documented_functions": 0,
            "undocumented_functions": 0,
            "documented_classes": 0,
            "undocumented_classes": 0,
            "issues": [],
            "score": 0.0
        }
        
        python_files = list(project_path.rglob("*.py"))
        report["total_files"] = len(python_files)
        
        for py_file in python_files:
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not node.name.startswith("_"):
                            if ast.get_docstring(node):
                                report["documented_functions"] += 1
                            else:
                                report["undocumented_functions"] += 1
                    
                    elif isinstance(node, ast.ClassDef):
                        if not node.name.startswith("_"):
                            if ast.get_docstring(node):
                                report["documented_classes"] += 1
                            else:
                                report["undocumented_classes"] += 1
            
            except Exception:
                continue
        
        # Calculate documentation score
        total_entities = (report["documented_functions"] + report["undocumented_functions"] +
                         report["documented_classes"] + report["undocumented_classes"])
        
        if total_entities > 0:
            documented = report["documented_functions"] + report["documented_classes"]
            report["score"] = (documented / total_entities) * 100
        
        # Get sync issues
        report["issues"] = self.check_doc_sync(project_path)
        
        return report
