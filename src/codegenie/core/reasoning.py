"""
Reasoning engine for chain-of-thought processing and decision making.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ..models.ollama_client import OllamaMessage
from ..models.model_router import ModelRouter, TaskType, TaskComplexity

logger = logging.getLogger(__name__)


class ReasoningStep(BaseModel):
    """A single step in the reasoning process."""
    
    step_number: int
    description: str
    reasoning: str
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class ReasoningTrace(BaseModel):
    """Complete reasoning trace for a problem."""
    
    problem: str
    steps: List[ReasoningStep]
    final_conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    alternative_approaches: List[str] = Field(default_factory=list)


class ReasoningEngine:
    """Engine for chain-of-thought reasoning and decision making."""
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        
        # Reasoning templates for different task types
        self.reasoning_templates = {
            TaskType.CODE_GENERATION: """
You are an expert software developer. Break down this coding task step by step:

Task: {task}

Please think through this systematically:

1. **Understanding**: What exactly needs to be built/implemented?
2. **Analysis**: What are the key requirements and constraints?
3. **Design**: What is the best approach and architecture?
4. **Implementation**: What are the specific steps to implement?
5. **Testing**: How should this be tested?
6. **Considerations**: What edge cases or potential issues should be considered?

Provide your reasoning for each step, then give a clear conclusion with your implementation plan.
""",
            
            TaskType.DEBUGGING: """
You are an expert debugger. Analyze this problem systematically:

Problem: {task}

Please think through this step by step:

1. **Symptom Analysis**: What exactly is going wrong?
2. **Root Cause Investigation**: What could be causing this issue?
3. **Hypothesis Formation**: What are the most likely causes?
4. **Testing Strategy**: How can we test each hypothesis?
5. **Solution Development**: What are the possible solutions?
6. **Verification**: How can we verify the fix works?

Provide your reasoning for each step, then give a clear debugging plan.
""",
            
            TaskType.PLANNING: """
You are a project planning expert. Break down this task into a comprehensive plan:

Task: {task}

Please think through this systematically:

1. **Goal Analysis**: What is the ultimate objective?
2. **Scope Definition**: What is included and excluded?
3. **Dependency Analysis**: What needs to be done first?
4. **Resource Assessment**: What resources are needed?
5. **Timeline Estimation**: How long will each part take?
6. **Risk Assessment**: What could go wrong?
7. **Success Criteria**: How will we know we're done?

Provide your reasoning for each step, then give a detailed implementation plan.
""",
            
            TaskType.REASONING: """
You are a logical reasoning expert. Analyze this problem step by step:

Problem: {task}

Please think through this systematically:

1. **Problem Decomposition**: Break down the problem into smaller parts
2. **Information Gathering**: What information do we have?
3. **Pattern Recognition**: Are there any patterns or similarities?
4. **Logical Analysis**: What logical connections can we make?
5. **Hypothesis Testing**: What conclusions can we draw?
6. **Validation**: How can we verify our reasoning?

