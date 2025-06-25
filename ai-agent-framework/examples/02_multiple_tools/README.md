# Example 2: Multiple Tools - File Operations

This example shows a more practical MCP server with multiple related tools for file operations.

## What You'll Learn

- Creating multiple tools in a single MCP server
- Implementing proper error handling
- Working with file paths safely
- Returning structured data from tools
- Parameter validation and security considerations

## Key Concepts

### Tool Organization
When building an MCP server, group related tools together. This file operations server provides:
- `read_file` - Read file contents
- `write_file` - Write content to files
- `list_directory` - List directory contents
- `file_info` - Get detailed file information
- `create_directory` - Create new directories

### Safety and Validation
The server implements several safety measures:
- Path validation to prevent access outside the base directory
- File size limits to prevent memory issues
- Proper error messages for debugging
- Graceful handling of exceptions

### FastMCP Benefits
Notice how FastMCP:
- Automatically generates tool schemas from type hints
- Handles the MCP protocol communication
- Manages async/await patterns
- Provides clean decorator-based API

## Running the Server

1. Ensure you're in the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Run the server:
   ```bash
   python file_operations_fastmcp.py
   ```

## Testing the Tools

You can test these tools by:
1. Configuring Claude Desktop to use this server
2. Creating a simple test client (see Example 3)
3. Using the MCP debugging tools

## Example Usage in Claude

Once connected, you could ask Claude:
- "List the files in the current directory"
- "Read the contents of README.md"
- "Create a new directory called 'test_output'"
- "Write a hello world Python script"

## Implementation Notes

### Error Handling
Each tool returns user-friendly error messages instead of raising exceptions. This helps AI agents understand what went wrong and potentially retry with corrections.

### Path Security
The `is_safe_path()` function ensures all file operations stay within the base directory, preventing security issues.

### Return Values
Tools return strings with clear success/error messages. For structured data (like file_info), we return JSON-formatted strings.

## What's Next?

In Example 3, you'll learn how to:
- Create an MCP client that connects to servers
- Call tools programmatically
- Handle responses and errors
- Build agent logic on top of MCP