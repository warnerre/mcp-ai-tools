# Example 4: Multi-Agent System

This example demonstrates the complete multi-agent framework where multiple specialized agents work together to accomplish complex tasks. It showcases the power of MCP (Model Context Protocol) for building scalable, coordinated agent systems.

## Key Learning Concepts

### Multi-Agent Architecture
- **Agent Specialization**: Each agent focuses on specific capabilities (files, tasks, coordination)
- **Shared Infrastructure**: Agents use common MCP servers for coordination
- **Scalable Design**: Framework supports adding new agents and capabilities
- **Distributed Intelligence**: Complex problems solved through agent collaboration

### Coordination Patterns
- **Workflow Orchestration**: Complex multi-step processes managed across agents
- **Resource Allocation**: Fair distribution of system resources
- **Conflict Resolution**: Automatic handling of agent conflicts
- **Communication Channels**: Structured inter-agent messaging

### System Resilience
- **Error Handling**: Graceful degradation when agents fail
- **Emergency Response**: Coordinated reaction to system emergencies
- **Performance Monitoring**: Real-time system health tracking
- **Fault Tolerance**: System continues operating despite individual agent failures

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                Multi-Agent Framework                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ File Agent  │  │ Task Agent  │  │Coordinator  │         │
│  │ (Files &    │  │ (Workflows &│  │Agent        │         │
│  │ Content)    │  │ Scheduling) │  │(Orchestration)│        │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                 │
│  ┌─────────────────────────────────────────────────────────┤
│  │                 Shared MCP Servers                      │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  │    File     │ │    Task     │ │    Comm     │       │
│  │  │ Operations  │ │ Management  │ │ Server      │       │
│  │  │   Server    │ │   Server    │ │             │       │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │
│  └─────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
```

## Running the Demo

### Prerequisites
Ensure you're in the ai-agent-framework directory with the environment set up:

```bash
cd ai-agent-framework
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Multi-Agent Demo
```bash
cd examples/04_multi_agent
python multi_agent_demo.py
```

The demo will execute 5 comprehensive demonstrations:

1. **Agent Coordination** - Basic collaboration between agents
2. **Complex Workflow Orchestration** - Multi-phase, multi-agent workflows
3. **Inter-Agent Communication** - Messaging and resource allocation
4. **Error Handling & Resilience** - System robustness testing
5. **Performance Analytics** - Monitoring and reporting

### Expected Output
```
🎯 MCP Agent Framework - Example 4: Multi-Agent System
============================================================

🤖 Setting up Multi-Agent System
=============================================
📁 Setting up File Agent...
✅ File Agent ready
📋 Setting up Task Agent...
✅ Task Agent ready
🎯 Setting up Coordinator Agent...
✅ Coordinator Agent ready

🎉 Multi-Agent System ready with 3 agents!

🔄 Demo 1: Agent Coordination
-----------------------------------
Step 1: File Agent creates project structure
✅ Project created: Created python project 'multi_agent_demo' with 8 items
...
```

## Key Components

### Specialized Agents

#### File Agent (`src/agents/file_agent.py`)
- **Purpose**: File system operations and content management
- **Capabilities**: Read/write files, directory operations, content analysis
- **Task Types**: `read_file`, `write_file`, `analyze_directory`, `backup_files`

#### Task Agent (`src/agents/task_agent.py`)
- **Purpose**: Task lifecycle management and workflow coordination
- **Capabilities**: Task creation, scheduling, monitoring, performance analysis
- **Task Types**: `create_task`, `manage_workflow`, `analyze_performance`

#### Coordinator Agent (`src/agents/coordinator_agent.py`)
- **Purpose**: System orchestration and multi-agent coordination
- **Capabilities**: Workflow orchestration, resource allocation, conflict resolution
- **Task Types**: `orchestrate_workflow`, `coordinate_agents`, `handle_emergencies`

### MCP Servers

#### Task Management Server (`src/servers/task_management_server.py`)
- **Tools**: `create_task`, `update_task_status`, `get_next_task`, `register_agent`
- **Resources**: Task queue, task history, agent registry
- **Purpose**: Centralized task coordination

#### Communication Server (`src/servers/communication_server.py`)
- **Tools**: `send_message`, `broadcast_message`, `create_channel`, `join_channel`
- **Resources**: Message queues, communication channels
- **Purpose**: Inter-agent messaging and coordination

## Demonstration Scenarios

### 1. Agent Coordination
Shows how agents work together on a shared goal:
- File Agent creates project structure
- Task Agent manages workflow tasks
- Coordinator monitors system health

