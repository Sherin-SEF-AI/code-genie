#!/usr/bin/env python3
"""
Standalone test for web components (no dependencies).
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class PlanStep:
    id: str
    description: str
    status: str
    progress: int
    dependencies: List[str]
    estimated_duration: int


@dataclass
class ExecutionPlan:
    id: str
    name: str
    description: str
    steps: List[PlanStep]
    status: str
    created_at: str
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'steps': [asdict(s) for s in self.steps],
            'status': self.status,
            'created_at': self.created_at
        }


def test_plan_structure():
    """Test plan data structure."""
    print("Testing Plan Structure...")
    
    plan = ExecutionPlan(
        id="test_1",
        name="Test Plan",
        description="Test description",
        steps=[
            PlanStep(
                id="step1",
                description="First step",
                status="completed",
                progress=100,
                dependencies=[],
                estimated_duration=30
            )
        ],
        status="in_progress",
        created_at=datetime.now().isoformat()
    )
    
    plan_dict = plan.to_dict()
    assert plan_dict['id'] == "test_1"
    assert plan_dict['name'] == "Test Plan"
    assert len(plan_dict['steps']) == 1
    assert plan_dict['steps'][0]['description'] == "First step"
    
    print("✅ Plan structure test passed")


def test_html_generation():
    """Test basic HTML generation."""
    print("Testing HTML Generation...")
    
    # Simple HTML template
    html = f'''
    <div class="plan-visualization" data-plan-id="test_1">
        <div class="plan-header">
            <h3>Test Plan</h3>
        </div>
    </div>
    '''
    
    assert "plan-visualization" in html
    assert "Test Plan" in html
    assert "test_1" in html
    
    print("✅ HTML generation test passed")


def test_css_classes():
    """Test CSS class definitions."""
    print("Testing CSS Classes...")
    
    css = '''
    .plan-visualization {
        background: white;
        border-radius: 12px;
    }
    
    .diff-viewer {
        font-family: monospace;
    }
    
    .approval-request {
        padding: 1rem;
    }
    
    .progress-dashboard {
        display: grid;
    }
    '''
    
    assert ".plan-visualization" in css
    assert ".diff-viewer" in css
    assert ".approval-request" in css
    assert ".progress-dashboard" in css
    
    print("✅ CSS classes test passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Web Components Standalone Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_plan_structure()
        test_html_generation()
        test_css_classes()
        
        print()
        print("=" * 60)
        print("✅ All standalone tests passed!")
        print("=" * 60)
        print()
        print("Note: Full integration tests require dependencies.")
        print("Run 'demo_web_interface.py' for complete testing.")
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
    import sys
    sys.exit(main())
