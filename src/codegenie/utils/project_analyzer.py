"""
Advanced project understanding and analysis capabilities.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    """Advanced project analysis and understanding system."""
    
    def __init__(self):
        self.project_patterns = {
            "web_app": {
                "indicators": ["package.json", "requirements.txt", "app.py", "main.py", "index.html"],
                "frameworks": {
                    "react": ["package.json", "src/", "public/"],
                    "vue": ["vue.config.js", "src/", "public/"],
                    "angular": ["angular.json", "src/", "package.json"],
                    "django": ["manage.py", "settings.py", "urls.py"],
                    "flask": ["app.py", "requirements.txt"],
                    "fastapi": ["main.py", "requirements.txt"],
                    "express": ["package.json", "app.js", "server.js"],
                }
            },
            "cli_tool": {
                "indicators": ["setup.py", "pyproject.toml", "main.py", "cli.py"],
                "frameworks": {
                    "click": ["click", "cli"],
                    "typer": ["typer"],
                    "argparse": ["argparse"],
                }
            },
            "library": {
                "indicators": ["setup.py", "pyproject.toml", "__init__.py", "src/"],
                "frameworks": {
                    "setuptools": ["setup.py"],
                    "poetry": ["pyproject.toml"],
                    "pipenv": ["Pipfile"],
                }
            },
            "data_science": {
                "indicators": ["jupyter", "notebooks/", "requirements.txt", "environment.yml"],
                "frameworks": {
                    "jupyter": ["jupyter", "notebooks/"],
                    "pandas": ["pandas"],
                    "numpy": ["numpy"],
                    "tensorflow": ["tensorflow"],
                    "pytorch": ["torch"],
                    "scikit-learn": ["sklearn"],
                }
            },
            "mobile_app": {
                "indicators": ["android/", "ios/", "pubspec.yaml", "package.json"],
                "frameworks": {
                    "react_native": ["react-native", "package.json"],
                    "flutter": ["pubspec.yaml", "lib/"],
                    "ionic": ["ionic", "package.json"],
                }
            },
            "devops": {
                "indicators": ["Dockerfile", "docker-compose.yml", ".github/", "Jenkinsfile"],
                "frameworks": {
                    "docker": ["Dockerfile", "docker-compose.yml"],
                    "kubernetes": ["k8s/", "deployment.yaml"],
                    "github_actions": [".github/workflows/"],
                    "jenkins": ["Jenkinsfile"],
                }
            }
        }
        
        self.architecture_patterns = {
            "mvc": ["models/", "views/", "controllers/"],
            "mvp": ["models/", "views/", "presenters/"],
            "mvvm": ["models/", "views/", "viewmodels/"],
            "microservices": ["services/", "api/", "gateway/"],
            "monolith": ["src/", "app/", "lib/"],
            "layered": ["data/", "business/", "presentation/"],
            "hexagonal": ["domain/", "infrastructure/", "application/"],
        }
        
        self.quality_indicators = {
            "testing": {
                "test_files": ["test_", "_test.py", ".test.js", ".spec.js", "tests/", "__tests__/"],
                "coverage": ["coverage/", ".coverage", "coverage.xml"],
                "frameworks": ["pytest", "jest", "mocha", "jasmine", "unittest", "vitest"]
            },
            "documentation": {
                "files": ["README.md", "docs/", "documentation/", "api.md", "CHANGELOG.md"],
                "code_docs": ["docstrings", "jsdoc", "javadoc", "godoc"]
            },
            "code_quality": {
                "linters": [".eslintrc", ".pylintrc", "flake8", "black", "prettier"],
                "formatters": ["black", "prettier", "gofmt", "rustfmt"],
                "type_checkers": ["mypy", "typescript", "pyright"]
            },
            "ci_cd": {
                "files": [".github/workflows/", ".gitlab-ci.yml", "Jenkinsfile", ".travis.yml"],
                "tools": ["github_actions", "gitlab_ci", "jenkins", "travis", "circleci"]
            }
        }
    
    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Perform comprehensive project analysis."""
        
        logger.info(f"Analyzing project: {project_path}")
        
        analysis = {
            "project_path": str(project_path),
            "project_type": self._detect_project_type(project_path),
            "architecture": self._detect_architecture(project_path),
            "frameworks": self._detect_frameworks(project_path),
            "languages": self._detect_languages(project_path),
            "dependencies": self._analyze_dependencies(project_path),
            "structure": self._analyze_structure(project_path),
            "quality": self._assess_quality(project_path),
            "complexity": self._assess_complexity(project_path),
            "patterns": self._detect_patterns(project_path),
            "recommendations": [],
            "statistics": self._calculate_statistics(project_path),
        }
        
        # Generate recommendations based on analysis
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _detect_project_type(self, project_path: Path) -> str:
        """Detect the type of project."""
        
        files = [f.name for f in project_path.rglob("*") if f.is_file()]
        
        for project_type, config in self.project_patterns.items():
            indicators = config["indicators"]
            if any(indicator in files for indicator in indicators):
                return project_type
        
        return "unknown"
    
    def _detect_architecture(self, project_path: Path) -> List[str]:
        """Detect architectural patterns."""
        
        directories = [d.name for d in project_path.rglob("*") if d.is_dir()]
        detected_patterns = []
        
        for pattern, indicators in self.architecture_patterns.items():
            if any(indicator in directories for indicator in indicators):
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    def _detect_frameworks(self, project_path: Path) -> Dict[str, List[str]]:
        """Detect frameworks and libraries used."""
        
        frameworks = {}
        
        for project_type, config in self.project_patterns.items():
            if project_type == self._detect_project_type(project_path):
                for framework, indicators in config["frameworks"].items():
                    if self._check_framework_indicators(project_path, indicators):
                        if project_type not in frameworks:
                            frameworks[project_type] = []
                        frameworks[project_type].append(framework)
        
        return frameworks
    
    def _check_framework_indicators(self, project_path: Path, indicators: List[str]) -> bool:
        """Check if framework indicators are present."""
        
        files = [f.name for f in project_path.rglob("*") if f.is_file()]
        directories = [d.name for d in project_path.rglob("*") if d.is_dir()]
        
        for indicator in indicators:
            if indicator in files or indicator in directories:
                return True
        
        # Check in file contents for package names
        for file_path in project_path.rglob("*.json"):
            if file_path.name in ["package.json", "requirements.txt", "pyproject.toml"]:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if any(indicator in content for indicator in indicators):
                        return True
                except Exception:
                    continue
        
        return False
    
    def _detect_languages(self, project_path: Path) -> Dict[str, int]:
        """Detect programming languages and file counts."""
        
        language_extensions = {
            'python': ['.py', '.pyi', '.pyc'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'cpp': ['.cpp', '.c', '.h', '.hpp'],
            'csharp': ['.cs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'swift': ['.swift'],
            'kotlin': ['.kt'],
            'html': ['.html', '.htm'],
            'css': ['.css', '.scss', '.sass'],
            'json': ['.json'],
            'yaml': ['.yaml', '.yml'],
            'markdown': ['.md'],
            'shell': ['.sh', '.bash', '.zsh'],
        }
        
        language_counts = {}
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                for language, extensions in language_extensions.items():
                    if suffix in extensions:
                        language_counts[language] = language_counts.get(language, 0) + 1
                        break
        
        return language_counts
    
    def _analyze_dependencies(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project dependencies."""
        
        dependencies = {
            "direct": {},
            "dev": {},
            "peer": {},
            "total_count": 0,
            "vulnerabilities": [],
            "outdated": [],
        }
        
        # Analyze package.json
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                dependencies["direct"] = data.get("dependencies", {})
                dependencies["dev"] = data.get("devDependencies", {})
                dependencies["peer"] = data.get("peerDependencies", {})
                dependencies["total_count"] = len(dependencies["direct"]) + len(dependencies["dev"])
                
            except Exception as e:
                logger.warning(f"Error reading package.json: {e}")
        
        # Analyze requirements.txt
        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            try:
                with open(requirements_txt, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                python_deps = {}
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package name and version
                        if '==' in line:
                            name, version = line.split('==', 1)
                            python_deps[name] = version
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                            python_deps[name] = f">={version}"
                        else:
                            python_deps[line] = "latest"
                
                dependencies["direct"].update(python_deps)
                dependencies["total_count"] += len(python_deps)
                
            except Exception as e:
                logger.warning(f"Error reading requirements.txt: {e}")
        
        return dependencies
    
    def _analyze_structure(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project structure and organization."""
        
        structure = {
            "directories": [],
            "files": [],
            "depth": 0,
            "organization_score": 0.0,
            "naming_conventions": {},
        }
        
        # Analyze directory structure
        for item in project_path.rglob("*"):
            if item.is_dir():
                structure["directories"].append(str(item.relative_to(project_path)))
            else:
                structure["files"].append(str(item.relative_to(project_path)))
        
        # Calculate depth
        structure["depth"] = max(
            len(Path(p).parts) for p in structure["directories"]
        ) if structure["directories"] else 0
        
        # Assess organization
        structure["organization_score"] = self._calculate_organization_score(structure)
        
        # Analyze naming conventions
        structure["naming_conventions"] = self._analyze_naming_conventions(structure["files"])
        
        return structure
    
    def _calculate_organization_score(self, structure: Dict[str, Any]) -> float:
        """Calculate project organization score."""
        
        score = 0.0
        files = structure["files"]
        directories = structure["directories"]
        
        # Check for common good practices
        if any("src/" in d for d in directories):
            score += 0.2
        if any("tests/" in d or "test/" in d for d in directories):
            score += 0.2
        if any("docs/" in d for d in directories):
            score += 0.1
        if any("config/" in d for d in directories):
            score += 0.1
        
        # Check for proper file organization
        if any(f.endswith('.py') for f in files):
            if any("__init__.py" in f for f in files):
                score += 0.1
        
        # Check for configuration files in root
        config_files = ["README.md", "LICENSE", ".gitignore", "requirements.txt", "package.json"]
        if any(any(cf in f for f in files) for cf in config_files):
            score += 0.1
        
        # Check for proper separation of concerns
        if len(directories) > 3:  # Good separation
            score += 0.1
        
        return min(score, 1.0)
    
    def _analyze_naming_conventions(self, files: List[str]) -> Dict[str, Any]:
        """Analyze naming conventions used in the project."""
        
        conventions = {
            "snake_case": 0,
            "camelCase": 0,
            "PascalCase": 0,
            "kebab-case": 0,
            "UPPER_CASE": 0,
        }
        
        for file_path in files:
            filename = Path(file_path).name
            
            if '_' in filename:
                conventions["snake_case"] += 1
            elif filename[0].isupper():
                conventions["PascalCase"] += 1
            elif '-' in filename:
                conventions["kebab-case"] += 1
            elif filename.isupper():
                conventions["UPPER_CASE"] += 1
            else:
                conventions["camelCase"] += 1
        
        return conventions
    
    def _assess_quality(self, project_path: Path) -> Dict[str, Any]:
        """Assess code quality indicators."""
        
        quality = {
            "testing": self._assess_testing(project_path),
            "documentation": self._assess_documentation(project_path),
            "code_quality": self._assess_code_quality(project_path),
            "ci_cd": self._assess_ci_cd(project_path),
            "overall_score": 0.0,
        }
        
        # Calculate overall quality score
        scores = [quality[key]["score"] for key in quality if isinstance(quality[key], dict) and "score" in quality[key]]
        quality["overall_score"] = sum(scores) / len(scores) if scores else 0.0
        
        return quality
    
    def _assess_testing(self, project_path: Path) -> Dict[str, Any]:
        """Assess testing setup and coverage."""
        
        testing = {
            "score": 0.0,
            "frameworks": [],
            "test_files": [],
            "coverage": False,
            "recommendations": [],
        }
        
        files = [f.name for f in project_path.rglob("*") if f.is_file()]
        directories = [d.name for d in project_path.rglob("*") if d.is_dir()]
        
        # Check for test frameworks
        for framework in self.quality_indicators["testing"]["frameworks"]:
            if framework in str(project_path):
                testing["frameworks"].append(framework)
                testing["score"] += 0.3
        
        # Check for test files
        test_files = [f for f in files if any(pattern in f for pattern in self.quality_indicators["testing"]["test_files"])]
        testing["test_files"] = test_files
        if test_files:
            testing["score"] += 0.4
        
        # Check for test directories
        if any("test" in d.lower() for d in directories):
            testing["score"] += 0.2
        
        # Check for coverage
        if any(pattern in str(project_path) for pattern in self.quality_indicators["testing"]["coverage"]):
            testing["coverage"] = True
            testing["score"] += 0.1
        
        # Generate recommendations
        if not testing["frameworks"]:
            testing["recommendations"].append("Add a testing framework (pytest, jest, etc.)")
        if not testing["test_files"]:
            testing["recommendations"].append("Create test files for your code")
        if not testing["coverage"]:
            testing["recommendations"].append("Set up code coverage reporting")
        
        return testing
    
    def _assess_documentation(self, project_path: Path) -> Dict[str, Any]:
        """Assess documentation quality."""
        
        documentation = {
            "score": 0.0,
            "files": [],
            "code_docs": False,
            "recommendations": [],
        }
        
        files = [f.name for f in project_path.rglob("*") if f.is_file()]
        
        # Check for documentation files
        doc_files = [f for f in files if any(pattern in f for pattern in self.quality_indicators["documentation"]["files"])]
        documentation["files"] = doc_files
        
        if "README.md" in files:
            documentation["score"] += 0.4
        if any("docs/" in f for f in files):
            documentation["score"] += 0.3
        if any("CHANGELOG" in f for f in files):
            documentation["score"] += 0.2
        if any("LICENSE" in f for f in files):
            documentation["score"] += 0.1
        
        # Check for code documentation
        # This would require analyzing actual code files for docstrings, comments, etc.
        documentation["code_docs"] = True  # Simplified for now
        
        # Generate recommendations
        if "README.md" not in files:
            documentation["recommendations"].append("Create a README.md file")
        if not any("docs/" in f for f in files):
            documentation["recommendations"].append("Create a docs/ directory")
        if not any("LICENSE" in f for f in files):
            documentation["recommendations"].append("Add a LICENSE file")
        
        return documentation
    
    def _assess_code_quality(self, project_path: Path) -> Dict[str, Any]:
        """Assess code quality tools and practices."""
        
        code_quality = {
            "score": 0.0,
            "linters": [],
            "formatters": [],
            "type_checkers": [],
            "recommendations": [],
        }
        
        files = [f.name for f in project_path.rglob("*") if f.is_file()]
        
        # Check for linters
        for linter in self.quality_indicators["code_quality"]["linters"]:
            if linter in str(project_path):
                code_quality["linters"].append(linter)
                code_quality["score"] += 0.2
        
        # Check for formatters
        for formatter in self.quality_indicators["code_quality"]["formatters"]:
            if formatter in str(project_path):
                code_quality["formatters"].append(formatter)
                code_quality["score"] += 0.2
        
        # Check for type checkers
        for type_checker in self.quality_indicators["code_quality"]["type_checkers"]:
            if type_checker in str(project_path):
                code_quality["type_checkers"].append(type_checker)
                code_quality["score"] += 0.2
        
        # Check for pre-commit hooks
        if ".pre-commit-config.yaml" in files:
            code_quality["score"] += 0.2
        
        # Generate recommendations
        if not code_quality["linters"]:
            code_quality["recommendations"].append("Add a linter (eslint, pylint, etc.)")
        if not code_quality["formatters"]:
            code_quality["recommendations"].append("Add a code formatter (prettier, black, etc.)")
        if not code_quality["type_checkers"]:
            code_quality["recommendations"].append("Add type checking (mypy, typescript, etc.)")
        
        return code_quality
    
    def _assess_ci_cd(self, project_path: Path) -> Dict[str, Any]:
        """Assess CI/CD setup."""
        
        ci_cd = {
            "score": 0.0,
            "tools": [],
            "files": [],
            "recommendations": [],
        }
        
        files = [f.name for f in project_path.rglob("*") if f.is_file()]
        directories = [d.name for d in project_path.rglob("*") if d.is_dir()]
        
        # Check for CI/CD files
        ci_files = [f for f in files if any(pattern in f for pattern in self.quality_indicators["ci_cd"]["files"])]
        ci_cd["files"] = ci_files
        
        if ci_files:
            ci_cd["score"] += 0.5
        
        # Check for specific tools
        if ".github/workflows/" in str(project_path):
            ci_cd["tools"].append("github_actions")
            ci_cd["score"] += 0.3
        if ".gitlab-ci.yml" in files:
            ci_cd["tools"].append("gitlab_ci")
            ci_cd["score"] += 0.3
        if "Jenkinsfile" in files:
            ci_cd["tools"].append("jenkins")
            ci_cd["score"] += 0.3
        
        # Generate recommendations
        if not ci_cd["files"]:
            ci_cd["recommendations"].append("Set up CI/CD pipeline")
        
        return ci_cd
    
    def _assess_complexity(self, project_path: Path) -> Dict[str, Any]:
        """Assess project complexity."""
        
        complexity = {
            "score": 0.0,
            "factors": [],
            "cyclomatic_complexity": 0,
            "maintainability_index": 0.0,
        }
        
        # Count files and lines
        total_files = 0
        total_lines = 0
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.java', '.go', '.rs']:
                total_files += 1
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                        total_lines += lines
                except Exception:
                    continue
        
        # Calculate complexity factors
        if total_files > 100:
            complexity["factors"].append("Large number of files")
            complexity["score"] += 0.3
        elif total_files > 50:
            complexity["factors"].append("Medium number of files")
            complexity["score"] += 0.2
        
        if total_lines > 10000:
            complexity["factors"].append("Large codebase")
            complexity["score"] += 0.3
        elif total_lines > 5000:
            complexity["factors"].append("Medium codebase")
            complexity["score"] += 0.2
        
        # Check for nested directories
        max_depth = max(len(Path(p).parts) for p in [str(f) for f in project_path.rglob("*") if f.is_file()])
        if max_depth > 5:
            complexity["factors"].append("Deep directory structure")
            complexity["score"] += 0.2
        
        return complexity
    
    def _detect_patterns(self, project_path: Path) -> Dict[str, Any]:
        """Detect common patterns and anti-patterns."""
        
        patterns = {
            "good_patterns": [],
            "anti_patterns": [],
            "design_patterns": [],
        }
        
        # Check for good patterns
        files = [f.name for f in project_path.rglob("*") if f.is_file()]
        
        if "README.md" in files:
            patterns["good_patterns"].append("Has README documentation")
        if any("test" in f for f in files):
            patterns["good_patterns"].append("Has test files")
        if ".gitignore" in files:
            patterns["good_patterns"].append("Has .gitignore")
        if "LICENSE" in files:
            patterns["good_patterns"].append("Has LICENSE file")
        
        # Check for anti-patterns
        if any("node_modules" in str(f) for f in project_path.rglob("*")):
            patterns["anti_patterns"].append("node_modules committed to repository")
        if any("__pycache__" in str(f) for f in project_path.rglob("*")):
            patterns["anti_patterns"].append("__pycache__ committed to repository")
        
        return patterns
    
    def _calculate_statistics(self, project_path: Path) -> Dict[str, Any]:
        """Calculate project statistics."""
        
        stats = {
            "total_files": 0,
            "total_directories": 0,
            "total_lines": 0,
            "total_size": 0,
            "file_types": {},
            "largest_files": [],
        }
        
        file_sizes = []
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                stats["total_files"] += 1
                stats["total_size"] += file_path.stat().st_size
                
                # Count by file type
                suffix = file_path.suffix.lower()
                stats["file_types"][suffix] = stats["file_types"].get(suffix, 0) + 1
                
                # Count lines for text files
                if suffix in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.md', '.txt']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = len(f.readlines())
                            stats["total_lines"] += lines
                    except Exception:
                        continue
                
                # Track largest files
                file_sizes.append((file_path, file_path.stat().st_size))
            
            elif file_path.is_dir():
                stats["total_directories"] += 1
        
        # Get largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        stats["largest_files"] = [
            {"path": str(f[0]), "size": f[1]} 
            for f in file_sizes[:10]
        ]
        
        return stats
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis."""
        
        recommendations = []
        
        # Quality recommendations
        quality = analysis.get("quality", {})
        
        if quality.get("testing", {}).get("score", 0) < 0.5:
            recommendations.append("Improve testing coverage and setup")
        
        if quality.get("documentation", {}).get("score", 0) < 0.5:
            recommendations.append("Enhance documentation")
        
        if quality.get("code_quality", {}).get("score", 0) < 0.5:
            recommendations.append("Add code quality tools (linters, formatters)")
        
        if quality.get("ci_cd", {}).get("score", 0) < 0.5:
            recommendations.append("Set up CI/CD pipeline")
        
        # Structure recommendations
        structure = analysis.get("structure", {})
        if structure.get("organization_score", 0) < 0.5:
            recommendations.append("Improve project organization and structure")
        
        # Complexity recommendations
        complexity = analysis.get("complexity", {})
        if complexity.get("score", 0) > 0.7:
            recommendations.append("Consider refactoring to reduce complexity")
        
        # Pattern recommendations
        patterns = analysis.get("patterns", {})
        if patterns.get("anti_patterns"):
            recommendations.append("Address anti-patterns in the codebase")
        
        return recommendations
