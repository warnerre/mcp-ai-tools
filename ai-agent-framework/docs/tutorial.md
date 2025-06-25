# AI Agent Framework Tutorial

Welcome to the AI Agent Framework tutorial! This guide will teach you how to build and use multi-agent systems with the Model Context Protocol (MCP).

## 📚 Learning Objectives

By the end of this tutorial, you will understand:
- How to build MCP servers and clients
- Multi-agent system architecture patterns
- Task routing and orchestration
- Inter-agent communication
- Context management and shared state
- Error handling and system resilience
- Performance monitoring and optimization

## 🎯 Prerequisites

- Basic Python knowledge
- Understanding of async/await concepts
- Familiarity with APIs and client-server architecture

## 📖 Tutorial Structure

### Part 1: Understanding MCP Fundamentals

#### What is MCP?
The Model Context Protocol (MCP) is a standardized way for AI agents to interact with external tools and data sources. It follows a client-server architecture:

```
AI Agent (Client) ←→ MCP Protocol ←→ MCP Server (Tools/Data)
```

**Key Components:**
- **Tools**: Functions the AI can call (e.g., `read_file`, `send_email`)
- **Resources**: Data sources the AI can access (e.g., files, databases)
- **Prompts**: Reusable templates for AI interactions

#### MCP in Action
```python
# MCP Server provides tools
@server.tool()
def read_file(path: str) -> str:
    return open(path).read()

# MCP Client (AI Agent) uses tools
result = await client.call_tool("read_file", {"path": "config.json"})
content = result.content[0].text
```

### Part 2: Building Your First MCP Server

Let's start with a simple file operations server:

```python
#!/usr/bin/env python3
"""Simple MCP Server Example"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("my-file-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "read_file":
        path = arguments["path"]
        try:
            with open(path, 'r') as f:
                content = f.read()
            return [TextContent(type="text", text=f"File contents:\n{content}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {e}")]

if __name__ == "__main__":
    import asyncio
    
    async def main():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())
    
    asyncio.run(main())
```

**Key Learning Points:**
- MCP servers expose tools through decorators
- Input validation is handled automatically
- Errors should be returned as text, not exceptions
- Tools return `TextContent` for AI-friendly responses

### Part 3: Creating MCP Clients (AI Agents)

Now let's build an AI agent that uses our MCP server:

```python
#!/usr/bin/env python3
"""Simple MCP Client Example"""

import asyncio
from mcp.client.stdio import stdio_client

class SimpleAgent:
    def __init__(self, name: str):
        self.name = name
        self.available_tools = {}
    
    async def connect_to_server(self, command: str, args: list):
        """Connect to an MCP server and discover tools."""
        server_params = {"command": command, "args": args}
        
        async with stdio_client(server_params) as (read, write, client):
            await client.initialize()
            
            # Discover available tools
            tools_result = await client.list_tools()
            for tool in tools_result.tools:
                self.available_tools[tool.name] = {
                    "description": tool.description,
                    "schema": tool.inputSchema
                }
                print(f"📋 Discovered tool: {tool.name}")
    
    async def call_tool(self, command: str, args: list, tool_name: str, parameters: dict):
        """Call a tool on the MCP server."""
        server_params = {"command": command, "args": args}
        
        async with stdio_client(server_params) as (read, write, client):
            await client.initialize()
            
            result = await client.call_tool(tool_name, parameters)
            return result.content[0].text

# Usage example
async def main():
    agent = SimpleAgent("file_reader")
    
    # Connect to our file server
    await agent.connect_to_server("python", ["file_server.py"])
    
    # Use the read_file tool
    result = await agent.call_tool(
        "python", ["file_server.py"],
        "read_file", {"path": "README.md"}
    )
    print(f"🤖 Agent result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Learning Points:**
- MCP clients connect to servers using stdio transport
- Tool discovery happens automatically
- Each tool call creates a new connection (simple but not optimized)
- Clients can connect to multiple servers

### Part 4: Multi-Agent Architecture

Now let's explore the full framework architecture:

```python
#!/usr/bin/env python3
"""Multi-Agent System Example"""

import asyncio
from src.core import create_framework, create_agent_registration
from src.agents.file_agent import FileAgent
from src.agents.task_agent import TaskAgent
from src.agents.coordinator_agent import CoordinatorAgent

