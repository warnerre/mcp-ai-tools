#!/usr/bin/env python3
"""
Example 1: Hello MCP Server
The simplest possible MCP server with a single tool.

This demonstrates:
- Creating an MCP server using FastMCP
- Defining a simple tool
- Tool parameter validation
- Basic response handling

Run this server:
    python hello_mcp_server.py
"""

from fastmcp import FastMCP

# Initialize FastMCP server with a name
mcp = FastMCP("hello-server")

# Define a simple tool using the @mcp.tool() decorator
@mcp.tool()
async def say_hello(name: str) -> str:
    """
    Say hello to someone.
    
    Args:
        name: The name of the person to greet
        
    Returns:
        A friendly greeting message
    """
    return f"Hello, {name}! Welcome to MCP (Model Context Protocol)!"


@mcp.tool()
async def add_numbers(a: int, b: int) -> str:
    """
    Add two numbers together.
    
    Args:
        a: First number to add
        b: Second number to add
        
    Returns:
        The sum of the two numbers as a string message
    """
    result = a + b
    return f"The sum of {a} and {b} is {result}"


# The server runs automatically when this script is executed
# FastMCP handles all the MCP protocol details for you!