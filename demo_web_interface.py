#!/usr/bin/env python3
"""
Demo script for CodeGenie Web Interface with Real-time Updates.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codegenie.core.agent import CodeGenieAgent
from codegenie.core.config import Config
from codegenie.ui.web_interface import WebInterface


async def simulate_workflow(web_interface: WebInterface):
    """Simulate a workflow with real-time updates."""
    await asyncio.sleep(5)  # Wait for server to start
    
    print("\n🔄 Simulating workflow with real-time updates...")
    
    # Simulate task progress
    task_id = "demo_task_1"
    await web_interface.progress_tracker.start_task(
        task_id, 
        "Building REST API", 
        total_steps=5
    )
    
    await asyncio.sleep(2)
    await web_interface.progress_tracker.update_progress(
        task_id, 1, "Creating project structure"
    )
    
    await asyncio.sleep(2)
    await web_interface.progress_tracker.update_progress(
        task_id, 2, "Installing dependencies"
    )
    
    # Simulate command execution
    command_id = "cmd_1"
    await web_interface.command_streamer.start_command(
        command_id, "npm install express"
    )
    
    await asyncio.sleep(1)
    await web_interface.command_streamer.stream_output(
        command_id, "npm WARN deprecated...", "stderr"
    )
    
    await asyncio.sleep(1)
    await web_interface.command_streamer.stream_output(
        command_id, "added 50 packages in 3s", "stdout"
    )
    
    await asyncio.sleep(1)
    await web_interface.command_streamer.complete_command(command_id, 0)
    
    await asyncio.sleep(2)
    await web_interface.progress_tracker.update_progress(
        task_id, 3, "Implementing authentication"
    )
    
    # Simulate plan execution
    plan_id = "plan_1"
    await web_interface.plan_tracker.start_plan(
        plan_id,
        "Create REST API",
        ["step1", "step2", "step3"]
    )
    
    await asyncio.sleep(2)
    await web_interface.plan_tracker.update_step(
        plan_id, "step1", "completed", 100, "Project structure created"
    )
    
    await asyncio.sleep(2)
    await web_interface.plan_tracker.update_step(
        plan_id, "step2", "in_progress", 50, "Implementing authentication"
    )
    
    await asyncio.sleep(2)
    await web_interface.progress_tracker.update_progress(
        task_id, 4, "Creating API endpoints"
    )
    
    await asyncio.sleep(2)
    await web_interface.plan_tracker.update_step(
        plan_id, "step2", "completed", 100, "Authentication complete"
    )
    
    await asyncio.sleep(2)
    await web_interface.progress_tracker.update_progress(
        task_id, 5, "Running tests"
    )
    
    await asyncio.sleep(2)
    await web_interface.plan_tracker.update_step(
        plan_id, "step3", "completed", 100, "API endpoints created"
    )
    
    await asyncio.sleep(1)
    await web_interface.progress_tracker.complete_task(
        task_id, "REST API successfully built!"
    )
    
    await asyncio.sleep(1)
    await web_interface.plan_tracker.complete_plan(plan_id)
    
    print("✅ Workflow simulation complete!")


async def main():
    """Main demo function."""
    print("=" * 60)
    print("CodeGenie Web Interface Demo")
    print("=" * 60)
    
    # Create config
    config = Config()
    config.debug = True
    config.verbose = True
    
    # Create agent
    agent = CodeGenieAgent(config)
    
    # Create web interface
    web_interface = WebInterface(agent, config)
    
    print("\n🚀 Starting web server...")
    print("📱 Open your browser to: http://localhost:8080")
    print("\n💡 Features to try:")
    print("   - 💬 Chat: Interactive chat with the agent")
    print("   - 📋 Plans: View execution plan visualizations")
    print("   - ✓ Approvals: Review and approve operations")
    print("   - 📊 Progress: Real-time progress dashboard")
    print("   - 🔄 Workflows: Create and execute workflows")
    print("\n🔴 Press Ctrl+C to stop the server\n")
    
    # Start workflow simulation in background
    asyncio.create_task(simulate_workflow(web_interface))
    
    # Start server (this will block)
    try:
        await web_interface.start_server(host="localhost", port=8080)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")


if __name__ == "__main__":
    asyncio.run(main())
