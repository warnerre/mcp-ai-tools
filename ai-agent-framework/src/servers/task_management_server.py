#!/usr/bin/env python3
"""
Task Management MCP Server

This server provides task lifecycle management for multi-agent coordination.
It demonstrates how MCP servers can manage state and enable agent collaboration.

Key Features:
- Task creation, tracking, and completion
- Task queues and priority management  
- Dependency tracking between tasks
- Agent assignment and workload balancing
- Task history and analytics
"""

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent


# Server instance
server = Server("task-management-server")

# Database setup
DB_PATH = Path("data/tasks.db")
DB_PATH.parent.mkdir(exist_ok=True)

# Configuration
MAX_TASKS = 1000
TASK_RETENTION_DAYS = 30
DEFAULT_PRIORITY = 5


def init_database():
    """Initialize the task database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        description TEXT NOT NULL,
        parameters TEXT NOT NULL,
        priority INTEGER DEFAULT 5,
        status TEXT DEFAULT 'pending',
        assigned_agent TEXT,
        dependencies TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        deadline TIMESTAMP,
        execution_start TIMESTAMP,
        execution_end TIMESTAMP,
        result TEXT,
        error TEXT,
        metadata TEXT DEFAULT '{}'
    )
    """)
    
    # Task history table for analytics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_data TEXT,
        agent TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Agents table for workload tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        name TEXT PRIMARY KEY,
        capabilities TEXT NOT NULL,
        max_concurrent_tasks INTEGER DEFAULT 1,
        current_task_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'offline',
        last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()


