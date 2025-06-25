"""
AI Agent Framework Core Components

This module provides the core components for building multi-agent systems using MCP.
It includes orchestration, task routing, context management, and type definitions.

Educational Focus:
- Demonstrates enterprise-grade orchestration patterns
- Shows intelligent task routing and load balancing
- Teaches context management in distributed systems
- Provides clean APIs for learners to build upon
"""

# Core type definitions
from .types import (
    Task, TaskResult, TaskStatus, Context,
    AgentRegistration, AgentInfo, AgentStatus,
    MCPServerConfig, Message
)

# Core framework components
from .orchestrator import Orchestrator
from .task_router import TaskRouter
from .context_manager import ContextManager

# Framework API
__all__ = [
    # Types
    "Task", "TaskResult", "TaskStatus", "Context",
    "AgentRegistration", "AgentInfo", "AgentStatus", 
    "MCPServerConfig", "Message",
    
    # Core Components
    "Orchestrator", "TaskRouter", "ContextManager",
    
    # Convenience API
    "create_framework", "create_agent_registration"
]


def create_framework(name: str = "ai_agent_framework", 
                    storage_path: str = "data") -> tuple[Orchestrator, TaskRouter, ContextManager]:
    """
    Create a complete framework instance with all core components.
    
    Educational Purpose:
    This convenience function shows learners how to properly initialize
    and configure a multi-agent framework for production use.
    
    Args:
        name: Framework instance name
        storage_path: Path for persistent storage
        
    Returns:
        Tuple of (orchestrator, task_router, context_manager)
        
    Example:
        ```python
        orchestrator, router, context_mgr = create_framework("my_framework")
        
        # Register agents
        await orchestrator.register_agent(file_agent)
        await orchestrator.register_agent(task_agent)
        
        # Start the framework
        await orchestrator.start()
        ```
    """
    orchestrator = Orchestrator(name=f"{name}_orchestrator")
    task_router = TaskRouter(name=f"{name}_router")
    context_manager = ContextManager(name=f"{name}_context", storage_path=storage_path)
    
    # Configure framework components to work together
    orchestrator._task_router = task_router
    orchestrator._context_manager = context_manager
    
    return orchestrator, task_router, context_manager


def create_agent_registration(name: str, capabilities: list[str], 
                            supported_task_types: list[str],
                            priority: int = 5, max_concurrent_tasks: int = 3,
                            config: dict = None) -> AgentRegistration:
    """
    Create an agent registration with sensible defaults.
    
    Educational Purpose:
    This helper function teaches learners proper agent configuration
    patterns and shows how to structure agent capabilities.
    
    Args:
        name: Agent name
        capabilities: List of agent capabilities
        supported_task_types: Task types the agent can handle
        priority: Agent priority (1-10, higher = more important)
        max_concurrent_tasks: Maximum concurrent tasks
        config: Additional configuration
        
    Returns:
        Configured AgentRegistration
        
    Example:
        ```python
        registration = create_agent_registration(
            name="file_processor",
            capabilities=["file_operations", "content_analysis"],
            supported_task_types=["read_file", "analyze_content", "backup_files"],
            priority=7,
            max_concurrent_tasks=5
        )
        
        agent = MyAgent(registration)
        ```
    """
    return AgentRegistration(
        name=name,
        capabilities=capabilities,
        supported_task_types=supported_task_types,
        priority=priority,
        max_concurrent_tasks=max_concurrent_tasks,
        config=config or {}
    )