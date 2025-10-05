"""
Intelligent task planning and breakdown system.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ..models.ollama_client import OllamaMessage
from ..models.model_router import ModelRouter, TaskType, TaskComplexity

logger = logging.getLogger(__name__)


class PlanStep(BaseModel):
    """A single step in a plan."""
    
    id: str
    description: str
    action_type: str  # "code_generation", "file_operation", "command_execution", "analysis"
    details: Dict[str, Any]
    dependencies: List[str] = Field(default_factory=list)
    estimated_duration: int = Field(default=300, ge=1)  # seconds
    priority: int = Field(default=1, ge=1, le=10)
    success_criteria: List[str] = Field(default_factory=list)
    rollback_plan: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed, skipped
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None


class Plan(BaseModel):
    """A complete plan for accomplishing a task."""
    
    id: str
    goal: str
    description: str
    steps: List[PlanStep]
    estimated_total_duration: int
    complexity: str
    success_criteria: List[str]
    risk_assessment: Dict[str, Any]
    alternative_approaches: List[str] = Field(default_factory=list)
    created_at: float
    status: str = "draft"  # draft, active, completed, failed, cancelled
    current_step: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)


class TaskPlanner:
    """Intelligent task planning system."""
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        
        # Planning templates for different task types
        self.planning_templates = {
            TaskType.CODE_GENERATION: """
You are an expert software architect. Create a detailed implementation plan for this task:

Task: {task}

Please create a comprehensive plan with the following structure:

1. **Goal Analysis**: What exactly needs to be accomplished?
2. **Requirements**: What are the specific requirements and constraints?
3. **Architecture**: What is the best approach and structure?
4. **Implementation Steps**: Break down into specific, actionable steps
5. **Testing Strategy**: How will this be tested?
6. **Risk Assessment**: What could go wrong and how to mitigate?
7. **Success Criteria**: How will we know we're done?

For each implementation step, provide:
- Clear description
- Action type (code_generation, file_operation, command_execution, analysis)
- Dependencies
- Estimated duration
- Success criteria
- Rollback plan if needed

Format your response as a structured plan that can be executed step by step.
""",
            
            TaskType.DEBUGGING: """
You are an expert debugger. Create a systematic debugging plan for this issue:

Issue: {task}

Please create a comprehensive debugging plan with:

1. **Problem Analysis**: What exactly is wrong?
2. **Hypothesis Formation**: What are the most likely causes?
3. **Investigation Steps**: How to test each hypothesis?
4. **Solution Development**: How to fix each potential cause?
5. **Verification**: How to confirm the fix works?
6. **Prevention**: How to prevent this in the future?

For each step, provide:
- Clear description
- Action type (analysis, command_execution, code_generation)
- Dependencies
- Estimated duration
- Success criteria

Format as a structured debugging plan.
""",
            
            TaskType.REFACTORING: """
You are an expert software engineer. Create a refactoring plan for this task:

Task: {task}

Please create a comprehensive refactoring plan with:

1. **Current State Analysis**: What needs to be improved?
2. **Target State**: What should the code look like?
3. **Impact Assessment**: What will be affected?
4. **Refactoring Strategy**: What approach to take?
5. **Implementation Steps**: Specific steps to refactor
6. **Testing Plan**: How to ensure nothing breaks?
7. **Migration Strategy**: How to transition safely?

For each step, provide:
- Clear description
- Action type (analysis, code_generation, file_operation)
- Dependencies
- Estimated duration
- Success criteria
- Rollback plan