async def multi_agent_example():
    # 1. Create the framework
    orchestrator, task_router, context_manager = create_framework("my_system")
    
    # 2. Create specialized agents
    file_agent = FileAgent()
    task_agent = TaskAgent()
    coordinator = CoordinatorAgent()
    
    # 3. Setup agents (connects to MCP servers)
    await file_agent.setup()
    await task_agent.setup()
    await coordinator.setup()
    
    # 4. Register agents with orchestrator
    await orchestrator.register_agent(file_agent)
    await orchestrator.register_agent(task_agent)
    await orchestrator.register_agent(coordinator)
    
    # 5. Create context for task coordination
    context = context_manager.create_context(
        conversation_id="demo_session",
        user_id="tutorial_user"
    )
    
    # 6. Submit tasks - orchestrator routes them automatically
    from src.core.types import Task
    
    # File operation task -> routes to FileAgent
    file_task = Task(
        id="task_001",
        type="create_directory",
        description="Create project structure",
        parameters={"path": "my_project"}
    )
    
    # Task management -> routes to TaskAgent
    workflow_task = Task(
        id="task_002", 
        type="create_task",
        description="Create development workflow",
        parameters={
            "type": "write_file",
            "description": "Add README file",
            "parameters": {"path": "my_project/README.md", "content": "# My Project"}
        }
    )
    
    # Orchestration -> routes to CoordinatorAgent
    coord_task = Task(
        id="task_003",
        type="monitor_system",
        description="Monitor system health",
        parameters={"scope": "full_system"}
    )
    
    # Submit all tasks
    await orchestrator.submit_task(file_task, context)
    await orchestrator.submit_task(workflow_task, context)
    await orchestrator.submit_task(coord_task, context)
    
    # Wait for processing
    await asyncio.sleep(3)
    
    # Check results
    for task_id in ["task_001", "task_002", "task_003"]:
        result = await orchestrator.get_task_result(task_id)
        if result:
            print(f"✅ Task {task_id}: {'Success' if result.success else 'Failed'}")
            if not result.success:
                print(f"   Error: {result.error}")
    
    # Cleanup
    await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(multi_agent_example())
```

**Key Learning Points:**
- Framework provides orchestration, routing, and context management
- Agents specialize in specific capabilities
- Task routing happens automatically based on agent capabilities
- Context enables shared state across agent interactions

### Part 5: Advanced Patterns

#### Agent Specialization Pattern
```python
# Create custom agent with specific capabilities
registration = create_agent_registration(
    name="email_agent",
    capabilities=["email_operations", "communication"],
    supported_task_types=["send_email", "read_inbox", "schedule_email"],
    priority=6,
    max_concurrent_tasks=3
)

class EmailAgent(BaseAgent):
    def __init__(self):
        super().__init__("email_agent", registration)
    
    def _can_handle_task_specific(self, task):
        return task.type in ["send_email", "read_inbox", "schedule_email"]
    
    async def _execute_task_specific(self, task, context):
        if task.type == "send_email":
            return await self._send_email(task.parameters)
        # ... handle other task types
```

#### Workflow Orchestration Pattern
```python
# Complex multi-agent workflow
workflow = {
    "name": "document_processing",
    "phases": [
        {
            "name": "preparation",
            "type": "sequential",  # Steps run in order
            "steps": [
                {"agent": "file_agent", "type": "create_directory", "params": {"path": "output"}},
                {"agent": "file_agent", "type": "backup_files", "params": {"source": "docs"}}
            ]
        },
        {
            "name": "processing", 
            "type": "parallel",  # Steps run simultaneously
            "steps": [
                {"agent": "file_agent", "type": "analyze_directory", "params": {"path": "docs"}},
                {"agent": "task_agent", "type": "generate_reports", "params": {"type": "summary"}}
            ]
        }
    ]
}

# Coordinator executes the workflow
result = await coordinator.execute_task(Task(
    type="execute_complex_workflow",
    description="Process documents",
    parameters={"workflow": workflow}
))
```

#### Inter-Agent Communication Pattern
```python
# Agents communicate through MCP communication server
await coordinator.call_tool("send_message", {
    "from_agent": "coordinator_agent",
    "to_agent": "file_agent",
    "message_type": "request",
    "subject": "Task Assignment",
    "content": "Please process the uploaded documents"
})

