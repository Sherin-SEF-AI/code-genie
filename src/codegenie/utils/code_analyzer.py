"""
Code analysis utilities for understanding and manipulating code.
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes code structure, dependencies, and patterns."""
    
    def __init__(self):
        self.supported_languages = {
            '.py': self._analyze_python,
            '.js': self._analyze_javascript,
            '.ts': self._analyze_typescript,
            '.jsx': self._analyze_javascript,
            '.tsx': self._analyze_typescript,
            '.go': self._analyze_go,
            '.rs': self._analyze_rust,
            '.java': self._analyze_java,
            '.cpp': self._analyze_cpp,
            '.c': self._analyze_cpp,
            '.h': self._analyze_cpp,
            '.hpp': self._analyze_cpp,
        }
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file and return its structure."""
        
        if not file_path.exists():
            return {"error": "File does not exist"}
        
        suffix = file_path.suffix.lower()
        if suffix not in self.supported_languages:
            return {"error": f"Unsupported file type: {suffix}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analyzer_func = self.supported_languages[suffix]
            analysis = analyzer_func(content, file_path)
            
            # Add common metadata
            analysis.update({
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "language": self._get_language_from_extension(suffix),
                "line_count": len(content.splitlines()),
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {"error": str(e)}
    
    def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze an entire project and return its structure."""
        
        if not project_path.exists() or not project_path.is_dir():
            return {"error": "Project path does not exist or is not a directory"}
        
        analysis = {
            "project_path": str(project_path),
            "files": {},
            "languages": set(),
            "dependencies": set(),
            "frameworks": set(),
            "patterns": {},
            "statistics": {
                "total_files": 0,
                "total_lines": 0,
                "total_size": 0,
            }
        }
        
        # Analyze all supported files
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_languages:
                file_analysis = self.analyze_file(file_path)
                
                if "error" not in file_analysis:
                    analysis["files"][str(file_path)] = file_analysis
                    analysis["languages"].add(file_analysis["language"])
                    analysis["statistics"]["total_files"] += 1
                    analysis["statistics"]["total_lines"] += file_analysis["line_count"]
                    analysis["statistics"]["total_size"] += file_analysis["file_size"]
                    
                    # Collect dependencies and frameworks
                    if "dependencies" in file_analysis:
                        analysis["dependencies"].update(file_analysis["dependencies"])
                    if "frameworks" in file_analysis:
                        analysis["frameworks"].update(file_analysis["frameworks"])
        
        # Convert sets to lists for JSON serialization
        analysis["languages"] = list(analysis["languages"])
        analysis["dependencies"] = list(analysis["dependencies"])
        analysis["frameworks"] = list(analysis["frameworks"])
        
        return analysis
    
    def _analyze_python(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze Python code."""
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {"error": f"Syntax error: {e}"}
        
        analysis = {
            "functions": [],
            "classes": [],
            "imports": [],
            "dependencies": set(),
            "frameworks": set(),
            "complexity": 0,
        }
        
        # Analyze AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis["functions"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list],
                })
            
            elif isinstance(node, ast.ClassDef):
                analysis["classes"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [base.id if hasattr(base, 'id') else str(base) for base in node.bases],
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                })
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append({
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                        })
                        analysis["dependencies"].add(alias.name.split('.')[0])
                else:
                    module = node.module or ""
                    for alias in node.names:
                        analysis["imports"].append({
                            "module": module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                        })
                        if module:
                            analysis["dependencies"].add(module.split('.')[0])
        
        # Detect frameworks
        for dep in analysis["dependencies"]:
            if dep in ["django", "flask", "fastapi", "tornado"]:
                analysis["frameworks"].add(dep)
            elif dep in ["pytest", "unittest", "nose"]:
                analysis["frameworks"].add("testing")
        
        # Calculate complexity (simple metric)
        analysis["complexity"] = len(analysis["functions"]) + len(analysis["classes"]) * 2
        
        # Convert set to list
        analysis["dependencies"] = list(analysis["dependencies"])
        analysis["frameworks"] = list(analysis["frameworks"])
        
        return analysis
    
    def _analyze_javascript(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze JavaScript/JSX code."""
        
        analysis = {
            "functions": [],
            "classes": [],
            "imports": [],
            "dependencies": set(),
            "frameworks": set(),
            "complexity": 0,
        }
        
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Extract imports
            if line.startswith(('import ', 'const ', 'let ', 'var ')) and 'from' in line:
                match = re.search(r'from\s+[\'"]([^\'"]+)[\'"]', line)
                if match:
                    module = match.group(1)
                    analysis["imports"].append({
                        "module": module,
                        "line": i,
                    })
                    analysis["dependencies"].add(module.split('/')[0])
            
            # Extract function declarations
            if re.match(r'^(function|const|let|var)\s+\w+.*=>', line) or re.match(r'^function\s+\w+', line):
                func_match = re.search(r'(?:function\s+)?(\w+)', line)
                if func_match:
                    analysis["functions"].append({
                        "name": func_match.group(1),
                        "line": i,
                    })
            
            # Extract class declarations
            if re.match(r'^class\s+\w+', line):
                class_match = re.search(r'class\s+(\w+)', line)
                if class_match:
                    analysis["classes"].append({
                        "name": class_match.group(1),
                        "line": i,
                    })
        
        # Detect frameworks
        for dep in analysis["dependencies"]:
            if dep in ["react", "vue", "angular", "svelte"]:
                analysis["frameworks"].add(dep)
            elif dep in ["express", "koa", "fastify"]:
                analysis["frameworks"].add("backend")
            elif dep in ["jest", "mocha", "jasmine"]:
                analysis["frameworks"].add("testing")
        
        analysis["complexity"] = len(analysis["functions"]) + len(analysis["classes"]) * 2
        analysis["dependencies"] = list(analysis["dependencies"])
        analysis["frameworks"] = list(analysis["frameworks"])
        
        return analysis
    
    def _analyze_typescript(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze TypeScript/TSX code."""
        
        # For now, use JavaScript analysis (TypeScript is a superset)
        analysis = self._analyze_javascript(content, file_path)
        analysis["language"] = "typescript"
        
        # Add TypeScript-specific analysis
        analysis["interfaces"] = []
        analysis["types"] = []
        
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Extract interface declarations
            if re.match(r'^interface\s+\w+', line):
                interface_match = re.search(r'interface\s+(\w+)', line)
                if interface_match:
                    analysis["interfaces"].append({
                        "name": interface_match.group(1),
                        "line": i,
                    })
            
            # Extract type declarations
            if re.match(r'^type\s+\w+', line):
                type_match = re.search(r'type\s+(\w+)', line)
                if type_match:
                    analysis["types"].append({
                        "name": type_match.group(1),
                        "line": i,
                    })
        
        return analysis
    
    def _analyze_go(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze Go code."""
        
        analysis = {
            "functions": [],
            "structs": [],
            "imports": [],
            "dependencies": set(),
            "packages": set(),
            "complexity": 0,
        }
        
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Extract imports
            if line.startswith('import '):
                if '"' in line:
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        module = match.group(1)
                        analysis["imports"].append({
                            "module": module,
                            "line": i,
                        })
                        analysis["dependencies"].add(module.split('/')[0])
            
            # Extract function declarations
            if re.match(r'^func\s+', line):
                func_match = re.search(r'func\s+(\w+)', line)
                if func_match:
                    analysis["functions"].append({
                        "name": func_match.group(1),
                        "line": i,
                    })
            
            # Extract struct declarations
            if re.match(r'^type\s+\w+\s+struct', line):
                struct_match = re.search(r'type\s+(\w+)\s+struct', line)
                if struct_match:
                    analysis["structs"].append({
                        "name": struct_match.group(1),
                        "line": i,
                    })
        
        analysis["complexity"] = len(analysis["functions"]) + len(analysis["structs"]) * 2
        analysis["dependencies"] = list(analysis["dependencies"])
        analysis["packages"] = list(analysis["packages"])
        
        return analysis
    
    def _analyze_rust(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze Rust code."""
        
        analysis = {
            "functions": [],
            "structs": [],
            "enums": [],
            "imports": [],
            "dependencies": set(),
            "complexity": 0,
        }
        
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Extract imports
            if line.startswith('use '):
                if '::' in line:
                    module = line.split('::')[0].replace('use ', '').strip()
                    analysis["imports"].append({
                        "module": module,
                        "line": i,
                    })
                    analysis["dependencies"].add(module)
            
            # Extract function declarations
            if re.match(r'^(pub\s+)?fn\s+', line):
                func_match = re.search(r'fn\s+(\w+)', line)
                if func_match:
                    analysis["functions"].append({
                        "name": func_match.group(1),
                        "line": i,
                    })
            
            # Extract struct declarations
            if re.match(r'^(pub\s+)?struct\s+', line):
                struct_match = re.search(r'struct\s+(\w+)', line)
                if struct_match:
                    analysis["structs"].append({
                        "name": struct_match.group(1),
                        "line": i,
                    })
            
            # Extract enum declarations
            if re.match(r'^(pub\s+)?enum\s+', line):
                enum_match = re.search(r'enum\s+(\w+)', line)
                if enum_match:
                    analysis["enums"].append({
                        "name": enum_match.group(1),
                        "line": i,
                    })
        
        analysis["complexity"] = len(analysis["functions"]) + len(analysis["structs"]) * 2 + len(analysis["enums"]) * 2
        analysis["dependencies"] = list(analysis["dependencies"])
        
        return analysis
    
    def _analyze_java(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze Java code."""
        
        analysis = {
            "classes": [],
            "methods": [],
            "imports": [],
            "dependencies": set(),
            "packages": set(),
            "complexity": 0,
        }
        
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Extract imports
            if line.startswith('import '):
                match = re.search(r'import\s+([^;]+);', line)
                if match:
                    module = match.group(1)
                    analysis["imports"].append({
                        "module": module,
                        "line": i,
                    })
                    analysis["dependencies"].add(module.split('.')[0])
            
            # Extract class declarations
            if re.match(r'^(public\s+|private\s+|protected\s+)?class\s+', line):
                class_match = re.search(r'class\s+(\w+)', line)
                if class_match:
                    analysis["classes"].append({
                        "name": class_match.group(1),
                        "line": i,
                    })
            
            # Extract method declarations
            if re.match(r'^(public\s+|private\s+|protected\s+)?(static\s+)?\w+\s+\w+\s*\(', line):
                method_match = re.search(r'(\w+)\s*\(', line)
                if method_match:
                    analysis["methods"].append({
                        "name": method_match.group(1),
                        "line": i,
                    })
        
        analysis["complexity"] = len(analysis["classes"]) * 3 + len(analysis["methods"])
        analysis["dependencies"] = list(analysis["dependencies"])
        analysis["packages"] = list(analysis["packages"])
        
        return analysis
    
    def _analyze_cpp(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze C/C++ code."""
        
        analysis = {
            "functions": [],
            "classes": [],
            "includes": [],
            "dependencies": set(),
            "complexity": 0,
        }
        
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Extract includes
            if line.startswith('#include'):
                match = re.search(r'#include\s*[<"]([^>"]+)[>"]', line)
                if match:
                    header = match.group(1)
                    analysis["includes"].append({
                        "header": header,
                        "line": i,
                    })
                    analysis["dependencies"].add(header.split('/')[0])
            
            # Extract function declarations
            if re.match(r'^\w+.*\s+\w+\s*\(', line) and not line.endswith(';'):
                func_match = re.search(r'(\w+)\s*\(', line)
                if func_match:
                    analysis["functions"].append({
                        "name": func_match.group(1),
                        "line": i,
                    })
            
            # Extract class declarations
            if re.match(r'^(class|struct)\s+\w+', line):
                class_match = re.search(r'(?:class|struct)\s+(\w+)', line)
                if class_match:
                    analysis["classes"].append({
                        "name": class_match.group(1),
                        "line": i,
                    })
        
        analysis["complexity"] = len(analysis["functions"]) + len(analysis["classes"]) * 2
        analysis["dependencies"] = list(analysis["dependencies"])
        
        return analysis
    
    def _get_language_from_extension(self, extension: str) -> str:
        """Get language name from file extension."""
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
        }
        
        return language_map.get(extension, 'unknown')
    
    def find_code_patterns(self, content: str, language: str) -> Dict[str, List[Dict[str, Any]]]:
        """Find common code patterns in the content."""
        
        patterns = {
            "functions": [],
            "classes": [],
            "imports": [],
            "comments": [],
            "todos": [],
            "errors": [],
        }
        
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Find TODO comments
            if 'TODO' in line_stripped.upper() or 'FIXME' in line_stripped.upper():
                patterns["todos"].append({
                    "line": i,
                    "content": line_stripped,
                })
            
            # Find error handling
            if any(keyword in line_stripped.lower() for keyword in ['error', 'exception', 'catch', 'throw']):
                patterns["errors"].append({
                    "line": i,
                    "content": line_stripped,
                })
        
        return patterns
    
    def get_code_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate code quality metrics."""
        
        lines = content.splitlines()
        
        metrics = {
            "total_lines": len(lines),
            "code_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "average_line_length": 0,
            "max_line_length": 0,
            "complexity_estimate": 0,
        }
        
        total_length = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                metrics["blank_lines"] += 1
            elif line_stripped.startswith('#') or line_stripped.startswith('//') or line_stripped.startswith('/*'):
                metrics["comment_lines"] += 1
            else:
                metrics["code_lines"] += 1
            
            line_length = len(line)
            total_length += line_length
            metrics["max_line_length"] = max(metrics["max_line_length"], line_length)
        
        if metrics["total_lines"] > 0:
            metrics["average_line_length"] = total_length / metrics["total_lines"]
        
        # Simple complexity estimate based on control structures
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'catch', 'switch', 'case']
        for line in lines:
            for keyword in complexity_keywords:
                if keyword in line.lower():
                    metrics["complexity_estimate"] += 1
        
        return metrics
