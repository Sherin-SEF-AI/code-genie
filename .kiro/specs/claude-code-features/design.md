# Design Document - Claude Code Features

## Overview

This design implements advanced AI coding assistant features that enable CodeGenie to function like Claude Code, with intelligent planning, automatic file operations, safe command execution, and autonomous project management capabilities.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  (CLI, Web Interface, IDE Integration)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Planning & Orchestration                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Planning   │  │   Approval   │  │   Progress   │     │
│  │    Agent     │  │    System    │  │   Tracker    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Execution Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     File     │  │   Command    │  │    Code      │     │
│  │   Creator    │  │   Executor   │  │  Generator   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Support Services                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Diff      │  │   Context    │  │  Template    │     │
│  │   Engine     │  │   Analyzer   │  │   Manager    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Planning Agent

**Purpose:** Creates detailed execution plans before taking actions

**Interface:**
```python
class PlanningAgent:
    def create_plan(self, user_request: str, context: ProjectContext) -> ExecutionPlan
    def break_down_task(self, task: str) -> List[Step]
    def estimate_complexity(self, plan: ExecutionPlan) -> ComplexityEstimate
    def validate_plan(self, plan: ExecutionPlan) -> ValidationResult
    def execute_plan(self, plan: ExecutionPlan, approval_callback: Callable) -> ExecutionResult
```

**Key Features:**
- Natural language understanding of user requests
- Task decomposition into atomic steps
- Dependency analysis between steps
- Risk assessment for each operation
- Progress tracking and reporting

### 2. File Creator

**Purpose:** Automatically creates and modifies files with intelligent content generation

**Interface:**
```python
class FileCreator:
    def create_file(self, path: Path, content: str, preview: bool = True) -> FileOperation
    def modify_file(self, path: Path, changes: List[Change]) -> FileOperation
    def delete_file(self, path: Path, safe: bool = True) -> FileOperation
    def create_directory_structure(self, structure: Dict) -> List[FileOperation]
    def generate_content(self, file_type: str, context: Dict) -> str
```

**Key Features:**
- Template-based content generation
- Context-aware code generation
- Diff preview before applying changes
- Backup creation for safety
- Atomic file operations

### 3. Command Executor

**Purpose:** Safely executes system commands with approval workflows

**Interface:**
```python
class CommandExecutor:
    def execute_command(self, command: str, approval_required: bool = True) -> CommandResult
    def classify_command(self, command: str) -> CommandRiskLevel
    def get_approval(self, command: str, risk_level: CommandRiskLevel) -> bool
    def execute_with_streaming(self, command: str) -> AsyncIterator[str]
    def handle_command_error(self, error: CommandError) -> RecoveryAction
```

**Command Classification:**
- **Safe:** Read-only operations (ls, cat, grep, git status)
- **Risky:** Write operations (npm install, pip install, git commit)
- **Dangerous:** Destructive operations (rm -rf, format, system commands)

### 4. Project Scaffolder

**Purpose:** Creates complete project structures from templates

**Interface:**
```python
class ProjectScaffolder:
    def create_project(self, project_type: str, name: str, options: Dict) -> Project
    def detect_project_type(self, description: str) -> ProjectType
    def generate_structure(self, project_type: ProjectType) -> DirectoryStructure
    def initialize_git(self, project_path: Path) -> bool
    def install_dependencies(self, project_path: Path) -> InstallResult
```

**Supported Project Types:**
- Python (FastAPI, Django, Flask, CLI)
- JavaScript/TypeScript (React, Next.js, Express, Vue)
- Go (CLI, Web Service, gRPC)
- Rust (CLI, Web, Library)
- Generic (Custom templates)

### 5. Diff Engine

**Purpose:** Shows changes before applying them

**Interface:**
```python
class DiffEngine:
    def generate_diff(self, original: str, modified: str) -> Diff
    def show_unified_diff(self, diff: Diff) -> str
    def show_side_by_side_diff(self, diff: Diff) -> str
    def apply_diff(self, file_path: Path, diff: Diff) -> bool
    def create_patch(self, changes: List[FileChange]) -> Patch
```

**Features:**
- Syntax-highlighted diffs
- Line-by-line comparison
- Context lines for clarity
- Multiple diff formats (unified, side-by-side, inline)

### 6. Approval System

**Purpose:** Manages user approval workflows

**Interface:**
```python
class ApprovalSystem:
    def request_approval(self, operation: Operation) -> ApprovalDecision
    def batch_approval(self, operations: List[Operation]) -> List[ApprovalDecision]
    def remember_preference(self, operation_type: str, decision: bool) -> None
    def get_preference(self, operation_type: str) -> Optional[bool]
    def create_undo_point(self, operations: List[Operation]) -> UndoPoint
```

**Approval Modes:**
- Interactive: Ask for each operation
- Auto-approve safe: Automatically approve safe operations
- Batch: Show all operations, approve/reject in bulk
- Trust mode: Auto-approve all (with confirmation)

### 7. Context Analyzer

**Purpose:** Understands project structure and conventions

**Interface:**
```python
class ContextAnalyzer:
    def analyze_project(self, project_path: Path) -> ProjectContext
    def detect_language(self, file_path: Path) -> Language
    def detect_framework(self, project_path: Path) -> Framework
    def extract_conventions(self, project_path: Path) -> CodingConventions
    def find_similar_code(self, code_snippet: str) -> List[CodeMatch]
```

