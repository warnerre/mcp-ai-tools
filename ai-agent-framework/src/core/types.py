"""Core type definitions for the agent framework."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(Enum):
    """Agent health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class Task:
    """Represents a task to be executed by an agent."""
    id: str
    type: str
    description: str
    parameters: Dict[str, Any]
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None


@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    """Conversation and execution context."""
    conversation_id: str
    user_id: str
    session_data: Dict[str, Any] = field(default_factory=dict)
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    active_tasks: List[Task] = field(default_factory=list)
    agent_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentRegistration:
    """Agent registration information."""
    name: str
    capabilities: List[str]
    supported_task_types: List[str]
    priority: int = 0
    max_concurrent_tasks: int = 1
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    health_check_endpoint: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInfo:
    """Runtime information about an agent."""
    registration: AgentRegistration
    status: AgentStatus = AgentStatus.HEALTHY
    current_tasks: List[str] = field(default_factory=list)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    total_tasks_completed: int = 0


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    transport_type: str
    command: str
    args: List[str]
    tools: List[str]
    resources: List[str]
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """Inter-agent message."""
    id: str
    from_agent: str
    to_agent: Optional[str] = None  # None for broadcast
    channel: Optional[str] = None
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str = "info"
    priority: int = 0