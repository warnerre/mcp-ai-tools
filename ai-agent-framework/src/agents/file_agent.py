#!/usr/bin/env python3
"""
File Agent Implementation

Specialized agent for file system operations and content management.
This agent connects to the file operations MCP server and provides
intelligent file handling capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.base_agent import BaseAgent
from src.core.types import (
    Task, TaskResult, Context, AgentRegistration, MCPServerConfig
)


class FileAgent(BaseAgent):
    """
    Specialized agent for file operations.
    
    Capabilities:
    - File reading, writing, and manipulation
    - Directory operations and analysis
    - Content processing and transformation
    - Batch file operations
    - File system monitoring
    """
    
    def __init__(self):
        registration = AgentRegistration(
            name="file_agent",
            capabilities=[
                "file_operations",
                "directory_operations", 
                "file_search",
                "file_analysis",
                "content_processing",
                "batch_operations"
            ],
            supported_task_types=[
                "read_file",
                "write_file", 
                "list_directory",
                "create_directory",
                "delete_file",
                "analyze_directory",
                "search_files",
                "batch_process_files",
                "organize_files",
                "backup_files"
            ],
            priority=7,
            max_concurrent_tasks=3,
            config={
                "max_file_size": "10MB",
                "allowed_extensions": [".txt", ".json", ".py", ".md", ".yml", ".yaml", ".csv"],
                "base_directory": ".",
                "backup_directory": "backups"
            }
        )
        
        super().__init__("file_agent", registration)
    
    async def setup(self) -> bool:
        """Setup the file agent by connecting to required servers."""
        try:
            # Connect to file operations server
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
            self.logger.info("File Agent setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"File Agent setup failed: {e}")
            return False
    
    def _can_handle_task_specific(self, task: Task) -> bool:
        """Check if this agent can handle the specific task."""
        # File agent can handle all file-related tasks
        return task.type in self.registration.supported_task_types
    
    async def _execute_task_specific(self, task: Task, context: Optional[Context]) -> Dict[str, Any]:
        """Execute file-specific tasks."""
        
        if task.type == "read_file":
            return await self._handle_read_file(task)
        elif task.type == "write_file":
            return await self._handle_write_file(task)
        elif task.type == "list_directory":
            return await self._handle_list_directory(task)
        elif task.type == "create_directory":
            return await self._handle_create_directory(task)
        elif task.type == "delete_file":
            return await self._handle_delete_file(task)
        elif task.type == "analyze_directory":
            return await self._handle_analyze_directory(task)
        elif task.type == "search_files":
            return await self._handle_search_files(task)
        elif task.type == "batch_process_files":
            return await self._handle_batch_process_files(task)
        elif task.type == "organize_files":
            return await self._handle_organize_files(task)
        elif task.type == "backup_files":
            return await self._handle_backup_files(task)
        else:
            raise ValueError(f"Unsupported task type: {task.type}")
    
    async def _handle_read_file(self, task: Task) -> Dict[str, Any]:
        """Read a file and return its contents."""
        file_path = task.parameters.get("path")
        encoding = task.parameters.get("encoding", "utf-8")
        
        if not file_path:
            raise ValueError("File path is required")
        
        self.logger.info(f"Reading file: {file_path}")
        
        # Read file using MCP tool
        result = await self.call_tool("read_file", {"path": file_path})
        content = result.content[0].text
        
        # Get file metadata
        info_result = await self.call_tool("get_file_info", {"path": file_path})
        file_info = info_result.content[0].text
        
        # Analyze content
        lines = content.split('\n')
        words = len(content.split())
        
        return {
            "file_path": file_path,
            "content": content,
            "file_info": file_info,
            "analysis": {
                "line_count": len(lines),
                "word_count": words,
                "character_count": len(content),
                "encoding": encoding
            },
            "summary": f"Read {len(content)} characters from {file_path}"
        }
    
    async def _handle_write_file(self, task: Task) -> Dict[str, Any]:
        """Write content to a file."""
        file_path = task.parameters.get("path")
        content = task.parameters.get("content")
        mode = task.parameters.get("mode", "write")
        create_dirs = task.parameters.get("create_dirs", True)
        
        if not file_path or content is None:
            raise ValueError("File path and content are required")
        
        self.logger.info(f"Writing to file: {file_path} (mode: {mode})")
        
        # Create parent directories if needed
        if create_dirs:
            parent_dir = str(Path(file_path).parent)
            if parent_dir != ".":
                try:
                    await self.call_tool("create_directory", {"path": parent_dir})
                except Exception:
                    pass  # Directory might already exist
        
        # Write file
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
    
    async def _handle_list_directory(self, task: Task) -> Dict[str, Any]:
        """List directory contents."""
        dir_path = task.parameters.get("path", ".")
        include_hidden = task.parameters.get("include_hidden", False)
        recursive = task.parameters.get("recursive", False)
        
        self.logger.info(f"Listing directory: {dir_path}")
        
        # Get directory listing
        result = await self.call_tool("list_directory", {
            "path": dir_path,
            "include_hidden": include_hidden
        })
        
        listing = result.content[0].text
        
        # Parse the listing for analysis
        lines = listing.split('\n')[1:]  # Skip header
        files = []
        directories = []
        
        for line in lines:
            if line.strip():
                if line.startswith("file:"):
                    files.append(line.split(": ", 1)[1].split(" (")[0])
                elif line.startswith("directory:"):
                    directories.append(line.split(": ", 1)[1])
        
        # If recursive, get subdirectory contents
        if recursive and directories:
            subdirs_content = {}
            for subdir in directories[:5]:  # Limit to avoid deep recursion
                try:
                    subdir_path = f"{dir_path}/{subdir}" if dir_path != "." else subdir
                    sub_result = await self.call_tool("list_directory", {"path": subdir_path})
                    subdirs_content[subdir] = sub_result.content[0].text
                except Exception as e:
                    subdirs_content[subdir] = f"Error: {e}"
        
        response = {
            "directory": dir_path,
            "file_count": len(files),
            "directory_count": len(directories),
            "files": files,
            "directories": directories,
            "listing": listing
        }
        
        if recursive and directories:
            response["subdirectories"] = subdirs_content
        
        return response
    
    async def _handle_create_directory(self, task: Task) -> Dict[str, Any]:
        """Create a directory."""
        dir_path = task.parameters.get("path")
        parents = task.parameters.get("parents", True)
        
        if not dir_path:
            raise ValueError("Directory path is required")
        
        self.logger.info(f"Creating directory: {dir_path}")
        
        result = await self.call_tool("create_directory", {
            "path": dir_path,
            "parents": parents
        })
        
        return {
            "directory": dir_path,
            "result": result.content[0].text
        }
    
    async def _handle_delete_file(self, task: Task) -> Dict[str, Any]:
        """Delete a file or directory."""
        file_path = task.parameters.get("path")
        recursive = task.parameters.get("recursive", False)
        confirm = task.parameters.get("confirm", False)
        
        if not file_path:
            raise ValueError("File path is required")
        
        if not confirm:
            raise ValueError("Deletion requires explicit confirmation (confirm=true)")
        
        self.logger.info(f"Deleting: {file_path} (recursive: {recursive})")
        
        result = await self.call_tool("delete_file", {
            "path": file_path,
            "recursive": recursive
        })
        
        return {
            "deleted_path": file_path,
            "recursive": recursive,
            "result": result.content[0].text
        }
    
    async def _handle_analyze_directory(self, task: Task) -> Dict[str, Any]:
        """Analyze directory structure and contents."""
        dir_path = task.parameters.get("path", ".")
        depth = task.parameters.get("depth", 2)
        include_content_analysis = task.parameters.get("include_content_analysis", False)
        
        self.logger.info(f"Analyzing directory: {dir_path}")
        
        # Get directory listing
        listing_result = await self.call_tool("list_directory", {
            "path": dir_path,
            "include_hidden": False
        })
        
        listing = listing_result.content[0].text
        
        # Parse and analyze
        lines = listing.split('\n')[1:]
        files = []
        directories = []
        total_size = 0
        
        for line in lines:
            if line.strip():
                if line.startswith("file:"):
                    file_info = line.split(": ", 1)[1]
                    if "(" in file_info and " bytes)" in file_info:
                        file_name = file_info.split(" (")[0]
                        size_str = file_info.split("(")[1].split(" bytes)")[0]
                        try:
                            size = int(size_str)
                            total_size += size
                        except ValueError:
                            pass
                    else:
                        file_name = file_info
                    files.append(file_name)
                elif line.startswith("directory:"):
                    directories.append(line.split(": ", 1)[1])
        
        analysis = {
            "directory": dir_path,
            "summary": {
                "total_files": len(files),
                "total_directories": len(directories),
                "total_size_bytes": total_size,
                "files": files,
                "directories": directories
            },
            "raw_listing": listing
        }
        
        # Content analysis for text files
        if include_content_analysis and files:
            content_analysis = {}
            text_files = [f for f in files if any(f.endswith(ext) for ext in ['.txt', '.md', '.py', '.json'])]
            
            for file_name in text_files[:5]:  # Analyze first 5 text files
                try:
                    file_path = f"{dir_path}/{file_name}" if dir_path != "." else file_name
                    content_result = await self.call_tool("read_file", {"path": file_path})
                    content = content_result.content[0].text
                    
                    content_analysis[file_name] = {
                        "size": len(content),
                        "lines": len(content.split('\n')),
                        "words": len(content.split()),
                        "preview": content[:200] + ("..." if len(content) > 200 else "")
                    }
                except Exception as e:
                    content_analysis[file_name] = {"error": str(e)}
            
            analysis["content_analysis"] = content_analysis
        
        return analysis
    
    async def _handle_search_files(self, task: Task) -> Dict[str, Any]:
        """Search for files by name pattern or content."""
        search_dir = task.parameters.get("directory", ".")
        name_pattern = task.parameters.get("name_pattern")
        content_pattern = task.parameters.get("content_pattern")
        file_extensions = task.parameters.get("file_extensions", [])
        
        if not name_pattern and not content_pattern:
            raise ValueError("Either name_pattern or content_pattern is required")
        
        self.logger.info(f"Searching files in {search_dir}")
        
        # Get directory listing
        listing_result = await self.call_tool("list_directory", {"path": search_dir})
        listing = listing_result.content[0].text
        
        # Extract file names
        lines = listing.split('\n')[1:]
        all_files = []
        for line in lines:
            if line.strip() and line.startswith("file:"):
                file_name = line.split(": ", 1)[1].split(" (")[0]
                all_files.append(file_name)
        
        matches = []
        
        # Name pattern matching
        if name_pattern:
            import re
            pattern_re = re.compile(name_pattern, re.IGNORECASE)
            for file_name in all_files:
                if pattern_re.search(file_name):
                    matches.append({
                        "file": file_name,
                        "match_type": "name",
                        "pattern": name_pattern
                    })
        
        # Content pattern matching
        if content_pattern:
            import re
            pattern_re = re.compile(content_pattern, re.IGNORECASE)
            
            # Filter by extensions if specified
            search_files = all_files
            if file_extensions:
                search_files = [f for f in all_files if any(f.endswith(ext) for ext in file_extensions)]
            
            for file_name in search_files[:10]:  # Limit search to prevent overload
                try:
                    file_path = f"{search_dir}/{file_name}" if search_dir != "." else file_name
                    content_result = await self.call_tool("read_file", {"path": file_path})
                    content = content_result.content[0].text
                    
                    if pattern_re.search(content):
                        # Find line numbers of matches
                        lines = content.split('\n')
                        match_lines = []
                        for i, line in enumerate(lines, 1):
                            if pattern_re.search(line):
                                match_lines.append({
                                    "line_number": i,
                                    "content": line.strip()
                                })
                        
                        matches.append({
                            "file": file_name,
                            "match_type": "content",
                            "pattern": content_pattern,
                            "match_lines": match_lines[:5]  # First 5 matches
                        })
                except Exception as e:
                    self.logger.debug(f"Could not search in {file_name}: {e}")
        
        return {
            "search_directory": search_dir,
            "name_pattern": name_pattern,
            "content_pattern": content_pattern,
            "total_matches": len(matches),
            "matches": matches
        }
    
    async def _handle_batch_process_files(self, task: Task) -> Dict[str, Any]:
        """Process multiple files in batch."""
        operation = task.parameters.get("operation")
        directory = task.parameters.get("directory", ".")
        file_pattern = task.parameters.get("file_pattern", "*")
        
        if not operation:
            raise ValueError("Operation is required")
        
        self.logger.info(f"Batch processing files in {directory}")
        
        # Get files to process
        listing_result = await self.call_tool("list_directory", {"path": directory})
        listing = listing_result.content[0].text
        
        # Extract file names
        lines = listing.split('\n')[1:]
        files = []
        for line in lines:
            if line.strip() and line.startswith("file:"):
                file_name = line.split(": ", 1)[1].split(" (")[0]
                files.append(file_name)
        
        results = []
        
        if operation == "count_lines":
            total_lines = 0
            for file_name in files:
                try:
                    file_path = f"{directory}/{file_name}" if directory != "." else file_name
                    content_result = await self.call_tool("read_file", {"path": file_path})
                    content = content_result.content[0].text
                    line_count = len(content.split('\n'))
                    total_lines += line_count
                    
                    results.append({
                        "file": file_name,
                        "lines": line_count,
                        "status": "success"
                    })
                except Exception as e:
                    results.append({
                        "file": file_name,
                        "error": str(e),
                        "status": "error"
                    })
            
            return {
                "operation": operation,
                "directory": directory,
                "total_files": len(files),
                "total_lines": total_lines,
                "results": results
            }
        
        elif operation == "get_file_sizes":
            total_size = 0
            for file_name in files:
                try:
                    file_path = f"{directory}/{file_name}" if directory != "." else file_name
                    info_result = await self.call_tool("get_file_info", {"path": file_path})
                    info_text = info_result.content[0].text
                    
                    # Extract size from info (simple parsing)
                    size = 0
                    for line in info_text.split('\n'):
                        if 'size:' in line.lower():
                            try:
                                size = int(line.split(':')[1].strip())
                                break
                            except (ValueError, IndexError):
                                pass
                    
                    total_size += size
                    results.append({
                        "file": file_name,
                        "size": size,
                        "status": "success"
                    })
                except Exception as e:
                    results.append({
                        "file": file_name,
                        "error": str(e),
                        "status": "error"
                    })
            
            return {
                "operation": operation,
                "directory": directory,
                "total_files": len(files),
                "total_size": total_size,
                "results": results
            }
        
        else:
            raise ValueError(f"Unsupported batch operation: {operation}")
    
    async def _handle_organize_files(self, task: Task) -> Dict[str, Any]:
        """Organize files by type or other criteria."""
        source_dir = task.parameters.get("source_directory", ".")
        organize_by = task.parameters.get("organize_by", "extension")
        create_structure = task.parameters.get("create_structure", True)
        
        self.logger.info(f"Organizing files in {source_dir} by {organize_by}")
        
        # Get files to organize
        listing_result = await self.call_tool("list_directory", {"path": source_dir})
        listing = listing_result.content[0].text
        
        # Extract file names
        lines = listing.split('\n')[1:]
        files = []
        for line in lines:
            if line.strip() and line.startswith("file:"):
                file_name = line.split(": ", 1)[1].split(" (")[0]
                files.append(file_name)
        
        organization_plan = {}
        
        if organize_by == "extension":
            for file_name in files:
                ext = Path(file_name).suffix.lower() or "no_extension"
                if ext not in organization_plan:
                    organization_plan[ext] = []
                organization_plan[ext].append(file_name)
        
        elif organize_by == "size":
            # Get file sizes and categorize
            for file_name in files:
                try:
                    file_path = f"{source_dir}/{file_name}" if source_dir != "." else file_name
                    info_result = await self.call_tool("get_file_info", {"path": file_path})
                    # Simple size categorization
                    category = "large"  # Default
                    organization_plan.setdefault(category, []).append(file_name)
                except Exception:
                    organization_plan.setdefault("unknown", []).append(file_name)
        
        # Create directory structure if requested
        directories_created = []
        if create_structure:
            for category in organization_plan.keys():
                target_dir = f"{source_dir}/{category}"
                try:
                    await self.call_tool("create_directory", {"path": target_dir})
                    directories_created.append(target_dir)
                except Exception as e:
                    self.logger.debug(f"Could not create directory {target_dir}: {e}")
        
        return {
            "source_directory": source_dir,
            "organize_by": organize_by,
            "organization_plan": organization_plan,
            "directories_created": directories_created,
            "total_files": len(files),
            "categories": len(organization_plan)
        }
    
    async def _handle_backup_files(self, task: Task) -> Dict[str, Any]:
        """Create backups of specified files."""
        source_files = task.parameters.get("source_files", [])
        source_directory = task.parameters.get("source_directory")
        backup_directory = task.parameters.get("backup_directory", "backup")
        include_timestamp = task.parameters.get("include_timestamp", True)
        
        if not source_files and not source_directory:
            raise ValueError("Either source_files or source_directory must be specified")
        
        self.logger.info(f"Creating backups to {backup_directory}")
        
        # Create backup directory
        try:
            await self.call_tool("create_directory", {"path": backup_directory})
        except Exception:
            pass  # Directory might already exist
        
        backup_results = []
        
        # If backing up directory, get file list
        if source_directory:
            listing_result = await self.call_tool("list_directory", {"path": source_directory})
            listing = listing_result.content[0].text
            
            lines = listing.split('\n')[1:]
            for line in lines:
                if line.strip() and line.startswith("file:"):
                    file_name = line.split(": ", 1)[1].split(" (")[0]
                    source_files.append(f"{source_directory}/{file_name}")
        
        # Backup each file
        for source_file in source_files:
            try:
                # Read source file
                content_result = await self.call_tool("read_file", {"path": source_file})
                content = content_result.content[0].text
                
                # Create backup filename
                file_name = Path(source_file).name
                if include_timestamp:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    name_parts = file_name.rsplit('.', 1)
                    if len(name_parts) == 2:
                        backup_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                    else:
                        backup_name = f"{file_name}_{timestamp}"
                else:
                    backup_name = file_name
                
                backup_path = f"{backup_directory}/{backup_name}"
                
                # Write backup
                await self.call_tool("write_file", {
                    "path": backup_path,
                    "content": content
                })
                
                backup_results.append({
                    "source": source_file,
                    "backup": backup_path,
                    "status": "success",
                    "size": len(content)
                })
                
            except Exception as e:
                backup_results.append({
                    "source": source_file,
                    "error": str(e),
                    "status": "error"
                })
        
        successful_backups = len([r for r in backup_results if r["status"] == "success"])
        
        return {
            "backup_directory": backup_directory,
            "total_files": len(source_files),
            "successful_backups": successful_backups,
            "failed_backups": len(source_files) - successful_backups,
            "backup_results": backup_results
        }
    
    def _get_tools_used_in_task(self, task: Task) -> List[str]:
        """Return tools used for specific task types."""
        tool_mapping = {
            "read_file": ["read_file", "get_file_info"],
            "write_file": ["write_file", "create_directory"],
            "list_directory": ["list_directory"],
            "create_directory": ["create_directory"],
            "delete_file": ["delete_file"],
            "analyze_directory": ["list_directory", "read_file", "get_file_info"],
            "search_files": ["list_directory", "read_file"],
            "batch_process_files": ["list_directory", "read_file", "get_file_info"],
            "organize_files": ["list_directory", "get_file_info", "create_directory"],
            "backup_files": ["read_file", "write_file", "create_directory"]
        }
        return tool_mapping.get(task.type, [])