Format as a structured refactoring plan.
""",
        }
    
    async def create_plan(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        task_type: Optional[str] = None,
    ) -> Plan:
        """Create a comprehensive plan for a task."""
        
        logger.info(f"Creating plan for task: {task[:100]}...")
        
        # Determine task type if not provided
        if not task_type:
            task_type, complexity = self.model_router.analyze_task(task, context)
        else:
            _, complexity = self.model_router.analyze_task(task, context)
        
        # Get appropriate planning template
        template = self.planning_templates.get(
            task_type,
            self.planning_templates[TaskType.CODE_GENERATION]
        )
        
        # Format the planning prompt
        planning_prompt = template.format(task=task)
        
        # Add context if available
        if context:
            context_str = self._format_context(context)
            planning_prompt += f"\n\nAdditional Context:\n{context_str}"
        
        # Create messages for the model
        messages = [
            OllamaMessage(
                role="system",
                content="You are an expert project planner. Create detailed, actionable plans that can be executed step by step. Be specific about actions, dependencies, and success criteria."
            ),
            OllamaMessage(role="user", content=planning_prompt)
        ]
        
        # Get planning response
        response = await self.model_router.route_request(
            user_input=task,
            messages=messages,
            context=context,
        )
        
        # Parse the planning response
        plan = self._parse_planning_response(
            task=task,
            response=response.message.content,
            task_type=task_type,
            complexity=complexity,
            context=context
        )
        
        logger.info(f"Created plan with {len(plan.steps)} steps")
        return plan
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for planning."""
        
        context_parts = []
        
        if "project_type" in context:
            context_parts.append(f"Project Type: {context['project_type']}")
        
        if "languages" in context:
            context_parts.append(f"Languages: {', '.join(context['languages'])}")
        
        if "frameworks" in context:
            context_parts.append(f"Frameworks: {', '.join(context['frameworks'])}")
        
        if "file_count" in context:
            context_parts.append(f"Files: {context['file_count']}")
        
        if "current_goal" in context:
            context_parts.append(f"Current Goal: {context['current_goal']}")
        
        if "recent_errors" in context:
            context_parts.append(f"Recent Errors: {', '.join(context['recent_errors'][:3])}")
        
        return "\n".join(context_parts)
    
    def _parse_planning_response(
        self,
        task: str,
        response: str,
        task_type: str,
        complexity: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Plan:
        """Parse the model's planning response into a structured plan."""
        
        plan_id = f"plan_{int(time.time())}"
        
        # Parse steps from response
        steps = self._extract_plan_steps(response)
        
        # Calculate total duration
        total_duration = sum(step.estimated_duration for step in steps)
        
        # Extract success criteria
        success_criteria = self._extract_success_criteria(response)
        
        # Assess risks
        risk_assessment = self._assess_risks(steps, context)
        
        # Extract alternative approaches
        alternative_approaches = self._extract_alternatives(response)
        
        plan = Plan(
            id=plan_id,
            goal=task,
            description=f"Plan for {task}",
            steps=steps,
            estimated_total_duration=total_duration,
            complexity=complexity,
            success_criteria=success_criteria,
            risk_assessment=risk_assessment,
            alternative_approaches=alternative_approaches,
            created_at=time.time(),
        )
        
        return plan
    
    def _extract_plan_steps(self, response: str) -> List[PlanStep]:
        """Extract plan steps from the response."""
        
        steps = []
        lines = response.split('\n')
        current_step = None
        step_number = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a new step
            if self._is_step_header(line):
                # Save previous step if exists
                if current_step:
                    steps.append(current_step)
                
                # Start new step
                step_id = f"step_{step_number}"
                current_step = PlanStep(
                    id=step_id,
                    description=self._extract_step_description(line),
                    action_type=self._infer_action_type(line),
                    details={},
                    estimated_duration=self._estimate_duration(line),
                    priority=self._infer_priority(step_number),
                )
                step_number += 1
            
            elif current_step:
                # Add to current step's details
                if "dependencies" in line.lower():
                    current_step.dependencies = self._extract_dependencies(line)
                elif "success criteria" in line.lower():
                    current_step.success_criteria = self._extract_success_criteria_line(line)
                elif "rollback" in line.lower():
                    current_step.rollback_plan = line
                else:
                    # Add to description
                    if current_step.description:
                        current_step.description += " " + line
                    else:
                        current_step.description = line
        
        # Add final step if exists
        if current_step:
            steps.append(current_step)
        
        # If no structured steps found, create a single step
        if not steps:
            steps.append(PlanStep(
                id="step_1",
                description="Execute the task",
                action_type="code_generation",
                details={},
                estimated_duration=300,
                priority=1,
            ))
        
        # Set dependencies based on step order
        for i, step in enumerate(steps):
            if i > 0:
                step.dependencies = [steps[i-1].id]
        
        return steps
    
    def _is_step_header(self, line: str) -> bool:
        """Check if a line is a step header."""
        
        step_indicators = [
            "step", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.",
            "**", "##", "###", "implementation", "analysis", "testing",
            "verification", "deployment", "configuration"
        ]
        
        line_lower = line.lower()
        return any(indicator in line_lower for indicator in step_indicators)
    
    def _extract_step_description(self, line: str) -> str:
        """Extract step description from header line."""
        
        # Remove common formatting
        line = line.replace("**", "").replace("##", "").replace("###", "")
        line = line.replace("Step", "").replace(":", "")
        
        # Remove numbers
        import re
        line = re.sub(r'^\d+\.?\s*', '', line)
        
        return line.strip()
    
    def _infer_action_type(self, line: str) -> str:
        """Infer action type from step description."""
        
        line_lower = line.lower()
        
        if any(word in line_lower for word in ["write", "create", "implement", "generate", "code"]):
            return "code_generation"
        elif any(word in line_lower for word in ["run", "execute", "command", "install", "build"]):
            return "command_execution"
        elif any(word in line_lower for word in ["move", "copy", "delete", "rename", "file"]):
            return "file_operation"
        elif any(word in line_lower for word in ["analyze", "review", "check", "inspect"]):
            return "analysis"
        else:
            return "code_generation"  # Default
    
    def _estimate_duration(self, line: str) -> int:
        """Estimate duration for a step in seconds."""
        
        line_lower = line.lower()
        
        if any(word in line_lower for word in ["quick", "simple", "basic"]):
            return 60
        elif any(word in line_lower for word in ["complex", "major", "comprehensive"]):
            return 600
        elif any(word in line_lower for word in ["test", "verify", "check"]):
            return 120
        else:
            return 300  # Default 5 minutes
    
    def _infer_priority(self, step_number: int) -> int:
        """Infer priority based on step number."""
        
        if step_number <= 2:
            return 1  # High priority
        elif step_number <= 5:
            return 2  # Medium priority
        else:
            return 3  # Low priority
    
    def _extract_dependencies(self, line: str) -> List[str]:
        """Extract dependencies from a line."""
        
        # Simple extraction - look for step references
        import re
        dependencies = re.findall(r'step\s*(\d+)', line.lower())
        return [f"step_{dep}" for dep in dependencies]
    
    def _extract_success_criteria_line(self, line: str) -> List[str]:
        """Extract success criteria from a line."""
        
        # Split by common separators
        criteria = []
        for part in line.split(','):
            part = part.strip()
            if part and "success criteria" not in part.lower():
                criteria.append(part)
        
        return criteria
    
    def _extract_success_criteria(self, response: str) -> List[str]:
        """Extract overall success criteria from response."""
        
        criteria = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if "success criteria" in line_lower or "success" in line_lower:
                # Extract the criteria
                criteria_text = line.split(':')[-1].strip()
                if criteria_text:
                    criteria.append(criteria_text)
        
        if not criteria:
            criteria = ["Task completed successfully"]
        
        return criteria
    
    def _assess_risks(self, steps: List[PlanStep], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess risks for the plan."""
        
        risks = {
            "high_risk_steps": [],
            "potential_issues": [],
            "mitigation_strategies": [],
        }
        
        # Identify high-risk steps
        for step in steps:
            if step.action_type == "file_operation":
                risks["high_risk_steps"].append(step.id)
                risks["potential_issues"].append(f"File operation in {step.description} could fail")
                risks["mitigation_strategies"].append("Create backups before file operations")
            
            elif step.estimated_duration > 600:  # More than 10 minutes
                risks["high_risk_steps"].append(step.id)
                risks["potential_issues"].append(f"Long-running step: {step.description}")
                risks["mitigation_strategies"].append("Break down into smaller steps")
        
        # Context-based risks
        if context:
            if context.get("file_count", 0) > 100:
                risks["potential_issues"].append("Large project - changes may have wide impact")
                risks["mitigation_strategies"].append("Test changes incrementally")
            
            if not context.get("has_tests", False):
                risks["potential_issues"].append("No tests - difficult to verify changes")
                risks["mitigation_strategies"].append("Add tests before making changes")
        
        return risks
    
    def _extract_alternatives(self, response: str) -> List[str]:
        """Extract alternative approaches from response."""
        
        alternatives = []
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ["alternative", "option", "could also", "instead"]):
                alternatives.append(line.strip())
        
        return alternatives
    
    async def revise_plan(
        self,
        plan: Plan,
        feedback: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Plan:
        """Revise a plan based on feedback."""
        
        revision_prompt = f"""
The following plan needs revision based on feedback:

Original Plan: {plan.description}
Feedback: {feedback}

Current Steps:
{chr(10).join(f"- {step.description}" for step in plan.steps)}

Please provide a revised plan that addresses the feedback. Keep the same structure but improve the steps as needed.
"""
        
        messages = [
            OllamaMessage(
                role="system",
                content="You are an expert project planner. Revise plans based on feedback while maintaining structure and completeness."
            ),
            OllamaMessage(role="user", content=revision_prompt)
        ]
        
        response = await self.model_router.route_request(
            user_input=plan.goal,
            messages=messages,
            context=context,
        )
        
        # Parse revised plan
        revised_plan = self._parse_planning_response(
            task=plan.goal,
            response=response.message.content,
            task_type="planning",
            complexity=plan.complexity,
            context=context
        )
        
        # Preserve original plan ID and creation time
        revised_plan.id = plan.id
        revised_plan.created_at = plan.created_at
        
        return revised_plan