**Analysis Capabilities:**
- Language and framework detection
- Coding style analysis (indentation, naming, etc.)
- Import pattern recognition
- Architecture pattern detection
- Dependency graph construction

### 8. Multi-File Editor

**Purpose:** Coordinates changes across multiple files

**Interface:**
```python
class MultiFileEditor:
    def plan_changes(self, intent: str, context: ProjectContext) -> ChangeSet
    def apply_changes(self, change_set: ChangeSet) -> ChangeResult
    def update_imports(self, moved_file: Path, new_path: Path) -> List[FileChange]
    def refactor_symbol(self, symbol: str, new_name: str) -> List[FileChange]
    def validate_changes(self, change_set: ChangeSet) -> ValidationResult
```

**Features:**
- Cross-file refactoring
- Import management
- Symbol renaming
- Move/rename file with reference updates
- Atomic multi-file commits

## Data Models

### ExecutionPlan
```python
@dataclass
class ExecutionPlan:
    id: str
    description: str
    steps: List[Step]
    estimated_duration: timedelta
    risk_level: RiskLevel
    affected_files: List[Path]
    required_approvals: List[ApprovalPoint]
    dependencies: Dict[str, List[str]]
```

### Step
```python
@dataclass
class Step:
    id: str
    description: str
    action_type: ActionType  # CREATE_FILE, MODIFY_FILE, EXECUTE_COMMAND, etc.
    parameters: Dict[str, Any]
    dependencies: List[str]
    estimated_duration: timedelta
    risk_level: RiskLevel
    status: StepStatus  # PENDING, IN_PROGRESS, COMPLETED, FAILED
```

### FileOperation
```python
@dataclass
class FileOperation:
    operation_type: OperationType  # CREATE, MODIFY, DELETE
    file_path: Path
    content: Optional[str]
    diff: Optional[Diff]
    backup_path: Optional[Path]
    requires_approval: bool
    status: OperationStatus
```

### CommandResult
```python
@dataclass
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: timedelta
    success: bool
    error_message: Optional[str]
```

### ProjectContext
```python
@dataclass
class ProjectContext:
    project_path: Path
    language: Language
    framework: Optional[Framework]
    conventions: CodingConventions
    dependencies: List[Dependency]
    file_structure: DirectoryTree
    git_info: Optional[GitInfo]
```

## Error Handling

### Error Recovery Strategy

1. **Automatic Recovery:**
   - Missing dependencies → Install automatically
   - Syntax errors → Suggest fixes
   - Import errors → Add missing imports
   - Formatting issues → Auto-format

2. **User-Assisted Recovery:**
   - Logical errors → Explain and suggest fixes
   - Design issues → Propose alternatives
   - Conflicts → Show options and let user choose

3. **Graceful Degradation:**
   - If automatic fix fails → Fall back to manual mode
   - If command fails → Show error and suggest alternatives
   - If file operation fails → Rollback and report

### Error Types and Handlers

```python
class ErrorHandler:
    def handle_syntax_error(self, error: SyntaxError) -> RecoveryAction
    def handle_import_error(self, error: ImportError) -> RecoveryAction
    def handle_command_error(self, error: CommandError) -> RecoveryAction
    def handle_file_error(self, error: FileError) -> RecoveryAction
    def handle_permission_error(self, error: PermissionError) -> RecoveryAction
```

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies
- Test error handling paths
- Verify data model validation

### Integration Tests
- Test component interactions
- Test file operations with real filesystem
- Test command execution in sandbox
- Test approval workflows

### End-to-End Tests
- Test complete user workflows
- Test project scaffolding
- Test multi-file refactoring
- Test error recovery scenarios

### Safety Tests
- Test dangerous command blocking
- Test file backup and restore
- Test atomic operations
- Test rollback mechanisms

## Security Considerations

### Command Execution Security
- Whitelist of safe commands
- Blacklist of dangerous commands
- Command parameter validation
- Execution in restricted environment
- Audit logging of all commands

### File Operation Security
- Path traversal prevention
- Permission checking
- Backup before destructive operations
- Atomic operations with rollback
- File size limits

### User Data Protection
- No sensitive data in logs
- Secure storage of preferences
- No external data transmission without consent
- Local-only operation by default

## Performance Considerations

### Optimization Strategies
- Lazy loading of project context
- Incremental diff generation
- Parallel file operations where safe
- Caching of analysis results
- Streaming command output

### Resource Management
- Memory limits for large files
- Timeout for long-running commands
- Cleanup of temporary files
- Connection pooling for external services

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- Planning Agent basic implementation
- File Creator with diff preview
- Command Executor with classification
- Approval System framework

### Phase 2: Project Management (Week 3-4)
- Project Scaffolder
- Template System
- Context Analyzer
- Dependency Manager

### Phase 3: Advanced Features (Week 5-6)
- Multi-File Editor
- Error Recovery System
- Documentation Generator
- Code Explanation

### Phase 4: Polish & Integration (Week 7-8)
- UI/UX improvements
- Performance optimization
- Comprehensive testing
- Documentation and examples
