#!/usr/bin/env python3
"""
Example 2: File Operations Server with FastMCP
A more practical MCP server that provides file system operations.

This demonstrates:
- Multiple related tools in one server
- Error handling and validation
- Working with file paths
- Returning structured data

Run this server:
    python file_operations_fastmcp.py
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import List, Dict, Any
import json

# Initialize the MCP server
mcp = FastMCP("file-operations")

# Configuration
BASE_DIR = Path.cwd()
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def is_safe_path(path_str: str) -> bool:
    """Check if a path is safe to access (within BASE_DIR)."""
    try:
        path = Path(path_str).resolve()
        return path.is_relative_to(BASE_DIR)
    except Exception:
        return False


@mcp.tool()
async def read_file(path: str) -> str:
    """
    Read the contents of a text file.
    
    Args:
        path: Path to the file to read (relative to current directory)
        
    Returns:
        The contents of the file
    """
    if not is_safe_path(path):
        return f"Error: Access denied - path must be within {BASE_DIR}"
    
    file_path = Path(path)
    
    if not file_path.exists():
        return f"Error: File not found - {path}"
    
    if not file_path.is_file():
        return f"Error: Path is not a file - {path}"
    
    if file_path.stat().st_size > MAX_FILE_SIZE:
        return f"Error: File too large - maximum size is {MAX_FILE_SIZE} bytes"
    
    try:
        content = file_path.read_text(encoding='utf-8')
        return f"Contents of {path}:\n\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        path: Path where to write the file
        content: Content to write to the file
        
    Returns:
        Success or error message
    """
    if not is_safe_path(path):
        return f"Error: Access denied - path must be within {BASE_DIR}"
    
    file_path = Path(path)
    
    try:
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content
        file_path.write_text(content, encoding='utf-8')
        
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
async def list_directory(path: str = ".") -> str:
    """
    List contents of a directory.
    
    Args:
        path: Path to the directory (defaults to current directory)
        
    Returns:
        A formatted list of directory contents
    """
    if not is_safe_path(path):
        return f"Error: Access denied - path must be within {BASE_DIR}"
    
    dir_path = Path(path)
    
    if not dir_path.exists():
        return f"Error: Directory not found - {path}"
    
    if not dir_path.is_dir():
        return f"Error: Path is not a directory - {path}"
    
    try:
        items = []
        for item in sorted(dir_path.iterdir()):
            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                items.append(f"📄 {item.name} ({size} bytes)")
        
        if not items:
            return f"Directory {path} is empty"
        
        return f"Contents of {path}:\n" + "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@mcp.tool()
async def file_info(path: str) -> str:
    """
    Get detailed information about a file or directory.
    
    Args:
        path: Path to the file or directory
        
    Returns:
        Detailed information in JSON format
    """
    if not is_safe_path(path):
        return f"Error: Access denied - path must be within {BASE_DIR}"
    
    file_path = Path(path)
    
    if not file_path.exists():
        return f"Error: Path not found - {path}"
    
    try:
        stat = file_path.stat()
        info = {
            "path": str(file_path),
            "name": file_path.name,
            "type": "directory" if file_path.is_dir() else "file",
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_hidden": file_path.name.startswith('.'),
        }
        
        if file_path.is_file():
            info["extension"] = file_path.suffix
            info["stem"] = file_path.stem
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error getting file info: {str(e)}"


@mcp.tool()
async def create_directory(path: str) -> str:
    """
    Create a new directory.
    
    Args:
        path: Path of the directory to create
        
    Returns:
        Success or error message
    """
    if not is_safe_path(path):
        return f"Error: Access denied - path must be within {BASE_DIR}"
    
    dir_path = Path(path)
    
    try:
        dir_path.mkdir(parents=True, exist_ok=False)
        return f"Successfully created directory: {path}"
    except FileExistsError:
        return f"Error: Directory already exists - {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"


# The FastMCP server will run automatically when this script is executed