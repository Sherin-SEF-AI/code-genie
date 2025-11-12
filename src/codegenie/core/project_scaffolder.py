"""
Project Scaffolder for automated project structure generation.

This module provides intelligent project scaffolding with:
- Project type detection from descriptions
- Directory structure generation
- Configuration file creation
- Git initialization and .gitignore generation
- Dependency installation with progress tracking
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

from .file_creator import FileCreator, FileOperation, OperationType
from .command_executor import CommandExecutor, CommandResult

logger = logging.getLogger(__name__)


class ProjectType(Enum):
    """Supported project types."""
    PYTHON_FASTAPI = "python_fastapi"
    PYTHON_DJANGO = "python_django"
    PYTHON_FLASK = "python_flask"
    PYTHON_CLI = "python_cli"
    PYTHON_GENERIC = "python_generic"
    
    JAVASCRIPT_REACT = "javascript_react"
    JAVASCRIPT_NEXTJS = "javascript_nextjs"
    JAVASCRIPT_EXPRESS = "javascript_express"
    JAVASCRIPT_VUE = "javascript_vue"
    JAVASCRIPT_GENERIC = "javascript_generic"
    
    TYPESCRIPT_REACT = "typescript_react"
    TYPESCRIPT_NEXTJS = "typescript_nextjs"
    TYPESCRIPT_EXPRESS = "typescript_express"
    TYPESCRIPT_GENERIC = "typescript_generic"
    
    GO_CLI = "go_cli"
    GO_WEB = "go_web"
    GO_GRPC = "go_grpc"
    GO_GENERIC = "go_generic"
    
    RUST_CLI = "rust_cli"
    RUST_WEB = "rust_web"
    RUST_LIB = "rust_lib"
    RUST_GENERIC = "rust_generic"
    
    GENERIC = "generic"


class PackageManager(Enum):
    """Supported package managers."""
    PIP = "pip"
    POETRY = "poetry"
    PIPENV = "pipenv"
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    CARGO = "cargo"
    GO_MOD = "go"


@dataclass
class DirectoryStructure:
    """Represents a directory structure."""
    directories: List[Path]
    files: Dict[Path, str]  # Path -> content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'directories': [str(d) for d in self.directories],
            'files': {str(k): v for k, v in self.files.items()},
        }


@dataclass
class ProjectConfig:
    """Configuration for a project."""
    name: str
    project_type: ProjectType
    description: str = ""
    author: str = ""
    version: str = "0.1.0"
    license: str = "MIT"
    python_version: str = "3.9"
    node_version: str = "18"
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'project_type': self.project_type.value,
            'description': self.description,
            'author': self.author,
            'version': self.version,
            'license': self.license,
            'python_version': self.python_version,
            'node_version': self.node_version,
            'dependencies': self.dependencies,
            'dev_dependencies': self.dev_dependencies,
        }


@dataclass
class Project:
    """Represents a created project."""
    name: str
    path: Path
    project_type: ProjectType
    config: ProjectConfig
    structure: DirectoryStructure
    git_initialized: bool = False
    dependencies_installed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'path': str(self.path),
            'project_type': self.project_type.value,
            'config': self.config.to_dict(),
            'structure': self.structure.to_dict(),
            'git_initialized': self.git_initialized,
            'dependencies_installed': self.dependencies_installed,
        }


@dataclass
class InstallResult:
    """Result of dependency installation."""
    success: bool
    package_manager: PackageManager
    installed_packages: List[str]
    failed_packages: List[str]
    output: str
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'package_manager': self.package_manager.value,
            'installed_packages': self.installed_packages,
            'failed_packages': self.failed_packages,
            'output': self.output,
            'error_message': self.error_message,
        }


class ProjectScaffolder:
    """
    Automated project scaffolding system.
    
    Creates complete project structures from templates with:
    - Intelligent project type detection
    - Directory structure generation
    - Configuration file creation
    - Git initialization
    - Dependency installation
    """
    
    def __init__(
        self,
        file_creator: Optional[FileCreator] = None,
        command_executor: Optional[CommandExecutor] = None,
        base_path: Optional[Path] = None
    ):
        """
        Initialize project scaffolder.
        
        Args:
            file_creator: FileCreator instance for file operations
            command_executor: CommandExecutor for running commands
            base_path: Base path for creating projects (defaults to current directory)
        """
        self.file_creator = file_creator or FileCreator()
        self.command_executor = command_executor or CommandExecutor()
        self.base_path = base_path or Path.cwd()
        
        # Project type detection patterns
        self.type_patterns = self._initialize_type_patterns()
        
        # Template configurations
        self.templates = self._initialize_templates()
    
    def _initialize_type_patterns(self) -> Dict[ProjectType, List[str]]:
        """Initialize patterns for project type detection."""
        return {
            ProjectType.PYTHON_FASTAPI: [
                r'fastapi', r'fast\s*api', r'rest\s*api.*python',
                r'python.*api', r'async.*python.*web'
            ],
            ProjectType.PYTHON_DJANGO: [
                r'django', r'python.*web.*framework', r'orm.*python'
            ],
            ProjectType.PYTHON_FLASK: [
                r'flask', r'micro.*framework.*python', r'simple.*python.*web'
            ],
            ProjectType.PYTHON_CLI: [
                r'python.*cli', r'command.*line.*python', r'python.*tool',
                r'python.*script'
            ],
            ProjectType.JAVASCRIPT_REACT: [
                r'react(?!.*next)', r'react.*app', r'spa.*react', r'frontend.*react'
            ],
            ProjectType.JAVASCRIPT_NEXTJS: [
                r'next\.?js', r'next.*react', r'ssr.*react', r'react.*ssr'
            ],
            ProjectType.JAVASCRIPT_EXPRESS: [
                r'express', r'node.*server', r'node.*api', r'backend.*node'
            ],
            ProjectType.JAVASCRIPT_VUE: [
                r'vue', r'vue\.?js', r'frontend.*vue'
            ],
            ProjectType.TYPESCRIPT_REACT: [
                r'typescript.*react', r'react.*typescript', r'ts.*react'
            ],
            ProjectType.TYPESCRIPT_NEXTJS: [
                r'typescript.*next', r'next.*typescript', r'ts.*next'
            ],
            ProjectType.TYPESCRIPT_EXPRESS: [
                r'typescript.*express', r'express.*typescript', r'ts.*express'
            ],
            ProjectType.GO_CLI: [
                r'go.*cli', r'golang.*cli', r'go.*tool', r'go.*command'
            ],
            ProjectType.GO_WEB: [
                r'go.*web', r'golang.*web', r'go.*server', r'go.*api'
            ],
            ProjectType.GO_GRPC: [
                r'go.*grpc', r'golang.*grpc', r'go.*rpc'
            ],
            ProjectType.RUST_CLI: [
                r'rust.*cli', r'rust.*tool', r'rust.*command'
            ],
            ProjectType.RUST_WEB: [
                r'rust.*web', r'rust.*server', r'rust.*api', r'actix', r'rocket'
            ],
            ProjectType.RUST_LIB: [
                r'rust.*library', r'rust.*lib', r'rust.*crate'
            ],
        }
    
    def _initialize_templates(self) -> Dict[ProjectType, Dict[str, Any]]:
        """Initialize project templates."""
        return {
            ProjectType.PYTHON_FASTAPI: {
                'directories': ['app', 'app/api', 'app/models', 'app/services', 'tests'],
                'dependencies': ['fastapi', 'uvicorn[standard]', 'pydantic', 'python-dotenv'],
                'dev_dependencies': ['pytest', 'pytest-asyncio', 'httpx', 'black', 'flake8'],
                'package_manager': PackageManager.PIP,
            },
            ProjectType.PYTHON_DJANGO: {
                'directories': ['config', 'apps', 'static', 'media', 'templates'],
                'dependencies': ['django', 'djangorestframework', 'python-dotenv', 'psycopg2-binary'],
                'dev_dependencies': ['pytest', 'pytest-django', 'black', 'flake8'],
                'package_manager': PackageManager.PIP,
            },
            ProjectType.PYTHON_FLASK: {
                'directories': ['app', 'app/routes', 'app/models', 'app/templates', 'tests'],
                'dependencies': ['flask', 'flask-sqlalchemy', 'python-dotenv'],
                'dev_dependencies': ['pytest', 'pytest-flask', 'black', 'flake8'],
                'package_manager': PackageManager.PIP,
            },
            ProjectType.PYTHON_CLI: {
                'directories': ['src', 'tests'],
                'dependencies': ['click', 'rich'],
                'dev_dependencies': ['pytest', 'black', 'flake8'],
                'package_manager': PackageManager.PIP,
            },
            ProjectType.JAVASCRIPT_REACT: {
                'directories': ['src', 'src/components', 'src/hooks', 'src/utils', 'public'],
                'dependencies': ['react', 'react-dom'],
                'dev_dependencies': ['vite', '@vitejs/plugin-react', 'eslint', 'prettier'],
                'package_manager': PackageManager.NPM,
            },
            ProjectType.JAVASCRIPT_NEXTJS: {
                'directories': ['app', 'components', 'lib', 'public'],
                'dependencies': ['next', 'react', 'react-dom'],
                'dev_dependencies': ['eslint', 'eslint-config-next', 'prettier'],
                'package_manager': PackageManager.NPM,
            },
            ProjectType.JAVASCRIPT_EXPRESS: {
                'directories': ['src', 'src/routes', 'src/controllers', 'src/models', 'tests'],
                'dependencies': ['express', 'dotenv', 'cors'],
                'dev_dependencies': ['nodemon', 'jest', 'supertest', 'eslint', 'prettier'],
                'package_manager': PackageManager.NPM,
            },
            ProjectType.GO_CLI: {
                'directories': ['cmd', 'internal', 'pkg'],
                'dependencies': [],
                'dev_dependencies': [],
                'package_manager': PackageManager.GO_MOD,
            },
            ProjectType.GO_WEB: {
                'directories': ['cmd', 'internal', 'pkg', 'api'],
                'dependencies': [],
                'dev_dependencies': [],
                'package_manager': PackageManager.GO_MOD,
            },
            ProjectType.RUST_CLI: {
                'directories': ['src'],
                'dependencies': ['clap'],
                'dev_dependencies': [],
                'package_manager': PackageManager.CARGO,
            },
            ProjectType.RUST_WEB: {
                'directories': ['src', 'src/handlers', 'src/models'],
                'dependencies': ['actix-web', 'tokio', 'serde'],
                'dev_dependencies': [],
                'package_manager': PackageManager.CARGO,
            },
        }

    def detect_project_type(self, description: str) -> ProjectType:
        """
        Detect project type from description.
        
        Args:
            description: Natural language description of the project
            
        Returns:
            Detected ProjectType
        """
        description_lower = description.lower()
        
        # Score each project type based on pattern matches
        scores: Dict[ProjectType, int] = {}
        
        for project_type, patterns in self.type_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, description_lower):
                    score += 1
            if score > 0:
                scores[project_type] = score
        
        # Return the type with highest score
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])[0]
            logger.info(f"Detected project type: {best_type.value} (score: {scores[best_type]})")
            return best_type
        
        # Fallback to generic types based on language keywords
        if any(kw in description_lower for kw in ['python', 'py']):
            return ProjectType.PYTHON_GENERIC
        elif any(kw in description_lower for kw in ['javascript', 'js', 'node']):
            return ProjectType.JAVASCRIPT_GENERIC
        elif any(kw in description_lower for kw in ['typescript', 'ts']):
            return ProjectType.TYPESCRIPT_GENERIC
        elif any(kw in description_lower for kw in ['go', 'golang']):
            return ProjectType.GO_GENERIC
        elif any(kw in description_lower for kw in ['rust', 'rs']):
            return ProjectType.RUST_GENERIC
        
        logger.warning("Could not detect specific project type, using GENERIC")
        return ProjectType.GENERIC
    
    def generate_structure(self, project_type: ProjectType, name: str) -> DirectoryStructure:
        """
        Generate directory structure for project type.
        
        Args:
            project_type: Type of project to create
            name: Name of the project
            
        Returns:
            DirectoryStructure with directories and files
        """
        template = self.templates.get(project_type, {})
        directories = template.get('directories', [])
        
        # Convert to Path objects relative to project root
        dir_paths = [Path(name) / d for d in directories]
        
        # Generate configuration files based on project type
        files = self._generate_config_files(project_type, name, template)
        
        structure = DirectoryStructure(
            directories=dir_paths,
            files=files
        )
        
        logger.info(f"Generated structure for {project_type.value}: {len(dir_paths)} dirs, {len(files)} files")
        return structure
    
    def _generate_config_files(
        self,
        project_type: ProjectType,
        name: str,
        template: Dict[str, Any]
    ) -> Dict[Path, str]:
        """Generate configuration files for the project."""
        files: Dict[Path, str] = {}
        project_root = Path(name)
        
        # Python projects
        if project_type.value.startswith('python'):
            files[project_root / 'requirements.txt'] = self._generate_requirements_txt(template)
            files[project_root / 'setup.py'] = self._generate_setup_py(name, template)
            files[project_root / 'README.md'] = self._generate_readme(name, project_type)
            files[project_root / '.env.example'] = self._generate_env_example(project_type)
            
            if project_type == ProjectType.PYTHON_FASTAPI:
                files[project_root / 'app' / '__init__.py'] = ''
                files[project_root / 'app' / 'main.py'] = self._generate_fastapi_main()
                files[project_root / 'app' / 'api' / '__init__.py'] = ''
            elif project_type == ProjectType.PYTHON_FLASK:
                files[project_root / 'app' / '__init__.py'] = self._generate_flask_init()
                files[project_root / 'run.py'] = self._generate_flask_run()
            elif project_type == ProjectType.PYTHON_CLI:
                files[project_root / 'src' / '__init__.py'] = ''
                files[project_root / 'src' / 'cli.py'] = self._generate_python_cli(name)
        
        # JavaScript/TypeScript projects
        elif project_type.value.startswith(('javascript', 'typescript')):
            files[project_root / 'package.json'] = self._generate_package_json(name, project_type, template)
            files[project_root / 'README.md'] = self._generate_readme(name, project_type)
            files[project_root / '.env.example'] = self._generate_env_example(project_type)
            files[project_root / '.gitignore'] = self._generate_gitignore(project_type)
            
            if project_type == ProjectType.JAVASCRIPT_REACT:
                files[project_root / 'index.html'] = self._generate_react_html(name)
                files[project_root / 'src' / 'main.jsx'] = self._generate_react_main()
                files[project_root / 'src' / 'App.jsx'] = self._generate_react_app()
                files[project_root / 'vite.config.js'] = self._generate_vite_config()
            elif project_type == ProjectType.JAVASCRIPT_EXPRESS:
                files[project_root / 'src' / 'index.js'] = self._generate_express_main()
                files[project_root / 'src' / 'routes' / 'index.js'] = self._generate_express_routes()
        
        # Go projects
        elif project_type.value.startswith('go'):
            files[project_root / 'go.mod'] = self._generate_go_mod(name)
            files[project_root / 'README.md'] = self._generate_readme(name, project_type)
            files[project_root / 'cmd' / name / 'main.go'] = self._generate_go_main(name, project_type)
        
        # Rust projects
        elif project_type.value.startswith('rust'):
            files[project_root / 'Cargo.toml'] = self._generate_cargo_toml(name, template)
            files[project_root / 'README.md'] = self._generate_readme(name, project_type)
            files[project_root / 'src' / 'main.rs'] = self._generate_rust_main(project_type)
        
        return files
    
    def create_project(
        self,
        project_type: str,
        name: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Create a complete project structure.
        
        Args:
            project_type: Type of project (string or ProjectType enum)
            name: Name of the project
            options: Additional options (description, author, etc.)
            
        Returns:
            Created Project object
        """
        options = options or {}
        
        # Convert string to ProjectType if needed
        if isinstance(project_type, str):
            try:
                proj_type = ProjectType(project_type)
            except ValueError:
                # Try to detect from description
                proj_type = self.detect_project_type(project_type)
        else:
            proj_type = project_type
        
        # Create project configuration
        config = ProjectConfig(
            name=name,
            project_type=proj_type,
            description=options.get('description', f'A {proj_type.value} project'),
            author=options.get('author', ''),
            version=options.get('version', '0.1.0'),
            license=options.get('license', 'MIT'),
        )
        
        # Add template dependencies to config
        template = self.templates.get(proj_type, {})
        config.dependencies = template.get('dependencies', [])
        config.dev_dependencies = template.get('dev_dependencies', [])
        
        # Generate structure
        structure = self.generate_structure(proj_type, name)
        
        # Create directories
        project_path = self.base_path / name
        logger.info(f"Creating project at: {project_path}")
        
        for directory in structure.directories:
            full_path = self.base_path / directory
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {full_path}")
        
        # Create files
        for file_path, content in structure.files.items():
            full_path = self.base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            operation = self.file_creator.create_file(
                path=full_path,
                content=content,
                preview=False  # Don't preview during scaffolding
            )
            logger.debug(f"Created file: {full_path}")
        
        # Create project object
        project = Project(
            name=name,
            path=project_path,
            project_type=proj_type,
            config=config,
            structure=structure,
        )
        
        logger.info(f"Successfully created {proj_type.value} project: {name}")
        return project

    # Template generation methods
    
    def _generate_requirements_txt(self, template: Dict[str, Any]) -> str:
        """Generate requirements.txt content."""
        deps = template.get('dependencies', [])
        dev_deps = template.get('dev_dependencies', [])
        
        content = "# Production dependencies\n"
        content += "\n".join(deps)
        content += "\n\n# Development dependencies\n"
        content += "\n".join(dev_deps)
        return content
    
    def _generate_setup_py(self, name: str, template: Dict[str, Any]) -> str:
        """Generate setup.py content."""
        return f'''from setuptools import setup, find_packages

setup(
    name="{name}",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        {", ".join(f'"{dep}"' for dep in template.get('dependencies', []))}
    ],
    python_requires=">=3.9",
)
'''
    
    def _generate_readme(self, name: str, project_type: ProjectType) -> str:
        """Generate README.md content."""
        return f'''# {name}

A {project_type.value.replace('_', ' ').title()} project.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {name}

# Install dependencies
# (See project-specific instructions below)
```

## Usage

TODO: Add usage instructions

## Development

TODO: Add development instructions

## License

MIT
'''
    
    def _generate_env_example(self, project_type: ProjectType) -> str:
        """Generate .env.example content."""
        if project_type.value.startswith('python'):
            return '''# Environment variables
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./app.db
'''
        elif project_type.value.startswith(('javascript', 'typescript')):
            return '''# Environment variables
NODE_ENV=development
PORT=3000
API_URL=http://localhost:3000
'''
        return '# Environment variables\n'
    
    def _generate_gitignore(self, project_type: ProjectType) -> str:
        """Generate .gitignore content."""
        if project_type.value.startswith('python'):
            return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# Testing
