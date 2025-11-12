"""
End-to-end workflow orchestration integrating all CodeGenie components.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WorkflowContext:
    """Context for end-to-end workflow execution."""
    
    project_path: Path
    goal: str
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    gathered_context: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowResult:
    """Result of end-to-end workflow execution."""
    
    success: bool
    goal: str
    steps_completed: int
    total_steps: int
    duration: float
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class EndToEndWorkflowOrchestrator:
    """Orchestrates complete end-to-end workflows integrating all components."""
    
    def __init__(
        self,
        tool_executor,
        agentic_search,
        proactive_assistant,
        workflow_engine,
        agent_coordinator,
        learning_engine,
        context_engine
    ):
        self.tool_executor = tool_executor
        self.agentic_search = agentic_search
        self.proactive_assistant = proactive_assistant
        self.workflow_engine = workflow_engine
        self.agent_coordinator = agent_coordinator
        self.learning_engine = learning_engine
        self.context_engine = context_engine
    
    async def execute_complete_workflow(
        self,
        goal: str,
        project_path: Path,
        workflow_type: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """Execute a complete end-to-end workflow."""
        
        context = WorkflowContext(
            project_path=project_path,
            goal=goal,
            user_preferences=user_preferences or {}
        )
        
        try:
            # Phase 1: Context Gathering
            await self._gather_context(context)
            
            # Phase 2: Planning
            plan = await self._create_comprehensive_plan(context, workflow_type)
            
            # Phase 3: Execution
            result = await self._execute_plan_with_monitoring(context, plan)
            
            # Phase 4: Verification
            await self._verify_and_validate(context, result)
            
            # Phase 5: Learning
            await self._learn_from_execution(context, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return WorkflowResult(
                success=False,
                goal=goal,
                steps_completed=len(context.execution_history),
                total_steps=0,
                duration=(datetime.now() - context.start_time).total_seconds(),
                errors=[str(e)]
            )
    
    async def _gather_context(self, context: WorkflowContext) -> None:
        """Gather comprehensive context using agentic search."""
        
        logger.info("Gathering context for workflow")
        
        # Use agentic search to gather relevant files and context
        search_result = await self.agentic_search.search_codebase(
            query=context.goal,
            project_path=context.project_path
        )
        
        context.gathered_context["relevant_files"] = search_result.get("files", [])
        context.gathered_context["symbols"] = search_result.get("symbols", [])
        context.gathered_context["dependencies"] = search_result.get("dependencies", [])
        
        # Get proactive suggestions
        suggestions = await self.proactive_assistant.analyze_context(
            context.project_path,
            context.goal
        )
        
        context.gathered_context["proactive_suggestions"] = suggestions
        
        # Retrieve historical context
        historical_context = await self.context_engine.retrieve_relevant_context(
            context.goal
        )
        
        context.gathered_context["historical_context"] = historical_context
    
    async def _create_comprehensive_plan(
        self,
        context: WorkflowContext,
        workflow_type: Optional[str]
    ) -> Dict[str, Any]:
        """Create comprehensive execution plan."""
        
        logger.info("Creating comprehensive execution plan")
        
        # Determine workflow type if not specified
        if not workflow_type:
            workflow_type = await self._infer_workflow_type(context.goal)
        
        # Use workflow engine to create base plan
        base_plan = await self.workflow_engine.create_execution_plan(context.goal)
        
        # Enhance plan with agent coordination
        if self.agent_coordinator:
            agent_assignments = await self.agent_coordinator.delegate_task({
                "description": context.goal,
                "context": context.gathered_context
            })
            
            base_plan["agent_assignments"] = agent_assignments
        
        # Add proactive enhancements
        if context.gathered_context.get("proactive_suggestions"):
            base_plan["proactive_enhancements"] = context.gathered_context["proactive_suggestions"]
        
        return base_plan
    
    async def _execute_plan_with_monitoring(
        self,
        context: WorkflowContext,
        plan: Dict[str, Any]
    ) -> WorkflowResult:
        """Execute plan with comprehensive monitoring and error handling."""
        
        logger.info("Executing plan with monitoring")
        
        steps_completed = 0
        total_steps = len(plan.get("steps", []))
        outputs = {}
        errors = []
        
        for step in plan.get("steps", []):
            try:
                # Create checkpoint before step
                checkpoint = await self._create_checkpoint(context, step)
                context.checkpoints.append(checkpoint)
                
                # Execute step with tool executor
                step_result = await self._execute_step_with_tools(context, step)
                
                # Verify step result
                verification = await self.workflow_engine.result_verifier.verify_result(
                    step,
                    step_result
                )
                
                if not verification.success:
                    # Attempt recovery
                    recovery_result = await self._attempt_recovery(
                        context,
                        step,
                        verification.errors
                    )
                    
                    if not recovery_result.success:
                        errors.append(f"Step {step.get('id')} failed: {verification.errors}")
                        
                        if step.get("critical", False):
                            break
                    else:
                        step_result = recovery_result
                
                # Record execution
                context.execution_history.append({
                    "step": step,
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                outputs[step.get("id")] = step_result
                steps_completed += 1
                
            except Exception as e:
                logger.error(f"Error executing step {step.get('id')}: {e}")
                errors.append(str(e))
                
                if step.get("critical", False):
                    break
        
        duration = (datetime.now() - context.start_time).total_seconds()
        
        return WorkflowResult(
            success=len(errors) == 0,
            goal=context.goal,
            steps_completed=steps_completed,
            total_steps=total_steps,
            duration=duration,
            outputs=outputs,
            errors=errors
        )
    
    async def _execute_step_with_tools(
        self,
        context: WorkflowContext,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a step using appropriate tools."""
        
        step_type = step.get("type")
        
        if step_type == "command":
            result = await self.tool_executor.execute_command(
                step.get("command"),
                cwd=context.project_path
            )
            return {"type": "command", "result": result}
        
        elif step_type == "file_edit":
            result = await self.tool_executor.edit_file(
                context.project_path / step.get("file"),
                step.get("edits")
            )
            return {"type": "file_edit", "result": result}
        
        elif step_type == "agent_task":
            if self.agent_coordinator:
                result = await self.agent_coordinator.execute_agent_task(
                    step.get("agent"),
                    step.get("task")
                )
                return {"type": "agent_task", "result": result}
        
        elif step_type == "analysis":
            result = await self.agentic_search.analyze_code(
                context.project_path,
                step.get("target")
            )
            return {"type": "analysis", "result": result}
        
        return {"type": "unknown", "result": None}
    
    async def _attempt_recovery(
        self,
        context: WorkflowContext,
        step: Dict[str, Any],
        errors: List[str]
    ) -> WorkflowResult:
        """Attempt to recover from step failure."""
        
        logger.info(f"Attempting recovery for step {step.get('id')}")
        
        for error in errors:
            fix_result = await self.tool_executor.fix_and_retry(
                step.get("command"),
                error
            )
            
            if fix_result.success:
                return WorkflowResult(
                    success=True,
                    goal=step.get("description"),
                    steps_completed=1,
                    total_steps=1,
                    duration=0,
                    outputs={"recovery": fix_result}
                )
        
        return WorkflowResult(
            success=False,
            goal=step.get("description"),
            steps_completed=0,
            total_steps=1,
            duration=0,
            errors=errors
        )
    
    async def _verify_and_validate(
        self,
        context: WorkflowContext,
        result: WorkflowResult
    ) -> None:
        """Verify and validate workflow results."""
        
        logger.info("Verifying and validating results")
        
        # Run tests if available
        test_result = await self.tool_executor.execute_command(
            "pytest --tb=short",
            cwd=context.project_path
        )
        
        if not test_result.success:
            result.errors.append("Tests failed after workflow execution")
    
    async def _learn_from_execution(
        self,
        context: WorkflowContext,
        result: WorkflowResult
    ) -> None:
        """Learn from workflow execution."""
        
        if not self.learning_engine:
            return
        
        logger.info("Learning from workflow execution")
        
        await self.learning_engine.record_workflow_execution({
            "goal": context.goal,
            "success": result.success,
            "duration": result.duration,
            "steps_completed": result.steps_completed,
            "errors": result.errors,
            "user_preferences": context.user_preferences
        })
    
    async def _create_checkpoint(
        self,
        context: WorkflowContext,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a checkpoint for rollback."""
        
        return {
            "step_id": step.get("id"),
            "timestamp": datetime.now().isoformat(),
            "project_state": {},
            "context_snapshot": context.gathered_context.copy()
        }
    
    async def _infer_workflow_type(self, goal: str) -> str:
        """Infer workflow type from goal description."""
        
        goal_lower = goal.lower()
        
        if any(word in goal_lower for word in ["create", "implement", "add", "build"]):
            return "feature_development"
        elif any(word in goal_lower for word in ["review", "analyze", "check"]):
            return "code_review"
        elif any(word in goal_lower for word in ["refactor", "improve", "optimize"]):
            return "refactoring"
        elif any(word in goal_lower for word in ["test", "testing", "coverage"]):
            return "testing"
        elif any(word in goal_lower for word in ["security", "vulnerability", "secure"]):
            return "security_audit"
        elif any(word in goal_lower for word in ["performance", "speed"]):
            return "performance_optimization"
        elif any(word in goal_lower for word in ["document", "documentation", "docs"]):
            return "documentation"
        
        return "feature_development"
