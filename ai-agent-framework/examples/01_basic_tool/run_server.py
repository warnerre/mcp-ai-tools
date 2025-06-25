#!/usr/bin/env python3
"""
Run the Hello MCP Server

This script shows how to run a FastMCP server.
"""

import subprocess
import sys

if __name__ == "__main__":
    print("🚀 Starting Hello MCP Server...")
    print("=" * 40)
    print("Server is running and waiting for connections via stdio")
    print("To connect: Configure Claude Desktop or use an MCP client")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    # Run the FastMCP server
    subprocess.run([sys.executable, "-m", "fastmcp", "run", "hello_mcp_server.py"])