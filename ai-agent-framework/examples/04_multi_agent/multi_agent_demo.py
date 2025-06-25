#!/usr/bin/env python3
"""
Example 4: Multi-Agent System Demo

This demo showcases the complete multi-agent framework with:
- Multiple specialized agents working together
- Task coordination and communication
- Complex workflow orchestration
- Inter-agent messaging and resource allocation

Key Learning Concepts:
- Multi-agent coordination patterns
- Shared MCP server usage
- Agent-to-agent communication
- Workflow orchestration
- Resource allocation and conflict resolution
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.file_agent import FileAgent
from src.agents.task_agent import TaskAgent
from src.agents.coordinator_agent import CoordinatorAgent
from src.core.types import Task, Context


class MultiAgentOrchestrator:
    """
    Orchestrates multiple agents working together on complex tasks.
    
    This demonstrates the full multi-agent architecture where:
    - Each agent specializes in specific capabilities
    - Agents communicate through shared MCP servers
    - Complex workflows are coordinated across agents
    - Resource allocation and conflict resolution occur
    """
    
    def __init__(self):
        self.agents = {}
        self.active_workflows = {}
        self.task_counter = 0
    
    async def setup_agents(self):
        """Setup all agents in the system."""
        print("🤖 Setting up Multi-Agent System")
        print("=" * 45)
        
        # Create and setup File Agent
        print("📁 Setting up File Agent...")
        self.agents["file_agent"] = FileAgent()
        success = await self.agents["file_agent"].setup()
        if success:
            print("✅ File Agent ready")
        else:
            print("❌ File Agent failed to setup")
            return False
        
        # Create and setup Task Agent
        print("📋 Setting up Task Agent...")
        self.agents["task_agent"] = TaskAgent()
        success = await self.agents["task_agent"].setup()
        if success:
            print("✅ Task Agent ready")
        else:
            print("❌ Task Agent failed to setup")
            return False
        
        # Create and setup Coordinator Agent
        print("🎯 Setting up Coordinator Agent...")
        self.agents["coordinator_agent"] = CoordinatorAgent()
        success = await self.agents["coordinator_agent"].setup()
        if success:
            print("✅ Coordinator Agent ready")
        else:
            print("❌ Coordinator Agent failed to setup")
            return False
        
        print(f"\n🎉 Multi-Agent System ready with {len(self.agents)} agents!")
        return True
    
    def create_task(self, task_type: str, description: str, parameters: dict, agent: str = None) -> Task:
        """Create a task with unique ID."""
        self.task_counter += 1
        return Task(
            id=f"demo_task_{self.task_counter:03d}",
            type=task_type,
            description=description,
            parameters=parameters,
            assigned_agent=agent
        )
    
    async def demo_agent_coordination(self):
        """Demonstrate basic agent coordination."""
        print("\n🔄 Demo 1: Agent Coordination")
        print("-" * 35)
        
        # File Agent creates a project structure
        print("Step 1: File Agent creates project structure")
        create_project_task = self.create_task(
            "create_project",
            "Create a multi-agent demo project",
            {
                "name": "multi_agent_demo",
                "type": "python"
            }
        )
        
        result = await self.agents["file_agent"].execute_task(create_project_task)
        if result.success:
            print(f"✅ Project created: {result.data['summary']}")
        else:
            print(f"❌ Project creation failed: {result.error}")
        
        # Task Agent creates tasks for the project
        print("\nStep 2: Task Agent manages workflow")
        create_workflow_task = self.create_task(
            "create_task",
            "Create development workflow",
            {
                "type": "write_file",
                "description": "Add configuration file to project",
                "parameters": {
                    "path": "multi_agent_demo/config.json",
                    "content": json.dumps({
                        "project": "Multi-Agent Demo",
                        "agents": ["file_agent", "task_agent", "coordinator_agent"],
                        "version": "1.0.0"
                    }, indent=2)
                },
                "priority": 7
            }
        )
        
        result = await self.agents["task_agent"].execute_task(create_workflow_task)
        if result.success:
            print(f"✅ Workflow task created: {result.data['task_id']}")
        else:
            print(f"❌ Workflow creation failed: {result.error}")
        
        # Coordinator monitors the system
        print("\nStep 3: Coordinator monitors system status")
        monitor_task = self.create_task(
            "monitor_system",
            "Monitor multi-agent system health",
            {
                "scope": "full_system",
                "thresholds": {"tasks_pending": 10}
            }
        )
        
        result = await self.agents["coordinator_agent"].execute_task(monitor_task)
        if result.success:
            print(f"✅ System monitored - Status: {result.data['health_status']}")
            print(f"   Tasks pending: {result.data['system_status'].get('tasks_pending', 0)}")
            print(f"   Active agents: {result.data['system_status'].get('active_agents', 0)}")
        else:
            print(f"❌ Monitoring failed: {result.error}")
    
    async def demo_complex_workflow(self):
        """Demonstrate complex workflow orchestration."""
        print("\n🚀 Demo 2: Complex Workflow Orchestration")
        print("-" * 45)
        
        # Define a complex workflow
        workflow_definition = {
            "name": "document_processing_pipeline",
            "phases": [
                {
                    "name": "setup_phase",
                    "type": "sequential",
                    "steps": [
                        {
                            "name": "create_workspace",
                            "type": "create_directory",
                            "agent": "file_agent",
                            "parameters": {"path": "document_pipeline"},
                            "priority": 8
                        },
                        {
                            "name": "setup_structure",
                            "type": "organize_files",
                            "agent": "file_agent",
                            "parameters": {
                                "source_directory": ".",
                                "organize_by": "extension"
                            },
                            "priority": 7
                        }
                    ]
                },
                {
                    "name": "processing_phase",
                    "type": "parallel",
                    "steps": [
                        {
                            "name": "analyze_content",
                            "type": "analyze_directory",
                            "agent": "file_agent",
                            "parameters": {
                                "path": ".",
                                "include_content_analysis": True
                            },
                            "priority": 6
                        },
                        {
                            "name": "generate_report",
                            "type": "generate_reports",
                            "agent": "task_agent",
                            "parameters": {
                                "type": "summary",
                                "period": "current",
                                "include_details": True
                            },
                            "priority": 6
                        }
                    ]
                }
            ]
        }
        
        # Coordinator orchestrates the complex workflow
        orchestrate_task = self.create_task(
            "execute_complex_workflow",
            "Execute document processing pipeline",
            {
                "workflow": workflow_definition,
                "coordination_points": [1],  # Coordinate before processing phase
                "failure_handling": "retry"
            }
        )
        
        print("🎯 Coordinator executing complex workflow...")
        result = await self.agents["coordinator_agent"].execute_task(orchestrate_task)
        
        if result.success:
            print(f"✅ Complex workflow executed successfully!")
            print(f"   Workflow: {result.data['workflow_name']}")
            print(f"   Total phases: {result.data['total_phases']}")
            print(f"   Completed phases: {result.data['completed_phases']}")
            print(f"   Status: {result.data['execution_status']}")
        else:
            print(f"❌ Complex workflow failed: {result.error}")
    
    async def demo_communication_patterns(self):
        """Demonstrate inter-agent communication."""
        print("\n💬 Demo 3: Inter-Agent Communication")
        print("-" * 40)
        
        # Coordinator manages communications
        print("Step 1: Setting up communication channels")
        comm_task = self.create_task(
            "manage_communications",
            "Setup system communication",
            {
                "action": "status_check"
            }
        )
        
        result = await self.agents["coordinator_agent"].execute_task(comm_task)
        if result.success:
            print("✅ Communication system checked")
        
        # Demonstrate workload balancing
        print("\nStep 2: Coordinating agent workloads")
        coordination_task = self.create_task(
            "coordinate_agents",
            "Balance workload across agents",
            {
                "type": "workload_balance",
                "agents": ["file_agent", "task_agent"],
                "goal": "Optimize task distribution"
            }
        )
        
        result = await self.agents["coordinator_agent"].execute_task(coordination_task)
        if result.success:
            print(f"✅ Agent coordination completed")
            print(f"   Actions taken: {len(result.data['actions_taken'])}")
            for action in result.data['actions_taken']:
                print(f"   - {action}")
        
        # Demonstrate resource allocation
        print("\nStep 3: Allocating resources")
        allocation_task = self.create_task(
            "allocate_resources",
            "Allocate task capacity to agents",
            {
                "resource_type": "task_capacity",
                "strategy": "fair_share",
                "requestors": ["file_agent", "task_agent"]
            }
        )
        
        result = await self.agents["coordinator_agent"].execute_task(allocation_task)
        if result.success:
            print(f"✅ Resources allocated")
            print(f"   Allocation plan: {result.data['allocation_plan']}")
    
    async def demo_error_handling_resilience(self):
        """Demonstrate error handling and system resilience."""
        print("\n⚠️  Demo 4: Error Handling & Resilience")
        print("-" * 42)
        
        # Test 1: Invalid file operation
        print("Test 1: Handling invalid file operations")
        invalid_task = self.create_task(
            "read_file",
            "Try to read non-existent file",
            {"path": "/nonexistent/file.txt"}
        )
        
        result = await self.agents["file_agent"].execute_task(invalid_task)
        if not result.success:
            print(f"✅ Error handled gracefully: {result.error}")
        
        # Test 2: Emergency handling
        print("\nTest 2: Emergency response coordination")
        emergency_task = self.create_task(
            "handle_emergencies",
            "Simulate system emergency",
            {
                "type": "resource_exhaustion",
                "severity": "medium",
                "affected_systems": ["file_system", "task_queue"]
            }
        )
        
        result = await self.agents["coordinator_agent"].execute_task(emergency_task)
        if result.success:
            print(f"✅ Emergency handled - Status: {result.data['status']}")
            print(f"   Actions taken: {len(result.data['emergency_actions'])}")
        
        # Test 3: Conflict resolution
        print("\nTest 3: Conflict resolution")
        conflict_task = self.create_task(
            "resolve_conflicts",
            "Resolve resource conflict",
            {
                "type": "resource_conflict",
                "parties": ["file_agent", "task_agent"],
                "strategy": "mediation"
            }
        )
        
        result = await self.agents["coordinator_agent"].execute_task(conflict_task)
        if result.success:
            print(f"✅ Conflict resolved - Status: {result.data['status']}")
    
    async def demo_performance_analytics(self):
        """Demonstrate performance monitoring and analytics."""
        print("\n📊 Demo 5: Performance Analytics")
        print("-" * 35)
        
        # Task Agent analyzes performance
        print("Analyzing system performance...")
        performance_task = self.create_task(
            "analyze_performance",
            "Analyze multi-agent system performance",
            {
                "period": "current_session",
                "metrics": ["completion_rate", "error_rate", "avg_execution_time"]
            }
        )
        
        result = await self.agents["task_agent"].execute_task(performance_task)
        if result.success:
            print(f"✅ Performance analysis completed")
            perf_data = result.data['performance_data']
            print(f"   Completion rate: {perf_data.get('completion_rate', 0):.2%}")
            print(f"   Error rate: {perf_data.get('error_rate', 0):.2%}")
            print(f"   Summary: {result.data['summary']}")
        
        # Generate comprehensive report
        print("\nGenerating system report...")
        report_task = self.create_task(
            "generate_reports",
            "Generate comprehensive system report",
            {
                "type": "summary",
                "period": "current_session",
                "include_details": True
            }
        )
        
        result = await self.agents["task_agent"].execute_task(report_task)
        if result.success:
            print(f"✅ System report generated")
            report_data = result.data
            print(f"   Total tasks: {report_data['total_tasks']}")
            print(f"   Total agents: {report_data['agent_summary']['total_agents']}")
            print(f"   Active agents: {report_data['agent_summary']['active_agents']}")
    
    async def cleanup_demo_files(self):
        """Clean up files created during demos."""
        print("\n🧹 Cleaning up demo files...")
        
        cleanup_tasks = [
            ("multi_agent_demo", True),
            ("document_pipeline", True)
        ]
        
        for path, recursive in cleanup_tasks:
            try:
                cleanup_task = self.create_task(
                    "delete_file",
                    f"Clean up {path}",
                    {
                        "path": path,
                        "recursive": recursive,
                        "confirm": True
                    }
                )
                
                result = await self.agents["file_agent"].execute_task(cleanup_task)
                if result.success:
                    print(f"✅ Cleaned up {path}")
                else:
                    print(f"⚠️  Could not clean up {path}: {result.error}")
            except Exception as e:
                print(f"⚠️  Cleanup note for {path}: {e}")
    
    async def shutdown_agents(self):
        """Gracefully shutdown all agents."""
        print("\n👋 Shutting down agents...")
        for name, agent in self.agents.items():
            await agent.stop()
            print(f"✅ {name} stopped")


async def main():
    """Main multi-agent demo."""
    print("🎯 MCP Agent Framework - Example 4: Multi-Agent System")
    print("=" * 60)
    print()
    print("This demo showcases a complete multi-agent system where:")
    print("• Multiple specialized agents work together")
    print("• Agents communicate through shared MCP servers")
    print("• Complex workflows are orchestrated across agents")
    print("• Resource allocation and conflict resolution occur")
    print("• System monitoring and analytics are performed")
    print()
    
    orchestrator = MultiAgentOrchestrator()
    
    try:
        # Setup the multi-agent system
        success = await orchestrator.setup_agents()
        if not success:
            print("❌ Failed to setup multi-agent system")
            return
        
        # Run all demonstrations
        await orchestrator.demo_agent_coordination()
        await orchestrator.demo_complex_workflow() 
        await orchestrator.demo_communication_patterns()
        await orchestrator.demo_error_handling_resilience()
        await orchestrator.demo_performance_analytics()
        
        # Cleanup
        await orchestrator.cleanup_demo_files()
        
        print("\n🎉 Multi-Agent System Demo Completed Successfully!")
        print("\n🎓 Key Multi-Agent Concepts Demonstrated:")
        print("   • Agent specialization and collaboration")
        print("   • Shared MCP server architecture")
        print("   • Inter-agent communication patterns")
        print("   • Workflow orchestration and coordination")
        print("   • Resource allocation and conflict resolution")
        print("   • System monitoring and performance analytics")
        print("   • Error handling and resilience")
        print("   • Scalable agent framework design")
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted. Shutting down...")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    finally:
        await orchestrator.shutdown_agents()


if __name__ == "__main__":
    asyncio.run(main())