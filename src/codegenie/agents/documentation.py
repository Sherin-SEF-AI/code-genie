"""
Documentation Agent - Specialized agent for automated documentation generation.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base_agent import BaseAgent, Task, AgentResult, AgentCapability
from ..core.config import Config
from ..core.tool_executor import ToolExecutor
from ..models.model_router import ModelRouter

logger = logging.getLogger(__name__)


class DocumentationType(Enum):
    """Types of documentation."""
    
    API = "api"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    README = "readme"
    DOCSTRING = "docstring"
    CHANGELOG = "changelog"
    ARCHITECTURE = "architecture"


class DocumentationFormat(Enum):
    """Documentation formats."""
    
    MARKDOWN = "markdown"
    RST = "rst"
    HTML = "html"
    PDF = "pdf"


@dataclass
class DocumentationSection:
    """A section of documentation."""
    
    title: str
    content: str
    subsections: List['DocumentationSection'] = field(default_factory=list)
    code_examples: List[str] = field(default_factory=list)
    level: int = 1


@dataclass
class Documentation:
    """Complete documentation."""
    
    title: str
    doc_type: DocumentationType
    format: DocumentationFormat
    sections: List[DocumentationSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_content: str = ""


class DocumentationAgent(BaseAgent):
    """
    Specialized agent for automated documentation generation.
    
    Capabilities:
    - API documentation generation
    - User guide creation
    - Docstring generation
    - Documentation maintenance
    """
    
    def __init__(
        self,
        config: Config,
        model_router: ModelRouter,
        tool_executor: Optional[ToolExecutor] = None
    ):
        super().__init__(
            name="DocumentationAgent",
            capabilities=[
                AgentCapability.DOCUMENTATION,
                AgentCapability.CODE_ANALYSIS
            ],
            config=config,
            model_router=model_router
        )
        
        self.tool_executor = tool_executor
        self.doc_templates: Dict[str, str] = self._initialize_doc_templates()
        
        logger.info("Initialized DocumentationAgent")
    
    def _initialize_doc_templates(self) -> Dict[str, str]:
        """Initialize documentation templates."""
        return {
            "readme": '''# {title}

## Overview
{overview}

## Installation
{installation}

## Usage
{usage}

## API Reference
{api_reference}

## Contributing
{contributing}

## License
{license}
''',
            "api_doc": '''## {function_name}

{description}

### Parameters
{parameters}

### Returns
{returns}

### Example
```python
{example}
```
''',
            "docstring": '''"""
{summary}

Args:
{args}

Returns:
{returns}

