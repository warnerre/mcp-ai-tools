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

This is a learning project in active development. Current implementation status:

- [x] Project structure and documentation
- [x] Type definitions and interfaces
- [ ] MCP server implementations
- [ ] Agent base classes
- [ ] Framework core components
- [ ] Example implementations
- [ ] Integration tests

## Next Steps

1. Implement basic MCP servers
2. Create agent base classes
3. Build core framework components
4. Add example workflows
5. Create integration tests

## Learning Resources

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Architecture Documentation](docs/architecture.md)
- [Agent Specification](docs/agent-specification.md)