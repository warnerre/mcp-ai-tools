#!/usr/bin/env python3
"""
Test FastMCP Server Locally

This script shows how to test FastMCP servers without needing a full client.
FastMCP includes built-in testing capabilities.

Run: python test_fastmcp_server.py
"""

import asyncio
import sys
from pathlib import Path

# Add the examples directory to the path
sys.path.append(str(Path(__file__).parent))

# Import our servers
sys.path.append(str(Path(__file__).parent / "01_basic_tool"))
sys.path.append(str(Path(__file__).parent / "02_multiple_tools"))

from hello_mcp_server import mcp as hello_mcp
from file_operations_fastmcp import mcp as file_mcp


async def test_hello_server():
    """Test the basic hello server."""
    print("Testing Hello MCP Server")
    print("=" * 40)
    
    # Test say_hello tool
    result = await hello_mcp._tools["say_hello"]["handler"](name="MCP Learner")
    print(f"say_hello result: {result}")
    
    # Test add_numbers tool
    result = await hello_mcp._tools["add_numbers"]["handler"](a=5, b=3)
    print(f"add_numbers result: {result}")
    
    print()


async def test_file_operations_server():
    """Test the file operations server."""
    print("Testing File Operations Server")
    print("=" * 40)
    
    # Test creating a directory
    result = await file_mcp._tools["create_directory"]["handler"](path="test_dir")
    print(f"create_directory result: {result}")
    
    # Test writing a file
    content = "Hello from MCP!\nThis is a test file."
    result = await file_mcp._tools["write_file"]["handler"](
        path="test_dir/hello.txt", 
        content=content
    )
    print(f"write_file result: {result}")
    
    # Test reading the file
    result = await file_mcp._tools["read_file"]["handler"](path="test_dir/hello.txt")
    print(f"read_file result: {result[:100]}...")  # First 100 chars
    
    # Test listing directory
    result = await file_mcp._tools["list_directory"]["handler"](path="test_dir")
    print(f"list_directory result: {result}")
    
    # Test file info
    result = await file_mcp._tools["file_info"]["handler"](path="test_dir/hello.txt")
    print(f"file_info result: {result}")
    
    # Cleanup
    import shutil
    shutil.rmtree("test_dir", ignore_errors=True)
    print("\nCleanup completed!")


async def main():
    """Run all tests."""
    print("🚀 FastMCP Server Testing")
    print("This demonstrates how FastMCP servers work internally\n")
    
    await test_hello_server()
    await test_file_operations_server()
    
    print("\n✅ All tests completed!")
    print("\nKey Insights:")
    print("- FastMCP automatically creates tool handlers from decorated functions")
    print("- Each tool validates parameters based on type hints")
    print("- Tools can be tested directly without the full MCP protocol")
    print("- This makes development and debugging much easier!")


if __name__ == "__main__":
    asyncio.run(main())