# Example 3: Agent Client

This example demonstrates how to build AI agents that use MCP (Model Context Protocol) servers. It shows the **client side** of MCP - how agents discover, connect to, and use tools.

## Key Learning Concepts

### MCP Client Architecture
- **Server Connection**: How agents connect to MCP servers via stdio transport
- **Tool Discovery**: Automatic discovery of available tools and their schemas
- **Tool Invocation**: Calling MCP tools with parameters and handling responses
- **Error Handling**: Graceful error handling in client-server communication
- **Resource Access**: Reading resources from MCP servers

### Agent Patterns
- **Base Agent Class**: Common MCP client functionality for all agents
- **Task Analysis**: How agents analyze tasks and select appropriate tools
- **Multi-Tool Workflows**: Composing multiple tool calls into complex workflows
- **Context Management**: Maintaining state across tool invocations

## Files

### `simple_agent.py`
A complete agent implementation that specializes in file-based tasks:
- Connects to the file operations MCP server
- Handles 6 different task types
- Demonstrates intelligent tool selection
- Shows multi-step workflow execution

### `demo.py`
Interactive demonstrations of agent capabilities:
- **Basic Operations**: File read/write, project creation
- **Advanced Workflows**: Complex multi-file operations
- **Error Handling**: How agents handle various error conditions
- **Interactive Mode**: Command-line interface for testing

## Running the Examples

### Prerequisites
Make sure you're in the ai-agent-framework directory and have set up the environment:

```bash
cd ai-agent-framework
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Demo
```bash
cd examples/03_agent_client
python demo.py
```

The demo will show you a menu with different options:
1. **Basic file operations** - Simple read/write/create tasks
2. **Advanced workflows** - Complex multi-step operations
3. **Error handling** - How agents handle failures gracefully
4. **Interactive mode** - Try your own commands
5. **All demos** - Run all demonstrations

### Example Output
```
🤖 MCP Agent Demo: Basic File Operations
==================================================
🔧 Setting up agent...
✅ Agent setup complete!
📊 Agent Status: {'name': 'simple_task_agent', 'status': 'healthy', ...}

Example 1: Writing a file
------------------------------
✅ Successfully wrote welcome.txt
📝 Wrote 234 bytes
```

## What You'll Learn

### 1. MCP Client Connection Pattern
```python
# Connect to MCP server
server_config = MCPServerConfig(
    name="file_operations_server",
    transport_type="stdio", 
    command="python",
    args=["src/servers/file_operations_server.py"]
)
await agent.connect_to_server(server_config)
```

### 2. Tool Discovery and Usage
```python
# Discover available tools
await agent._discover_server_capabilities("file_operations_server")

# Call a tool
result = await agent.call_tool("read_file", {"path": "example.txt"})
```

### 3. Task-Driven Architecture
```python
# Define a task
task = Task(
    id="read_001",
    type="read_file", 
    description="Read a configuration file",
    parameters={"path": "config.json"}
)

# Execute the task
result = await agent.execute_task(task)
```

### 4. Multi-Tool Workflows
The agent demonstrates how to combine multiple MCP tools:
- Create directory → Write files → List contents → Analyze results
- Read file → Get file info → Generate summary → Return insights

### 5. Error Handling Patterns
- Tool not found errors
- Invalid parameter validation
- Network/connection failures
- Graceful degradation strategies

## Key Architecture Insights

### Client-Server Separation
MCP provides clean separation between:
- **Servers**: Provide tools and resources (file operations, APIs, databases)
- **Clients**: AI agents that use tools to accomplish tasks
- **Protocol**: Standardized communication layer

### Composable Intelligence
Agents can combine multiple specialized servers:
- File operations server + Task management server + Communication server
- Each server focused on specific domain expertise
- Agents orchestrate cross-server workflows

### Tool Abstraction
MCP tools provide a consistent interface:
- JSON Schema parameter validation
- Structured error responses  
- Rich metadata for discovery
- Language-agnostic protocol

## Next Steps

After running this example, you'll understand:
✅ How MCP clients connect to servers  
✅ Tool discovery and invocation patterns  
✅ Agent task analysis and execution  
✅ Error handling in distributed systems  
✅ Multi-tool workflow composition  

**Ready for Example 4?** The next example shows how multiple agents can work together using shared MCP servers to accomplish complex tasks that require coordination and specialization.

## Troubleshooting

### Connection Issues
- Ensure the file operations server path is correct
- Check that Python environment has MCP dependencies
- Verify no other processes are using stdio

### Tool Errors
- Review tool parameter requirements in error messages
- Check file permissions for file operations
- Ensure target directories exist for write operations

### Performance
- Each tool call creates a new stdio connection (simple but not optimized)
- Production agents would maintain persistent connections
- Consider connection pooling for high-throughput scenarios