Raises:
{raises}
"""'''
        }
    
    async def can_handle_task(self, task: Task) -> bool:
        """Determine if this agent can handle the task."""
        doc_keywords = [
            "document", "documentation", "docstring", "readme",
            "api doc", "guide", "manual", "changelog"
        ]
        
        task_text = f"{task.description} {task.task_type}".lower()
        return any(keyword in task_text for keyword in doc_keywords)
    
    async def execute_task(self, task: Task) -> AgentResult:
        """Execute a documentation task."""
        try:
            task_type = task.task_type.lower()
            
            if "generate" in task_type or "create" in task_type:
                result = await self.generate_documentation(task.context)
            elif "update" in task_type:
                result = await self.update_documentation(task.context)
            elif "docstring" in task_type:
                result = await self.generate_docstrings(task.context)
            else:
                result = await self._general_documentation_consultation(task)
            
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=True,
                output=result,
                confidence=0.85,
                reasoning=f"Completed documentation task: {task.task_type}",
                suggestions=self._generate_suggestions(result),
                next_steps=self._generate_next_steps(task, result)
            )
            
        except Exception as e:
            logger.error(f"DocumentationAgent task execution failed: {e}")
            return AgentResult(
                agent_name=self.name,
                task_id=task.id,
                success=False,
                confidence=0.0,
                reasoning=f"Task execution failed: {str(e)}",
                error=str(e)
            )
    
    async def generate_documentation(self, context: Dict[str, Any]) -> Documentation:
        """Generate documentation."""
        logger.info("Generating documentation")
        
        doc_type = context.get("doc_type", DocumentationType.README)
        format_type = context.get("format", DocumentationFormat.MARKDOWN)
        code = context.get("code", "")
        project_info = context.get("project_info", {})
        
        sections = []
        
        if doc_type == DocumentationType.README:
            sections = self._generate_readme_sections(project_info)
        elif doc_type == DocumentationType.API:
            sections = self._generate_api_sections(code)
        elif doc_type == DocumentationType.DOCSTRING:
            sections = self._generate_docstring_sections(code)
        
        # Generate content
        content = self._render_documentation(sections, format_type)
        
        doc = Documentation(
            title=project_info.get("name", "Documentation"),
            doc_type=doc_type,
            format=format_type,
            sections=sections,
            metadata=project_info,
            generated_content=content
        )
        
        logger.info(f"Generated {doc_type.value} documentation")
        return doc
    
    async def update_documentation(self, context: Dict[str, Any]) -> Documentation:
        """Update existing documentation."""
        logger.info("Updating documentation")
        
        existing_doc = context.get("existing_doc", "")
        changes = context.get("changes", [])
        
        # Parse and update documentation
        doc = Documentation(
            title="Updated Documentation",
            doc_type=DocumentationType.README,
            format=DocumentationFormat.MARKDOWN,
            generated_content=existing_doc + "\n\n## Updates\n" + "\n".join(changes)
        )
        
        logger.info("Documentation updated")
        return doc
    
    async def generate_docstrings(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate docstrings for code."""
        logger.info("Generating docstrings")
        
        code = context.get("code", "")
        
        docstrings = {}
        
        # Parse code and generate docstrings
        import re
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
        
        for func_name in functions:
            docstring = self._generate_function_docstring(func_name, code)
            docstrings[func_name] = docstring
        
        logger.info(f"Generated {len(docstrings)} docstrings")
        return docstrings
    
    async def provide_expertise(self, question: str) -> Dict[str, Any]:
        """Provide documentation expertise."""
        logger.info(f"Providing documentation expertise for: {question}")
        
        recommendations = [
            "Keep documentation up to date with code",
            "Write clear and concise descriptions",
            "Include code examples",
            "Document edge cases and limitations",
            "Use consistent formatting"
        ]
        
        return {
            "expertise": f"Documentation guidance on: {question}",
            "confidence": 0.85,
            "recommendations": recommendations
        }
    
    def _generate_readme_sections(self, project_info: Dict[str, Any]) -> List[DocumentationSection]:
        """Generate README sections."""
        sections = [
            DocumentationSection(
                title="Overview",
                content=project_info.get("description", "Project description"),
                level=2
            ),
            DocumentationSection(
                title="Installation",
                content="```bash\npip install " + project_info.get("name", "package") + "\n```",
                level=2
            ),
            DocumentationSection(
                title="Usage",
                content="Basic usage examples",
                level=2,
                code_examples=["# Example code here"]
            )
        ]
        return sections
    
    def _generate_api_sections(self, code: str) -> List[DocumentationSection]:
        """Generate API documentation sections."""
        sections = []
        
        import re
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
        
        for func_name in functions:
            if not func_name.startswith('_'):
                section = DocumentationSection(
                    title=func_name,
                    content=f"Function: {func_name}",
                    level=2
                )
                sections.append(section)
        
        return sections
    
    def _generate_docstring_sections(self, code: str) -> List[DocumentationSection]:
        """Generate docstring sections."""
        return [
            DocumentationSection(
                title="Docstrings",
                content="Generated docstrings for code",
                level=1
            )
        ]
    
    def _render_documentation(
        self,
        sections: List[DocumentationSection],
        format_type: DocumentationFormat
    ) -> str:
        """Render documentation in specified format."""
        if format_type == DocumentationFormat.MARKDOWN:
            return self._render_markdown(sections)
        return "# Documentation\n\nContent here"
    
    def _render_markdown(self, sections: List[DocumentationSection]) -> str:
        """Render documentation as Markdown."""
        content = []
        
        for section in sections:
            # Add heading
            content.append(f"{'#' * section.level} {section.title}\n")
            content.append(f"{section.content}\n")
            
            # Add code examples
            for example in section.code_examples:
                content.append(f"```python\n{example}\n```\n")
            
            # Add subsections
            if section.subsections:
                content.append(self._render_markdown(section.subsections))
        
        return "\n".join(content)
    
    def _generate_function_docstring(self, func_name: str, code: str) -> str:
        """Generate docstring for a function."""
        template = self.doc_templates["docstring"]
        return template.format(
            summary=f"Function {func_name}",
            args="    None",
            returns="    None",
            raises="    None"
        )
    
    async def _general_documentation_consultation(self, task: Task) -> Dict[str, Any]:
        """Provide general documentation consultation."""
        return {
            "consultation": f"Documentation guidance for: {task.description}",
            "recommendations": [
                "Document public APIs thoroughly",
                "Keep documentation synchronized with code",
                "Use examples to illustrate usage",
                "Document assumptions and limitations",
                "Review documentation regularly"
            ]
        }
    
    def _generate_suggestions(self, result: Any) -> List[str]:
        """Generate suggestions based on result."""
        suggestions = []
        
        if isinstance(result, Documentation):
            suggestions.append("Review generated documentation")
            suggestions.append("Add more examples")
            suggestions.append("Update with project-specific details")
        elif isinstance(result, dict):
            suggestions.append("Apply generated docstrings")
            suggestions.append("Review for accuracy")
        
        return suggestions
    
    def _generate_next_steps(self, task: Task, result: Any) -> List[str]:
        """Generate next steps."""
        next_steps = []
        
        if isinstance(result, Documentation):
            next_steps.extend([
                "Save documentation to file",
                "Generate additional formats if needed",
                "Set up documentation hosting"
            ])
        elif isinstance(result, dict):
            next_steps.extend([
                "Apply docstrings to code",
                "Generate API documentation",
                "Update README"
            ])
        
        return next_steps
