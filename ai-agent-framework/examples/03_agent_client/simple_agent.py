#!/usr/bin/env python3
"""
Example 3: Simple Task Agent

This example demonstrates how to build an AI agent that uses MCP servers.
It shows the client side of MCP - how agents discover, connect to, and use tools.

Key Learning Concepts:
- MCP client implementation patterns
- Agent task analysis and tool selection
- Error handling in agent workflows
- Context management across tool calls
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.base_agent import BaseAgent
from src.core.types import (
    Task, TaskResult, Context, AgentRegistration, MCPServerConfig
)
from typing import Dict, Any, Optional, List


class SimpleTaskAgent(BaseAgent):
    """
    A simple agent that specializes in file-based tasks.
    
    This agent demonstrates:
    - Connecting to the file operations MCP server
    - Analyzing tasks to determine required tools
    - Executing multi-step workflows using MCP tools
    - Providing intelligent responses based on tool results
    """
    
    def __init__(self):
        # Define this agent's capabilities and configuration
        registration = AgentRegistration(
            name="simple_task_agent",
            capabilities=[
                "file_operations",
                "text_processing", 
                "project_setup",
                "content_creation"
            ],
            supported_task_types=[
                "read_file",
                "write_file", 
                "create_project",
                "analyze_directory",
                "file_summary",
                "bulk_operations"
            ],
            priority=5,
            max_concurrent_tasks=2,
            config={
                "preferred_file_formats": ["txt", "md", "py", "json"],
                "max_file_size": "10MB"
            }
        )
        
        super().__init__("simple_task_agent", registration)
        
        # Task-specific state
        self._current_context: Optional[Dict[str, Any]] = None
        
    async def setup(self) -> bool:
        """Setup the agent by connecting to required MCP servers."""
        try:
            # Connect to the file operations server
            file_server_config = MCPServerConfig(
                name="file_operations_server",
                transport_type="stdio",
                command="python",
                args=["src/servers/file_operations_server.py"],
                tools=[
                    "read_file", "write_file", "list_directory", 
                    "create_directory", "get_file_info", "delete_file"
                ],
                resources=["file_system"]
            )
            
            success = await self.connect_to_server(file_server_config)
            if not success:
                self.logger.error("Failed to connect to file operations server")
                return False
            
            await self.start()
            self.logger.info("Simple Task Agent setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Agent setup failed: {e}")
            return False
    
    def _can_handle_task_specific(self, task: Task) -> bool:
        """Check if this agent can handle the specific task type."""
        # Check if we have the required tools for this task type
        required_tools = self._get_required_tools_for_task(task.type)
        available_tools = set(self._available_tools.keys())
        
        return all(tool in available_tools for tool in required_tools)
    
    def _get_required_tools_for_task(self, task_type: str) -> List[str]:
        """Map task types to required MCP tools."""
        tool_mapping = {
            "read_file": ["read_file"],
            "write_file": ["write_file"],
            "create_project": ["create_directory", "write_file", "list_directory"],
            "analyze_directory": ["list_directory", "get_file_info", "read_file"],
            "file_summary": ["read_file", "get_file_info"],
            "bulk_operations": ["list_directory", "read_file", "write_file"]
        }
        return tool_mapping.get(task_type, [])
    
    async def _execute_task_specific(self, task: Task, context: Optional[Context]) -> Dict[str, Any]:
        """Execute the task using appropriate MCP tools."""
        self._current_context = context.session_data if context else {}
        
        # Route to specific task handlers
        if task.type == "read_file":
            return await self._handle_read_file(task)
        elif task.type == "write_file":
            return await self._handle_write_file(task)
        elif task.type == "create_project":
            return await self._handle_create_project(task)
        elif task.type == "analyze_directory":
            return await self._handle_analyze_directory(task)
        elif task.type == "file_summary":
            return await self._handle_file_summary(task)
        elif task.type == "bulk_operations":
            return await self._handle_bulk_operations(task)
        else:
            raise ValueError(f"Unsupported task type: {task.type}")
    
    async def _handle_read_file(self, task: Task) -> Dict[str, Any]:
        """Handle file reading tasks."""
        file_path = task.parameters.get("path")
        if not file_path:
            raise ValueError("File path is required for read_file task")
        
        self.logger.info(f"Reading file: {file_path}")
        
        # Use MCP tool to read the file
        result = await self.call_tool("read_file", {"path": file_path})
        content = result.content[0].text
        
        # Get file info for additional context
        info_result = await self.call_tool("get_file_info", {"path": file_path})
        file_info = info_result.content[0].text
        
        return {
            "file_path": file_path,
            "content": content,
            "file_info": file_info,
            "summary": f"Successfully read {len(content)} characters from {file_path}"
        }
    
    async def _handle_write_file(self, task: Task) -> Dict[str, Any]:
        """Handle file writing tasks."""
        file_path = task.parameters.get("path")
        content = task.parameters.get("content")
        mode = task.parameters.get("mode", "write")
        
        if not file_path or content is None:
            raise ValueError("File path and content are required for write_file task") 
        
        self.logger.info(f"Writing to file: {file_path} (mode: {mode})")
        
        # Use MCP tool to write the file
        result = await self.call_tool("write_file", {
            "path": file_path,
            "content": content,
            "mode": mode
        })
        
        return {
            "file_path": file_path,
            "bytes_written": len(content),
            "mode": mode,
            "result": result.content[0].text
        }
    
    async def _handle_create_project(self, task: Task) -> Dict[str, Any]:
        """Handle project creation tasks - demonstrates multi-tool workflows."""
        project_name = task.parameters.get("name")
        project_type = task.parameters.get("type", "basic")
        
        if not project_name:
            raise ValueError("Project name is required")
        
        self.logger.info(f"Creating {project_type} project: {project_name}")
        
        created_items = []
        
        # Step 1: Create main project directory
        await self.call_tool("create_directory", {"path": project_name})
        created_items.append(f"directory: {project_name}/")
        
        # Step 2: Create project structure based on type
        if project_type == "python":
            # Python project structure
            dirs = ["src", "tests", "docs"]
            files = {
                "README.md": f"# {project_name}\n\nA Python project created by MCP Agent.\n",
                "requirements.txt": "# Add your dependencies here\n",
                "src/__init__.py": "",
                "src/main.py": f'"""\nMain module for {project_name}\n"""\n\ndef main():\n    print("Hello from {project_name}!")\n\nif __name__ == "__main__":\n    main()\n',
                "tests/__init__.py": "",
                "tests/test_main.py": f'"""\nTests for {project_name}\n"""\n\ndef test_example():\n    assert True\n'
            }
        else:
            # Basic project structure
            dirs = ["docs"]
            files = {
                "README.md": f"# {project_name}\n\nA project created by MCP Agent.\n",
                "notes.txt": "Project notes and ideas go here.\n"
            }
        
        # Create directories
        for dir_name in dirs:
            await self.call_tool("create_directory", {"path": f"{project_name}/{dir_name}"})
            created_items.append(f"directory: {project_name}/{dir_name}/")
        
        # Create files
        for file_path, content in files.items():
            await self.call_tool("write_file", {
                "path": f"{project_name}/{file_path}",
                "content": content
            })
            created_items.append(f"file: {project_name}/{file_path}")
        
        # Step 3: Verify the project structure
        result = await self.call_tool("list_directory", {"path": project_name})
        
        return {
            "project_name": project_name,
            "project_type": project_type,
            "created_items": created_items,
            "structure": result.content[0].text,
            "summary": f"Created {project_type} project '{project_name}' with {len(created_items)} items"
        }
    
    async def _handle_analyze_directory(self, task: Task) -> Dict[str, Any]:
        """Analyze a directory and provide insights."""
        dir_path = task.parameters.get("path", ".")
        include_content = task.parameters.get("include_content", False)
        
        self.logger.info(f"Analyzing directory: {dir_path}")
        
        # Get directory listing
        list_result = await self.call_tool("list_directory", {
            "path": dir_path,
            "include_hidden": False
        })
        
        directory_content = list_result.content[0].text
        
        # Parse the directory listing to get individual files
        lines = directory_content.split('\n')[1:]  # Skip header
        files = []
        directories = []
        total_size = 0
        
        for line in lines:
            if line.strip():
                if line.startswith("file:"):
                    file_name = line.split(": ", 1)[1]
                    # Extract size if present
                    if "(" in file_name and " bytes)" in file_name:
                        name_part = file_name.split(" (")[0]
                        size_part = file_name.split("(")[1].split(" bytes)")[0]
                        try:
                            size = int(size_part)
                            total_size += size
                        except ValueError:
                            pass
                        files.append(name_part)
                    else:
                        files.append(file_name)
                elif line.startswith("directory:"):
                    dir_name = line.split(": ", 1)[1]
                    directories.append(dir_name)
        
        analysis = {
            "path": dir_path,
            "total_files": len(files),
            "total_directories": len(directories),
            "total_size_bytes": total_size,
            "files": files,
            "directories": directories,
            "raw_listing": directory_content
        }
        
        # If requested, sample some file contents
        if include_content and files:
            sample_files = files[:3]  # Sample first 3 files
            file_samples = {}
            
            for file_name in sample_files:
                try:
                    file_path = f"{dir_path}/{file_name}" if dir_path != "." else file_name
                    content_result = await self.call_tool("read_file", {"path": file_path})
                    content = content_result.content[0].text
                    
                    # Store just first 200 characters as sample
                    file_samples[file_name] = content[:200] + ("..." if len(content) > 200 else "")
                except Exception as e:
                    file_samples[file_name] = f"Error reading file: {e}"
            
            analysis["file_samples"] = file_samples
        
        return analysis
    
    async def _handle_file_summary(self, task: Task) -> Dict[str, Any]:
        """Create a summary of a file's contents and metadata."""
        file_path = task.parameters.get("path")
        if not file_path:
            raise ValueError("File path is required")
        
        # Get file content
        content_result = await self.call_tool("read_file", {"path": file_path})
        content = content_result.content[0].text
        
        # Get file metadata
        info_result = await self.call_tool("get_file_info", {"path": file_path})
        file_info = info_result.content[0].text
        
        # Analyze content
        lines = content.split('\n')
        words = len(content.split())
        characters = len(content)
        
        # Detect file type based on content
        file_type = "text"
        if file_path.endswith(('.py',)):
            file_type = "python"
        elif file_path.endswith(('.md',)):
            file_type = "markdown"  
        elif file_path.endswith(('.json',)):
            file_type = "json"
        
        # Create summary
        summary = {
            "file_path": file_path,
            "file_type": file_type,
            "size_stats": {
                "lines": len(lines),
                "words": words,
                "characters": characters
            },
            "content_preview": content[:300] + ("..." if len(content) > 300 else ""),
            "file_info": file_info,
            "analysis": f"This {file_type} file contains {len(lines)} lines, {words} words, and {characters} characters."
        }
        
        return summary
    
    async def _handle_bulk_operations(self, task: Task) -> Dict[str, Any]:
        """Handle bulk file operations."""
        operation = task.parameters.get("operation")
        pattern = task.parameters.get("pattern", "*")
        directory = task.parameters.get("directory", ".")
        
        if not operation:
            raise ValueError("Operation type is required")
        
        self.logger.info(f"Performing bulk operation: {operation} in {directory}")
        
        # First, list the directory to get files
        list_result = await self.call_tool("list_directory", {"path": directory})
        directory_content = list_result.content[0].text
        
        # Extract file names (simple parsing)
        lines = directory_content.split('\n')[1:]  # Skip header
        files = []
        for line in lines:
            if line.strip() and line.startswith("file:"):
                file_name = line.split(": ", 1)[1].split(" (")[0]  # Remove size info
                files.append(file_name)
        
        results = []
        
        if operation == "count_lines":
            # Count lines in each file
            total_lines = 0
            for file_name in files:
                try:
                    file_path = f"{directory}/{file_name}" if directory != "." else file_name
                    content_result = await self.call_tool("read_file", {"path": file_path})
                    content = content_result.content[0].text
                    line_count = len(content.split('\n'))
                    total_lines += line_count
                    results.append({"file": file_name, "lines": line_count})
                except Exception as e:
                    results.append({"file": file_name, "error": str(e)})
            
            return {
                "operation": operation,
                "directory": directory,
                "files_processed": len(files),
                "total_lines": total_lines,
                "results": results
            }
        else:
            raise ValueError(f"Unsupported bulk operation: {operation}")
    
    def _get_tools_used_in_task(self, task: Task) -> List[str]:
        """Return the tools that would be used for this task."""
        return self._get_required_tools_for_task(task.type)