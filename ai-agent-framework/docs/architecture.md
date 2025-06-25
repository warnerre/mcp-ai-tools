# AI Agent Framework Architecture

## Overview

The AI Agent Framework is a learning project that demonstrates how to build a multi-agent system using the Model Context Protocol (MCP). The framework allows multiple AI agents to collaborate on tasks using shared MCP servers.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Framework                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ File Agent  │  │ Task Agent  │  │Coord Agent  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                 │
│  ┌─────────────────────────────────────────────────────────┤
│  │             Agent Framework Core                        │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  │   Agent     │ │    Task     │ │  Context    │       │
│  │  │  Registry   │ │   Router    │ │  Manager    │       │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │
│  └─────────────────────────────────────────────────────────┤
│                          │                                 │
│  ┌─────────────────────────────────────────────────────────┤
│  │                 MCP Server Layer                        │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  │    File     │ │    Task     │ │    Comm     │       │
│  │  │   Server    │ │   Server    │ │   Server    │       │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │
│  └─────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### MCP Server Layer

**File Operations Server**
- Tools: `read_file`, `write_file`, `list_directory`, `create_directory`
- Resources: File system access, directory listings
- Purpose: Provides file system operations to agents

**Task Management Server**
- Tools: `create_task`, `update_task`, `get_task_status`, `list_tasks`
- Resources: Task queue, task history
- Purpose: Manages task lifecycle and coordination

**Communication Server**
- Tools: `send_message`, `broadcast_message`, `get_messages`
- Resources: Message queues, agent communication logs
- Purpose: Enables inter-agent communication

### Agent Framework Core

**Agent Registry**
- Maintains list of available agents and their capabilities
- Handles agent registration and discovery
- Provides capability matching for task routing

**Task Router**
- Analyzes incoming tasks and routes to appropriate agents
- Supports complex task decomposition
- Handles task dependencies and sequencing

**Context Manager**
- Maintains conversation context across agent interactions
- Manages shared state and memory
- Provides context persistence and retrieval

**Orchestrator**
- Coordinates multi-agent workflows
- Manages task execution and monitoring
- Handles error recovery and retry logic

### Agent Implementations

**Base Agent Class**
- Common MCP client functionality
- Connection management to MCP servers
- Tool invocation and result handling
- Standard agent lifecycle methods

**File Agent**
- Specializes in file system operations
- Uses File Operations Server tools
- Handles file-based tasks and queries

**Task Agent**
- Manages task creation and tracking
- Uses Task Management Server tools
- Coordinates task execution workflows

**Coordinator Agent**
- Orchestrates multi-agent collaboration
- Uses Communication Server for coordination
- Manages complex workflow execution

## Data Flow

1. **Task Submission**: User submits task to framework
2. **Task Analysis**: Task Router analyzes task requirements
3. **Agent Selection**: Router identifies capable agents
4. **Task Dispatch**: Task sent to selected agent(s)
5. **Tool Invocation**: Agent calls appropriate MCP server tools
6. **Result Processing**: Agent processes tool results
7. **Response Generation**: Agent generates response
8. **Context Update**: Context Manager updates shared state

## Configuration

The framework uses JSON configuration files:

- `config/agents.json` - Agent definitions and capabilities
- `config/servers.json` - MCP server connection details
- `config/framework.json` - Framework-level settings

## Learning Objectives

This architecture teaches:
- MCP server implementation patterns
- MCP client usage and tool invocation
- Multi-agent coordination strategies
- Task routing and orchestration
- Context management in agent systems
- Error handling and recovery in distributed systems