# Broadcast to multiple agents
await coordinator.call_tool("broadcast_message", {
    "from_agent": "coordinator_agent", 
    "channel": "alerts",
    "message_type": "announcement",
    "content": "System maintenance starting in 5 minutes"
})
```

### Part 6: Error Handling and Resilience

#### Graceful Error Handling
```python
class ResilientAgent(BaseAgent):
    async def _execute_task_specific(self, task, context):
        try:
            # Attempt primary approach
            return await self._primary_execution(task)
        except Exception as e:
            self.logger.warning(f"Primary execution failed: {e}")
            
            # Try fallback approach
            try:
                return await self._fallback_execution(task)
            except Exception as e2:
                self.logger.error(f"Fallback also failed: {e2}")
                
                # Return graceful error
                return {
                    "success": False,
                    "error": f"All execution methods failed: {e}, {e2}",
                    "fallback_attempted": True
                }
```

#### System Health Monitoring
```python
# Continuous system monitoring
async def monitor_system_health(orchestrator):
    while True:
        status = orchestrator.get_system_status()
        
        # Check agent health
        unhealthy_agents = 0
        for agent_name in status["agent_list"]:
            agent_status = orchestrator.get_agent_status(agent_name)
            if agent_status["status"] != "healthy":
                unhealthy_agents += 1
        
        # Alert if too many unhealthy agents
        if unhealthy_agents > len(status["agent_list"]) / 2:
            print(f"⚠️  System health degraded: {unhealthy_agents} unhealthy agents")
        
        await asyncio.sleep(30)  # Check every 30 seconds
```

### Part 7: Performance Optimization

#### Connection Pooling
```python
class OptimizedAgent(BaseAgent):
    def __init__(self, name, registration):
        super().__init__(name, registration)
        self._connection_pool = {}
    
    async def _get_connection(self, server_name):
        """Reuse connections when possible."""
        if server_name not in self._connection_pool:
            # Create new connection
            self._connection_pool[server_name] = await self._create_connection(server_name)
        return self._connection_pool[server_name]
```

#### Parallel Task Execution
```python
# Execute multiple tasks in parallel
async def parallel_execution(orchestrator, tasks):
    # Submit all tasks
    task_ids = []
    for task in tasks:
        task_id = await orchestrator.submit_task(task)
        task_ids.append(task_id)
    
    # Wait for all to complete
    results = {}
    while len(results) < len(task_ids):
        for task_id in task_ids:
            if task_id not in results:
                result = await orchestrator.get_task_result(task_id)
                if result:
                    results[task_id] = result
        await asyncio.sleep(0.1)
    
    return results
```

## 🚀 Building Your Own Agents

### Step 1: Plan Your Agent
1. **Define Purpose**: What specific problem will your agent solve?
2. **Identify Capabilities**: What tools and skills does it need?
3. **Choose Task Types**: What kinds of tasks will it handle?
4. **Plan MCP Servers**: What external tools/data will it need?

### Step 2: Create MCP Server
```python
# Example: Database Agent Server
@server.tool()
async def query_database(sql: str, params: list = None) -> str:
    # Implement database query logic
    pass

@server.tool() 
async def update_record(table: str, id: int, data: dict) -> str:
    # Implement record update logic
    pass
```

### Step 3: Implement Agent
```python
class DatabaseAgent(BaseAgent):
    def __init__(self):
        registration = create_agent_registration(
            name="database_agent",
            capabilities=["database_operations", "data_analysis"],
            supported_task_types=["query_data", "update_data", "analyze_data"],
            priority=7
        )
        super().__init__("database_agent", registration)
    
    async def setup(self):
        # Connect to database MCP server
        db_server_config = MCPServerConfig(
            name="database_server",
            transport_type="stdio", 
            command="python",
            args=["servers/database_server.py"],
            tools=["query_database", "update_record"]
        )
        return await self.connect_to_server(db_server_config)
```

### Step 4: Integration Testing
```python
async def test_database_agent():
    agent = DatabaseAgent()
    await agent.setup()
    
    # Test query capability
    task = Task(
        type="query_data",
        description="Get user count",
        parameters={"sql": "SELECT COUNT(*) FROM users"}
    )
    
    result = await agent.execute_task(task)
    assert result.success
    print(f"Query result: {result.data}")
