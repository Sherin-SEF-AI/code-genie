#!/usr/bin/env python3
"""
Demo: Predictive Development Assistant

This demo showcases the predictive development assistant capabilities including:
- Development pattern analysis
- Velocity and productivity metrics
- Proactive suggestion generation
- Future issue prediction
- Process optimization recommendations
"""

import asyncio
from datetime import datetime, timedelta
from src.codegenie.core.predictive_engine import (
    PredictiveDevelopmentAssistant,
    PatternType,
    PredictionType,
    ConfidenceLevel
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_pattern(pattern):
    """Print a development pattern."""
    print(f"📊 {pattern.name}")
    print(f"   Type: {pattern.type.value}")
    print(f"   Description: {pattern.description}")
    print(f"   Frequency: {pattern.frequency}")
    print(f"   Confidence: {pattern.confidence.value}")
    print(f"   Context: {pattern.context}")
    print()


def print_velocity_metrics(metrics):
    """Print velocity metrics."""
    print(f"📈 Development Velocity Metrics:")
    print(f"   Commits per day: {metrics.commits_per_day:.2f}")
    print(f"   Lines changed per day: {metrics.lines_changed_per_day:.2f}")
    print(f"   Files modified per day: {metrics.files_modified_per_day:.2f}")
    print(f"   Features completed per week: {metrics.features_completed_per_week:.2f}")
    print(f"   Bugs fixed per week: {metrics.bugs_fixed_per_week:.2f}")
    print(f"   Code review time (hours): {metrics.code_review_time_hours:.2f}")
    print(f"   Build success rate: {metrics.build_success_rate:.1f}%")
    print(f"   Test coverage: {metrics.test_coverage_percentage:.1f}%")
    print(f"   Technical debt ratio: {metrics.technical_debt_ratio:.2f}%")
    print()


def print_collaboration_pattern(pattern):
    """Print collaboration pattern."""
    print(f"👥 Team Collaboration Patterns:")
    print(f"   Pair programming frequency: {pattern.pair_programming_frequency:.2f}")
    print(f"   Code review participation: {pattern.code_review_participation:.1f}%")
    print(f"   Knowledge sharing events: {pattern.knowledge_sharing_events}")
    print(f"   Cross-team interactions: {pattern.cross_team_interactions}")
    print(f"   Communication channels: {', '.join(pattern.communication_channels_used)}")
    print(f"   Meeting frequency (per week): {pattern.meeting_frequency:.1f}")
    print(f"   Documentation updates: {pattern.documentation_updates}")
    print()


def print_project_trends(trends):
    """Print project trends."""
    print(f"📉 Project Evolution Trends:")
    print(f"   Complexity trend: {trends.complexity_trend}")
    print(f"   Quality trend: {trends.quality_trend}")
    print(f"   Velocity trend: {trends.velocity_trend}")
    print(f"   Team size trend: {trends.team_size_trend}")
    print(f"   Technology adoption rate: {trends.technology_adoption_rate:.2f}")
    print(f"   Refactoring frequency: {trends.refactoring_frequency:.2f}")
    print(f"   Bug introduction rate: {trends.bug_introduction_rate:.2f}")
    print(f"   Feature completion rate: {trends.feature_completion_rate:.2f}")
    print()


def print_suggestion(suggestion):
    """Print a predictive suggestion."""
    priority_emoji = "🔴" if suggestion.priority >= 8 else "🟡" if suggestion.priority >= 5 else "🟢"
    print(f"{priority_emoji} {suggestion.title} (Priority: {suggestion.priority}/10)")
    print(f"   Type: {suggestion.type.value}")
    print(f"   Confidence: {suggestion.confidence.value}")
    print(f"   Description: {suggestion.description}")
    print(f"   Reasoning: {suggestion.reasoning}")
    print(f"   Estimated Impact: {suggestion.estimated_impact}")
    print(f"   Estimated Effort: {suggestion.estimated_effort}")
    print(f"   Suggested Actions:")
    for action in suggestion.suggested_actions:
        print(f"      • {action}")
    print()


async def demo_pattern_analysis():
    """Demonstrate development pattern analysis."""
    print_section("1. Development Pattern Analysis")
    
    assistant = PredictiveDevelopmentAssistant()
    
    # Sample project data
    project_data = {
        'commits': [
            {
                'timestamp': '2024-01-01T09:00:00',
                'message': 'Add user authentication',
                'author': 'alice'
            },
            {
                'timestamp': '2024-01-01T14:30:00',
                'message': 'Fix security vulnerability',
                'author': 'bob'
            },
            {
                'timestamp': '2024-01-02T10:15:00',
                'message': 'Refactor database layer',
                'author': 'alice'
            },
            {
                'timestamp': '2024-01-02T15:45:00',
                'message': 'Add integration tests',
                'author': 'charlie'
            },
            {
                'timestamp': '2024-01-03T09:30:00',
                'message': 'Update documentation',
                'author': 'alice'
            }
        ],
        'file_changes': [
            {
                'file_path': 'src/auth.py',
                'lines_added': 120,
                'lines_deleted': 20
            },
            {
                'file_path': 'src/security.py',
                'lines_added': 30,
                'lines_deleted': 5
            },
            {
                'file_path': 'tests/test_auth.py',
                'lines_added': 80,
                'lines_deleted': 0
            },
            {
                'file_path': 'src/database.py',
                'lines_added': 150,
                'lines_deleted': 75
            },
            {
                'file_path': 'README.md',
                'lines_added': 25,
                'lines_deleted': 10
            }
        ],
        'test_data': {
            'test_runs_per_week': 25,
            'average_coverage': 78,
            'test_types': ['unit', 'integration', 'e2e']
        },
        'features': [
            {'name': 'User Auth', 'status': 'completed'},
            {'name': 'API Gateway', 'status': 'completed'},
            {'name': 'Payment Integration', 'status': 'in_progress'}
        ],
        'bugs': [
            {'id': 1, 'status': 'fixed'},
            {'id': 2, 'status': 'fixed'},
            {'id': 3, 'status': 'open'}
        ],
        'code_reviews': [
            {'review_time_hours': 1.5},
            {'review_time_hours': 2.0},
            {'review_time_hours': 1.0}
        ],
        'builds': [
            {'status': 'success'},
            {'status': 'success'},
            {'status': 'failure'},
            {'status': 'success'}
        ],
        'test_results': {
            'coverage_percentage': 78
        },
        'code_smells': ['long_method', 'duplicate_code', 'complex_conditional']
    }
    
    # Analyze patterns
    print("Analyzing development patterns...")
    patterns = await assistant.pattern_analyzer.analyze_workflow_patterns(project_data)
    
    print(f"\nFound {len(patterns)} development patterns:\n")
    for pattern in patterns:
        print_pattern(pattern)


async def demo_velocity_metrics():
    """Demonstrate velocity and productivity metrics."""
    print_section("2. Velocity and Productivity Metrics")
    
    assistant = PredictiveDevelopmentAssistant()
    
    project_data = {
        'commits': [
            {'timestamp': f'2024-01-{i:02d}T10:00:00', 'message': f'Commit {i}'}
            for i in range(1, 11)
        ],
        'file_changes': [
            {'file_path': f'src/module_{i}.py', 'lines_added': 50 + i * 10, 'lines_deleted': 10 + i * 2}
            for i in range(1, 11)
        ],
        'features': [
            {'name': f'Feature {i}', 'status': 'completed' if i <= 7 else 'in_progress'}
            for i in range(1, 11)
        ],
        'bugs': [
            {'id': i, 'status': 'fixed' if i <= 5 else 'open'}
            for i in range(1, 8)
        ],
        'code_reviews': [
            {'review_time_hours': 1.5 + i * 0.2}
            for i in range(5)
        ],
        'builds': [
            {'status': 'success' if i % 4 != 0 else 'failure'}
            for i in range(20)
        ],
        'test_results': {
            'coverage_percentage': 82
        },
        'code_smells': ['long_method'] * 3
    }
    
    print("Calculating velocity metrics...")
    metrics = await assistant.pattern_analyzer.calculate_velocity_metrics(project_data)
    print_velocity_metrics(metrics)


async def demo_collaboration_analysis():
    """Demonstrate team collaboration pattern analysis."""
    print_section("3. Team Collaboration Analysis")
    
    assistant = PredictiveDevelopmentAssistant()
    
    team_data = {
        'pair_programming_sessions': [
            {'date': '2024-01-01', 'participants': ['alice', 'bob']},
            {'date': '2024-01-03', 'participants': ['bob', 'charlie']}
        ],
        'code_reviews': [
            {'participated': True, 'review_time_hours': 1.5},
            {'participated': True, 'review_time_hours': 2.0},
            {'participated': False, 'review_time_hours': 0},
            {'participated': True, 'review_time_hours': 1.0}
        ],
        'meetings': [
            {'type': 'knowledge_sharing', 'duration_minutes': 60},
            {'type': 'standup', 'duration_minutes': 15},
            {'type': 'standup', 'duration_minutes': 15},
            {'type': 'retrospective', 'duration_minutes': 90}
        ],
        'communications': [
            {'channel': 'slack', 'cross_team': True},
            {'channel': 'slack', 'cross_team': False},
            {'channel': 'email', 'cross_team': True},
            {'channel': 'teams', 'cross_team': False}
        ],
        'documentation_updates': [
            {'file': 'README.md'},
            {'file': 'API.md'},
            {'file': 'CONTRIBUTING.md'}
        ]
    }
    
    print("Analyzing collaboration patterns...")
    collaboration = await assistant.pattern_analyzer.analyze_collaboration_patterns(team_data)
    print_collaboration_pattern(collaboration)


async def demo_project_trends():
    """Demonstrate project evolution trend analysis."""
    print_section("4. Project Evolution Trends")
    
    assistant = PredictiveDevelopmentAssistant()
    
    historical_data = [
        {
            'date': f'2024-01-{i:02d}',
            'complexity_score': 5.0 + (i * 0.15),
            'quality_score': 8.5 - (i * 0.05),
            'velocity_score': 7.0 + (i * 0.1),
            'team_size': 3 + (i // 10),
            'technology_changes': 1 if i % 7 == 0 else 0,
            'refactoring_events': 1 if i % 5 == 0 else 0,
            'bugs_introduced': 1 if i % 3 == 0 else 0,
            'features_completed': 1 if i % 4 == 0 else 0
        }
        for i in range(1, 21)
    ]
    
    print("Analyzing project trends...")
    trends = await assistant.pattern_analyzer.analyze_project_trends(historical_data)
    print_project_trends(trends)


async def demo_proactive_suggestions():
    """Demonstrate proactive suggestion generation."""
    print_section("5. Proactive Suggestions")
    
    assistant = PredictiveDevelopmentAssistant()
    
    context = {
        'current_files': ['src/auth.py', 'src/payment.py', 'src/utils.py'],
        'recent_changes': [
            {'file_path': 'src/auth.py', 'lines_changed': 180},
            {'file_path': 'src/payment.py', 'lines_changed': 150}
        ],
        'project_state': {
            'test_coverage': 55,
            'has_readme': False
        },
        'complexity_trend': 'increasing',
        'performance_metrics': {
            'response_time_trend': 'increasing'
        },
        'average_build_time_minutes': 12,
        'outdated_dependencies': 8
    }
    
    print("Generating proactive suggestions...")
    suggestions = await assistant.generate_proactive_suggestions(context)
    
    print(f"\nGenerated {len(suggestions)} suggestions:\n")
    for suggestion in suggestions[:5]:  # Show top 5
        print_suggestion(suggestion)


async def demo_comprehensive_analysis():
    """Demonstrate comprehensive development context analysis."""
    print_section("6. Comprehensive Development Analysis")
    
    assistant = PredictiveDevelopmentAssistant()
    
    comprehensive_data = {
        'commits': [
            {'timestamp': f'2024-01-{i:02d}T{(i % 24):02d}:00:00', 'message': f'Commit {i}', 'author': f'dev{i % 3}'}
            for i in range(1, 16)
        ],
        'file_changes': [
            {'file_path': f'src/module_{i}.py', 'lines_added': 50 + i * 5, 'lines_deleted': 10 + i}
            for i in range(1, 11)
        ],
        'test_data': {
            'test_runs_per_week': 30,
            'average_coverage': 75,
            'test_types': ['unit', 'integration']
        },
        'team_data': {
            'pair_programming_sessions': [{'date': '2024-01-01'}],
            'code_reviews': [
                {'participated': True, 'review_time_hours': 1.5},
                {'participated': True, 'review_time_hours': 2.0}
            ],
            'meetings': [
                {'type': 'knowledge_sharing'},
                {'type': 'standup'}
            ],
            'communications': [
                {'channel': 'slack', 'cross_team': True}
            ],
            'documentation_updates': [{'file': 'README.md'}]
        },
        'historical_data': [
            {
                'complexity_score': 5.0 + (i * 0.1),
                'quality_score': 8.0 - (i * 0.05),
                'velocity_score': 7.0 + (i * 0.02),
                'team_size': 3,
                'technology_changes': 0,
                'refactoring_events': 1 if i % 5 == 0 else 0,
                'bugs_introduced': 1 if i % 3 == 0 else 0,
                'features_completed': 1 if i % 4 == 0 else 0
            }
            for i in range(10)
        ],
        'features': [
            {'name': 'Feature A', 'status': 'completed'},
            {'name': 'Feature B', 'status': 'completed'}
        ],
        'bugs': [
            {'id': 1, 'status': 'fixed'},
            {'id': 2, 'status': 'fixed'}
        ],
        'code_reviews': [{'review_time_hours': 1.5}],
        'builds': [{'status': 'success'}] * 10,
        'test_results': {'coverage_percentage': 75},
        'code_smells': ['long_method']
    }
    
    print("Performing comprehensive analysis...")
    analysis = await assistant.analyze_development_context(comprehensive_data)
    
    print("\n📊 Analysis Results:\n")
    print(f"Patterns detected: {len(analysis['patterns'])}")
    print(f"Analysis timestamp: {analysis['analysis_timestamp']}")
    print()
    
    print_velocity_metrics(analysis['velocity_metrics'])
    print_collaboration_pattern(analysis['collaboration_patterns'])
    print_project_trends(analysis['project_trends'])


async def demo_prediction_accuracy():
    """Demonstrate prediction accuracy metrics."""
    print_section("7. Prediction Accuracy Metrics")
    
    assistant = PredictiveDevelopmentAssistant()
    
    print("Calculating prediction accuracy metrics...")
    metrics = await assistant.get_prediction_accuracy_metrics()
    
    print("📈 Prediction Accuracy Metrics:\n")
    for metric_name, value in metrics.items():
        percentage = value * 100
        bar_length = int(percentage / 5)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"   {metric_name.replace('_', ' ').title()}: {bar} {percentage:.1f}%")
    print()


async def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("  PREDICTIVE DEVELOPMENT ASSISTANT DEMO")
    print("=" * 80)
    
    try:
        await demo_pattern_analysis()
        await demo_velocity_metrics()
        await demo_collaboration_analysis()
        await demo_project_trends()
        await demo_proactive_suggestions()
        await demo_comprehensive_analysis()
        await demo_prediction_accuracy()
        
        print_section("Demo Complete!")
        print("✅ All predictive development assistant features demonstrated successfully!")
        print("\nKey Capabilities:")
        print("  • Development pattern recognition and analysis")
        print("  • Velocity and productivity metrics calculation")
        print("  • Team collaboration pattern detection")
        print("  • Project evolution trend analysis")
        print("  • Proactive suggestion generation")
        print("  • Future issue prediction")
        print("  • Process optimization recommendations")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
