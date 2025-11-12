#!/usr/bin/env python3
"""
Test script for web interface components.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.ui.web_components import (
    WebComponentsManager, ExecutionPlan, PlanStep, FileDiff,
    ApprovalRequest, ProgressMetrics
)


def test_plan_visualization():
    """Test plan visualization component."""
    print("Testing Plan Visualization Component...")
    
    plan = ExecutionPlan(
        id="test_plan_1",
        name="Test Plan",
        description="A test execution plan",
        steps=[
            PlanStep(
                id="step1",
                description="First step",
                status="completed",
                progress=100,
                dependencies=[],
                estimated_duration=30
            ),
            PlanStep(
                id="step2",
                description="Second step",
                status="in_progress",
                progress=50,
                dependencies=["step1"],
                estimated_duration=60
            )
        ],
        status="in_progress",
        created_at=datetime.now().isoformat()
    )
    
    manager = WebComponentsManager()
    html = manager.render_plan(plan)
    
    assert "test_plan_1" in html
    assert "Test Plan" in html
    assert "First step" in html
    assert "Second step" in html
    print("✅ Plan visualization test passed")


def test_diff_viewer():
    """Test diff viewer component."""
    print("Testing Diff Viewer Component...")
    
    diff = FileDiff(
        file_path="test.py",
        old_content="",
        new_content="",
        diff_lines=[
            {'type': 'addition', 'old_line': '', 'new_line': 1, 'content': 'def hello():'},
            {'type': 'addition', 'old_line': '', 'new_line': 2, 'content': '    print("Hello")'}
        ],
        additions=2,
        deletions=0
    )
    
    manager = WebComponentsManager()
    html = manager.render_diff(diff)
    
    assert "test.py" in html
    assert "+2" in html
    assert "def hello():" in html
    print("✅ Diff viewer test passed")


def test_approval_interface():
    """Test approval interface component."""
    print("Testing Approval Interface Component...")
    
    request = ApprovalRequest(
        id="approval_1",
        title="Test Approval",
        description="A test approval request",
        operation_type="file_create",
        risk_level="safe",
        details={'file': 'test.py'},
        status="pending",
        timestamp=datetime.now().isoformat()
    )
    
    manager = WebComponentsManager()
    html = manager.render_approval(request)
    
    assert "approval_1" in html
    assert "Test Approval" in html
    assert "safe" in html
    print("✅ Approval interface test passed")


def test_progress_dashboard():
    """Test progress dashboard component."""
    print("Testing Progress Dashboard Component...")
    
    metrics = ProgressMetrics(
        total_tasks=10,
        completed_tasks=5,
        failed_tasks=1,
        in_progress_tasks=2,
        estimated_time_remaining=300,
        elapsed_time=450
    )
    
    activities = [
        {'icon': '✅', 'text': 'Task completed', 'time': '1m ago'}
    ]
    
    manager = WebComponentsManager()
    html = manager.render_dashboard(metrics, activities)
    
    assert "10" in html  # total tasks
    assert "5" in html   # completed tasks
    assert "Task completed" in html
    print("✅ Progress dashboard test passed")


def test_css_generation():
    """Test CSS generation."""
    print("Testing CSS Generation...")
    
    manager = WebComponentsManager()
    css = manager.get_all_css()
    
    assert ".plan-visualization" in css
    assert ".diff-viewer" in css
    assert ".approval-request" in css
    assert ".progress-dashboard" in css
    print("✅ CSS generation test passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Web Interface Components Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_plan_visualization()
        test_diff_viewer()
        test_approval_interface()
        test_progress_dashboard()
        test_css_generation()
        
        print()
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
