# AI Agent Framework

A learning project to understand and explore the Model Context Protocol (MCP) through building a multi-agent system.

## Overview

This framework demonstrates how to build a distributed AI agent system using MCP. Multiple specialized agents collaborate on tasks by communicating through MCP servers that provide tools, resources, and coordination capabilities.

## Architecture

The framework consists of three main layers:

1. **MCP Server Layer** - Provides tools and resources
   - File Operations Server
   - Task Management Server  
   - Communication Server

2. **Agent Framework Core** - Coordinates agents and tasks
   - Agent Registry
   - Task Router
   - Context Manager
   - Orchestrator

3. **Agent Implementations** - Specialized agents for different tasks
   - File Agent
   - Task Agent
   - Coordinator Agent

## Learning Objectives

- Understand MCP protocol implementation
- Learn multi-agent coordination patterns
- Practice building MCP servers and clients
- Explore task routing and orchestration
- Implement inter-agent communication

## Project Structure

```
ai-agent-framework/
├── src/
│   ├── servers/          # MCP server implementations
│   ├── agents/           # Agent implementations
│   └── core/             # Framework core components
├── config/               # Configuration files
├── docs/                 # Architecture and specifications
├── tests/                # Test files
├── examples/             # Usage examples
└── requirements.txt      # Python dependencies
```

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Review the architecture:
   - Read `docs/architecture.md` for system overview
   - Review `docs/agent-specification.md` for agent interfaces

3. Explore configurations:
   - `config/agents.json` - Agent definitions
   - `config/servers.json` - MCP server configurations
   - `config/framework.json` - Framework settings

## Development Status

This educational MCP learning project is **COMPLETE** and ready for learning! ✅

**✅ FULLY IMPLEMENTED:**
- [x] **Complete MCP Server Layer**: File Operations, Task Management, Communication servers
- [x] **Advanced Agent Framework**: BaseAgent + 3 specialized agents (File, Task, Coordinator)
- [x] **Core Framework Components**: Orchestrator, TaskRouter, ContextManager with enterprise patterns
- [x] **Multi-Agent Demo**: 5 comprehensive scenarios demonstrating real coordination
- [x] **Integration Tests**: End-to-end validation with educational test patterns
- [x] **Complete Documentation**: Step-by-step tutorial and architecture guides
- [x] **Clean Framework API**: Production-ready interfaces with helper functions

**🎓 EDUCATIONAL FEATURES:**
- **Progressive Learning**: Start simple (single tool) → build to complex (multi-agent orchestration)
- **Real-world Patterns**: Enterprise-grade orchestration, monitoring, error handling
- **Hands-on Examples**: Working code that learners can run and modify
- **MCP Best Practices**: Proper client-server patterns, tool composition, resource management

## Quick Start - Run the Demo!

Experience the complete multi-agent system in action:

```bash
# 1. Setup environment
cd ai-agent-framework
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Run the full multi-agent demo
cd examples/04_multi_agent
python multi_agent_demo.py
```

**You'll see 5 comprehensive demonstrations:**
1. **Agent Coordination** - Multiple agents collaborating on shared goals
2. **Complex Workflow Orchestration** - Multi-phase, multi-agent workflows with coordination points
3. **Inter-Agent Communication** - Messaging, resource allocation, and workload balancing
4. **Error Handling & Resilience** - System robustness and emergency response
5. **Performance Analytics** - Monitoring, reporting, and system health tracking

## Learning Path

**📚 For MCP Beginners:**
1. Read [MCP Learning Guide](docs/mcp-learning-guide.md) for protocol fundamentals
2. Explore [Examples 1-3](examples/) for basic MCP patterns
3. Review [Architecture Documentation](docs/architecture.md) for system design

**🚀 For Framework Users:**
1. Follow the [Complete Tutorial](docs/tutorial.md) for step-by-step learning
2. Run the [Multi-Agent Demo](examples/04_multi_agent/) to see everything working
3. Study [Integration Tests](tests/) for testing patterns

**🏗️ For Advanced Builders:**
1. Examine core components in [src/core/](src/core/) for enterprise patterns
2. Study specialized agents in [src/agents/](src/agents/) for design patterns
3. Analyze MCP servers in [src/servers/](src/servers/) for protocol implementation

## Learning Resources

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Architecture Documentation](docs/architecture.md)
- [Agent Specification](docs/agent-specification.md)