.pytest_cache/
.coverage
htmlcov/
'''
        elif project_type.value.startswith(('javascript', 'typescript')):
            return '''# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Production
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local
.env.production

# Testing
coverage/
.nyc_output/
'''
        return '''# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
'''
    
    def _generate_fastapi_main(self) -> str:
        """Generate FastAPI main.py content."""
        return '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    def _generate_flask_init(self) -> str:
        """Generate Flask __init__.py content."""
        return '''from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    @app.route('/')
    def index():
        return {'message': 'Welcome to the API'}
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}
    
    return app
'''
    
    def _generate_flask_run(self) -> str:
        """Generate Flask run.py content."""
        return '''from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    def _generate_python_cli(self, name: str) -> str:
        """Generate Python CLI content."""
        return f'''import click

@click.group()
def cli():
    """
    {name} - A command-line tool
    """
    pass

@cli.command()
@click.option('--name', default='World', help='Name to greet')
def hello(name):
    """Say hello"""
    click.echo(f'Hello, {{name}}!')

if __name__ == '__main__':
    cli()
'''
    
    def _generate_package_json(
        self,
        name: str,
        project_type: ProjectType,
        template: Dict[str, Any]
    ) -> str:
        """Generate package.json content."""
        deps = {dep: "latest" for dep in template.get('dependencies', [])}
        dev_deps = {dep: "latest" for dep in template.get('dev_dependencies', [])}
        
        scripts = {}
        if project_type == ProjectType.JAVASCRIPT_REACT:
            scripts = {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            }
        elif project_type == ProjectType.JAVASCRIPT_EXPRESS:
            scripts = {
                "start": "node src/index.js",
                "dev": "nodemon src/index.js",
                "test": "jest"
            }
        
        package = {
            "name": name,
            "version": "0.1.0",
            "description": f"A {project_type.value} project",
            "main": "src/index.js",
            "scripts": scripts,
            "dependencies": deps,
            "devDependencies": dev_deps,
            "license": "MIT"
        }
        
        return json.dumps(package, indent=2)
    
    def _generate_react_html(self, name: str) -> str:
        """Generate React index.html content."""
        return f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''
    
    def _generate_react_main(self) -> str:
        """Generate React main.jsx content."""
        return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'''
    
    def _generate_react_app(self) -> str:
        """Generate React App.jsx content."""
        return '''import React from 'react'

