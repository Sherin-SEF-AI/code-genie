"""
Agentic Search Engine for automatic context gathering.

This module provides intelligent codebase search and context gathering:
- Automatic scanning and indexing of entire codebase
- Intelligent file and symbol relevance scoring
- Automatic context gathering based on task intent
- Search strategy selection algorithms
- Incremental index updates
"""

import asyncio
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import hashlib


@dataclass
class Symbol:
    """Represents a code symbol (function, class, variable, etc.)."""
    name: str
    type: str  # function, class, method, variable, import
    file_path: Path
    line_number: int
    definition: str
    docstring: Optional[str] = None
    references: List[Tuple[Path, int]] = field(default_factory=list)
    score: float = 0.0


@dataclass
class FileIndex:
    """Index information for a file."""
    path: Path
    symbols: List[Symbol]
    imports: List[str]
    dependencies: Set[Path]
    content_hash: str
    last_indexed: datetime
    language: str
    lines_of_code: int


@dataclass
class SearchResult:
    """Result of agentic search."""
    query: str
    relevant_files: List[Path]
    relevant_symbols: List[Symbol]
    context_summary: str
    confidence: float
    search_strategy: str
    gathered_context: Dict[str, Any]
    file_scores: Dict[Path, float] = field(default_factory=dict)


@dataclass
class SearchIntent:
    """Parsed search intent."""
    primary_goal: str
    keywords: List[str]
    symbol_names: List[str]
    file_patterns: List[str]
    language_hints: List[str]
    context_type: str  # implementation, documentation, testing, debugging


