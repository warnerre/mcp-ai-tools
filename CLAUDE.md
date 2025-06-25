# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of 14 learning projects designed to explore and understand how MCP (Model Context Protocol) works. Each subdirectory contains educational project specifications for different AI-powered automation systems, serving as hands-on learning exercises rather than production implementations.

## Project Structure

Each project follows a consistent documentation pattern:
- `claude.md` - Project description, technologies, and high-level todos
- `project_instructions.md` - Detailed technical requirements and implementation approach

The 14 project templates cover domains including:
- Development workflows (`ai-dev-workflow`, `ai-code-review`, `ai-documentation-generator`)
- Multi-agent systems (`multi-agent-system`, `ai-agent-framework`)
- Data integration (`custom-mcp-server`, `knowledge-management`)
- Specialized automation (`smart-home-controller`, `natural-language-sysadmin`)
- Content and research (`content-generation-pipeline`, `ai-research-assistant`)

## MCP Protocol Fundamentals

### Core Architecture
MCP follows a **client-server architecture**:
- **MCP Server** = Exposes tools, resources, and prompts
- **MCP Client** = AI agent that uses the exposed capabilities  
- **Transport Layer** = Communication method (stdio, HTTP, WebSocket)

```
AI Agent (Client) ←→ MCP Protocol ←→ MCP Server (Tools/Data)
```

### Key Components

**Tools** - Functions the AI can call:
```json
{
  "name": "read_file",
  "description": "Read contents of a file", 
  "inputSchema": {
    "type": "object",
    "properties": {"path": {"type": "string"}}
  }
}
```

**Resources** - Data sources the AI can access:
```json
{
  "uri": "file:///path/to/document.txt",
  "name": "Project Documentation",
  "mimeType": "text/plain" 
}
```

**Prompts** - Reusable prompt templates:
```json
{
  "name": "code_review",
  "description": "Review code for quality",
  "arguments": [{"name": "code", "description": "Code to review"}]
}
```

### Protocol Flow
1. **Discovery**: Client asks "What tools do you have?"
2. **Invocation**: Client calls tool with parameters
3. **Execution**: Server runs tool and returns results  
4. **Response**: Client uses results to continue conversation

### Composable Agent Architecture
MCP enables building **composable agents** where each server provides specialized capabilities:
- **Database Server** → SQL queries, data analysis
- **API Server** → Web requests, integrations
- **File Server** → File operations, code analysis  
- **Search Server** → Information retrieval

Agent frameworks can **orchestrate** these capabilities for complex automation.

## Architecture Patterns

### MCP Server Pattern
All projects implement custom MCP servers as the core architecture:
- MCP SDK for protocol handling
- Custom server implementations for specialized functionality
- API-first integration approach with external systems
- Real-time data synchronization via webhooks/polling

### Common Technology Stack
- **Core**: MCP Protocol, Python/TypeScript
- **Authentication**: OAuth 2.0, JWT tokens
- **Databases**: SQLite, PostgreSQL for data persistence
- **Integration**: REST APIs (Google, Notion, GitHub, etc.)
- **Security**: Encrypted storage, secure token handling

## Development Approach

### Implementation Phases (Common Pattern)
1. MCP server framework setup
2. Core functionality implementation  
3. External system integration
4. User interface development
5. Performance optimization
6. Comprehensive testing
7. Documentation and deployment

### Key Technical Considerations
- Scalable design for growth and extensibility
- API versioning and backward compatibility
- Error handling and retry mechanisms
- Comprehensive logging and monitoring
- Rate limiting for external API calls

## Working with Projects

### Starting a Learning Project
1. Choose a learning project from the subdirectories based on your interests
2. Read both `claude.md` and `project_instructions.md` to understand the MCP concepts being explored
3. Set up MCP SDK and development environment for hands-on learning
4. Implement authentication flows to understand MCP security patterns
5. Build core functionality to learn MCP protocol implementation

### Common Learning Tasks
- Setting up MCP protocol handling to understand the core framework
- Implementing OAuth 2.0 authentication flows to learn MCP security
- Creating data source connectors to explore MCP integration patterns
- Building monitoring and logging systems to understand MCP observability
- Writing API documentation to practice MCP best practices
- Testing integration with various AI models to learn MCP compatibility

### Dependencies and Setup
Each project requires:
- MCP SDK installation and configuration
- Appropriate language runtime (Python/Node.js)
- Database setup (SQLite/PostgreSQL)
- API credentials for external service integrations
- Development tools for chosen technology stack

## Important Notes

- Each learning project is independent with its own educational focus
- No root-level build system - implement per project to learn different approaches
- Focus on understanding MCP protocol compliance and standards through practice
- Learn security best practices through external integrations
- Explore design patterns for extensibility and AI model compatibility