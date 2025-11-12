"""
Web UI components for CodeGenie - Plan visualization, diff viewer, approval interface, and progress dashboard.
"""

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PlanStep:
    """Represents a step in an execution plan."""
    id: str
    description: str
    status: str  # pending, in_progress, completed, failed
    progress: int  # 0-100
    dependencies: List[str]
    estimated_duration: int  # seconds
    actual_duration: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Represents a complete execution plan."""
    id: str
    name: str
    description: str
    steps: List[PlanStep]
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'steps': [asdict(step) for step in self.steps],
            'status': self.status,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }


class PlanVisualizationComponent:
    """Component for visualizing execution plans."""
    
    @staticmethod
    def generate_html(plan: ExecutionPlan) -> str:
        """Generate HTML for plan visualization."""
        steps_html = ""
        for step in plan.steps:
            status_class = f"step-{step.status}"
            progress_width = step.progress
            
            dependencies_html = ""
            if step.dependencies:
                deps = ", ".join(step.dependencies)
                dependencies_html = f'<div class="step-dependencies">Depends on: {deps}</div>'
            
            error_html = ""
            if step.error_message:
                error_html = f'<div class="step-error">{step.error_message}</div>'
            
            steps_html += f'''
            <div class="plan-step {status_class}" data-step-id="{step.id}">
                <div class="step-header">
                    <span class="step-status-icon">{PlanVisualizationComponent._get_status_icon(step.status)}</span>
                    <span class="step-description">{step.description}</span>
                    <span class="step-duration">{step.estimated_duration}s</span>
                </div>
                <div class="step-progress-bar">
                    <div class="step-progress-fill" style="width: {progress_width}%"></div>
                </div>
                {dependencies_html}
                {error_html}
            </div>
            '''
        
        return f'''
        <div class="plan-visualization" data-plan-id="{plan.id}">
            <div class="plan-header">
                <h3>{plan.name}</h3>
                <p>{plan.description}</p>
                <div class="plan-status {plan.status}">{plan.status}</div>
            </div>
            <div class="plan-timeline">
                <div class="timeline-start">Created: {plan.created_at}</div>
                {f'<div class="timeline-progress">Started: {plan.started_at}</div>' if plan.started_at else ''}
                {f'<div class="timeline-end">Completed: {plan.completed_at}</div>' if plan.completed_at else ''}
            </div>
            <div class="plan-steps">
                {steps_html}
            </div>
        </div>
        '''
    
    @staticmethod
    def _get_status_icon(status: str) -> str:
        """Get icon for status."""
        icons = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'failed': '❌'
        }
        return icons.get(status, '❓')
    
    @staticmethod
    def generate_css() -> str:
        """Generate CSS for plan visualization."""
        return '''
        .plan-visualization {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }
        
        .plan-header {
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 1rem;
            margin-bottom: 1rem;
        }
        
        .plan-header h3 {
            margin-bottom: 0.5rem;
            color: #212529;
        }
        
        .plan-status {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }
        
        .plan-status.pending {
            background: #fff3cd;
            color: #856404;
        }
        
        .plan-status.in_progress {
            background: #cfe2ff;
            color: #084298;
        }
        
        .plan-status.completed {
            background: #d1e7dd;
            color: #0f5132;
        }
        
        .plan-status.failed {
            background: #f8d7da;
            color: #842029;
        }
        
        .plan-timeline {
            display: flex;
            gap: 1rem;
            font-size: 0.875rem;
            color: #6c757d;
            margin-bottom: 1rem;
        }
        
        .plan-steps {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        
        .plan-step {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            border-left: 4px solid #dee2e6;
            transition: all 0.3s ease;
        }
        
        .plan-step.step-pending {
            border-left-color: #ffc107;
        }
        
        .plan-step.step-in_progress {
            border-left-color: #0d6efd;
            background: #e7f1ff;
        }
        
        .plan-step.step-completed {
            border-left-color: #198754;
            background: #d1e7dd;
        }
        
        .plan-step.step-failed {
            border-left-color: #dc3545;
            background: #f8d7da;
        }
        
        .step-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }
        
        .step-status-icon {
            font-size: 1.25rem;
        }
        
        .step-description {
            flex: 1;
            font-weight: 500;
        }
        
        .step-duration {
            font-size: 0.875rem;
            color: #6c757d;
        }
        
        .step-progress-bar {
            height: 6px;
            background: #e9ecef;
            border-radius: 3px;
            overflow: hidden;
        }
        
        .step-progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #0d6efd, #0dcaf0);
            transition: width 0.5s ease;
        }
        
        .step-dependencies {
            font-size: 0.75rem;
            color: #6c757d;
            margin-top: 0.5rem;
        }
        
        .step-error {
            background: #dc3545;
            color: white;
            padding: 0.5rem;
            border-radius: 4px;
            margin-top: 0.5rem;
            font-size: 0.875rem;
        }
        '''


@dataclass
class FileDiff:
    """Represents a file diff."""
    file_path: str
    old_content: str
    new_content: str
    diff_lines: List[Dict[str, Any]]
    additions: int
    deletions: int


class DiffViewerComponent:
    """Component for viewing file diffs."""
    
    @staticmethod
    def generate_html(diff: FileDiff) -> str:
        """Generate HTML for diff viewer."""
        lines_html = ""
        for line in diff.diff_lines:
            line_type = line.get('type', 'context')
            line_number_old = line.get('old_line', '')
            line_number_new = line.get('new_line', '')
            content = line.get('content', '')
            
            line_class = f"diff-line-{line_type}"
            
            lines_html += f'''
            <div class="diff-line {line_class}">
                <span class="line-number old">{line_number_old}</span>
                <span class="line-number new">{line_number_new}</span>
                <span class="line-content">{DiffViewerComponent._escape_html(content)}</span>
            </div>
            '''
        
        return f'''
        <div class="diff-viewer">
            <div class="diff-header">
                <span class="diff-file-path">{diff.file_path}</span>
                <span class="diff-stats">
                    <span class="additions">+{diff.additions}</span>
                    <span class="deletions">-{diff.deletions}</span>
                </span>
            </div>
            <div class="diff-content">
                {lines_html}
            </div>
        </div>
        '''
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    @staticmethod
    def generate_css() -> str:
        """Generate CSS for diff viewer."""
        return '''
        .diff-viewer {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 0.875rem;
        }
        
        .diff-header {
            background: #f8f9fa;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .diff-file-path {
            font-weight: 600;
            color: #212529;
        }
        
        .diff-stats {
            display: flex;
            gap: 1rem;
            font-weight: 600;
        }
        
        .diff-stats .additions {
            color: #198754;
        }
        
        .diff-stats .deletions {
            color: #dc3545;
        }
        
        .diff-content {
            max-height: 500px;
            overflow-y: auto;
        }
        
        .diff-line {
            display: flex;
            line-height: 1.5;
        }
        
        .diff-line:hover {
            background: #f8f9fa;
        }
        
        .line-number {
            width: 50px;
            text-align: right;
            padding: 0 0.5rem;
            color: #6c757d;
            user-select: none;
            border-right: 1px solid #dee2e6;
        }
        
        .line-number.old {
            background: #f8f9fa;
        }
        
        .line-number.new {
            background: #f8f9fa;
        }
        
        .line-content {
            flex: 1;
            padding: 0 0.5rem;
            white-space: pre;
        }
        
        .diff-line-addition {
            background: #d1e7dd;
        }
        
        .diff-line-addition .line-content {
            color: #0f5132;
        }
        
        .diff-line-deletion {
            background: #f8d7da;
        }
        
        .diff-line-deletion .line-content {
            color: #842029;
        }
        
        .diff-line-context {
            background: white;
        }
        '''


@dataclass
class ApprovalRequest:
    """Represents an approval request."""
    id: str
    title: str
    description: str
    operation_type: str  # file_create, file_modify, file_delete, command_execute
    risk_level: str  # safe, risky, dangerous
    details: Dict[str, Any]
    status: str  # pending, approved, rejected
    timestamp: str


class ApprovalInterfaceComponent:
    """Component for approval interface."""
    
    @staticmethod
    def generate_html(request: ApprovalRequest) -> str:
        """Generate HTML for approval interface."""
        risk_class = f"risk-{request.risk_level}"
        
        details_html = ""
        for key, value in request.details.items():
            details_html += f'<div class="approval-detail"><strong>{key}:</strong> {value}</div>'
        
        buttons_html = ""
        if request.status == 'pending':
            buttons_html = f'''
            <div class="approval-actions">
                <button class="btn-approve" onclick="approveRequest('{request.id}')">✓ Approve</button>
                <button class="btn-reject" onclick="rejectRequest('{request.id}')">✗ Reject</button>
            </div>
            '''
        
        return f'''
        <div class="approval-request {risk_class}" data-request-id="{request.id}">
            <div class="approval-header">
                <div class="approval-title">
                    <span class="approval-icon">{ApprovalInterfaceComponent._get_operation_icon(request.operation_type)}</span>
                    <h4>{request.title}</h4>
                </div>
                <span class="approval-risk {risk_class}">{request.risk_level}</span>
            </div>
            <div class="approval-description">{request.description}</div>
            <div class="approval-details">
                {details_html}
            </div>
            <div class="approval-timestamp">Requested: {request.timestamp}</div>
            {buttons_html}
        </div>
        '''
    
    @staticmethod
    def _get_operation_icon(operation_type: str) -> str:
        """Get icon for operation type."""
        icons = {
            'file_create': '📄',
            'file_modify': '✏️',
            'file_delete': '🗑️',
            'command_execute': '⚡'
        }
        return icons.get(operation_type, '❓')
    
    @staticmethod
    def generate_css() -> str:
        """Generate CSS for approval interface."""
        return '''
        .approval-request {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            border-left: 4px solid #dee2e6;
        }
        
        .approval-request.risk-safe {
            border-left-color: #198754;
        }
        
        .approval-request.risk-risky {
            border-left-color: #ffc107;
        }
        
        .approval-request.risk-dangerous {
            border-left-color: #dc3545;
        }
        
        .approval-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .approval-title {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .approval-icon {
            font-size: 1.5rem;
        }
        
        .approval-title h4 {
            margin: 0;
            color: #212529;
        }
        
        .approval-risk {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .approval-risk.risk-safe {
            background: #d1e7dd;
            color: #0f5132;
        }
        
        .approval-risk.risk-risky {
            background: #fff3cd;
            color: #856404;
        }
        
        .approval-risk.risk-dangerous {
            background: #f8d7da;
            color: #842029;
        }
        
        .approval-description {
            color: #495057;
            margin-bottom: 1rem;
        }
        
        .approval-details {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }
        
        .approval-detail {
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }
        
        .approval-timestamp {
            font-size: 0.75rem;
            color: #6c757d;
            margin-bottom: 1rem;
        }
        
        .approval-actions {
            display: flex;
            gap: 1rem;
        }
        
        .btn-approve {
            background: #198754;
            color: white;
            padding: 0.5rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.3s ease;
        }
        
        .btn-approve:hover {
            background: #157347;
        }
        
        .btn-reject {
            background: #dc3545;
            color: white;
            padding: 0.5rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.3s ease;
        }
        
        .btn-reject:hover {
            background: #bb2d3b;
        }
        '''


@dataclass
class ProgressMetrics:
    """Represents progress metrics."""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    in_progress_tasks: int
    estimated_time_remaining: int  # seconds
    elapsed_time: int  # seconds


class ProgressDashboardComponent:
    """Component for progress dashboard."""
    
    @staticmethod
    def generate_html(metrics: ProgressMetrics, recent_activities: List[Dict[str, Any]]) -> str:
        """Generate HTML for progress dashboard."""
        completion_percentage = (metrics.completed_tasks / metrics.total_tasks * 100) if metrics.total_tasks > 0 else 0
        
        activities_html = ""
        for activity in recent_activities[:10]:  # Show last 10 activities
            activities_html += f'''
            <div class="activity-item">
                <span class="activity-icon">{activity.get('icon', '•')}</span>
                <span class="activity-text">{activity.get('text', '')}</span>
                <span class="activity-time">{activity.get('time', '')}</span>
            </div>
            '''
        
        return f'''
        <div class="progress-dashboard">
            <div class="dashboard-header">
                <h3>Progress Dashboard</h3>
            </div>
            
            <div class="dashboard-metrics">
                <div class="metric-card">
                    <div class="metric-value">{metrics.total_tasks}</div>
                    <div class="metric-label">Total Tasks</div>
                </div>
                <div class="metric-card success">
                    <div class="metric-value">{metrics.completed_tasks}</div>
                    <div class="metric-label">Completed</div>
                </div>
                <div class="metric-card warning">
                    <div class="metric-value">{metrics.in_progress_tasks}</div>
                    <div class="metric-label">In Progress</div>
                </div>
                <div class="metric-card danger">
                    <div class="metric-value">{metrics.failed_tasks}</div>
                    <div class="metric-label">Failed</div>
                </div>
            </div>
            
            <div class="dashboard-progress">
                <div class="progress-label">
                    <span>Overall Progress</span>
                    <span>{completion_percentage:.1f}%</span>
                </div>
                <div class="progress-bar-large">
                    <div class="progress-fill-large" style="width: {completion_percentage}%"></div>
                </div>
            </div>
            
            <div class="dashboard-time">
                <div class="time-metric">
                    <span class="time-label">Elapsed Time:</span>
                    <span class="time-value">{ProgressDashboardComponent._format_time(metrics.elapsed_time)}</span>
                </div>
                <div class="time-metric">
                    <span class="time-label">Estimated Remaining:</span>
                    <span class="time-value">{ProgressDashboardComponent._format_time(metrics.estimated_time_remaining)}</span>
                </div>
            </div>
            
            <div class="dashboard-activities">
                <h4>Recent Activities</h4>
                <div class="activities-list">
                    {activities_html}
                </div>
            </div>
        </div>
        '''
    
    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format time in human-readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def generate_css() -> str:
        """Generate CSS for progress dashboard."""
        return '''
        .progress-dashboard {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .dashboard-header h3 {
            margin-bottom: 1.5rem;
            color: #212529;
        }
        
        .dashboard-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .metric-card {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #dee2e6;
        }
        
        .metric-card.success {
            border-left-color: #198754;
        }
        
        .metric-card.warning {
            border-left-color: #ffc107;
        }
        
        .metric-card.danger {
            border-left-color: #dc3545;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #212529;
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: #6c757d;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .dashboard-progress {
            margin-bottom: 1.5rem;
        }
        
        .progress-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #495057;
        }
        
        .progress-bar-large {
            height: 24px;
            background: #e9ecef;
            border-radius: 12px;
            overflow: hidden;
        }
        
        .progress-fill-large {
            height: 100%;
            background: linear-gradient(90deg, #198754, #20c997);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 0.5rem;
            color: white;
            font-weight: 600;
            font-size: 0.875rem;
        }
        
        .dashboard-time {
            display: flex;
            gap: 2rem;
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .time-metric {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        
        .time-label {
            font-size: 0.875rem;
            color: #6c757d;
        }
        
        .time-value {
            font-size: 1.25rem;
            font-weight: 600;
            color: #212529;
        }
        
        .dashboard-activities h4 {
            margin-bottom: 1rem;
            color: #495057;
        }
        
        .activities-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .activity-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            border-bottom: 1px solid #e9ecef;
        }
        
        .activity-item:last-child {
            border-bottom: none;
        }
        
        .activity-icon {
            font-size: 1.25rem;
        }
        
        .activity-text {
            flex: 1;
            color: #495057;
        }
        
        .activity-time {
            font-size: 0.75rem;
            color: #6c757d;
        }
        '''


class WebComponentsManager:
    """Manager for all web components."""
    
    def __init__(self):
        self.plan_viz = PlanVisualizationComponent()
        self.diff_viewer = DiffViewerComponent()
        self.approval_interface = ApprovalInterfaceComponent()
        self.progress_dashboard = ProgressDashboardComponent()
    
    def get_all_css(self) -> str:
        """Get combined CSS for all components."""
        return "\n\n".join([
            self.plan_viz.generate_css(),
            self.diff_viewer.generate_css(),
            self.approval_interface.generate_css(),
            self.progress_dashboard.generate_css()
        ])
    
    def render_plan(self, plan: ExecutionPlan) -> str:
        """Render plan visualization."""
        return self.plan_viz.generate_html(plan)
    
    def render_diff(self, diff: FileDiff) -> str:
        """Render diff viewer."""
        return self.diff_viewer.generate_html(diff)
    
    def render_approval(self, request: ApprovalRequest) -> str:
        """Render approval interface."""
        return self.approval_interface.generate_html(request)
    
    def render_dashboard(self, metrics: ProgressMetrics, activities: List[Dict[str, Any]]) -> str:
        """Render progress dashboard."""
        return self.progress_dashboard.generate_html(metrics, activities)