### 2. Complex Workflow Orchestration
Demonstrates multi-phase workflows:
- **Setup Phase** (Sequential): Create workspace, organize files
- **Processing Phase** (Parallel): Analyze content, generate reports
- **Coordination Points**: Synchronization between phases

### 3. Inter-Agent Communication
Shows communication patterns:
- Communication channel management
- Workload balancing coordination
- Resource allocation strategies

### 4. Error Handling & Resilience
Tests system robustness:
- Invalid operation handling
- Emergency response coordination
- Conflict resolution mechanisms

### 5. Performance Analytics
Demonstrates monitoring capabilities:
- System performance analysis
- Comprehensive reporting
- Health status monitoring

## What You'll Learn

### Multi-Agent Design Patterns

**Agent Specialization**:
```python
# Each agent has focused capabilities
file_agent = FileAgent()  # File operations
task_agent = TaskAgent()  # Workflow management
coordinator = CoordinatorAgent()  # System orchestration
```

**Shared Infrastructure**:
```python
# All agents connect to same MCP servers
await agent.connect_to_server(task_management_server)
await agent.connect_to_server(communication_server)
```

**Workflow Orchestration**:
```python
# Coordinator manages complex workflows
workflow = {
    "phases": [
        {"name": "setup", "type": "sequential", "steps": [...]},
        {"name": "process", "type": "parallel", "steps": [...]}
    ]
}
await coordinator.execute_task(orchestrate_workflow_task)
```

### Communication Patterns

**Direct Messaging**:
```python
await comm_server.send_message({
    "from_agent": "coordinator",
    "to_agent": "file_agent", 
    "content": "Task assignment ready"
})
```

**Channel Broadcasting**:
```python
await comm_server.broadcast_message({
    "from_agent": "coordinator",
    "channel": "alerts",
    "content": "System maintenance starting"
})
```

### Resource Management

**Workload Balancing**:
```python
# Coordinator monitors agent capacity
workload = await task_server.get_agent_workload()
# Redistributes tasks based on capacity
```

**Conflict Resolution**:
```python
# Automatic resolution of resource conflicts
await coordinator.resolve_conflicts({
    "type": "resource_conflict",
    "parties": ["agent1", "agent2"],
    "strategy": "priority_based"
})
```

## Advanced Concepts

### Scalability Patterns
- **Horizontal Scaling**: Add more agents of the same type
- **Vertical Scaling**: Enhance individual agent capabilities
- **Load Distribution**: Automatic task routing based on capacity

### Fault Tolerance
- **Agent Failure Detection**: Health monitoring and automatic failover
- **Graceful Degradation**: System continues with reduced functionality
- **Recovery Mechanisms**: Automatic restart and state recovery

### Performance Optimization
- **Connection Pooling**: Reuse MCP server connections
- **Asynchronous Operations**: Parallel task execution
- **Resource Optimization**: Efficient memory and CPU usage

## Extending the Framework

### Adding New Agents
1. Inherit from `BaseAgent`
2. Define capabilities and supported task types
3. Implement `_execute_task_specific` method
4. Connect to required MCP servers

### Creating New MCP Servers
1. Define tools and resources
2. Implement tool handlers
3. Add database persistence if needed
4. Register with agents

### Workflow Patterns
- **Sequential**: Steps execute in order with dependencies
- **Parallel**: Steps execute simultaneously
- **Conditional**: Steps execute based on conditions
- **Loop**: Repeated execution with termination criteria

## Real-World Applications

This multi-agent framework can be applied to:

- **DevOps Automation**: Build, test, deploy coordination
- **Data Processing Pipelines**: ETL workflows across systems
- **Content Management**: Document processing and organization
- **System Administration**: Infrastructure monitoring and maintenance
- **Research Workflows**: Coordinated analysis and reporting

## Next Steps

After mastering this multi-agent system:

✅ **Understand agent specialization and collaboration**  
✅ **Master workflow orchestration patterns**  
✅ **Implement inter-agent communication**  
✅ **Design resilient distributed systems**  
✅ **Build scalable agent frameworks**  

**Ready for Production?** Consider adding authentication, persistent storage, monitoring dashboards, and deployment automation for production multi-agent systems.

## Troubleshooting

### Agent Setup Issues
- Ensure all MCP servers are accessible
- Check database permissions for task/communication servers
- Verify agent registration succeeds

### Communication Problems
- Check communication server connectivity
- Verify channel creation and membership
- Monitor message delivery status

### Performance Issues
- Monitor agent workloads and capacity
- Check for resource conflicts
- Optimize workflow coordination points

### Workflow Failures
- Review task dependencies and sequencing
- Check agent capability matching
- Monitor error handling and recovery