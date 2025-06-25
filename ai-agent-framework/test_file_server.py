#!/usr/bin/env python3
"""
Test script for the File Operations MCP Server

This script demonstrates how to interact with our MCP server.
Run this to verify the server implementation works correctly.
"""

import asyncio
import json
import tempfile
from pathlib import Path

from mcp.client.stdio import stdio_client


async def test_file_operations_server():
    """Test the file operations MCP server."""
    
    # Start the server
    from mcp.client.stdio import StdioServerParameters
    
    server_params = StdioServerParameters(
        command="python", 
        args=["src/servers/file_operations_server.py"]
    )
    
    print("🚀 Starting File Operations MCP Server...")
    
    async with stdio_client(server_params) as (read, write):
        from mcp.client.session import ClientSession
        
        # Create client session
        client = ClientSession(read, write)
        
        # Initialize the client
        result = await client.initialize()
        
        print("✅ Server initialized successfully!")
        
        # Test 1: List available tools
        print("\n📋 Testing tool discovery...")
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools.tools]}")
        
        # Test 2: List available resources  
        print("\n📋 Testing resource discovery...")
        resources = await client.list_resources()
        print(f"Available resources: {[resource.name for resource in resources.resources]}")
        
        # Test 3: Create a test directory
        print("\n📁 Testing directory creation...")
        result = await client.call_tool("create_directory", {
            "path": "test_data"
        })
        print(f"Directory creation result: {result.content[0].text}")
        
        # Test 4: Write a test file
        print("\n📝 Testing file writing...")
        test_content = "Hello, MCP World!\nThis is a test file created by our MCP server."
        result = await client.call_tool("write_file", {
            "path": "test_data/hello.txt",
            "content": test_content
        })
        print(f"File write result: {result.content[0].text}")
        
        # Test 5: Read the file back
        print("\n📖 Testing file reading...")
        result = await client.call_tool("read_file", {
            "path": "test_data/hello.txt"
        })
        print(f"File read result:\n{result.content[0].text}")
        
        # Test 6: List directory contents
        print("\n📂 Testing directory listing...")
        result = await client.call_tool("list_directory", {
            "path": "test_data"
        })
        print(f"Directory listing:\n{result.content[0].text}")
        
        # Test 7: Get file information
        print("\n📊 Testing file info...")
        result = await client.call_tool("get_file_info", {
            "path": "test_data/hello.txt"
        })
        print(f"File info:\n{result.content[0].text}")
        
        # Test 8: Append to file
        print("\n➕ Testing file append...")
        result = await client.call_tool("write_file", {
            "path": "test_data/hello.txt",
            "content": "\nAppended line!",
            "mode": "append"
        })
        print(f"File append result: {result.content[0].text}")
        
        # Test 9: Read updated file
        print("\n📖 Testing file reading after append...")
        result = await client.call_tool("read_file", {
            "path": "test_data/hello.txt"
        })
        print(f"Updated file content:\n{result.content[0].text}")
        
        # Test 10: Test resource reading
        print("\n📚 Testing resource reading...")
        resource_content = await client.read_resource("file://filesystem")
        print(f"Resource content:\n{resource_content.contents[0].text}")
        
        # Test 11: Error handling - try to read non-existent file
        print("\n⚠️  Testing error handling...")
        try:
            result = await client.call_tool("read_file", {
                "path": "nonexistent.txt"
            })
        except Exception as e:
            print(f"Expected error for non-existent file: {e}")
        
        # Cleanup
        print("\n🧹 Cleaning up test files...")
        try:
            result = await client.call_tool("delete_file", {
                "path": "test_data", 
                "recursive": True
            })
            print(f"Cleanup result: {result.content[0].text}")
        except Exception as e:
            print(f"Cleanup error (expected if directory doesn't exist): {e}")
        
        print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_file_operations_server())