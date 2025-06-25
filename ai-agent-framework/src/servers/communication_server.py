#!/usr/bin/env python3
"""
Communication MCP Server

This server provides inter-agent communication capabilities for multi-agent coordination.
It enables agents to send messages, broadcast information, and coordinate workflows.

Key Features:
- Direct agent-to-agent messaging
- Broadcast messaging to multiple agents
- Channel-based communication
- Message queues and delivery tracking
- Event notifications and subscriptions
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
server = Server("communication-server")

# Database setup
DB_PATH = Path("data/communication.db")
DB_PATH.parent.mkdir(exist_ok=True)

# Configuration
MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
MESSAGE_RETENTION_HOURS = 24
MAX_CHANNELS = 100


def init_database():
    """Initialize the communication database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        from_agent TEXT NOT NULL,
        to_agent TEXT,
        channel TEXT,
        message_type TEXT DEFAULT 'info',
        subject TEXT,
        content TEXT NOT NULL,
        priority INTEGER DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        delivered_at TIMESTAMP,
        read_at TIMESTAMP,
        status TEXT DEFAULT 'pending',
        metadata TEXT DEFAULT '{}'
    )
    """)
    
    # Channels table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        name TEXT PRIMARY KEY,
        description TEXT,
        created_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        member_count INTEGER DEFAULT 0,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Channel memberships
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channel_members (
        channel_name TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        role TEXT DEFAULT 'member',
        last_read TIMESTAMP,
        PRIMARY KEY (channel_name, agent_name)
    )
    """)
    
    # Agent subscriptions for events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        agent_name TEXT NOT NULL,
        event_type TEXT NOT NULL,
        filter_criteria TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (agent_name, event_type)
    )
    """)
    
    conn.commit()
    conn.close()


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available communication tools."""
    return [
        Tool(
            name="send_message",
            description="Send a direct message to another agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_agent": {
                        "type": "string",
                        "description": "Name of the sending agent"
                    },
                    "to_agent": {
                        "type": "string",
                        "description": "Name of the receiving agent"
                    },
                    "message_type": {
                        "type": "string",
                        "enum": ["info", "request", "response", "alert", "notification"],
                        "description": "Type of message",
                        "default": "info"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Message subject/title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content"
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Message priority (1-10)",
                        "default": 5
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional message metadata"
                    }
                },
                "required": ["from_agent", "to_agent", "content"]
            }
        ),
        Tool(
            name="broadcast_message",
            description="Broadcast a message to multiple agents or a channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_agent": {
                        "type": "string",
                        "description": "Name of the sending agent"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Channel to broadcast to (optional)"
                    },
                    "target_agents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific agents to broadcast to (if no channel)"
                    },
                    "message_type": {
                        "type": "string",
                        "enum": ["info", "announcement", "alert", "coordination"],
                        "description": "Type of broadcast",
                        "default": "info"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Broadcast subject/title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Broadcast content"
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Message priority",
                        "default": 5
                    }
                },
                "required": ["from_agent", "content"]
            }
        ),
        Tool(
            name="get_messages",
            description="Get messages for an agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Agent to get messages for"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "delivered", "read", "all"],
                        "description": "Filter by message status",
                        "default": "all"
                    },
                    "message_type": {
                        "type": "string",
                        "description": "Filter by message type"
                    },
                    "from_agent": {
                        "type": "string",
                        "description": "Filter by sender"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Filter by channel"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum messages to return",
                        "default": 50
                    },
                    "mark_as_read": {
                        "type": "boolean",
                        "description": "Mark retrieved messages as read",
                        "default": false
                    }
                },
                "required": ["agent_name"]
            }
        ),
        Tool(
            name="create_channel",
            description="Create a communication channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Channel name (unique)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Channel description"
                    },
                    "created_by": {
                        "type": "string",
                        "description": "Agent creating the channel"
                    }
                },
                "required": ["name", "created_by"]
            }
        ),
        Tool(
            name="join_channel",
            description="Join a communication channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_name": {
                        "type": "string",
                        "description": "Channel to join"
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Agent joining the channel"
                    }
                },
                "required": ["channel_name", "agent_name"]
            }
        ),
        Tool(
            name="leave_channel",
            description="Leave a communication channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_name": {
                        "type": "string",
                        "description": "Channel to leave"
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Agent leaving the channel"
                    }
                },
                "required": ["channel_name", "agent_name"]
            }
        ),
        Tool(
            name="list_channels",
            description="List available channels",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Show channels for specific agent (optional)"
                    }
                }
            }
        ),
        Tool(
            name="mark_message_read",
            description="Mark a message as read",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "ID of the message to mark as read"
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Agent marking the message as read"
                    }
                },
                "required": ["message_id", "agent_name"]
            }
        ),
        Tool(
            name="subscribe_to_events",
            description="Subscribe to event notifications",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Agent subscribing to events"
                    },
                    "event_type": {
                        "type": "string",
                        "enum": ["task_created", "task_completed", "agent_joined", "agent_left", "message_sent"],
                        "description": "Type of event to subscribe to"
                    },
                    "filter_criteria": {
                        "type": "object",
                        "description": "Criteria to filter events"
                    }
                },
                "required": ["agent_name", "event_type"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "send_message":
        return await handle_send_message(arguments)
    elif name == "broadcast_message":
        return await handle_broadcast_message(arguments)
    elif name == "get_messages":
        return await handle_get_messages(arguments)
    elif name == "create_channel":
        return await handle_create_channel(arguments)
    elif name == "join_channel":
        return await handle_join_channel(arguments)
    elif name == "leave_channel":
        return await handle_leave_channel(arguments)
    elif name == "list_channels":
        return await handle_list_channels(arguments)
    elif name == "mark_message_read":
        return await handle_mark_message_read(arguments)
    elif name == "subscribe_to_events":
        return await handle_subscribe_to_events(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_send_message(arguments: Dict[str, Any]) -> List[TextContent]:
    """Send a direct message between agents."""
    from_agent = arguments["from_agent"]
    to_agent = arguments["to_agent"]
    content = arguments["content"]
    message_type = arguments.get("message_type", "info")
    subject = arguments.get("subject", "")
    priority = arguments.get("priority", 5)
    metadata = arguments.get("metadata", {})
    
    if len(content) > MAX_MESSAGE_SIZE:
        raise ValueError(f"Message too large (max {MAX_MESSAGE_SIZE} bytes)")
    
    message_id = str(uuid.uuid4())[:8]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO messages (
            id, from_agent, to_agent, message_type, subject, content,
            priority, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id, from_agent, to_agent, message_type, subject,
            content, priority, json.dumps(metadata)
        ))
        
        conn.commit()
        
        return [TextContent(
            type="text",
            text=f"Message sent successfully!\n\nMessage ID: {message_id}\nFrom: {from_agent}\nTo: {to_agent}\nType: {message_type}\nSubject: {subject}"
        )]
        
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Failed to send message: {e}")
    finally:
        conn.close()


async def handle_broadcast_message(arguments: Dict[str, Any]) -> List[TextContent]:
    """Broadcast a message to multiple agents or a channel."""
    from_agent = arguments["from_agent"]
    content = arguments["content"]
    channel = arguments.get("channel")
    target_agents = arguments.get("target_agents", [])
    message_type = arguments.get("message_type", "info")
    subject = arguments.get("subject", "")
    priority = arguments.get("priority", 5)
    
    if len(content) > MAX_MESSAGE_SIZE:
        raise ValueError(f"Message too large (max {MAX_MESSAGE_SIZE} bytes)")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        recipients = []
        
        if channel:
            # Get channel members
            cursor.execute("""
            SELECT agent_name FROM channel_members WHERE channel_name = ?
            """, (channel,))
            recipients = [row[0] for row in cursor.fetchall()]
            
            if not recipients:
                raise ValueError(f"Channel '{channel}' has no members")
        else:
            recipients = target_agents
        
        if not recipients:
            raise ValueError("No recipients specified")
        
        # Create messages for each recipient
        message_ids = []
        for recipient in recipients:
            if recipient == from_agent:  # Don't send to self
                continue
                
            message_id = str(uuid.uuid4())[:8]
            cursor.execute("""
            INSERT INTO messages (
                id, from_agent, to_agent, channel, message_type, subject,
                content, priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id, from_agent, recipient, channel, message_type,
                subject, content, priority
            ))
            message_ids.append(message_id)
        
        conn.commit()
        
        return [TextContent(
            type="text",
            text=f"Broadcast sent successfully!\n\nMessages: {len(message_ids)}\nRecipients: {recipients}\nChannel: {channel or 'Direct'}\nType: {message_type}"
        )]
        
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Failed to broadcast message: {e}")
    finally:
        conn.close()


async def handle_get_messages(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get messages for an agent."""
    agent_name = arguments["agent_name"]
    status_filter = arguments.get("status", "all")
    message_type = arguments.get("message_type")
    from_agent = arguments.get("from_agent")
    channel = arguments.get("channel")
    limit = arguments.get("limit", 50)
    mark_as_read = arguments.get("mark_as_read", False)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build query
    query = """
    SELECT id, from_agent, to_agent, channel, message_type, subject, content,
           priority, created_at, delivered_at, read_at, status, metadata
    FROM messages 
    WHERE to_agent = ?
    """
    params = [agent_name]
    
    if status_filter != "all":
        query += " AND status = ?"
        params.append(status_filter)
    
    if message_type:
        query += " AND message_type = ?"
        params.append(message_type)
    
    if from_agent:
        query += " AND from_agent = ?"
        params.append(from_agent)
    
    if channel:
        query += " AND channel = ?"
        params.append(channel)
    
    query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    if not rows:
        return [TextContent(
            type="text",
            text=f"No messages found for agent '{agent_name}'"
        )]
    
    messages = []
    message_ids_to_mark = []
    
    for row in rows:
        message = {
            "id": row[0],
            "from_agent": row[1],
            "to_agent": row[2],
            "channel": row[3],
            "message_type": row[4],
            "subject": row[5],
            "content": row[6],
            "priority": row[7],
            "created_at": row[8],
            "delivered_at": row[9],
            "read_at": row[10],
            "status": row[11],
            "metadata": json.loads(row[12] or "{}")
        }
        messages.append(message)
        
        if mark_as_read and not message["read_at"]:
            message_ids_to_mark.append(message["id"])
    
    # Mark messages as read if requested
    if message_ids_to_mark:
        placeholders = ','.join(['?' for _ in message_ids_to_mark])
        cursor.execute(f"""
        UPDATE messages 
        SET read_at = CURRENT_TIMESTAMP, status = 'read'
        WHERE id IN ({placeholders})
        """, message_ids_to_mark)
        conn.commit()
    
    conn.close()
    
    response = {
        "agent": agent_name,
        "message_count": len(messages),
        "unread_count": len([m for m in messages if not m["read_at"]]),
        "messages": messages
    }
    
    if mark_as_read and message_ids_to_mark:
        response["marked_as_read"] = len(message_ids_to_mark)
    
    return [TextContent(
        type="text",
        text=f"Messages for '{agent_name}':\n\n" + json.dumps(response, indent=2, default=str)
    )]


async def handle_create_channel(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create a communication channel."""
    name = arguments["name"]
    description = arguments.get("description", "")
    created_by = arguments["created_by"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if channel already exists
        cursor.execute("SELECT name FROM channels WHERE name = ?", (name,))
        if cursor.fetchone():
            raise ValueError(f"Channel '{name}' already exists")
        
        # Create channel
        cursor.execute("""
        INSERT INTO channels (name, description, created_by)
        VALUES (?, ?, ?)
        """, (name, description, created_by))
        
        # Add creator as first member
        cursor.execute("""
        INSERT INTO channel_members (channel_name, agent_name, role)
        VALUES (?, ?, 'admin')
        """, (name, created_by))
        
        # Update member count
        cursor.execute("""
        UPDATE channels SET member_count = 1 WHERE name = ?
        """, (name,))
        
        conn.commit()
        
        return [TextContent(
            type="text",
            text=f"Channel '{name}' created successfully!\nCreated by: {created_by}\nDescription: {description}"
        )]
        
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Failed to create channel: {e}")
    finally:
        conn.close()


async def handle_join_channel(arguments: Dict[str, Any]) -> List[TextContent]:
    """Join a communication channel."""
    channel_name = arguments["channel_name"]
    agent_name = arguments["agent_name"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if channel exists
        cursor.execute("SELECT name FROM channels WHERE name = ?", (channel_name,))
        if not cursor.fetchone():
            raise ValueError(f"Channel '{channel_name}' does not exist")
        
        # Check if already a member
        cursor.execute("""
        SELECT agent_name FROM channel_members 
        WHERE channel_name = ? AND agent_name = ?
        """, (channel_name, agent_name))
        
        if cursor.fetchone():
            return [TextContent(
                type="text",
                text=f"Agent '{agent_name}' is already a member of channel '{channel_name}'"
            )]
        
        # Add to channel
        cursor.execute("""
        INSERT INTO channel_members (channel_name, agent_name)
        VALUES (?, ?)
        """, (channel_name, agent_name))
        
        # Update member count
        cursor.execute("""
        UPDATE channels 
        SET member_count = member_count + 1, last_activity = CURRENT_TIMESTAMP
        WHERE name = ?
        """, (channel_name,))
        
        conn.commit()
        
        return [TextContent(
            type="text",
            text=f"Agent '{agent_name}' joined channel '{channel_name}' successfully!"
        )]
        
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Failed to join channel: {e}")
    finally:
        conn.close()


async def handle_leave_channel(arguments: Dict[str, Any]) -> List[TextContent]:
    """Leave a communication channel."""
    channel_name = arguments["channel_name"]
    agent_name = arguments["agent_name"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if member of channel
        cursor.execute("""
        SELECT agent_name FROM channel_members 
        WHERE channel_name = ? AND agent_name = ?
        """, (channel_name, agent_name))
        
        if not cursor.fetchone():
            return [TextContent(
                type="text",
                text=f"Agent '{agent_name}' is not a member of channel '{channel_name}'"
            )]
        
        # Remove from channel
        cursor.execute("""
        DELETE FROM channel_members 
        WHERE channel_name = ? AND agent_name = ?
        """, (channel_name, agent_name))
        
        # Update member count
        cursor.execute("""
        UPDATE channels 
        SET member_count = member_count - 1, last_activity = CURRENT_TIMESTAMP
        WHERE name = ?
        """, (channel_name,))
        
        conn.commit()
        
        return [TextContent(
            type="text",
            text=f"Agent '{agent_name}' left channel '{channel_name}' successfully!"
        )]
        
    except Exception as e:
        conn.rollback()
        raise ValueError(f"Failed to leave channel: {e}")
    finally:
        conn.close()


async def handle_list_channels(arguments: Dict[str, Any]) -> List[TextContent]:
    """List available channels."""
    agent_name = arguments.get("agent_name")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if agent_name:
        # Get channels for specific agent
        cursor.execute("""
        SELECT c.name, c.description, c.created_by, c.member_count, c.last_activity,
               cm.role, cm.joined_at
        FROM channels c
        JOIN channel_members cm ON c.name = cm.channel_name
        WHERE cm.agent_name = ?
        ORDER BY c.last_activity DESC
        """, (agent_name,))
        
        result_text = f"Channels for agent '{agent_name}':\n\n"
    else:
        # Get all channels
        cursor.execute("""
        SELECT name, description, created_by, member_count, last_activity
        FROM channels
        ORDER BY last_activity DESC
        """)
        
        result_text = "All Channels:\n\n"
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        result_text += "No channels found."
    else:
        channels = []
        for row in rows:
            if agent_name:
                channel = {
                    "name": row[0],
                    "description": row[1],
                    "created_by": row[2],
                    "member_count": row[3],
                    "last_activity": row[4],
                    "my_role": row[5],
                    "joined_at": row[6]
                }
            else:
                channel = {
                    "name": row[0],
                    "description": row[1],
                    "created_by": row[2],
                    "member_count": row[3],
                    "last_activity": row[4]
                }
            channels.append(channel)
        
        result_text += json.dumps(channels, indent=2, default=str)
    
    return [TextContent(type="text", text=result_text)]


async def handle_mark_message_read(arguments: Dict[str, Any]) -> List[TextContent]:
    """Mark a message as read."""
    message_id = arguments["message_id"]
    agent_name = arguments["agent_name"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if message exists and is for this agent
    cursor.execute("""
    SELECT id, to_agent, read_at FROM messages 
    WHERE id = ? AND to_agent = ?
    """, (message_id, agent_name))
    
    row = cursor.fetchone()
    if not row:
        return [TextContent(
            type="text",
            text=f"Message '{message_id}' not found for agent '{agent_name}'"
        )]
    
    if row[2]:  # already read
        return [TextContent(
            type="text",
            text=f"Message '{message_id}' already marked as read"
        )]
    
    # Mark as read
    cursor.execute("""
    UPDATE messages 
    SET read_at = CURRENT_TIMESTAMP, status = 'read'
    WHERE id = ?
    """, (message_id,))
    
    conn.commit()
    conn.close()
    
    return [TextContent(
        type="text",
        text=f"Message '{message_id}' marked as read for agent '{agent_name}'"
    )]


async def handle_subscribe_to_events(arguments: Dict[str, Any]) -> List[TextContent]:
    """Subscribe to event notifications."""
    agent_name = arguments["agent_name"]
    event_type = arguments["event_type"]
    filter_criteria = arguments.get("filter_criteria", {})
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT OR REPLACE INTO subscriptions (agent_name, event_type, filter_criteria)
    VALUES (?, ?, ?)
    """, (agent_name, event_type, json.dumps(filter_criteria)))
    
    conn.commit()
    conn.close()
    
    return [TextContent(
        type="text",
        text=f"Agent '{agent_name}' subscribed to '{event_type}' events with filter: {filter_criteria}"
    )]


@server.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="comm://messages",
            name="Message Queue",
            description="All messages in the system",
            mimeType="application/json"
        ),
        Resource(
            uri="comm://channels",
            name="Channel Directory",
            description="Available communication channels",
            mimeType="application/json"
        ),
        Resource(
            uri="comm://stats",
            name="Communication Statistics",
            description="Usage statistics and metrics",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if uri == "comm://messages":
            cursor.execute("""
            SELECT from_agent, to_agent, channel, message_type, created_at, status
            FROM messages
            ORDER BY created_at DESC
            LIMIT 100
            """)
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "from_agent": row[0],
                    "to_agent": row[1],
                    "channel": row[2],
                    "message_type": row[3],
                    "created_at": row[4],
                    "status": row[5]
                })
            
            return json.dumps({
                "total_messages": len(messages),
                "recent_messages": messages
            }, indent=2, default=str)
            
        elif uri == "comm://channels":
            cursor.execute("""
            SELECT c.name, c.description, c.created_by, c.member_count, c.last_activity,
                   GROUP_CONCAT(cm.agent_name) as members
            FROM channels c
            LEFT JOIN channel_members cm ON c.name = cm.channel_name
            GROUP BY c.name
            ORDER BY c.last_activity DESC
            """)
            
            channels = []
            for row in cursor.fetchall():
                members = row[5].split(',') if row[5] else []
                channels.append({
                    "name": row[0],
                    "description": row[1],
                    "created_by": row[2],
                    "member_count": row[3],
                    "last_activity": row[4],
                    "members": members
                })
            
            return json.dumps({
                "total_channels": len(channels),
                "channels": channels
            }, indent=2, default=str)
            
        elif uri == "comm://stats":
            # Get message statistics
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages WHERE status = 'pending'")
            pending_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM channels")
            total_channels = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT agent_name) FROM channel_members")
            active_agents = cursor.fetchone()[0]
            
            # Message type breakdown
            cursor.execute("""
            SELECT message_type, COUNT(*) 
            FROM messages 
            GROUP BY message_type
            """)
            message_types = dict(cursor.fetchall())
            
            stats = {
                "total_messages": total_messages,
                "pending_messages": pending_messages,
                "total_channels": total_channels,
                "active_agents": active_agents,
                "message_types": message_types
            }
            
            return json.dumps(stats, indent=2)
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