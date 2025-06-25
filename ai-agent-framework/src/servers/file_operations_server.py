#!/usr/bin/env python3
"""
MCP Server for File Operations

This server provides file system operations as MCP tools.
It demonstrates core MCP server patterns:
- Tool registration and discovery
- Input validation with JSON schemas
- Error handling and responses
- Resource management
"""

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Server instance
server = Server("file-operations-server")

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.txt', '.json', '.py', '.md', '.yml', '.yaml', '.csv'}
BASE_DIRECTORY = Path.cwd()


def is_safe_path(path: str) -> bool:
    """Check if path is safe to access."""
    try:
        resolved_path = Path(path).resolve()
        return resolved_path.is_relative_to(BASE_DIRECTORY)
    except (OSError, ValueError):
        return False


def check_file_size(path: Path) -> bool:
    """Check if file size is within limits."""
    try:
        return path.stat().st_size <= MAX_FILE_SIZE
    except OSError:
        return False


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available file operation tools."""
    return [
        Tool(
            name="read_file",
            description="Read the contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file", 
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path where to write the file"
                    },
                    "content": {
                        "type": "string", 
                        "description": "Content to write to the file"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["write", "append"],
                        "description": "Write mode: 'write' (overwrite) or 'append'",
                        "default": "write"
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="List contents of a directory",
            inputSchema={
                "type": "object", 
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list",
                        "default": "."
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files/directories",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="create_directory",
            description="Create a new directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the directory to create"
                    },
                    "parents": {
                        "type": "boolean", 
                        "description": "Create parent directories if they don't exist",
                        "default": True
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="get_file_info",
            description="Get information about a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file or directory"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to delete"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Delete directories recursively",
                        "default": False
                    }
                },
                "required": ["path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "read_file":
        return await handle_read_file(arguments)
    elif name == "write_file":
        return await handle_write_file(arguments)
    elif name == "list_directory":
        return await handle_list_directory(arguments)
    elif name == "create_directory":
        return await handle_create_directory(arguments)
    elif name == "get_file_info":
        return await handle_get_file_info(arguments)
    elif name == "delete_file":
        return await handle_delete_file(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_read_file(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle read_file tool call."""
    path_str = arguments["path"]
    
    if not is_safe_path(path_str):
        raise ValueError(f"Access denied: {path_str}")
    
    path = Path(path_str)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path_str}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path_str}")
    
    if not check_file_size(path):
        raise ValueError(f"File too large: {path_str} (max {MAX_FILE_SIZE} bytes)")
    
    # Check file extension
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed: {path.suffix}")
    
    try:
        content = path.read_text(encoding='utf-8')
        return [TextContent(
            type="text",
            text=f"Contents of {path_str}:\n\n{content}"
        )]
    except UnicodeDecodeError:
        raise ValueError(f"Cannot read file as text: {path_str}")
    except OSError as e:
        raise ValueError(f"Error reading file: {e}")


async def handle_write_file(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle write_file tool call."""
    path_str = arguments["path"]
    content = arguments["content"]
    mode = arguments.get("mode", "write")
    
    if not is_safe_path(path_str):
        raise ValueError(f"Access denied: {path_str}")
    
    path = Path(path_str)
    
    # Check file extension
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed: {path.suffix}")
    
    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if mode == "append":
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
        else:
            path.write_text(content, encoding='utf-8')
        
        return [TextContent(
            type="text",
            text=f"Successfully {'appended to' if mode == 'append' else 'wrote'} {path_str}"
        )]
    except OSError as e:
        raise ValueError(f"Error writing file: {e}")


async def handle_list_directory(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle list_directory tool call."""
    path_str = arguments.get("path", ".")
    include_hidden = arguments.get("include_hidden", False)
    
    if not is_safe_path(path_str):
        raise ValueError(f"Access denied: {path_str}")
    
    path = Path(path_str)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path_str}")
    
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path_str}")
    
    try:
        items = []
        for item in sorted(path.iterdir()):
            if not include_hidden and item.name.startswith('.'):
                continue
                
            item_type = "directory" if item.is_dir() else "file"
            size = ""
            if item.is_file():
                try:
                    size = f" ({item.stat().st_size} bytes)"
                except OSError:
                    size = " (size unknown)"
            
            items.append(f"{item_type}: {item.name}{size}")
        
        if not items:
            result = f"Directory {path_str} is empty"
        else:
            result = f"Contents of {path_str}:\n" + "\n".join(items)
        
        return [TextContent(type="text", text=result)]
    except OSError as e:
        raise ValueError(f"Error listing directory: {e}")


async def handle_create_directory(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle create_directory tool call."""
    path_str = arguments["path"]
    parents = arguments.get("parents", True)
    
    if not is_safe_path(path_str):
        raise ValueError(f"Access denied: {path_str}")
    
    path = Path(path_str)
    
    try:
        path.mkdir(parents=parents, exist_ok=False)
        return [TextContent(
            type="text",
            text=f"Successfully created directory: {path_str}"
        )]
    except FileExistsError:
        raise ValueError(f"Directory already exists: {path_str}")
    except OSError as e:
        raise ValueError(f"Error creating directory: {e}")


async def handle_get_file_info(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_file_info tool call."""
    path_str = arguments["path"]
    
    if not is_safe_path(path_str):
        raise ValueError(f"Access denied: {path_str}")
    
    path = Path(path_str)
    
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path_str}")
    
    try:
        stat = path.stat()
        info = {
            "path": str(path),
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:],
        }
        
        if path.is_file():
            info["extension"] = path.suffix
        
        result = f"Information for {path_str}:\n"
        for key, value in info.items():
            result += f"  {key}: {value}\n"
        
        return [TextContent(type="text", text=result)]
    except OSError as e:
        raise ValueError(f"Error getting file info: {e}")


async def handle_delete_file(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle delete_file tool call."""
    path_str = arguments["path"]
    recursive = arguments.get("recursive", False)
    
    if not is_safe_path(path_str):
        raise ValueError(f"Access denied: {path_str}")
    
    path = Path(path_str)
    
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path_str}")
    
    try:
        if path.is_file():
            path.unlink()
            return [TextContent(
                type="text",
                text=f"Successfully deleted file: {path_str}"
            )]
        elif path.is_dir():
            if recursive:
                shutil.rmtree(path)
                return [TextContent(
                    type="text", 
                    text=f"Successfully deleted directory recursively: {path_str}"
                )]
            else:
                path.rmdir()
                return [TextContent(
                    type="text",
                    text=f"Successfully deleted empty directory: {path_str}"
                )]
        else:
            raise ValueError(f"Unknown path type: {path_str}")
    except OSError as e:
        raise ValueError(f"Error deleting: {e}")


@server.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="file://filesystem",
            name="File System",
            description="Access to local file system operations",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    if uri == "file://filesystem":
        # Return information about the file system access
        info = {
            "base_directory": str(BASE_DIRECTORY),
            "max_file_size": MAX_FILE_SIZE,
            "allowed_extensions": list(ALLOWED_EXTENSIONS),
            "available_tools": [
                "read_file", "write_file", "list_directory", 
                "create_directory", "get_file_info", "delete_file"
            ]
        }
        return json.dumps(info, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())