Provide your reasoning for each step, then give a clear conclusion.
""",
        }
    
    async def reason_about_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        task_type: Optional[str] = None,
    ) -> ReasoningTrace:
        """Perform chain-of-thought reasoning about a task."""
        
        # Determine task type if not provided
        if not task_type:
            task_type, _ = self.model_router.analyze_task(task, context)
        
        # Get appropriate reasoning template
        template = self.reasoning_templates.get(
            task_type,
            self.reasoning_templates[TaskType.REASONING]
        )
        
        # Format the reasoning prompt
        reasoning_prompt = template.format(task=task)
        
        # Add context if available
        if context:
            context_str = self._format_context(context)
            reasoning_prompt += f"\n\nAdditional Context:\n{context_str}"
        
        # Create messages for the model
        messages = [
            OllamaMessage(role="system", content="You are an expert problem solver. Think step by step and be thorough in your analysis."),
            OllamaMessage(role="user", content=reasoning_prompt)
        ]
        
        # Get reasoning response
        response = await self.model_router.route_request(
            user_input=task,
            messages=messages,
            context=context,
        )
        
        # Parse the reasoning response
        reasoning_trace = self._parse_reasoning_response(
            task, response.message.content, task_type
        )
        
        logger.debug(f"Generated reasoning trace with {len(reasoning_trace.steps)} steps")
        return reasoning_trace
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for reasoning."""
        
        context_parts = []
        
        if "project_type" in context:
            context_parts.append(f"Project Type: {context['project_type']}")
        
        if "languages" in context:
            context_parts.append(f"Languages: {', '.join(context['languages'])}")
        
        if "frameworks" in context:
            context_parts.append(f"Frameworks: {', '.join(context['frameworks'])}")
        
        if "file_count" in context:
            context_parts.append(f"Files: {context['file_count']}")
        
        if "recent_errors" in context:
            context_parts.append(f"Recent Errors: {context['recent_errors']}")
        
        if "user_preferences" in context:
            context_parts.append(f"User Preferences: {context['user_preferences']}")
        
        return "\n".join(context_parts)
    
    def _parse_reasoning_response(
        self,
        problem: str,
        response: str,
        task_type: str,
    ) -> ReasoningTrace:
        """Parse the model's reasoning response into structured steps."""
        
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
                current_step = ReasoningStep(
                    step_number=step_number,
                    description=self._extract_step_description(line),
                    reasoning="",
                    conclusion="",
                    confidence=0.8,  # Default confidence
                )
                step_number += 1
            
            elif current_step:
                # Add to current step's reasoning
                if current_step.reasoning:
                    current_step.reasoning += "\n" + line
                else:
                    current_step.reasoning = line
        
        # Add final step if exists
        if current_step:
            steps.append(current_step)
        
        # If no structured steps found, create a single step
        if not steps:
            steps.append(ReasoningStep(
                step_number=1,
                description="Analysis",
                reasoning=response,
                conclusion="See reasoning above",
                confidence=0.7,
            ))
        
        # Extract final conclusion
        final_conclusion = self._extract_final_conclusion(response)
        
        # Calculate overall confidence
        confidence = sum(step.confidence for step in steps) / len(steps) if steps else 0.5
        
        return ReasoningTrace(
            problem=problem,
            steps=steps,
            final_conclusion=final_conclusion,
            confidence=confidence,
        )
    
    def _is_step_header(self, line: str) -> bool:
        """Check if a line is a step header."""
        
        step_indicators = [
            "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.",
            "**", "##", "###", "Step", "Analysis", "Design", "Implementation",
            "Testing", "Consideration", "Conclusion"
        ]
        
        line_lower = line.lower()
        return any(indicator.lower() in line_lower for indicator in step_indicators)
    
    def _extract_step_description(self, line: str) -> str:
        """Extract step description from header line."""
        
        # Remove common formatting
        line = line.replace("**", "").replace("##", "").replace("###", "")
        line = line.replace("Step", "").replace(":", "")
        
        # Remove numbers
        import re
        line = re.sub(r'^\d+\.?\s*', '', line)
        
        return line.strip()
    
    def _extract_final_conclusion(self, response: str) -> str:
        """Extract final conclusion from response."""
        
        # Look for conclusion indicators
        conclusion_indicators = [
            "conclusion", "final", "summary", "result", "answer",
            "therefore", "thus", "in conclusion"
        ]
        
        lines = response.split('\n')
        conclusion_lines = []
        in_conclusion = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if we're entering conclusion section
            if any(indicator in line_lower for indicator in conclusion_indicators):
                in_conclusion = True
                continue
            
            # Collect conclusion lines
            if in_conclusion and line.strip():
                conclusion_lines.append(line.strip())
        
        if conclusion_lines:
            return "\n".join(conclusion_lines)
        
        # If no explicit conclusion, take the last few lines
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        if non_empty_lines:
            return non_empty_lines[-1]
        
        return "No clear conclusion found"
    
    async def validate_reasoning(
        self,
        reasoning_trace: ReasoningTrace,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate the reasoning trace and identify potential issues."""
        
        issues = []
        
        # Check if reasoning is complete
        if len(reasoning_trace.steps) < 2:
            issues.append("Reasoning appears incomplete (too few steps)")
        
        # Check confidence levels
        low_confidence_steps = [
            step for step in reasoning_trace.steps
            if step.confidence < 0.5
        ]
        if low_confidence_steps:
            issues.append(f"{len(low_confidence_steps)} steps have low confidence")
        
        # Check for logical consistency
        if reasoning_trace.confidence < 0.6:
            issues.append("Overall reasoning confidence is low")
        
        # Check if conclusion is present
        if not reasoning_trace.final_conclusion or len(reasoning_trace.final_conclusion) < 10:
            issues.append("Final conclusion is missing or too brief")
        
        # If there are issues, we might want to re-reason
        is_valid = len(issues) == 0
        
        return is_valid, issues
    
    async def improve_reasoning(
        self,
        reasoning_trace: ReasoningTrace,
        issues: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> ReasoningTrace:
        """Improve reasoning based on identified issues."""
        
        improvement_prompt = f"""
The previous reasoning had these issues:
{chr(10).join(f"- {issue}" for issue in issues)}

Original reasoning:
{reasoning_trace.final_conclusion}

Please provide an improved analysis that addresses these issues. Be more thorough and confident in your reasoning.
"""
        
        messages = [
            OllamaMessage(role="system", content="You are an expert problem solver. Provide improved reasoning that addresses the identified issues."),
            OllamaMessage(role="user", content=improvement_prompt)
        ]
        
        response = await self.model_router.route_request(
            user_input=reasoning_trace.problem,
            messages=messages,
            context=context,
        )
        
        # Parse improved reasoning
        improved_trace = self._parse_reasoning_response(
            reasoning_trace.problem,
            response.message.content,
            TaskType.REASONING
        )
        
        # Merge with original trace
        improved_trace.alternative_approaches = [reasoning_trace.final_conclusion]
        
        return improved_trace
