#!/bin/bash

# Integration script for CodeGenie features
# This script stages and commits all new features for integration

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     CodeGenie Feature Integration Script                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

echo "📋 Step 1: Staging new core modules..."
git add src/codegenie/core/planning_agent.py
git add src/codegenie/core/file_creator.py
git add src/codegenie/core/command_executor.py
git add src/codegenie/core/approval_system.py
git add src/codegenie/core/project_scaffolder.py
git add src/codegenie/core/template_manager.py
git add src/codegenie/core/builtin_templates.py
git add src/codegenie/core/context_analyzer.py
git add src/codegenie/core/dependency_manager.py
git add src/codegenie/core/diff_engine.py
git add src/codegenie/core/error_recovery_system.py
echo "✓ Core modules staged"

echo ""
echo "📋 Step 2: Staging modified files..."
git add src/codegenie/core/multi_file_editor.py
echo "✓ Modified files staged"

echo ""
echo "📋 Step 3: Staging documentation..."
git add docs/COMMAND_EXECUTOR_GUIDE.md
git add docs/CONTEXT_ANALYZER_GUIDE.md
git add docs/DIFF_ENGINE_GUIDE.md
git add docs/ERROR_RECOVERY_SYSTEM_GUIDE.md
git add docs/TEMPLATE_SYSTEM_GUIDE.md
echo "✓ Documentation staged"

echo ""
echo "📋 Step 4: Staging demo scripts..."
git add demo_planning_agent.py
git add demo_file_creator.py
git add demo_command_executor.py
git add demo_approval_system.py
git add demo_project_scaffolder.py
git add demo_template_system.py
git add demo_context_analyzer.py
git add demo_dependency_manager.py
git add demo_diff_engine.py
git add demo_multi_file_editor.py
git add demo_error_recovery_system.py
echo "✓ Demo scripts staged"

echo ""
echo "📋 Step 5: Staging test scripts..."
git add test_file_creator_simple.py test_file_creator_direct.py
git add test_command_executor_simple.py test_command_executor_standalone.py
git add test_approval_system_simple.py
git add test_project_scaffolder_simple.py test_scaffolder_direct.py
git add test_template_system_standalone.py
git add test_context_analyzer_simple.py
git add test_dependency_manager_simple.py
git add test_diff_engine_simple.py
git add test_multi_file_editor_simple.py
git add test_error_recovery_system_simple.py
echo "✓ Test scripts staged"

echo ""
echo "📋 Step 6: Staging examples..."
git add example_approval_integration.py
git add example_command_executor_integration.py
echo "✓ Examples staged"

echo ""
echo "📋 Step 7: Staging specifications..."
git add .kiro/specs/claude-code-features/
echo "✓ Specifications staged"

echo ""
echo "📋 Step 8: Staging summaries and guides..."
git add TASK_*_SUMMARY.md
git add CLAUDE_CODE_FEATURES_SPEC_SUMMARY.md
git add PHASE1_TASK1_SUMMARY.md
git add INTEGRATION_GUIDE.md
echo "✓ Summaries and guides staged"

echo ""
echo "📊 Git Status:"
git status --short

echo ""
echo "📝 Creating commit..."
git commit -m "feat: Add Claude Code-like features to CodeGenie

Implemented 11 major features across 3 phases:

Phase 1 - Core Infrastructure:
- Planning Agent: Intelligent task planning and execution
- File Creator: Automatic file generation with diff preview
- Command Executor: Safe command execution with approval
- Approval System: User approval workflows

Phase 2 - Project Management:
- Project Scaffolder: Automated project structure generation
- Template System: Project templates with customization
- Context Analyzer: Project structure and convention analysis
- Dependency Manager: Automatic dependency management

Phase 3 - Advanced Features:
- Diff Engine: Advanced diff generation and display
- Multi-File Editor: Coordinated multi-file editing
- Error Recovery System: Intelligent error recovery with learning

Features include:
✓ 11 new core modules (6,500+ lines of code)
✓ 5 comprehensive documentation guides
✓ 11 demo scripts with examples
✓ 13 test scripts for validation
✓ 2 integration examples
✓ Complete specifications (requirements, design, tasks)
✓ 11 implementation summaries

All requirements satisfied: 1.1-11.5 (12 major requirements)

This transforms CodeGenie into a Claude Code-like intelligent coding
assistant with automatic planning, file operations, error recovery,
and learning capabilities.
"

echo ""
echo "✅ Commit created successfully!"
echo ""
echo "🚀 Next steps:"
echo "   1. Review the commit: git show"
echo "   2. Push to origin: git push origin main"
echo "   3. Or push to fork: git push fork main"
echo ""
echo "📖 See INTEGRATION_GUIDE.md for detailed integration instructions"
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Integration Complete! Ready to push.                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
