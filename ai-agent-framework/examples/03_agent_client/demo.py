#!/usr/bin/env python3
"""
Example 3: Interactive Agent Demo

This demo shows how to use the Simple Task Agent to perform various file operations.
It demonstrates the complete MCP client-server workflow:

1. Agent connects to MCP server
2. Discovers available tools
3. Analyzes tasks and selects appropriate tools  
4. Executes multi-step workflows
5. Returns intelligent responses

Run this demo to see MCP in action from the client perspective!
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from simple_agent import SimpleTaskAgent
from src.core.types import Task, Context


async def demo_basic_file_operations():
    """Demonstrate basic file operations using the agent."""
    print("🤖 MCP Agent Demo: Basic File Operations")
    print("=" * 50)
    
    # Create and setup the agent
    agent = SimpleTaskAgent()
    
    print("🔧 Setting up agent...")
    setup_success = await agent.setup()
    if not setup_success:
        print("❌ Agent setup failed!")
        return
    
    print("✅ Agent setup complete!")
    print(f"📊 Agent Status: {agent.get_status_info()}")
    print()
    
    # Example 1: Write a file
    print("Example 1: Writing a file")
    print("-" * 30)
    
    write_task = Task(
        id="write_001",
        type="write_file",
        description="Create a welcome message file",
        parameters={
            "path": "welcome.txt",
            "content": "Hello from MCP Agent!\n\nThis file was created by an AI agent using the Model Context Protocol (MCP).\n\nMCP enables agents to:\n- Connect to specialized servers\n- Discover available tools\n- Execute complex workflows\n- Handle errors gracefully\n\nPretty cool, right? 🚀"
        }
    )
    
    result = await agent.execute_task(write_task)
    if result.success:
        print(f"✅ {result.data['result']}")
        print(f"📝 Wrote {result.data['bytes_written']} bytes")
    else:
        print(f"❌ Error: {result.error}")
    print()
    
    # Example 2: Read the file back
    print("Example 2: Reading the file")
    print("-" * 28)
    
    read_task = Task(
        id="read_001",
        type="read_file",
        description="Read the welcome message",
        parameters={"path": "welcome.txt"}
    )
    
    result = await agent.execute_task(read_task)
    if result.success:
        print(f"📄 File content ({len(result.data['content'])} chars):")
        print("-" * 40)
        print(result.data['content'].split('\n\n', 1)[1])  # Skip the header
        print("-" * 40)
    else:
        print(f"❌ Error: {result.error}")
    print()
    
    # Example 3: Create a project
    print("Example 3: Creating a Python project")
    print("-" * 37)
    
    project_task = Task(
        id="project_001",
        type="create_project",
        description="Create a sample Python project",
        parameters={
            "name": "mcp_demo_project",
            "type": "python"
        }
    )
    
    result = await agent.execute_task(project_task)
    if result.success:
        print(f"✅ {result.data['summary']}")
        print(f"📁 Project structure:")
        print(result.data['structure'])
        print(f"📝 Created items:")
        for item in result.data['created_items']:
            print(f"  - {item}")
    else:
        print(f"❌ Error: {result.error}")
    print()
    
    # Example 4: Analyze the current directory
    print("Example 4: Directory analysis")
    print("-" * 30)
    
    analyze_task = Task(
        id="analyze_001",
        type="analyze_directory",
        description="Analyze the current directory",
        parameters={
            "path": ".",
            "include_content": True
        }
    )
    
    result = await agent.execute_task(analyze_task)
    if result.success:
        data = result.data
        print(f"📊 Directory: {data['path']}")
        print(f"📁 Directories: {data['total_directories']}")
        print(f"📄 Files: {data['total_files']}")
        print(f"💾 Total size: {data['total_size_bytes']} bytes")
        
        if 'file_samples' in data:
            print(f"📋 File samples:")
            for file_name, sample in data['file_samples'].items():
                print(f"  {file_name}: {sample[:100]}...")
    else:
        print(f"❌ Error: {result.error}")
    print()
    
    # Example 5: File summary
    print("Example 5: File summary")
    print("-" * 23)
    
    summary_task = Task(
        id="summary_001",
        type="file_summary",
        description="Summarize the welcome file",
        parameters={"path": "welcome.txt"}
    )
    
    result = await agent.execute_task(summary_task)
    if result.success:
        data = result.data
        print(f"📄 File: {data['file_path']}")
        print(f"📊 Stats: {data['size_stats']['lines']} lines, {data['size_stats']['words']} words")
        print(f"🔍 Analysis: {data['analysis']}")
    else:
        print(f"❌ Error: {result.error}")
    print()
    
    # Cleanup
    print("🧹 Cleaning up demo files...")
    try:
        await agent.call_tool("delete_file", {"path": "welcome.txt"})
        await agent.call_tool("delete_file", {"path": "mcp_demo_project", "recursive": True})
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️  Cleanup note: {e}")
    
    await agent.stop()
    print()
    print("🎉 Demo completed successfully!")


async def demo_advanced_workflows():
    """Demonstrate more advanced agent workflows."""
    print("🚀 MCP Agent Demo: Advanced Workflows")
    print("=" * 45)
    
    agent = SimpleTaskAgent()
    await agent.setup()
    
    # Create a more complex project with multiple files
    print("Creating a multi-component project...")
    
    # Create main project
    project_task = Task(
        id="advanced_001",
        type="create_project",
        description="Create advanced project structure",
        parameters={
            "name": "advanced_mcp_demo", 
            "type": "python"
        }
    )
    
    await agent.execute_task(project_task)
    
    # Add configuration files
    config_content = {
        "app_name": "Advanced MCP Demo",
        "version": "1.0.0",
        "mcp_servers": [
            {"name": "file_ops", "type": "stdio"},
            {"name": "task_mgmt", "type": "stdio"}
        ],
        "agent_config": {
            "max_concurrent_tasks": 5,
            "timeout_seconds": 30
        }
    }
    
    config_task = Task(
        id="config_001",
        type="write_file",
        description="Create configuration file",
        parameters={
            "path": "advanced_mcp_demo/config.json",
            "content": json.dumps(config_content, indent=2)
        }
    )
    
    await agent.execute_task(config_task)
    
    # Perform bulk analysis
    bulk_task = Task(
        id="bulk_001",
        type="bulk_operations",
        description="Count lines in all project files",
        parameters={
            "operation": "count_lines",
            "directory": "advanced_mcp_demo"
        }
    )
    
    result = await agent.execute_task(bulk_task)
    if result.success:
        print(f"📊 Bulk Analysis Results:")
        print(f"  Files processed: {result.data['files_processed']}")
        print(f"  Total lines: {result.data['total_lines']}")
        
        print("  File breakdown:")
        for file_result in result.data['results']:
            if 'lines' in file_result:
                print(f"    {file_result['file']}: {file_result['lines']} lines")
    
    # Cleanup
    await agent.call_tool("delete_file", {"path": "advanced_mcp_demo", "recursive": True})
    await agent.stop()
    
    print("✅ Advanced workflow demo completed!")


async def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("⚠️  MCP Agent Demo: Error Handling")
    print("=" * 40)
    
    agent = SimpleTaskAgent()
    await agent.setup()
    
    # Test 1: Try to read a non-existent file
    print("Test 1: Reading non-existent file")
    
    error_task = Task(
        id="error_001",
        type="read_file",
        description="Try to read missing file",
        parameters={"path": "nonexistent_file.txt"}
    )
    
    result = await agent.execute_task(error_task)
    if not result.success:
        print(f"✅ Correctly handled error: {result.error}")
    else:
        print("❌ Expected error but task succeeded")
    
    # Test 2: Try unsupported task type
    print("\nTest 2: Unsupported task type")
    
    unsupported_task = Task(
        id="error_002",
        type="unsupported_operation",
        description="Try unsupported task",
        parameters={}
    )
    
    result = await agent.execute_task(unsupported_task)
    if not result.success:
        print(f"✅ Correctly rejected unsupported task: {result.error}")
    
    # Test 3: Invalid parameters
    print("\nTest 3: Invalid parameters")
    
    invalid_task = Task(
        id="error_003",
        type="write_file",
        description="Try to write file without required parameters",
        parameters={"path": "test.txt"}  # Missing content
    )
    
    result = await agent.execute_task(invalid_task)
    if not result.success:
        print(f"✅ Correctly handled invalid parameters: {result.error}")
    
    await agent.stop()
    print("\n✅ Error handling demo completed!")


async def interactive_mode():
    """Run an interactive session with the agent."""
    print("💬 MCP Agent Interactive Mode")
    print("=" * 35)
    print("Available commands:")
    print("  read <file>     - Read a file")
    print("  write <file>    - Write to a file")  
    print("  analyze <dir>   - Analyze directory")
    print("  project <name>  - Create project")
    print("  status          - Show agent status")
    print("  quit            - Exit")
    print()
    
    agent = SimpleTaskAgent()
    await agent.setup()
    
    task_counter = 0
    
    try:
        while True:
            try:
                user_input = input("🤖 > ").strip()
                if not user_input:
                    continue
                
                if user_input.lower() == "quit":
                    break
                elif user_input.lower() == "status":
                    status = agent.get_status_info()
                    print(f"📊 Agent Status: {json.dumps(status, indent=2)}")
                    continue
                
                parts = user_input.split(" ", 1)
                command = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""
                
                task_counter += 1
                task_id = f"interactive_{task_counter:03d}"
                
                if command == "read" and arg:
                    task = Task(
                        id=task_id,
                        type="read_file",
                        description=f"Read file {arg}",
                        parameters={"path": arg}
                    )
                elif command == "write" and arg:
                    content = input("Enter content: ")
                    task = Task(
                        id=task_id,
                        type="write_file", 
                        description=f"Write to file {arg}",
                        parameters={"path": arg, "content": content}
                    )
                elif command == "analyze" and arg:
                    task = Task(
                        id=task_id,
                        type="analyze_directory",
                        description=f"Analyze directory {arg}",
                        parameters={"path": arg}
                    )
                elif command == "project" and arg:
                    task = Task(
                        id=task_id,
                        type="create_project",
                        description=f"Create project {arg}",
                        parameters={"name": arg, "type": "python"}
                    )
                else:
                    print(f"❌ Unknown command or missing argument: {user_input}")
                    continue
                
                print(f"🔄 Executing task {task_id}...")
                result = await agent.execute_task(task)
                
                if result.success:
                    print("✅ Task completed successfully!")
                    if isinstance(result.data, dict):
                        # Pretty print the result
                        for key, value in result.data.items():
                            if key == "content" and len(str(value)) > 200:
                                print(f"  {key}: {str(value)[:200]}...")
                            else:
                                print(f"  {key}: {value}")
                    else:
                        print(f"  Result: {result.data}")
                else:
                    print(f"❌ Task failed: {result.error}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    finally:
        await agent.stop()


async def main():
    """Main demo runner."""
    print("🎯 MCP Agent Framework - Example 3: Agent Client")
    print("=" * 55)
    print()
    print("This demo shows how AI agents use MCP (Model Context Protocol)")
    print("to connect with specialized servers and execute tasks.")
    print()
    print("Choose a demo:")
    print("1. Basic file operations")
    print("2. Advanced workflows") 
    print("3. Error handling")
    print("4. Interactive mode")
    print("5. All demos")
    print()
    
    try:
        choice = input("Enter your choice (1-5): ").strip()
        print()
        
        if choice == "1":
            await demo_basic_file_operations()
        elif choice == "2":
            await demo_advanced_workflows()
        elif choice == "3":
            await demo_error_handling()
        elif choice == "4":
            await interactive_mode()
        elif choice == "5":
            await demo_basic_file_operations()
            print("\n" + "="*60 + "\n")
            await demo_advanced_workflows()
            print("\n" + "="*60 + "\n")
            await demo_error_handling()
        else:
            print("Invalid choice. Running basic demo...")
            await demo_basic_file_operations()
    
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Demo error: {e}")
    
    print("\n🎓 Key MCP Learning Points:")
    print("  • Agents connect to MCP servers via stdio transport")
    print("  • Tool discovery happens automatically via MCP protocol")
    print("  • Agents can compose multiple tool calls into workflows")
    print("  • Error handling is built into the MCP client-server model")
    print("  • Context can be maintained across tool invocations")
    print("  • Agents can analyze tasks and select appropriate tools")


if __name__ == "__main__":
    asyncio.run(main())