def log_task_event(task_id: str, event_type: str, event_data: Dict[str, Any] = None, agent: str = None):
    """Log a task event to history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO task_history (task_id, event_type, event_data, agent)
    VALUES (?, ?, ?, ?)
    """, (task_id, event_type, json.dumps(event_data or {}), agent))
    
    conn.commit()
    conn.close()


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available task management tools."""
    return [
        Tool(
            name="create_task",
            description="Create a new task in the system",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Type of task to create"
                    },
                    "description": {
                        "type": "string",
                        "description": "Human-readable task description"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Task-specific parameters"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Task priority (1-10, higher is more urgent)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of task IDs this task depends on",
                        "default": []
                    },
                    "deadline": {
                        "type": "string",
                        "description": "ISO format deadline (optional)"
                    },
                    "assigned_agent": {
                        "type": "string",
                        "description": "Specific agent to assign task to (optional)"
                    }
                },
                "required": ["type", "description", "parameters"]
            }
        ),
        Tool(
            name="get_task",
            description="Get details of a specific task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "ID of the task to retrieve"
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="update_task_status",
            description="Update the status of a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "ID of the task to update"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "running", "completed", "failed", "cancelled"],
                        "description": "New status for the task"
                    },
                    "agent": {
                        "type": "string",
                        "description": "Agent updating the status"
                    },
                    "result": {
                        "type": "object",
                        "description": "Task result data (for completed tasks)"
                    },
                    "error": {
                        "type": "string",
                        "description": "Error message (for failed tasks)"
                    }
                },
                "required": ["task_id", "status"]
            }
        ),
        Tool(
            name="list_tasks",
            description="List tasks with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "running", "completed", "failed", "cancelled"],
                        "description": "Filter by task status"
                    },
                    "assigned_agent": {
                        "type": "string",
                        "description": "Filter by assigned agent"
                    },
                    "task_type": {
                        "type": "string",
                        "description": "Filter by task type"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tasks to return",
                        "default": 50
                    },
                    "priority_min": {
                        "type": "integer",
                        "description": "Minimum priority level",
                        "minimum": 1,
                        "maximum": 10
                    }
                }
            }
        ),
        Tool(
            name="get_next_task",
            description="Get the next available task for an agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent requesting a task"
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Agent's capabilities"
                    }
                },
                "required": ["agent_name", "capabilities"]
            }
        ),
        Tool(
            name="register_agent",
            description="Register an agent with the task management system",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Agent name"
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Agent capabilities"
                    },
                    "max_concurrent_tasks": {
                        "type": "integer",
                        "description": "Maximum concurrent tasks for this agent",
                        "default": 1
                    }
                },
                "required": ["name", "capabilities"]
            }
        ),
        Tool(
            name="get_task_history",
            description="Get the history of events for a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "ID of the task"
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="get_agent_workload",
            description="Get current workload information for agents",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Specific agent name (optional)"
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "create_task":
        return await handle_create_task(arguments)
    elif name == "get_task":
        return await handle_get_task(arguments)
    elif name == "update_task_status":
        return await handle_update_task_status(arguments)
    elif name == "list_tasks":
        return await handle_list_tasks(arguments)
    elif name == "get_next_task":
        return await handle_get_next_task(arguments)
    elif name == "register_agent":
        return await handle_register_agent(arguments)
    elif name == "get_task_history":
        return await handle_get_task_history(arguments)
    elif name == "get_agent_workload":
        return await handle_get_agent_workload(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_create_task(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create a new task."""
    task_type = arguments["type"]
    description = arguments["description"]
    parameters = arguments["parameters"]
    priority = arguments.get("priority", DEFAULT_PRIORITY)
    dependencies = arguments.get("dependencies", [])
    deadline = arguments.get("deadline")
    assigned_agent = arguments.get("assigned_agent")
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())[:8]
    
    # Parse deadline if provided
    deadline_dt = None
    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid deadline format: {deadline}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check that dependencies exist
        if dependencies:
            placeholders = ','.join(['?' for _ in dependencies])
            cursor.execute(f"SELECT id FROM tasks WHERE id IN ({placeholders})", dependencies)
            found_deps = [row[0] for row in cursor.fetchall()]
            missing_deps = set(dependencies) - set(found_deps)
            if missing_deps:
                raise ValueError(f"Dependency tasks not found: {missing_deps}")
        
        # Insert task
        cursor.execute("""
        INSERT INTO tasks (
            id, type, description, parameters, priority, dependencies,
            deadline, assigned_agent, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, task_type, description, json.dumps(parameters),
            priority, json.dumps(dependencies), deadline_dt, assigned_agent,
            json.dumps({"created_by": "system"})
        ))
        
        # Log creation event
        log_task_event(task_id, "created", {
            "type": task_type,
            "priority": priority,
            "dependencies": dependencies
        })
        
        conn.commit()
        
        result = {
            "task_id": task_id,
            "type": task_type,
            "description": description,
            "priority": priority,
            "status": "pending",
            "dependencies": dependencies,
            "assigned_agent": assigned_agent
        }
        
        return [TextContent(
            type="text",
            text=f"Task created successfully!\n\nTask Details:\n{json.dumps(result, indent=2)}"
        )]
        
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Failed to create task: {e}")
    finally:
        conn.close()


async def handle_get_task(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get details of a specific task."""
    task_id = arguments["task_id"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, type, description, parameters, priority, status, assigned_agent,
           dependencies, created_at, updated_at, deadline, execution_start,
           execution_end, result, error, metadata
    FROM tasks WHERE id = ?
    """, (task_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise ValueError(f"Task not found: {task_id}")
    
    task = {
        "id": row[0],
        "type": row[1],
        "description": row[2],
        "parameters": json.loads(row[3]),
        "priority": row[4],
        "status": row[5],
        "assigned_agent": row[6],
        "dependencies": json.loads(row[7] or "[]"),
        "created_at": row[8],
        "updated_at": row[9],
        "deadline": row[10],
        "execution_start": row[11],
        "execution_end": row[12],
        "result": json.loads(row[13]) if row[13] else None,
        "error": row[14],
        "metadata": json.loads(row[15] or "{}")
    }
    
    return [TextContent(
        type="text",
        text=f"Task Details:\n{json.dumps(task, indent=2, default=str)}"
    )]


async def handle_update_task_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """Update task status."""
    task_id = arguments["task_id"]
    status = arguments["status"]
    agent = arguments.get("agent")
    result = arguments.get("result")
    error = arguments.get("error")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if task exists
        cursor.execute("SELECT status, assigned_agent FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Task not found: {task_id}")
        
        current_status = row[0]
        assigned_agent = row[1]
        
        # Update task
        now = datetime.now().isoformat()
        
        update_fields = ["status = ?", "updated_at = ?"]
        update_values = [status, now]
        
        if status == "running":
            update_fields.append("execution_start = ?")
            update_values.append(now)
            if agent:
                update_fields.append("assigned_agent = ?")
                update_values.append(agent)
        elif status in ["completed", "failed", "cancelled"]:
            update_fields.append("execution_end = ?")
            update_values.append(now)
            if result:
                update_fields.append("result = ?")
                update_values.append(json.dumps(result))
            if error:
                update_fields.append("error = ?")
                update_values.append(error)
        
        update_values.append(task_id)
        
        cursor.execute(f"""
        UPDATE tasks SET {', '.join(update_fields)}
        WHERE id = ?
        """, update_values)
        
        # Log status change event
        log_task_event(task_id, "status_changed", {
            "from_status": current_status,
            "to_status": status,
            "result": result,
            "error": error
        }, agent)
        
        conn.commit()
        
        return [TextContent(
            type="text",
            text=f"Task {task_id} status updated to '{status}'"
        )]
        
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Failed to update task status: {e}")
    finally:
        conn.close()


async def handle_list_tasks(arguments: Dict[str, Any]) -> List[TextContent]:
    """List tasks with filtering."""
    status_filter = arguments.get("status")
    agent_filter = arguments.get("assigned_agent")
    type_filter = arguments.get("task_type")
    limit = arguments.get("limit", 50)
    priority_min = arguments.get("priority_min")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build query
    query = """
    SELECT id, type, description, priority, status, assigned_agent, created_at, deadline
    FROM tasks WHERE 1=1
    """
    params = []
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    
    if agent_filter:
        query += " AND assigned_agent = ?"
        params.append(agent_filter)
    
    if type_filter:
        query += " AND type = ?"
        params.append(type_filter)
    
    if priority_min:
        query += " AND priority >= ?"
        params.append(priority_min)
    
    query += " ORDER BY priority DESC, created_at ASC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return [TextContent(
            type="text",
            text="No tasks found matching the criteria."
        )]
    
    tasks = []
    for row in rows:
        tasks.append({
            "id": row[0],
            "type": row[1],
            "description": row[2],
            "priority": row[3],
            "status": row[4],
            "assigned_agent": row[5],
            "created_at": row[6],
            "deadline": row[7]
        })
    
    return [TextContent(
        type="text",
        text=f"Found {len(tasks)} tasks:\n\n" + json.dumps(tasks, indent=2, default=str)
    )]


async def handle_get_next_task(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get next available task for an agent."""
    agent_name = arguments["agent_name"]
    capabilities = arguments["capabilities"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find pending tasks that match agent capabilities
    # For now, simple matching by task type being in capabilities
    capability_placeholders = ','.join(['?' for _ in capabilities])
    
    cursor.execute(f"""
    SELECT id, type, description, parameters, priority, dependencies
    FROM tasks 
    WHERE status = 'pending' 
    AND (assigned_agent IS NULL OR assigned_agent = ?)
    AND type IN ({capability_placeholders})
    ORDER BY priority DESC, created_at ASC
    LIMIT 1
    """, [agent_name] + capabilities)
    
    row = cursor.fetchone()
    
    if not row:
        return [TextContent(
            type="text",
            text=f"No available tasks for agent '{agent_name}' with capabilities {capabilities}"
        )]
    
    task_id, task_type, description, parameters, priority, dependencies = row
    dependencies = json.loads(dependencies or "[]")
    
    # Check if dependencies are completed
    if dependencies:
        dep_placeholders = ','.join(['?' for _ in dependencies])
        cursor.execute(f"""
        SELECT COUNT(*) FROM tasks 
        WHERE id IN ({dep_placeholders}) AND status != 'completed'
        """, dependencies)
        
        incomplete_deps = cursor.fetchone()[0]
        if incomplete_deps > 0:
            return [TextContent(
                type="text",
                text=f"Task {task_id} has incomplete dependencies. Checking next task..."
            )]
    
    # Assign task to agent
    cursor.execute("""
    UPDATE tasks SET assigned_agent = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (agent_name, task_id))
    
    conn.commit()
    conn.close()
    
    # Log assignment
    log_task_event(task_id, "assigned", {"agent": agent_name})
    
    task_info = {
        "id": task_id,
        "type": task_type,
        "description": description,
        "parameters": json.loads(parameters),
        "priority": priority,
        "dependencies": dependencies
    }
    
    return [TextContent(
        type="text",
        text=f"Next task for {agent_name}:\n\n" + json.dumps(task_info, indent=2)
    )]


async def handle_register_agent(arguments: Dict[str, Any]) -> List[TextContent]:
    """Register an agent."""
    name = arguments["name"]
    capabilities = arguments["capabilities"]
    max_concurrent = arguments.get("max_concurrent_tasks", 1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT OR REPLACE INTO agents (name, capabilities, max_concurrent_tasks, status)
    VALUES (?, ?, ?, 'online')
    """, (name, json.dumps(capabilities), max_concurrent))
    
    conn.commit()
    conn.close()
    
    return [TextContent(
        type="text",
        text=f"Agent '{name}' registered with capabilities: {capabilities}"
    )]


async def handle_get_task_history(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get task history."""
    task_id = arguments["task_id"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT event_type, event_data, agent, timestamp
    FROM task_history 
    WHERE task_id = ?
    ORDER BY timestamp ASC
    """, (task_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return [TextContent(
            type="text",
            text=f"No history found for task {task_id}"
        )]
    
    history = []
    for row in rows:
        history.append({
            "event_type": row[0],
            "event_data": json.loads(row[1]),
            "agent": row[2],
            "timestamp": row[3]
        })
    
    return [TextContent(
        type="text",
        text=f"Task {task_id} History:\n\n" + json.dumps(history, indent=2, default=str)
    )]


async def handle_get_agent_workload(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get agent workload information."""
    agent_name = arguments.get("agent_name")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if agent_name:
        # Get specific agent info
        cursor.execute("""
        SELECT name, capabilities, max_concurrent_tasks, status, last_heartbeat
        FROM agents WHERE name = ?
        """, (agent_name,))
        agent_row = cursor.fetchone()
        
        if not agent_row:
            return [TextContent(
                type="text",
                text=f"Agent '{agent_name}' not found"
            )]
        
        # Get current task count
        cursor.execute("""
        SELECT COUNT(*) FROM tasks 
        WHERE assigned_agent = ? AND status IN ('running', 'pending')
        """, (agent_name,))
        current_tasks = cursor.fetchone()[0]
        
        agent_info = {
            "name": agent_row[0],
            "capabilities": json.loads(agent_row[1]),
            "max_concurrent_tasks": agent_row[2],
            "current_tasks": current_tasks,
            "status": agent_row[3],
            "last_heartbeat": agent_row[4]
        }
        
        result_text = f"Agent '{agent_name}' Workload:\n\n" + json.dumps(agent_info, indent=2, default=str)
    else:
        # Get all agents
        cursor.execute("""
        SELECT a.name, a.capabilities, a.max_concurrent_tasks, a.status,
               COUNT(t.id) as current_tasks
        FROM agents a
        LEFT JOIN tasks t ON a.name = t.assigned_agent AND t.status IN ('running', 'pending')
        GROUP BY a.name
        """)
        
        rows = cursor.fetchall()
        if not rows:
            result_text = "No agents registered"
        else:
            agents = []
            for row in rows:
                agents.append({
                    "name": row[0],
                    "capabilities": json.loads(row[1]),
                    "max_concurrent_tasks": row[2],
                    "status": row[3],
                    "current_tasks": row[4] or 0
                })
            
            result_text = f"All Agents Workload:\n\n" + json.dumps(agents, indent=2)
    
    conn.close()
    
    return [TextContent(type="text", text=result_text)]


@server.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="task://queue",
            name="Task Queue",
            description="Current task queue and pending tasks",
            mimeType="application/json"
        ),
        Resource(
            uri="task://history",
            name="Task History",
            description="Complete task execution history",
            mimeType="application/json"
        ),
        Resource(
            uri="task://agents",
            name="Agent Registry",
            description="Registered agents and their status",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if uri == "task://queue":
            cursor.execute("""
            SELECT id, type, description, priority, status, assigned_agent, created_at
            FROM tasks WHERE status IN ('pending', 'running')
            ORDER BY priority DESC, created_at ASC
            """)
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    "id": row[0],
                    "type": row[1], 
                    "description": row[2],
                    "priority": row[3],
                    "status": row[4],
                    "assigned_agent": row[5],
                    "created_at": row[6]
                })
            
            return json.dumps({
                "queue_size": len(tasks),
                "tasks": tasks
            }, indent=2, default=str)
            
        elif uri == "task://history":
            cursor.execute("""
            SELECT t.id, t.type, t.status, t.created_at, t.execution_start, t.execution_end,
                   t.assigned_agent
            FROM tasks t
            WHERE t.status IN ('completed', 'failed', 'cancelled')
            ORDER BY t.updated_at DESC
            LIMIT 100
            """)
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "id": row[0],
                    "type": row[1],
                    "status": row[2],
                    "created_at": row[3],
                    "execution_start": row[4],
                    "execution_end": row[5],
                    "assigned_agent": row[6]
                })
            
            return json.dumps({
                "total_completed": len(history),
                "recent_tasks": history
            }, indent=2, default=str)
            
        elif uri == "task://agents":
            cursor.execute("""
            SELECT a.name, a.capabilities, a.max_concurrent_tasks, a.status,
                   COUNT(t.id) as current_tasks
            FROM agents a
            LEFT JOIN tasks t ON a.name = t.assigned_agent AND t.status IN ('running', 'pending')
            GROUP BY a.name
            """)
            
            agents = []
            for row in cursor.fetchall():
                agents.append({
                    "name": row[0],
                    "capabilities": json.loads(row[1]),
                    "max_concurrent_tasks": row[2],
                    "status": row[3],
                    "current_tasks": row[4] or 0
                })
            
            return json.dumps({
                "total_agents": len(agents),
                "agents": agents
            }, indent=2)
        else:
            raise ValueError(f"Unknown resource: {uri}")
    finally:
        conn.close()


# Initialize database on startup
init_database()


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())