```

## 🎓 Best Practices

### Design Principles
1. **Single Responsibility**: Each agent should have a focused purpose
2. **Loose Coupling**: Agents should interact through well-defined interfaces
3. **Fail Gracefully**: Handle errors without crashing the entire system
4. **Monitor Everything**: Instrument your agents for observability
5. **Plan for Scale**: Design with multiple agents and high load in mind

### Security Considerations
1. **Input Validation**: Always validate tool parameters
2. **Access Control**: Limit agent access to necessary resources only
3. **Error Messages**: Don't leak sensitive information in error messages
4. **Audit Logging**: Log all agent actions for security monitoring

### Performance Tips
1. **Connection Reuse**: Pool MCP server connections when possible
2. **Parallel Execution**: Use async/await for concurrent operations
3. **Resource Limits**: Set bounds on memory and CPU usage
4. **Caching**: Cache frequently accessed data and results
5. **Monitoring**: Track response times and resource usage

## 🔧 Troubleshooting Guide

### Common Issues

**Problem**: Agent fails to connect to MCP server
```
Solution: Check server command and args, verify server is executable
Debug: Run server manually to check for errors
```

**Problem**: Tool not found error
```
Solution: Verify tool name matches server implementation
Debug: Check available_tools after server connection
```

**Problem**: Task routing fails
```
Solution: Check agent capabilities match task requirements
Debug: Use task_router.validate_routing_decision()
```

**Problem**: High memory usage
```
Solution: Implement context cleanup and connection pooling
Debug: Monitor context_manager.get_context_stats()
```

### Debugging Techniques
```python
# Enable debug logging
import logging
logging.getLogger("agents").setLevel(logging.DEBUG)
logging.getLogger("orchestrator").setLevel(logging.DEBUG)

# Check system status
status = orchestrator.get_system_status()
print(f"System status: {json.dumps(status, indent=2)}")

# Validate task routing
validation = task_router.validate_routing_decision(task, selected_agent, agents)
print(f"Routing validation: {validation}")

# Monitor performance
stats = task_router.get_routing_stats()
print(f"Routing performance: {stats['success_rate']:.2%}")
```

## 🎯 Next Steps

### Advanced Topics to Explore
1. **Production Deployment**: Docker, Kubernetes, monitoring
2. **Authentication & Authorization**: Secure multi-agent systems
3. **Distributed Agents**: Agents running on different machines
4. **Machine Learning Integration**: AI-powered task routing
5. **Real-time Coordination**: WebSocket-based agent communication

### Project Ideas
1. **DevOps Agent System**: Build, test, deploy coordination
2. **Content Pipeline**: Multi-agent content creation and publishing
3. **Customer Service**: Ticket routing and automated responses
4. **Data Processing**: ETL workflows with specialized agents
5. **Smart Home Controller**: IoT device coordination

### Community Resources
- [MCP Official Documentation](https://modelcontextprotocol.io/)
- [Agent Framework GitHub](https://github.com/your-repo/ai-agent-framework)
- [Example Projects Repository](https://github.com/your-repo/mcp-examples)
- [Community Discord](https://discord.gg/mcp-community)

## 📋 Summary

Congratulations! You've learned how to:

✅ **Understand MCP Architecture**: Client-server patterns and protocol basics  
✅ **Build MCP Servers**: Create tools and resources for AI agents  
✅ **Develop MCP Clients**: Build AI agents that use external tools  
✅ **Design Multi-Agent Systems**: Orchestrate specialized agents  
✅ **Implement Task Routing**: Intelligent task distribution  
✅ **Manage Context**: Shared state and memory coordination  
✅ **Handle Errors**: Build resilient distributed systems  
✅ **Optimize Performance**: Scale and monitor agent systems  

### Key Takeaways

1. **MCP enables composable AI**: Build specialized tools and combine them
2. **Agent specialization works**: Focus each agent on specific capabilities
3. **Orchestration is crucial**: Central coordination prevents chaos
4. **Context matters**: Shared state enables complex workflows
5. **Design for failure**: Error handling and monitoring are essential

### Real-World Applications

This framework is production-ready for:
- **Enterprise Automation**: Complex workflow orchestration
- **DevOps Pipelines**: Build, test, deploy coordination
- **Content Management**: Multi-step publishing workflows
- **Customer Support**: Intelligent ticket routing and processing
- **Data Processing**: ETL and analysis workflows
- **IoT Coordination**: Smart device management and control

Start building your own multi-agent systems and explore the possibilities of composable AI architecture!

---

*Happy coding! 🚀*