function App() {
  return (
    <div>
      <h1>Welcome to React</h1>
      <p>Edit src/App.jsx to get started</p>
    </div>
  )
}

export default App
'''
    
    def _generate_vite_config(self) -> str:
        """Generate vite.config.js content."""
        return '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
'''
    
    def _generate_express_main(self) -> str:
        """Generate Express index.js content."""
        return '''const express = require('express')
const cors = require('cors')
require('dotenv').config()

const app = express()
const port = process.env.PORT || 3000

app.use(cors())
app.use(express.json())

app.get('/', (req, res) => {
  res.json({ message: 'Welcome to the API' })
})

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' })
})

app.listen(port, () => {
  console.log(`Server running on port ${port}`)
})
'''
    
    def _generate_express_routes(self) -> str:
        """Generate Express routes content."""
        return '''const express = require('express')
const router = express.Router()

router.get('/', (req, res) => {
  res.json({ message: 'API Routes' })
})

module.exports = router
'''
    
    def _generate_go_mod(self, name: str) -> str:
        """Generate go.mod content."""
        return f'''module {name}

go 1.21

require (
)
'''
    
    def _generate_go_main(self, name: str, project_type: ProjectType) -> str:
        """Generate Go main.go content."""
        if project_type == ProjectType.GO_WEB:
            return '''package main

import (
    "fmt"
    "log"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Welcome to the API")
    })
    
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, `{"status": "healthy"}`)
    })
    
    log.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
'''
        else:
            return '''package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
'''
    
    def _generate_cargo_toml(self, name: str, template: Dict[str, Any]) -> str:
        """Generate Cargo.toml content."""
        deps = template.get('dependencies', [])
        deps_section = "\n".join(f'{dep} = "*"' for dep in deps)
        
        return f'''[package]
name = "{name}"
version = "0.1.0"
edition = "2021"

[dependencies]
{deps_section}
'''
    
    def _generate_rust_main(self, project_type: ProjectType) -> str:
        """Generate Rust main.rs content."""
        if project_type == ProjectType.RUST_WEB:
            return '''use actix_web::{get, App, HttpResponse, HttpServer, Responder};

#[get("/")]
async fn index() -> impl Responder {
    HttpResponse::Ok().body("Welcome to the API")
}

#[get("/health")]
async fn health() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({"status": "healthy"}))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("Server starting on http://127.0.0.1:8080");
    
    HttpServer::new(|| {
        App::new()
            .service(index)
            .service(health)
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
'''
        else:
            return '''fn main() {
    println!("Hello, world!");
}
'''

    # Git integration methods
    
    def initialize_git(self, project_path: Path, create_initial_commit: bool = True) -> bool:
        """
        Initialize git repository in project.
        
        Args:
            project_path: Path to the project directory
            create_initial_commit: Whether to create an initial commit
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize git repository
            result = asyncio.run(self.command_executor.execute_command(
                f"git init",
                cwd=project_path,
                require_approval=False  # Git init is safe
            ))
            
            if not result.success:
                logger.error(f"Failed to initialize git: {result.stderr}")
                return False
            
            logger.info(f"Initialized git repository in {project_path}")
            
            # Create initial commit if requested
            if create_initial_commit:
                return self._create_initial_commit(project_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing git: {e}")
            return False
    
    def _create_initial_commit(self, project_path: Path) -> bool:
        """Create initial git commit."""
        try:
            # Add all files
            result = asyncio.run(self.command_executor.execute_command(
                "git add .",
                cwd=project_path,
                require_approval=False
            ))
            
            if not result.success:
                logger.error(f"Failed to add files to git: {result.stderr}")
                return False
            
            # Create initial commit
            result = asyncio.run(self.command_executor.execute_command(
                'git commit -m "Initial commit"',
                cwd=project_path,
                require_approval=False
            ))
            
            if not result.success:
                logger.error(f"Failed to create initial commit: {result.stderr}")
                return False
            
            logger.info("Created initial git commit")
            return True
            
        except Exception as e:
            logger.error(f"Error creating initial commit: {e}")
            return False
    
    def generate_gitignore(self, project_type: ProjectType, project_path: Path) -> bool:
        """
        Generate .gitignore file for project type.
        
        Args:
            project_type: Type of project
            project_path: Path to the project directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            gitignore_content = self._generate_gitignore(project_type)
            gitignore_path = project_path / '.gitignore'
            
            operation = self.file_creator.create_file(
                path=gitignore_path,
                content=gitignore_content,
                preview=False
            )
            
            logger.info(f"Generated .gitignore for {project_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating .gitignore: {e}")
            return False

    # Dependency installation methods
    
    def detect_package_manager(self, project_path: Path, project_type: ProjectType) -> PackageManager:
        """
        Detect appropriate package manager for project.
        
        Args:
            project_path: Path to the project directory
            project_type: Type of project
            
        Returns:
            Detected PackageManager
        """
        # Check for lock files first
        if (project_path / 'poetry.lock').exists():
            return PackageManager.POETRY
        elif (project_path / 'Pipfile.lock').exists():
            return PackageManager.PIPENV
        elif (project_path / 'yarn.lock').exists():
            return PackageManager.YARN
        elif (project_path / 'pnpm-lock.yaml').exists():
            return PackageManager.PNPM
        elif (project_path / 'package-lock.json').exists():
            return PackageManager.NPM
        elif (project_path / 'Cargo.lock').exists():
            return PackageManager.CARGO
        elif (project_path / 'go.sum').exists():
            return PackageManager.GO_MOD
        
        # Fall back to project type defaults
        template = self.templates.get(project_type, {})
        default_pm = template.get('package_manager')
        
        if default_pm:
            return default_pm
        
        # Final fallback based on language
        if project_type.value.startswith('python'):
            return PackageManager.PIP
        elif project_type.value.startswith(('javascript', 'typescript')):
            return PackageManager.NPM
        elif project_type.value.startswith('go'):
            return PackageManager.GO_MOD
        elif project_type.value.startswith('rust'):
            return PackageManager.CARGO
        
        return PackageManager.PIP
    
    def install_dependencies(
        self,
        project_path: Path,
        package_manager: Optional[PackageManager] = None,
        project_type: Optional[ProjectType] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> InstallResult:
        """
        Install project dependencies.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager to use (auto-detected if None)
            project_type: Type of project (for auto-detection)
            progress_callback: Optional callback for progress updates
            
        Returns:
            InstallResult with installation details
        """
        # Auto-detect package manager if not provided
        if not package_manager and project_type:
            package_manager = self.detect_package_manager(project_path, project_type)
        elif not package_manager:
            # Try to detect from files
            if (project_path / 'requirements.txt').exists():
                package_manager = PackageManager.PIP
            elif (project_path / 'package.json').exists():
                package_manager = PackageManager.NPM
            elif (project_path / 'Cargo.toml').exists():
                package_manager = PackageManager.CARGO
            elif (project_path / 'go.mod').exists():
                package_manager = PackageManager.GO_MOD
            else:
                return InstallResult(
                    success=False,
                    package_manager=PackageManager.PIP,
                    installed_packages=[],
                    failed_packages=[],
                    output="",
                    error_message="Could not detect package manager"
                )
        
        logger.info(f"Installing dependencies using {package_manager.value}")
        
        # Get install command
        install_cmd = self._get_install_command(package_manager)
        
        if not install_cmd:
            return InstallResult(
                success=False,
                package_manager=package_manager,
                installed_packages=[],
                failed_packages=[],
                output="",
                error_message=f"Unsupported package manager: {package_manager.value}"
            )
        
        # Execute installation
        try:
            if progress_callback:
                progress_callback(f"Installing dependencies with {package_manager.value}...")
            
            result = asyncio.run(self.command_executor.execute_command(
                install_cmd,
                cwd=project_path,
                require_approval=True  # Installation requires approval
            ))
            
            if progress_callback:
                progress_callback("Installation complete" if result.success else "Installation failed")
            
            # Parse installed packages from output
            installed_packages = self._parse_installed_packages(
                result.stdout,
                package_manager
            )
            
            return InstallResult(
                success=result.success,
                package_manager=package_manager,
                installed_packages=installed_packages,
                failed_packages=[],
                output=result.stdout,
                error_message=result.stderr if not result.success else None
            )
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return InstallResult(
                success=False,
                package_manager=package_manager,
                installed_packages=[],
                failed_packages=[],
                output="",
                error_message=str(e)
            )
    
    def _get_install_command(self, package_manager: PackageManager) -> Optional[str]:
        """Get installation command for package manager."""
        commands = {
            PackageManager.PIP: "pip install -r requirements.txt",
            PackageManager.POETRY: "poetry install",
            PackageManager.PIPENV: "pipenv install",
            PackageManager.NPM: "npm install",
            PackageManager.YARN: "yarn install",
            PackageManager.PNPM: "pnpm install",
            PackageManager.CARGO: "cargo build",
            PackageManager.GO_MOD: "go mod download",
        }
        return commands.get(package_manager)
    
    def _parse_installed_packages(
        self,
        output: str,
        package_manager: PackageManager
    ) -> List[str]:
        """Parse installed packages from command output."""
        packages = []
        
        if package_manager in [PackageManager.PIP, PackageManager.POETRY, PackageManager.PIPENV]:
            # Look for "Successfully installed" lines
            for line in output.split('\n'):
                if 'Successfully installed' in line:
                    # Extract package names
                    parts = line.split('Successfully installed')[1].strip().split()
                    packages.extend(parts)
        
        elif package_manager in [PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM]:
            # Look for "added" or "installed" lines
            for line in output.split('\n'):
                if 'added' in line.lower() or 'installed' in line.lower():
                    # Try to extract package count
                    match = re.search(r'(\d+)\s+package', line)
                    if match:
                        count = match.group(1)
                        packages.append(f"{count} packages")
                        break
        
        return packages
    
    def create_project_with_git_and_deps(
        self,
        project_type: str,
        name: str,
        options: Optional[Dict[str, Any]] = None,
        initialize_git: bool = True,
        install_deps: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Project:
        """
        Create a complete project with git and dependencies.
        
        This is a convenience method that combines project creation,
        git initialization, and dependency installation.
        
        Args:
            project_type: Type of project
            name: Name of the project
            options: Additional options
            initialize_git: Whether to initialize git
            install_deps: Whether to install dependencies
            progress_callback: Optional callback for progress updates
            
        Returns:
            Created Project object
        """
        if progress_callback:
            progress_callback("Creating project structure...")
        
        # Create project
        project = self.create_project(project_type, name, options)
        
        # Initialize git if requested
        if initialize_git:
            if progress_callback:
                progress_callback("Initializing git repository...")
            
            # Generate .gitignore first
            self.generate_gitignore(project.project_type, project.path)
            
            # Initialize git
            git_success = self.initialize_git(project.path, create_initial_commit=True)
            project.git_initialized = git_success
            
            if git_success:
                logger.info("Git repository initialized successfully")
            else:
                logger.warning("Failed to initialize git repository")
        
        # Install dependencies if requested
        if install_deps:
            if progress_callback:
                progress_callback("Installing dependencies...")
            
            install_result = self.install_dependencies(
                project.path,
                project_type=project.project_type,
                progress_callback=progress_callback
            )
            
            project.dependencies_installed = install_result.success
            
            if install_result.success:
                logger.info(f"Dependencies installed: {', '.join(install_result.installed_packages)}")
            else:
                logger.warning(f"Failed to install dependencies: {install_result.error_message}")
        
        if progress_callback:
            progress_callback("Project creation complete!")
        
        return project
