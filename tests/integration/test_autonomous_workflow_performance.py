"""
Performance tests for autonomous workflow system.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock
from typing import List

from src.codegenie.core.workflow_engine import (
    WorkflowEngine, TaskPlanner, ExecutionEngine, WorkflowPlan, WorkflowStep,
    DependencyAnalyzer, TaskScheduler, RiskLevel
)
from src.codegenie.agents.coordinator import AgentCoordinator


class TestWorkflowPlanningPerformance:
    """Test performance of workflow planning operations."""
    
    @pytest.fixture
    async def agent_coordinator(self):
        """Create mock agent coordinator."""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.coordinate_complex_task = AsyncMock()
        coordinator.execute_coordination_plan = AsyncMock(return_value=True)
        return coordinator
    
    @pytest.fixture
    async def task_planner(self, agent_coordinator):
        """Create task planner for performance testing."""
        return TaskPlanner(agent_coordinator)
    
    async def test_large_workflow_planning_performance(self, task_planner):
        """Test planning performance with large, complex workflows."""
        # Create a very complex goal that should generate many steps
        complex_goal = """
        Build a comprehensive enterprise software platform including:
        
        Backend Services:
        - User authentication and authorization system with OAuth2, SAML, and LDAP integration
        - RESTful API gateway with rate limiting, caching, and load balancing
        - Microservices for user management, product catalog, order processing, inventory management
        - Message queue system for asynchronous processing
        - Database layer with master-slave replication and sharding
        - Caching layer with Redis and Memcached
        - Search engine integration with Elasticsearch
        - File storage system with AWS S3 integration
        - Logging and monitoring system with ELK stack
        - Configuration management system
        
        Frontend Applications:
        - Web application with React and TypeScript
        - Mobile applications for iOS and Android
        - Admin dashboard with advanced analytics
        - Customer support portal
        - Partner portal for third-party integrations
        
        DevOps and Infrastructure:
        - CI/CD pipeline with automated testing and deployment
        - Infrastructure as Code with Terraform
        - Container orchestration with Kubernetes
        - Monitoring and alerting with Prometheus and Grafana
        - Security scanning and vulnerability assessment
        - Performance testing and optimization
        - Disaster recovery and backup systems
        
        Quality Assurance:
        - Comprehensive unit test suite with 90%+ coverage
        - Integration tests for all API endpoints
        - End-to-end tests for critical user journeys
        - Performance tests for load and stress testing
        - Security tests for penetration testing
        - Accessibility tests for WCAG compliance
        
        Documentation:
        - API documentation with OpenAPI/Swagger
        - User manuals and tutorials
        - Developer documentation and guides
        - Architecture documentation and diagrams
        - Deployment and operations guides
        """
        
        context = {
            "project_type": "enterprise_platform",
            "languages": ["python", "javascript", "typescript", "java"],
            "frameworks": ["django", "react", "spring_boot"],
            "databases": ["postgresql", "redis", "elasticsearch"],
            "cloud_provider": "aws",
            "team_size": "large",
            "timeline": "12_months"
        }
        
        # Measure planning time
        start_time = time.time()
        plan = await task_planner.create_workflow_plan(complex_goal, context, "hierarchical")
        planning_time = time.time() - start_time
        
        # Performance assertions
        assert planning_time < 10.0, f"Planning took {planning_time:.2f}s, should be < 10s"
        assert len(plan.steps) >= 50, f"Expected at least 50 steps, got {len(plan.steps)}"
        assert len(plan.steps) <= 200, f"Too many steps: {len(plan.steps)}, should be manageable"
        
        # Verify plan quality
        assert plan.status.value == "ready"
        assert plan.overall_risk in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert len(plan.dependencies) > 0
        assert len(plan.checkpoints) > 0
        
        print(f"Planning completed in {planning_time:.2f}s with {len(plan.steps)} steps")
    
    async def test_dependency_analysis_scalability(self):
        """Test dependency analysis performance with many tasks."""
        analyzer = DependencyAnalyzer()
        
        # Create a large number of workflow steps with various dependencies
        steps = []
        step_count = 100
        
        for i in range(step_count):
            step_type = i % 5
            
            if step_type == 0:  # Implementation steps
                description = f"Implement feature module {i}"
            elif step_type == 1:  # Testing steps
                description = f"Test feature module {i}"
            elif step_type == 2:  # Documentation steps
                description = f"Document feature module {i}"
            elif step_type == 3:  # Integration steps
                description = f"Integrate module {i} with system"
            else:  # Deployment steps
                description = f"Deploy module {i} to environment"
            
            step = WorkflowStep(
                name=f"Step {i}",
                description=description,
                risk_level=RiskLevel.LOW if i % 10 != 0 else RiskLevel.HIGH
            )
            steps.append(step)
        
        # Measure dependency analysis time
        start_time = time.time()
        dependencies = analyzer.analyze_dependencies(steps)
        analysis_time = time.time() - start_time
        
        # Performance assertions
        assert analysis_time < 5.0, f"Dependency analysis took {analysis_time:.2f}s, should be < 5s"
        assert len(dependencies) == step_count
        
        # Verify dependency quality
        total_deps = sum(len(deps) for deps in dependencies.values())
        avg_deps_per_step = total_deps / step_count
        assert avg_deps_per_step < 10, f"Too many dependencies per step: {avg_deps_per_step:.2f}"
        
        # Test execution order generation
        start_time = time.time()
        execution_order = analyzer.get_execution_order(dependencies)
        order_time = time.time() - start_time
        
        assert order_time < 2.0, f"Execution order generation took {order_time:.2f}s, should be < 2s"
        assert len(execution_order) > 1, "Should have multiple execution batches"
        
        # Verify all steps are included
        all_scheduled_steps = [step for batch in execution_order for step in batch]
        assert len(all_scheduled_steps) == step_count
        
        print(f"Analyzed {step_count} steps in {analysis_time:.2f}s, execution order in {order_time:.2f}s")
    
    async def test_scheduling_performance(self):
        """Test task scheduling performance with resource constraints."""
        scheduler = TaskScheduler()
        
        # Create steps with various resource requirements
        steps = []
        step_count = 75
        
        for i in range(step_count):
            resource_type = i % 4
            
            if resource_type == 0:
                description = f"CPU intensive compilation task {i}"
            elif resource_type == 1:
                description = f"Memory intensive data processing task {i}"
            elif resource_type == 2:
                description = f"I/O intensive file operation task {i}"
            else:
                description = f"Network intensive API call task {i}"
            
            step = WorkflowStep(
                name=f"Task {i}",
                description=description,
                estimated_duration=30.0 + (i % 60),  # 30-90 seconds
                risk_level=RiskLevel.LOW if i % 15 != 0 else RiskLevel.MEDIUM
            )
            steps.append(step)
        
        # Create dependencies (some steps depend on previous ones)
        dependencies = {}
        for i, step in enumerate(steps):
            deps = []
            if i > 0 and i % 5 == 0:  # Every 5th step depends on previous 2
                deps = [steps[max(0, i-2)].id, steps[max(0, i-1)].id]
            elif i > 0 and i % 10 == 0:  # Every 10th step depends on previous 5
                deps = [steps[max(0, i-j)].id for j in range(1, min(6, i+1))]
            
            dependencies[step.id] = deps
        
        # Measure scheduling time
        start_time = time.time()
        schedule = scheduler.create_schedule(steps, dependencies)
        scheduling_time = time.time() - start_time
        
        # Performance assertions
        assert scheduling_time < 3.0, f"Scheduling took {scheduling_time:.2f}s, should be < 3s"
        
        # Verify schedule quality
        assert "batches" in schedule
        assert "total_estimated_time" in schedule
        assert "critical_path" in schedule
        
        # Check that scheduling actually optimizes execution time
        sequential_time = sum(step.estimated_duration for step in steps)
        scheduled_time = schedule["total_estimated_time"]
        
        # Scheduled time should be less than sequential (due to parallelization)
        time_savings = sequential_time - scheduled_time
        assert time_savings > 0, f"No time savings from scheduling: {time_savings:.2f}s"
        
        print(f"Scheduled {step_count} tasks in {scheduling_time:.2f}s")
        print(f"Time savings: {time_savings:.2f}s ({time_savings/sequential_time*100:.1f}%)")


class TestWorkflowExecutionPerformance:
    """Test performance of workflow execution operations."""
    
    @pytest.fixture
    async def workflow_engine(self):
        """Create workflow engine for performance testing."""
        coordinator = Mock(spec=AgentCoordinator)
        
        # Mock fast execution
        async def fast_execution(plan):
            await asyncio.sleep(0.01)  # Simulate very fast execution
            return True
        
        coordinator.execute_coordination_plan = AsyncMock(side_effect=fast_execution)
        return WorkflowEngine(coordinator)
    
    async def test_concurrent_workflow_execution(self, workflow_engine):
        """Test performance with multiple concurrent workflows."""
        workflow_count = 10
        
        # Create multiple workflow plans
        plans = []
        for i in range(workflow_count):
            goal = f"Concurrent workflow {i}: Implement feature set {i}"
            context = {"feature_id": i, "priority": "normal"}
            
            plan = await workflow_engine.task_planner.create_workflow_plan(goal, context)
            plans.append(plan)
        
        # Execute workflows concurrently
        start_time = time.time()
        
        # Execute all workflows concurrently
        execution_tasks = [
            workflow_engine.execution_engine.execute_workflow(plan) 
            for plan in plans
        ]
        
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        execution_time = time.time() - start_time
        
        # Performance assertions
        assert execution_time < 5.0, f"Concurrent execution took {execution_time:.2f}s, should be < 5s"
        
        # Verify results
        successful_executions = sum(1 for result in results if result is True)
        assert successful_executions >= workflow_count * 0.8, f"Only {successful_executions}/{workflow_count} workflows succeeded"
        
        print(f"Executed {workflow_count} workflows concurrently in {execution_time:.2f}s")
        print(f"Success rate: {successful_executions}/{workflow_count} ({successful_executions/workflow_count*100:.1f}%)")
    
    async def test_checkpoint_performance(self, workflow_engine):
        """Test checkpoint creation and rollback performance."""
        checkpoint_manager = workflow_engine.execution_engine.checkpoint_manager
        rollback_manager = workflow_engine.execution_engine.rollback_manager
        
        workflow_id = "performance_test_workflow"
        checkpoint_count = 50
        
        # Create many checkpoints
        checkpoints = []
        
        start_time = time.time()
        
        for i in range(checkpoint_count):
            state_snapshot = {
                "completed_steps": [f"step_{j}" for j in range(i)],
                "modified_files": [f"file_{j}.py" for j in range(i % 10)],
                "active_agents": [f"agent_{j}" for j in range(i % 3)],
                "execution_context": {"iteration": i, "data": f"test_data_{i}"}
            }
            
            checkpoint = checkpoint_manager.create_checkpoint(
                workflow_id, f"step_{i}", state_snapshot, f"Checkpoint {i}"
            )
            checkpoints.append(checkpoint)
        
        checkpoint_creation_time = time.time() - start_time
        
        # Test checkpoint retrieval performance
        start_time = time.time()
        
        all_checkpoints = checkpoint_manager.get_checkpoints(workflow_id)
        latest_checkpoint = checkpoint_manager.get_latest_checkpoint(workflow_id)
        
        retrieval_time = time.time() - start_time
        
        # Test rollback performance
        start_time = time.time()
        
        # Rollback to middle checkpoint
        middle_checkpoint = checkpoints[checkpoint_count // 2]
        checkpoint_data = checkpoint_manager.get_checkpoint_data(middle_checkpoint.id)
        rollback_success = await rollback_manager.rollback_to_checkpoint(
            middle_checkpoint, checkpoint_data
        )
        
        rollback_time = time.time() - start_time
        
        # Performance assertions
        assert checkpoint_creation_time < 2.0, f"Checkpoint creation took {checkpoint_creation_time:.2f}s, should be < 2s"
        assert retrieval_time < 0.1, f"Checkpoint retrieval took {retrieval_time:.2f}s, should be < 0.1s"
        assert rollback_time < 1.0, f"Rollback took {rollback_time:.2f}s, should be < 1s"
        
        # Verify correctness
        assert len(all_checkpoints) == checkpoint_count
        assert latest_checkpoint == checkpoints[-1]
        assert rollback_success is True
        
        print(f"Created {checkpoint_count} checkpoints in {checkpoint_creation_time:.2f}s")
        print(f"Retrieved checkpoints in {retrieval_time:.3f}s")
        print(f"Performed rollback in {rollback_time:.2f}s")
    
    async def test_state_management_performance(self, workflow_engine):
        """Test state management performance with frequent updates."""
        state_manager = workflow_engine.execution_engine.state_manager
        
        # Create test workflow
        plan = WorkflowPlan(name="Performance Test Workflow")
        step_count = 100
        
        for i in range(step_count):
            step = WorkflowStep(name=f"Step {i}", description=f"Performance test step {i}")
            plan.steps.append(step)
        
        # Initialize state
        state_manager.initialize_workflow_state(plan)
        
        # Measure state update performance
        start_time = time.time()
        
        for i, step in enumerate(plan.steps):
            # Start step
            state_manager.update_step_state(plan.id, step, "started")
            
            # Complete step
            from src.codegenie.agents.base_agent import AgentResult
            result = AgentResult(
                agent_name="performance_agent",
                task_id=step.id,
                success=True,
                output=f"Completed step {i}",
                confidence=0.9,
                execution_time=0.1
            )
            
            state_manager.update_step_state(plan.id, step, "completed", result)
            
            # Create state snapshot every 10 steps
            if i % 10 == 0:
                snapshot = state_manager.create_state_snapshot(plan.id)
                assert snapshot is not None
        
        state_update_time = time.time() - start_time
        
        # Test state retrieval performance
        start_time = time.time()
        
        final_state = state_manager.get_current_state(plan.id)
        final_snapshot = state_manager.create_state_snapshot(plan.id)
        
        retrieval_time = time.time() - start_time
        
        # Performance assertions
        assert state_update_time < 1.0, f"State updates took {state_update_time:.2f}s, should be < 1s"
        assert retrieval_time < 0.05, f"State retrieval took {retrieval_time:.3f}s, should be < 0.05s"
        
        # Verify correctness
        assert len(final_state["completed_steps"]) == step_count
        assert final_state["current_step"] is None
        assert len(final_state["step_results"]) == step_count
        
        print(f"Updated state {step_count * 2} times in {state_update_time:.2f}s")
        print(f"Retrieved state in {retrieval_time:.3f}s")


class TestMemoryAndResourceUsage:
    """Test memory usage and resource efficiency."""
    
    async def test_memory_usage_with_large_workflows(self):
        """Test memory usage doesn't grow excessively with large workflows."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.execute_coordination_plan = AsyncMock(return_value=True)
        
        workflow_engine = WorkflowEngine(coordinator)
        
        # Create and process multiple large workflows
        workflow_count = 5
        
        for i in range(workflow_count):
            goal = f"""
            Large workflow {i}: Build comprehensive system with:
            - 20 microservices with full CRUD operations
            - Complete test suite for each service
            - API documentation for all endpoints
            - Monitoring and logging for each component
            - CI/CD pipeline for automated deployment
            - Security scanning and vulnerability assessment
            - Performance testing and optimization
            - Database migration and data seeding
            - Frontend applications for each service
            - Integration with external APIs and services
            """
            
            plan = await workflow_engine.create_and_execute_workflow(
                goal=goal,
                auto_execute=False
            )
            
            # Verify plan was created
            assert len(plan.steps) > 20
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB for this test)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB, should be < 100MB"
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
    
    async def test_cleanup_efficiency(self):
        """Test that resources are properly cleaned up after workflow completion."""
        coordinator = Mock(spec=AgentCoordinator)
        coordinator.execute_coordination_plan = AsyncMock(return_value=True)
        
        workflow_engine = WorkflowEngine(coordinator)
        
        # Create and execute workflows
        completed_workflows = []
        
        for i in range(10):
            goal = f"Test workflow {i} for cleanup testing"
            plan = await workflow_engine.create_and_execute_workflow(goal=goal, auto_execute=True)
            completed_workflows.append(plan)
        
        # Check that active workflows are cleaned up
        active_workflows = workflow_engine.execution_engine.get_active_workflows()
        assert len(active_workflows) == 0, f"Should have no active workflows, found {len(active_workflows)}"
        
        # Check that history is maintained but limited
        history = workflow_engine.execution_engine.execution_history
        assert len(history) <= 10, f"History should be limited, found {len(history)} entries"
        
        # Check that state manager cleaned up workflow states
        state_manager = workflow_engine.execution_engine.state_manager
        active_states = len(state_manager.workflow_states)
        assert active_states == 0, f"Should have no active states, found {active_states}"
        
        print(f"Processed {len(completed_workflows)} workflows, cleanup verified")


