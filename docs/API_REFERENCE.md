# CodeGenie API Reference

## Table of Contents
1. [Core API](#core-api)
2. [Agent System API](#agent-system-api)
3. [Workflow Engine API](#workflow-engine-api)
4. [Code Intelligence API](#code-intelligence-api)
5. [Integration API](#integration-api)
6. [REST API](#rest-api)

## Core API

### CodeGenieAgent

Main agent class for interacting with CodeGenie.

```python
from codegenie.core.agent import CodeGenieAgent

# Initialize agent
agent = CodeGenieAgent(
    project_path="/path/to/project",
    model="llama3.1:8b",
    config=config
)

# Execute a task
result = await agent.execute_task(
    "Create a REST API endpoint for user registration"
)

# Get project analysis
analysis = await agent.analyze_project()
```

#### Methods

##### `execute_task(task: str, context: Optional[Dict] = None) -> TaskResult`

Execute a development task.

**Parameters:**
- `task` (str): Natural language description of the task
- `context` (Dict, optional): Additional context for the task

**Returns:**
- `TaskResult`: Result object containing execution details

**Example:**
```python
result = await agent.execute_task(
    "Add authentication to the API",
    context={"framework": "fastapi", "auth_type": "jwt"}
)

print(result.success)  # True/False
print(result.files_modified)  # List of modified files
print(result.explanation)  # Explanation of changes
```

##### `analyze_project() -> ProjectAnalysis`

Analyze the current project structure and patterns.

**Returns:**
- `ProjectAnalysis`: Comprehensive project analysis

**Example:**
```python
analysis = await agent.analyze_project()

print(analysis.framework)  # "fastapi"
print(analysis.language)  # "python"
print(analysis.patterns)  # ["repository_pattern", "dependency_injection"]
print(analysis.dependencies)  # List of dependencies
```

##### `get_suggestions(context: str) -> List[Suggestion]`

Get AI-powered suggestions based on context.

**Parameters:**
- `context` (str): Context for suggestions

**Returns:**
- `List[Suggestion]`: List of suggestions

**Example:**
```python
suggestions = await agent.get_suggestions(
    "I'm working on user authentication"
)

for suggestion in suggestions:
    print(f"{suggestion.title}: {suggestion.description}")
```

### Session Management

```python
from codegenie.core.session import Session

# Create a new session
session = Session(project_path="/path/to/project")

# Save session state
await session.save()

# Load previous session
session = await Session.load(session_id="abc123")

# Get session history
history = session.get_history()
```

## Agent System API

### Multi-Agent Coordination

```python
from codegenie.agents.coordinator import AgentCoordinator
from codegenie.agents.architect import ArchitectAgent
from codegenie.agents.developer import DeveloperAgent

# Initialize coordinator
coordinator = AgentCoordinator()

# Register agents
coordinator.register_agent(ArchitectAgent())
coordinator.register_agent(DeveloperAgent())

# Delegate task to appropriate agent
result = await coordinator.delegate_task(
    task="Design a microservices architecture",
    context=context
)
```

### Specialized Agents

#### ArchitectAgent

```python
from codegenie.agents.architect import ArchitectAgent

architect = ArchitectAgent()

# Design system architecture
architecture = await architect.design_architecture(
    requirements=requirements,
    constraints=constraints
)

# Select technology stack
stack = await architect.select_technology_stack(
    project_type="web_api",
    requirements=["high_performance", "scalability"]
)

# Review existing architecture
review = await architect.review_architecture(
    architecture=current_architecture
)
```

#### SecurityAgent

```python
from codegenie.agents.security import SecurityAgent

security = SecurityAgent()

# Scan for vulnerabilities
vulnerabilities = await security.scan_vulnerabilities(
    code_path="/path/to/code"
)

# Generate security fixes
fixes = await security.generate_fixes(
    vulnerabilities=vulnerabilities
)

# Perform threat modeling
threats = await security.threat_model(
    architecture=architecture
)
```

#### PerformanceAgent

```python
from codegenie.agents.performance import PerformanceAgent

performance = PerformanceAgent()

# Analyze performance
analysis = await performance.analyze_performance(
    code_path="/path/to/code"
)

# Generate optimizations
optimizations = await performance.generate_optimizations(
    bottlenecks=analysis.bottlenecks
)

# Simulate optimization impact
impact = await performance.simulate_optimization(
    optimization=optimizations[0]
)
```

## Workflow Engine API

### Autonomous Workflows

```python
from codegenie.core.workflow_engine import WorkflowEngine

engine = WorkflowEngine()

# Create execution plan
plan = await engine.create_execution_plan(
    goal="Create a complete REST API with authentication",
    context=context
)

# Execute workflow
result = await engine.execute_workflow(
    plan=plan,
    autonomous=True,
    intervention_points=True
)

# Monitor progress
async for update in engine.monitor_execution(plan.id):
    print(f"Step {update.step}/{update.total}: {update.description}")
    print(f"Progress: {update.progress}%")
```

### Task Planning

```python
from codegenie.core.workflow_engine import TaskPlanner

planner = TaskPlanner()

# Decompose complex task
subtasks = await planner.decompose_task(
    task="Build user authentication system",
    max_depth=3
)

# Identify dependencies
dependencies = await planner.identify_dependencies(
    tasks=subtasks
)

# Estimate effort
estimates = await planner.estimate_effort(
    tasks=subtasks
)
```

### Rollback Management

```python
from codegenie.core.workflow_engine import RollbackManager

rollback = RollbackManager()

# Create checkpoint
checkpoint = await rollback.create_checkpoint(
    state=current_state,
    description="Before database migration"
)

# Rollback to checkpoint
await rollback.rollback_to_checkpoint(
    checkpoint_id=checkpoint.id
)

# List available checkpoints
checkpoints = await rollback.list_checkpoints()
```

## Code Intelligence API

### Semantic Analysis

```python
from codegenie.core.code_intelligence import SemanticAnalyzer

analyzer = SemanticAnalyzer()

# Analyze code semantics
analysis = await analyzer.analyze_code(
    code=code_string,
    language="python"
)

# Extract entities
entities = await analyzer.extract_entities(code)

# Identify relationships
relationships = await analyzer.identify_relationships(entities)

# Detect patterns
patterns = await analyzer.detect_patterns(code)
```

### Knowledge Graph

```python
from codegenie.core.knowledge_graph import CodeKnowledgeGraph

graph = CodeKnowledgeGraph()

# Add code entity
await graph.add_entity(
    entity_type="function",
    name="create_user",
    location="src/services/user.py:45",
    metadata={"complexity": 5, "lines": 20}
)

# Add relationship
await graph.add_relationship(
    from_entity="create_user",
    to_entity="UserRepository",
    relationship_type="calls"
)

# Query relationships
related = await graph.query_relationships(
    entity="create_user",
    relationship_type="calls"
)

# Find similar patterns
similar = await graph.find_similar_patterns(
    pattern=pattern_definition
)
```

### Impact Analysis

```python
from codegenie.core.impact_analysis import ChangeImpactAnalyzer

analyzer = ChangeImpactAnalyzer()

# Analyze change impact
impact = await analyzer.analyze_impact(
    change={
        "file": "src/models/user.py",
        "type": "modify",
        "description": "Add email field to User model"
    }
)

print(impact.direct_dependencies)  # Files directly affected
print(impact.indirect_dependencies)  # Files indirectly affected
print(impact.risk_level)  # "low", "medium", "high"
print(impact.recommendations)  # List of recommendations
```

## Integration API

### IDE Integration

```python
from codegenie.integrations.ide_integration import IDEIntegration

ide = IDEIntegration(ide_type="vscode")

# Provide code suggestions
suggestions = await ide.provide_suggestions(
    code=current_code,
    cursor_position=cursor_pos
)

# Analyze code in editor
analysis = await ide.analyze_code_in_editor(
    code=editor_content,
    file_path=file_path
)

# Apply code changes
await ide.apply_changes(
    changes=changes,
    file_path=file_path
)
```

### CI/CD Integration

```python
from codegenie.integrations.cicd_integration import CICDIntegration

cicd = CICDIntegration(platform="github_actions")

# Review pull request
review = await cicd.review_pull_request(
    pr_number=123,
    repository="owner/repo"
)

# Generate deployment plan
plan = await cicd.generate_deployment_plan(
    changes=changes,
    environment="production"
)

# Run automated checks
checks = await cicd.run_checks(
    commit_sha="abc123"
)
```

### Webhook System

```python
from codegenie.integrations.api_system import WebhookSystem

webhooks = WebhookSystem()

# Register webhook
await webhooks.register_webhook(
    event="code_generated",
    url="https://example.com/webhook",
    secret="webhook_secret"
)

# Trigger webhook
await webhooks.trigger_webhook(
    event="code_generated",
    payload={"files": ["src/main.py"], "changes": 10}
)
```

## REST API

### Authentication

All API requests require authentication using API keys.

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.codegenie.dev/v1/analyze
```

### Endpoints

#### POST /v1/tasks

Execute a development task.

**Request:**
```json
{
  "task": "Create a REST API endpoint for user registration",
  "context": {
    "framework": "fastapi",
    "language": "python"
  },
  "autonomous": true
}
```

**Response:**
```json
{
  "task_id": "task_abc123",
  "status": "in_progress",
  "estimated_duration": 300
}
```

#### GET /v1/tasks/{task_id}

Get task status and results.

**Response:**
```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "result": {
    "success": true,
    "files_modified": ["src/api/users.py", "tests/test_users.py"],
    "explanation": "Created user registration endpoint with validation"
  }
}
```

#### POST /v1/analyze

Analyze code or project.

**Request:**
```json
{
  "type": "project",
  "path": "/path/to/project",
  "analysis_type": ["structure", "patterns", "dependencies"]
}
```

**Response:**
```json
{
  "framework": "fastapi",
  "language": "python",
  "patterns": ["repository_pattern", "dependency_injection"],
  "dependencies": [...],
  "recommendations": [...]
}
```

#### POST /v1/suggestions

Get AI-powered suggestions.

**Request:**
```json
{
  "context": "I'm working on user authentication",
  "code": "def login(username, password):\n    ...",
  "cursor_position": 45
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "title": "Add password hashing",
      "description": "Hash passwords using bcrypt before storage",
      "code": "hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
      "confidence": 0.95
    }
  ]
}
```

## Data Models

### TaskResult

```python
@dataclass
class TaskResult:
    success: bool
    task_id: str
    files_modified: List[str]
    files_created: List[str]
    explanation: str
    warnings: List[str]
    next_steps: List[str]
    execution_time: float
```

### ProjectAnalysis

```python
@dataclass
class ProjectAnalysis:
    framework: str
    language: str
    patterns: List[str]
    dependencies: List[Dependency]
    structure: ProjectStructure
    quality_metrics: QualityMetrics
    recommendations: List[Recommendation]
```

### Suggestion

```python
@dataclass
class Suggestion:
    title: str
    description: str
    code: Optional[str]
    confidence: float
    category: str  # "security", "performance", "style", etc.
    priority: str  # "low", "medium", "high"
```

## Error Handling

All API methods raise specific exceptions:

```python
from codegenie.core.exceptions import (
    CodeGenieError,
    TaskExecutionError,
    AnalysisError,
    ConfigurationError
)

try:
    result = await agent.execute_task(task)
except TaskExecutionError as e:
    print(f"Task failed: {e.message}")
    print(f"Rollback available: {e.can_rollback}")
except AnalysisError as e:
    print(f"Analysis failed: {e.message}")
except CodeGenieError as e:
    print(f"General error: {e.message}")
```

## Rate Limiting

API endpoints are rate limited:

- Free tier: 100 requests/hour
- Pro tier: 1000 requests/hour
- Enterprise: Unlimited

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

## Webhooks

Subscribe to events:

- `task.started`
- `task.completed`
- `task.failed`
- `code.generated`
- `analysis.completed`
- `error.detected`

Webhook payload:
```json
{
  "event": "task.completed",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "task_id": "task_abc123",
    "result": {...}
  }
}
```

## SDK Examples

### Python SDK

```python
from codegenie import CodeGenie

# Initialize client
client = CodeGenie(api_key="your_api_key")

# Execute task
task = client.tasks.create(
    task="Create a REST API",
    autonomous=True
)

# Wait for completion
result = task.wait()

# Get suggestions
suggestions = client.suggestions.get(
    context="authentication code"
)
```

### JavaScript SDK

```javascript
const CodeGenie = require('codegenie-sdk');

const client = new CodeGenie({ apiKey: 'your_api_key' });

// Execute task
const task = await client.tasks.create({
  task: 'Create a REST API',
  autonomous: true
});

// Monitor progress
task.on('progress', (update) => {
  console.log(`Progress: ${update.progress}%`);
});

// Get result
const result = await task.wait();
```

## Support

- API Status: https://status.codegenie.dev
- Documentation: https://docs.codegenie.dev
- Support: support@codegenie.dev