class CodebaseScanner:
    """Scans and indexes codebase for comprehensive understanding."""
    
    def __init__(self, project_root: Path):
        """
        Initialize codebase scanner.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.file_index: Dict[Path, FileIndex] = {}
        self.symbol_index: Dict[str, List[Symbol]] = defaultdict(list)
        self.ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.pytest_cache', '.mypy_cache'
        ]
    
    async def scan_project(self) -> Dict[Path, FileIndex]:
        """
        Scan entire project and build index.
        
        Returns:
            Dictionary mapping file paths to their indices
        """
        python_files = self._find_python_files()
        
        tasks = [self._index_file(file_path) for file_path in python_files]
        indices = await asyncio.gather(*tasks)
        
        for index in indices:
            if index:
                self.file_index[index.path] = index
                for symbol in index.symbols:
                    self.symbol_index[symbol.name].append(symbol)
        
        return self.file_index
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in project."""
        python_files = []
        
        for path in self.project_root.rglob('*.py'):
            # Skip ignored directories
            if any(ignore in str(path) for ignore in self.ignore_patterns):
                continue
            python_files.append(path)
        
        return python_files
    
    async def _index_file(self, file_path: Path) -> Optional[FileIndex]:
        """
        Index a single file.
        
        Args:
            file_path: Path to file to index
            
        Returns:
            FileIndex or None if indexing fails
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Parse Python AST
            tree = ast.parse(content)
            
            symbols = []
            imports = []
            
            # Extract symbols
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbol = Symbol(
                        name=node.name,
                        type='function',
                        file_path=file_path,
                        line_number=node.lineno,
                        definition=ast.get_source_segment(content, node) or '',
                        docstring=ast.get_docstring(node)
                    )
                    symbols.append(symbol)
                
                elif isinstance(node, ast.ClassDef):
                    symbol = Symbol(
                        name=node.name,
                        type='class',
                        file_path=file_path,
                        line_number=node.lineno,
                        definition=ast.get_source_segment(content, node) or '',
                        docstring=ast.get_docstring(node)
                    )
                    symbols.append(symbol)
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            
            return FileIndex(
                path=file_path,
                symbols=symbols,
                imports=imports,
                dependencies=set(),
                content_hash=content_hash,
                last_indexed=datetime.now(),
                language='python',
                lines_of_code=lines_of_code
            )
            
        except Exception as e:
            print(f"Error indexing {file_path}: {e}")
            return None
    
    async def update_file_index(self, file_path: Path) -> Optional[FileIndex]:
        """
        Update index for a single file (incremental update).
        
        Args:
            file_path: Path to file to update
            
        Returns:
            Updated FileIndex or None
        """
        # Check if file needs reindexing
        if file_path in self.file_index:
            old_index = self.file_index[file_path]
            try:
                content = file_path.read_text(encoding='utf-8')
                new_hash = hashlib.md5(content.encode()).hexdigest()
                
                if new_hash == old_index.content_hash:
                    # File unchanged, no need to reindex
                    return old_index
            except:
                pass
        
        # Reindex file
        new_index = await self._index_file(file_path)
        
        if new_index:
            # Remove old symbols from symbol index
            if file_path in self.file_index:
                for symbol in self.file_index[file_path].symbols:
                    if symbol in self.symbol_index[symbol.name]:
                        self.symbol_index[symbol.name].remove(symbol)
            
            # Add new symbols
            self.file_index[file_path] = new_index
            for symbol in new_index.symbols:
                self.symbol_index[symbol.name].append(symbol)
        
        return new_index
    
    def find_symbol(self, name: str) -> List[Symbol]:
        """
        Find symbols by name.
        
        Args:
            name: Symbol name to search for
            
        Returns:
            List of matching symbols
        """
        return self.symbol_index.get(name, [])
    
    def find_files_by_pattern(self, pattern: str) -> List[Path]:
        """
        Find files matching a pattern.
        
        Args:
            pattern: File name pattern (supports wildcards)
            
        Returns:
            List of matching file paths
        """
        import fnmatch
        
        matching_files = []
        for file_path in self.file_index.keys():
            if fnmatch.fnmatch(file_path.name, pattern):
                matching_files.append(file_path)
        
        return matching_files


class RelevanceScorer:
    """Scores files and symbols for relevance to a query."""
    
    def __init__(self):
        """Initialize relevance scorer."""
        self.weights = {
            'keyword_match': 0.3,
            'symbol_match': 0.25,
            'import_relevance': 0.15,
            'recency': 0.1,
            'file_size': 0.1,
            'documentation': 0.1
        }
    
    def score_file(
        self,
        file_index: FileIndex,
        intent: SearchIntent,
        query_keywords: Set[str]
    ) -> float:
        """
        Score a file's relevance to search intent.
        
        Args:
            file_index: File index to score
            intent: Search intent
            query_keywords: Keywords from query
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        
        # Keyword matching in file path
        file_path_lower = str(file_index.path).lower()
        keyword_matches = sum(1 for kw in query_keywords if kw in file_path_lower)
        score += (keyword_matches / max(len(query_keywords), 1)) * self.weights['keyword_match']
        
        # Symbol matching
        symbol_names = {s.name.lower() for s in file_index.symbols}
        intent_symbols = {s.lower() for s in intent.symbol_names}
        symbol_matches = len(symbol_names & intent_symbols)
        score += (symbol_matches / max(len(intent_symbols), 1)) * self.weights['symbol_match']
        
        # Import relevance
        import_matches = sum(1 for imp in file_index.imports if any(kw in imp.lower() for kw in query_keywords))
        score += (import_matches / max(len(file_index.imports), 1)) * self.weights['import_relevance']
        
        # Recency (files modified recently are more relevant)
        hours_since_index = (datetime.now() - file_index.last_indexed).total_seconds() / 3600
        recency_score = max(0, 1 - (hours_since_index / 168))  # Decay over a week
        score += recency_score * self.weights['recency']
        
        # File size (moderate size files often more relevant)
        size_score = min(1.0, file_index.lines_of_code / 500)
        if file_index.lines_of_code > 1000:
            size_score = max(0, 1 - ((file_index.lines_of_code - 1000) / 2000))
        score += size_score * self.weights['file_size']
        
        # Documentation presence
        doc_score = sum(1 for s in file_index.symbols if s.docstring) / max(len(file_index.symbols), 1)
        score += doc_score * self.weights['documentation']
        
        return min(1.0, score)
    
    def score_symbol(
        self,
        symbol: Symbol,
        intent: SearchIntent,
        query_keywords: Set[str]
    ) -> float:
        """
        Score a symbol's relevance to search intent.
        
        Args:
            symbol: Symbol to score
            intent: Search intent
            query_keywords: Keywords from query
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        
        # Name matching
        symbol_name_lower = symbol.name.lower()
        if symbol_name_lower in {s.lower() for s in intent.symbol_names}:
            score += 0.5
        
        # Keyword matching in name
        keyword_matches = sum(1 for kw in query_keywords if kw in symbol_name_lower)
        score += (keyword_matches / max(len(query_keywords), 1)) * 0.3
        
        # Documentation presence
        if symbol.docstring:
            doc_lower = symbol.docstring.lower()
            doc_matches = sum(1 for kw in query_keywords if kw in doc_lower)
            score += (doc_matches / max(len(query_keywords), 1)) * 0.2
        
        return min(1.0, score)


class SearchStrategySelector:
    """Selects optimal search strategy based on query characteristics."""
    
    def select_strategy(self, intent: SearchIntent) -> str:
        """
        Select search strategy based on intent.
        
        Args:
            intent: Parsed search intent
            
        Returns:
            Strategy name
        """
        # If specific symbols mentioned, use symbol-focused search
        if intent.symbol_names:
            return 'symbol_focused'
        
        # If file patterns specified, use file-focused search
        if intent.file_patterns:
            return 'file_focused'
        
        # If looking for implementation, use code-focused search
        if intent.context_type == 'implementation':
            return 'code_focused'
        
        # If looking for documentation, use doc-focused search
        if intent.context_type == 'documentation':
            return 'documentation_focused'
        
        # Default to broad search
        return 'broad_search'


class AgenticSearchEngine:
    """
    Main agentic search engine that automatically gathers relevant context.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize agentic search engine.
        
        Args:
            project_root: Root directory of the project
        """
        self.scanner = CodebaseScanner(project_root)
        self.scorer = RelevanceScorer()
        self.strategy_selector = SearchStrategySelector()
        self.indexed = False
    
    async def initialize(self) -> None:
        """Initialize the search engine by scanning the codebase."""
        if not self.indexed:
            await self.scanner.scan_project()
            self.indexed = True
    
    def _parse_intent(self, query: str) -> SearchIntent:
        """
        Parse search query to extract intent.
        
        Args:
            query: Search query
            
        Returns:
            Parsed SearchIntent
        """
        query_lower = query.lower()
        
        # Extract keywords
        keywords = [word for word in re.findall(r'\b\w+\b', query_lower) if len(word) > 2]
        
        # Identify potential symbol names (CamelCase or snake_case)
        symbol_names = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b|\b[a-z_][a-z0-9_]*\b', query)
        
        # Identify file patterns
        file_patterns = re.findall(r'\b\w+\.py\b', query)
        
        # Determine context type
        context_type = 'implementation'
        if any(word in query_lower for word in ['test', 'testing', 'spec']):
            context_type = 'testing'
        elif any(word in query_lower for word in ['doc', 'documentation', 'comment']):
            context_type = 'documentation'
        elif any(word in query_lower for word in ['debug', 'error', 'fix']):
            context_type = 'debugging'
        
        return SearchIntent(
            primary_goal=query,
            keywords=keywords,
            symbol_names=symbol_names,
            file_patterns=file_patterns,
            language_hints=['python'],
            context_type=context_type
        )
    
    async def search(
        self,
        query: str,
        max_files: int = 10,
        max_symbols: int = 20
    ) -> SearchResult:
        """
        Perform agentic search to gather relevant context.
        
        Args:
            query: Search query describing what to find
            max_files: Maximum number of files to return
            max_symbols: Maximum number of symbols to return
            
        Returns:
            SearchResult with relevant files and symbols
        """
        # Ensure index is initialized
        if not self.indexed:
            await self.initialize()
        
        # Parse intent
        intent = self._parse_intent(query)
        query_keywords = set(intent.keywords)
        
        # Select strategy
        strategy = self.strategy_selector.select_strategy(intent)
        
        # Score all files
        file_scores = {}
        for file_path, file_index in self.scanner.file_index.items():
            score = self.scorer.score_file(file_index, intent, query_keywords)
            file_scores[file_path] = score
        
        # Get top files
        sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
        relevant_files = [path for path, score in sorted_files[:max_files] if score > 0.1]
        
        # Score all symbols
        all_symbols = []
        for file_index in self.scanner.file_index.values():
            for symbol in file_index.symbols:
                symbol.score = self.scorer.score_symbol(symbol, intent, query_keywords)
                if symbol.score > 0.1:
                    all_symbols.append(symbol)
        
        # Get top symbols
        relevant_symbols = sorted(all_symbols, key=lambda s: s.score, reverse=True)[:max_symbols]
        
        # Generate context summary
        context_summary = self._generate_context_summary(
            relevant_files,
            relevant_symbols,
            intent
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(relevant_files, relevant_symbols, file_scores)
        
        # Gather additional context
        gathered_context = {
            'total_files_scanned': len(self.scanner.file_index),
            'total_symbols_found': sum(len(idx.symbols) for idx in self.scanner.file_index.values()),
            'intent': intent,
            'strategy_used': strategy
        }
        
        return SearchResult(
            query=query,
            relevant_files=relevant_files,
            relevant_symbols=relevant_symbols,
            context_summary=context_summary,
            confidence=confidence,
            search_strategy=strategy,
            gathered_context=gathered_context,
            file_scores={path: score for path, score in sorted_files[:max_files]}
        )
    
    def _generate_context_summary(
        self,
        files: List[Path],
        symbols: List[Symbol],
        intent: SearchIntent
    ) -> str:
        """Generate a summary of gathered context."""
        summary_parts = []
        
        summary_parts.append(f"Found {len(files)} relevant files and {len(symbols)} relevant symbols.")
        
        if files:
            summary_parts.append(f"\nTop files: {', '.join(f.name for f in files[:3])}")
        
        if symbols:
            symbol_types = defaultdict(int)
            for symbol in symbols:
                symbol_types[symbol.type] += 1
            summary_parts.append(f"\nSymbols: {dict(symbol_types)}")
        
        summary_parts.append(f"\nContext type: {intent.context_type}")
        
        return ' '.join(summary_parts)
    
    def _calculate_confidence(
        self,
        files: List[Path],
        symbols: List[Symbol],
        file_scores: Dict[Path, float]
    ) -> float:
        """Calculate confidence in search results."""
        if not files and not symbols:
            return 0.0
        
        # Average of top file scores
        if files:
            avg_file_score = sum(file_scores.get(f, 0) for f in files) / len(files)
        else:
            avg_file_score = 0.0
        
        # Average of top symbol scores
        if symbols:
            avg_symbol_score = sum(s.score for s in symbols) / len(symbols)
        else:
            avg_symbol_score = 0.0
        
        # Combined confidence
        confidence = (avg_file_score + avg_symbol_score) / 2
        
        return min(1.0, confidence)
    
    async def auto_gather_context(self, task_description: str) -> Dict[str, Any]:
        """
        Automatically gather all relevant context for a task.
        
        Args:
            task_description: Description of the task
            
        Returns:
            Dictionary with gathered context
        """
        search_result = await self.search(task_description)
        
        context = {
            'task': task_description,
            'relevant_files': search_result.relevant_files,
            'relevant_symbols': search_result.relevant_symbols,
            'summary': search_result.context_summary,
            'confidence': search_result.confidence,
            'file_contents': {}
        }
        
        # Load content of relevant files
        for file_path in search_result.relevant_files[:5]:  # Limit to top 5
            try:
                context['file_contents'][str(file_path)] = file_path.read_text()
            except:
                pass
        
        return context
    
    async def update_index(self, changed_files: List[Path]) -> None:
        """
        Update index for changed files (incremental update).
        
        Args:
            changed_files: List of files that have changed
        """
        for file_path in changed_files:
            await self.scanner.update_file_index(file_path)