class TestScalabilityLimits:
    """Test system behavior at scalability limits."""
    
    async def test_maximum_workflow_size(self):
        """Test behavior with extremely large workflows."""
        coordinator = Mock(spec=AgentCoordinator)
        planner = TaskPlanner(coordinator)
        
        # Create an extremely complex goal
        massive_goal = """
        Build a complete enterprise ecosystem including:
        """ + "\n".join([
            f"- Microservice {i} with full CRUD, testing, documentation, and deployment"
            for i in range(50)
        ]) + """
        
        Plus comprehensive infrastructure:
        - Load balancers and API gateways
        - Database clusters with replication
        - Caching layers and CDN integration
        - Monitoring and alerting systems
        - Security scanning and compliance
        - Backup and disaster recovery
        - Performance testing and optimization
        - Documentation and training materials
        """
        
        start_time = time.time()
        
        try:
            plan = await planner.create_workflow_plan(massive_goal)
            planning_time = time.time() - start_time
            
            # Should handle large workflows gracefully
            assert planning_time < 30.0, f"Planning took {planning_time:.2f}s, should be < 30s"
            assert len(plan.steps) > 100, "Should generate substantial workflow"
            assert len(plan.steps) < 1000, "Should not generate unmanageably large workflow"
            
            print(f"Handled massive workflow: {len(plan.steps)} steps in {planning_time:.2f}s")
            
        except Exception as e:
            # Should fail gracefully if limits are exceeded
            print(f"Gracefully handled workflow size limit: {e}")
            assert "too large" in str(e).lower() or "limit" in str(e).lower()
    
    async def test_dependency_complexity_limits(self):
        """Test behavior with highly complex dependency graphs."""
        analyzer = DependencyAnalyzer()
        
        # Create steps with complex interdependencies
        step_count = 200
        steps = []
        
        for i in range(step_count):
            step = WorkflowStep(
                name=f"Complex Step {i}",
                description=f"Step {i} with complex dependencies"
            )
            
            # Create complex dependency patterns
            if i > 0:
                # Each step depends on multiple previous steps
                dependency_count = min(5, i)
                for j in range(dependency_count):
                    dep_index = i - j - 1
                    if dep_index >= 0:
                        step.dependencies.append(steps[dep_index].id)
            
            steps.append(step)
        
        start_time = time.time()
        
        try:
            dependencies = analyzer.analyze_dependencies(steps)
            analysis_time = time.time() - start_time
            
            # Should handle complex dependencies
            assert analysis_time < 10.0, f"Analysis took {analysis_time:.2f}s, should be < 10s"
            
            # Test execution order generation
            start_time = time.time()
            execution_order = analyzer.get_execution_order(dependencies)
            order_time = time.time() - start_time
            
            assert order_time < 5.0, f"Order generation took {order_time:.2f}s, should be < 5s"
            
            print(f"Handled complex dependencies: {step_count} steps in {analysis_time:.2f}s")
            
        except Exception as e:
            # Should fail gracefully if complexity is too high
            print(f"Gracefully handled dependency complexity limit: {e}")
            assert "complex" in str(e).lower() or "limit" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])