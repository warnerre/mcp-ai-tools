#!/usr/bin/env python3
"""
Base Agent Class for MCP Client Functionality

This class provides the foundational MCP client capabilities that all agents inherit.
It demonstrates core MCP client patterns:
- Server connection management
- Tool discovery and enumeration
- Tool invocation with error handling
- Resource access
- Context management
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent

from ..core.types import (
    Task, TaskResult, TaskStatus, Context, 
    AgentRegistration, AgentStatus, MCPServerConfig
)


class BaseAgent(ABC):
    """
    Base class for all MCP-enabled agents.
    
    Provides common MCP client functionality and agent lifecycle management.
    Agents inherit from this class to get MCP connectivity and tool access.
    """
    
    def __init__(self, name: str, registration: AgentRegistration):
        """
        Initialize the base agent.
        
        Args:
            name: Unique agent identifier
            registration: Agent registration information
        """
        self.name = name
        self.registration = registration
        self.status = AgentStatus.OFFLINE
        self.current_tasks: List[str] = []
        self.logger = self._setup_logging()
        
        # MCP client state
        self._connected_servers: Dict[str, Any] = {}
        self._available_tools: Dict[str, Dict[str, Any]] = {}
        self._available_resources: Dict[str, Dict[str, Any]] = {}
        
        # Agent state
        self._context: Optional[Context] = None
        self._error_count = 0
        self._total_tasks_completed = 0
        
    def _setup_logging(self) -> logging.Logger:
        """Setup agent-specific logging."""
        logger = logging.getLogger(f"agent.{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    async def connect_to_server(self, server_config: MCPServerConfig) -> bool:
        """
        Connect to an MCP server and discover its capabilities.
        
        Args:
            server_config: Configuration for the MCP server to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to MCP server: {server_config.name}")
            
            # Create server parameters for stdio connection
            server_params = {
                "command": server_config.command,
                "args": server_config.args
            }
            
            # Store the connection parameters for later use
            self._connected_servers[server_config.name] = {
                "config": server_config,
                "params": server_params,
                "tools": {},
                "resources": {}
            }
            
            # Test connection and discover capabilities
            await self._discover_server_capabilities(server_config.name)
            
            self.logger.info(f"Successfully connected to {server_config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {server_config.name}: {e}")
            self._error_count += 1
            return False
    
    async def _discover_server_capabilities(self, server_name: str) -> None:
        """
        Discover tools and resources available from a connected server.
        
        Args:
            server_name: Name of the server to discover capabilities for
        """
        if server_name not in self._connected_servers:
            raise ValueError(f"Server {server_name} not connected")
            
        server_info = self._connected_servers[server_name]
        server_params = server_info["params"]
        
        try:
            # Use temporary connection for discovery
            async with stdio_client(server_params) as (read, write, client):
                await client.initialize()
                
                # Discover tools
                tools_result = await client.list_tools()
                for tool in tools_result.tools:
                    tool_info = {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                        "server": server_name
                    }
                    self._available_tools[tool.name] = tool_info
                    server_info["tools"][tool.name] = tool_info
                
                # Discover resources
                try:
                    resources_result = await client.list_resources()
                    for resource in resources_result.resources:
                        resource_info = {
                            "uri": resource.uri,
                            "name": resource.name,
                            "description": resource.description,
                            "mimeType": resource.mimeType,
                            "server": server_name
                        }
                        self._available_resources[resource.uri] = resource_info
                        server_info["resources"][resource.uri] = resource_info
                except Exception as e:
                    # Resources are optional, don't fail if not supported
                    self.logger.debug(f"Resource discovery failed for {server_name}: {e}")
                
                self.logger.info(
                    f"Discovered {len(server_info['tools'])} tools and "
                    f"{len(server_info['resources'])} resources from {server_name}"
                )
                
        except Exception as e:
            self.logger.error(f"Capability discovery failed for {server_name}: {e}")
            raise
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> CallToolResult:
        """
        Call an MCP tool with the given parameters.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Parameters to pass to the tool
            
        Returns:
            Result from the tool call
            
        Raises:
            ValueError: If tool not found or server not connected
            Exception: If tool call fails
        """
        if tool_name not in self._available_tools:
            raise ValueError(f"Tool '{tool_name}' not available. Available tools: {list(self._available_tools.keys())}")
        
        tool_info = self._available_tools[tool_name]
        server_name = tool_info["server"]
        
        if server_name not in self._connected_servers:
            raise ValueError(f"Server '{server_name}' not connected")
        
        server_params = self._connected_servers[server_name]["params"]
        
        try:
            self.logger.debug(f"Calling tool {tool_name} with parameters: {parameters}")
            
            async with stdio_client(server_params) as (read, write, client):
                await client.initialize()
                result = await client.call_tool(tool_name, parameters)
                
                self.logger.debug(f"Tool {tool_name} returned: {result}")
                return result
                
        except Exception as e:
            self.logger.error(f"Tool call failed - {tool_name}: {e}")
            self._error_count += 1
            raise
    
    async def read_resource(self, resource_uri: str) -> str:
        """
        Read content from an MCP resource.
        
        Args:
            resource_uri: URI of the resource to read
            
        Returns:
            Resource content as string
        """
        if resource_uri not in self._available_resources:
            raise ValueError(f"Resource '{resource_uri}' not available")
        
        resource_info = self._available_resources[resource_uri]
        server_name = resource_info["server"]
        server_params = self._connected_servers[server_name]["params"]
        
        try:
            async with stdio_client(server_params) as (read, write, client):
                await client.initialize()
                content = await client.read_resource(resource_uri)
                return content
                
        except Exception as e:
            self.logger.error(f"Resource read failed - {resource_uri}: {e}")
            raise
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get list of all available tools from connected servers."""
        return self._available_tools.copy()
    
    def get_available_resources(self) -> Dict[str, Dict[str, Any]]:
        """Get list of all available resources from connected servers."""
        return self._available_resources.copy()
    
    def can_handle_task(self, task: Task) -> bool:
        """
        Check if this agent can handle the given task.
        
        Args:
            task: Task to evaluate
            
        Returns:
            True if agent can handle the task
        """
        # Check if task type is supported
        if task.type not in self.registration.supported_task_types:
            return False
        
        # Check if we have capacity for more tasks
        if len(self.current_tasks) >= self.registration.max_concurrent_tasks:
            return False
        
        # Agent-specific checks (implemented by subclasses)
        return self._can_handle_task_specific(task)
    
    @abstractmethod
    def _can_handle_task_specific(self, task: Task) -> bool:
        """
        Agent-specific task handling check.
        
        Subclasses implement this to add custom task evaluation logic.
        """
        pass
    
    async def execute_task(self, task: Task, context: Optional[Context] = None) -> TaskResult:
        """
        Execute a task using available MCP tools.
        
        Args:
            task: Task to execute
            context: Optional execution context
            
        Returns:
            Task execution result
        """
        if not self.can_handle_task(task):
            return TaskResult(
                task_id=task.id,
                success=False,
                error=f"Agent {self.name} cannot handle task type {task.type}"
            )
        
        self.current_tasks.append(task.id)
        self._context = context
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.info(f"Executing task {task.id}: {task.description}")
            
            # Agent-specific task execution
            result_data = await self._execute_task_specific(task, context)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            self._total_tasks_completed += 1
            
            return TaskResult(
                task_id=task.id,
                success=True,
                data=result_data,
                execution_time=execution_time,
                metadata={
                    "agent": self.name,
                    "tools_used": self._get_tools_used_in_task(task)
                }
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self._error_count += 1
            self.logger.error(f"Task execution failed {task.id}: {e}")
            
            return TaskResult(
                task_id=task.id,
                success=False,
                error=str(e),
                execution_time=execution_time,
                metadata={"agent": self.name}
            )
        finally:
            if task.id in self.current_tasks:
                self.current_tasks.remove(task.id)
    
    @abstractmethod
    async def _execute_task_specific(self, task: Task, context: Optional[Context]) -> Dict[str, Any]:
        """
        Agent-specific task execution logic.
        
        Subclasses implement this to define how they execute tasks using MCP tools.
        
        Args:
            task: Task to execute
            context: Optional execution context
            
        Returns:
            Task result data
        """
        pass
    
    def _get_tools_used_in_task(self, task: Task) -> List[str]:
        """
        Get list of tools that would be used for a task.
        
        Default implementation returns empty list.
        Subclasses can override to provide task-specific tool analysis.
        """
        return []
    
    async def start(self) -> None:
        """Start the agent and mark it as healthy."""
        self.status = AgentStatus.HEALTHY
        self.logger.info(f"Agent {self.name} started")
    
    async def stop(self) -> None:
        """Stop the agent and clean up resources."""
        self.status = AgentStatus.OFFLINE
        self.current_tasks.clear()
        self._connected_servers.clear()
        self._available_tools.clear()
        self._available_resources.clear()
        self.logger.info(f"Agent {self.name} stopped")
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get current agent status information."""
        return {
            "name": self.name,
            "status": self.status.value,
            "current_tasks": len(self.current_tasks),
            "max_concurrent_tasks": self.registration.max_concurrent_tasks,
            "capabilities": self.registration.capabilities,
            "connected_servers": list(self._connected_servers.keys()),
            "available_tools": list(self._available_tools.keys()),
            "available_resources": list(self._available_resources.keys()),
            "error_count": self._error_count,
            "total_tasks_completed": self._total_tasks_completed
        }
    
    def __str__(self) -> str:
        return f"Agent({self.name}, status={self.status.value}, tasks={len(self.current_tasks)})"
    
    def __repr__(self) -> str:
        return self.__str__()