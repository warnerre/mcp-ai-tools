# Example 1: Basic MCP Tool

This is the simplest possible MCP server implementation using FastMCP.

## What You'll Learn

- How to create an MCP server with FastMCP
- How to define tools that AI agents can call
- How MCP handles parameter validation
- The basic structure of MCP tool responses

## Key Concepts

### Tools
Tools are functions that AI agents can call. Each tool:
- Has a name (the function name)
- Has a description (from the docstring)
- Defines parameters with types
- Returns a response

### FastMCP
FastMCP simplifies MCP server creation by:
- Handling all protocol details
- Automatically generating tool schemas from type hints
- Managing the server lifecycle

## Running the Server

1. Make sure you're in the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Run the server:
   ```bash
   python hello_mcp_server.py
   ```

The server will start and wait for connections via stdio.

## Testing with Claude Desktop

To test with Claude Desktop, add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hello-server": {
      "command": "python",
      "args": ["/path/to/hello_mcp_server.py"]
    }
  }
}
```

## What's Next?

Once you understand this basic example, move on to Example 2 which shows:
- Multiple related tools
- Working with files
- Error handling
- More complex parameter types