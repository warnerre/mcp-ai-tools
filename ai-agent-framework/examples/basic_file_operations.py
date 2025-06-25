#!/usr/bin/env python3
"""
Basic File Operations Example

This example shows how to use the File Operations MCP Server
to perform common file system tasks.
"""

import asyncio
from mcp.client.stdio import stdio_client


async def basic_file_operations_example():
    """Demonstrate basic file operations using MCP."""
    
    print("🔧 MCP File Operations Example")
    print("=" * 40)
    
    # Server configuration
    server_params = {
        "command": "python",
        "args": ["src/servers/file_operations_server.py"]
    }
    
    async with stdio_client(server_params) as (read, write, client):
        await client.initialize()
        print("📡 Connected to File Operations MCP Server\n")
        
        # Example 1: Create a project structure
        print("Example 1: Creating a project structure")
        print("-" * 35)
        
        # Create main project directory
        result = await client.call_tool("create_directory", {
            "path": "my_project"
        })
        print(f"✅ {result.content[0].text}")
        
        # Create subdirectories
        for subdir in ["src", "tests", "docs"]:
            result = await client.call_tool("create_directory", {
                "path": f"my_project/{subdir}"
            })
            print(f"✅ {result.content[0].text}")
        
        # Example 2: Create some files
        print("\nExample 2: Creating project files")
        print("-" * 32)
        
        # Create a README file
        readme_content = """# My Project

This is a sample project created using MCP File Operations.

## Structure
- src/ - Source code
- tests/ - Test files  
- docs/ - Documentation
"""
        
        result = await client.call_tool("write_file", {
            "path": "my_project/README.md",
            "content": readme_content
        })
        print(f"✅ {result.content[0].text}")
        
        # Create a Python file
        python_content = '''#!/usr/bin/env python3
"""
Sample Python module created via MCP.
"""

def hello_mcp():
    """Say hello to MCP!"""
    return "Hello from MCP File Operations!"

if __name__ == "__main__":
    print(hello_mcp())
'''
        
        result = await client.call_tool("write_file", {
            "path": "my_project/src/main.py", 
            "content": python_content
        })
        print(f"✅ {result.content[0].text}")
        
        # Example 3: Explore the project structure
        print("\nExample 3: Exploring the project structure")
        print("-" * 42)
        
        # List the main directory
        result = await client.call_tool("list_directory", {
            "path": "my_project"
        })
        print(result.content[0].text)
        
        # List the src directory
        result = await client.call_tool("list_directory", {
            "path": "my_project/src"
        })
        print(f"\n{result.content[0].text}")
        
        # Example 4: Read and display a file
        print("\nExample 4: Reading file contents")
        print("-" * 32)
        
        result = await client.call_tool("read_file", {
            "path": "my_project/README.md"
        })
        print(result.content[0].text)
        
        # Example 5: Get detailed file information
        print("\nExample 5: File information")
        print("-" * 26)
        
        result = await client.call_tool("get_file_info", {
            "path": "my_project/src/main.py"
        })
        print(result.content[0].text)
        
        # Example 6: Append to a file
        print("\nExample 6: Appending to a file")
        print("-" * 30)
        
        additional_content = "\n## Installation\n\nRun: `pip install -r requirements.txt`"
        result = await client.call_tool("write_file", {
            "path": "my_project/README.md",
            "content": additional_content, 
            "mode": "append"
        })
        print(f"✅ {result.content[0].text}")
        
        # Read the updated file
        result = await client.call_tool("read_file", {
            "path": "my_project/README.md"
        })
        print(f"\nUpdated README.md:\n{'-' * 20}")
        print(result.content[0].text.split('\n\n', 1)[1])  # Skip the header
        
        print("\n🎉 Example completed successfully!")
        print("\n💡 Key MCP Concepts Demonstrated:")
        print("   • Tool discovery and invocation")
        print("   • Parameter validation")
        print("   • Error handling")
        print("   • Stateless server operations")
        print("   • Resource management")
        
        # Cleanup (optional)
        print("\n🧹 Cleaning up example files...")
        try:
            result = await client.call_tool("delete_file", {
                "path": "my_project",
                "recursive": True
            })
            print(f"✅ {result.content[0].text}")
        except Exception as e:
            print(f"⚠️  Cleanup note: {e}")


if __name__ == "__main__":
    asyncio.run(basic_file_operations_example())