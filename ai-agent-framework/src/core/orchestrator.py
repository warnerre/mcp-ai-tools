#!/usr/bin/env python3
"""
Orchestrator - Core Framework Component

The orchestrator is the central controller that manages the entire multi-agent system.
It coordinates between agents, manages workflows, handles resource allocation,
and provides the main interface for complex multi-agent operations.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

from .types import (
    Task, TaskResult, Context, AgentRegistration, AgentInfo, 
    TaskStatus, AgentStatus, MCPServerConfig
)


class Orchestrator:
    """
    Central orchestrator for multi-agent system coordination.
    
    The orchestrator provides:
    - Agent lifecycle management
    - Task routing and distribution
    - Workflow coordination
    - Resource allocation
    - System monitoring and health checks
    - Inter-agent communication facilitation
    """
    
    def __init__(self, name: str = "main_orchestrator"):
        self.name = name
        self.logger = self._setup_logging()
        
        # Agent management
        self._registered_agents: Dict[str, AgentInfo] = {}
        self._agent_instances: Dict[str, Any] = {}  # Actual agent instances
        
        # Task management
        self._active_tasks: Dict[str, Task] = {}
        self._task_results: Dict[str, TaskResult] = {}
        self._task_queue: List[Task] = []
        
        # Workflow management
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Context management
        self._active_contexts: Dict[str, Context] = {}
        
        # System state
        self._is_running = False
        self._shutdown_requested = False
        
        # Configuration
        self.config = {
            "max_concurrent_tasks": 50,
            "task_timeout": 300,
            "heartbeat_interval": 30,
            "health_check_interval": 60,
            "workflow_timeout": 1800
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup orchestrator logging."""
        logger = logging.getLogger(f"orchestrator.{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def start(self) -> None:
        """Start the orchestrator and its management tasks."""
        if self._is_running:
            self.logger.warning("Orchestrator is already running")
            return
        
        self.logger.info("Starting orchestrator...")
        self._is_running = True
        self._shutdown_requested = False
        
        # Start background tasks
        await asyncio.gather(
            self._heartbeat_loop(),
            self._health_check_loop(),
            self._task_processor_loop(),
            return_exceptions=True
        )
    
    async def stop(self) -> None:
        """Stop the orchestrator and clean up resources."""
        self.logger.info("Stopping orchestrator...")
        self._shutdown_requested = True
        
        # Stop all agents
        for agent_name, agent_instance in self._agent_instances.items():
            try:
                await agent_instance.stop()
                self.logger.info(f"Stopped agent: {agent_name}")
            except Exception as e:
                self.logger.error(f"Error stopping agent {agent_name}: {e}")
        
        self._is_running = False
        self.logger.info("Orchestrator stopped")
    
    async def register_agent(self, agent_instance: Any) -> bool:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent_instance: Instance of an agent (must have BaseAgent interface)
            
        Returns:
            True if registration successful
        """
        try:
            agent_name = agent_instance.name
            registration = agent_instance.registration
            
            # Create agent info
            agent_info = AgentInfo(
                registration=registration,
                status=AgentStatus.OFFLINE,
                current_tasks=[],
                last_heartbeat=datetime.now(),
                error_count=0,
                total_tasks_completed=0
            )
            
            # Store agent
            self._registered_agents[agent_name] = agent_info
            self._agent_instances[agent_name] = agent_instance
            
            # Start the agent
            await agent_instance.setup()
            agent_info.status = AgentStatus.HEALTHY
            
            self.logger.info(f"Registered agent: {agent_name} with capabilities: {registration.capabilities}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent: {e}")
            return False
    
    async def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from the orchestrator.
        
        Args:
            agent_name: Name of the agent to unregister
            
        Returns:
            True if unregistration successful
        """
        try:
            if agent_name in self._agent_instances:
                agent_instance = self._agent_instances[agent_name]
                await agent_instance.stop()
                
                del self._agent_instances[agent_name]
                del self._registered_agents[agent_name]
                
                self.logger.info(f"Unregistered agent: {agent_name}")
                return True
            else:
                self.logger.warning(f"Agent not found for unregistration: {agent_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_name}: {e}")
            return False
    
    async def submit_task(self, task: Task, context: Optional[Context] = None) -> str:
        """
        Submit a task for execution.
        
        Args:
            task: Task to execute
            context: Optional execution context
            
        Returns:
            Task ID for tracking
        """
        # Assign task ID if not present
        if not task.id:
            task.id = str(uuid.uuid4())[:8]
        
        # Store task
        self._active_tasks[task.id] = task
        self._task_queue.append(task)
        
        # Store context if provided
        if context:
            self._active_contexts[task.id] = context
        
        self.logger.info(f"Submitted task {task.id}: {task.description}")
        return task.id
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """
        Get the result of a completed task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            TaskResult if available, None otherwise
        """
        return self._task_results.get(task_id)
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the current status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            TaskStatus if task exists, None otherwise
        """
        task = self._active_tasks.get(task_id)
        return task.status if task else None
    
    async def create_workflow(self, workflow_name: str, steps: List[Dict[str, Any]], 
                            execution_mode: str = "sequential") -> str:
        """
        Create and execute a multi-step workflow.
        
        Args:
            workflow_name: Name of the workflow
            steps: List of workflow steps
            execution_mode: "sequential" or "parallel"
            
        Returns:
            Workflow ID for tracking
        """
        workflow_id = f"workflow_{workflow_name}_{uuid.uuid4().hex[:8]}"
        
        workflow_data = {
            "name": workflow_name,
            "steps": steps,
            "execution_mode": execution_mode,
            "status": "created",
            "created_at": datetime.now(),
            "task_ids": [],
            "completed_steps": 0,
            "failed_steps": 0
        }
        
        self._active_workflows[workflow_id] = workflow_data
        
        # Create tasks for workflow steps
        if execution_mode == "sequential":
            await self._create_sequential_workflow(workflow_id, steps)
        elif execution_mode == "parallel":
            await self._create_parallel_workflow(workflow_id, steps)
        
        self.logger.info(f"Created workflow {workflow_id}: {workflow_name}")
        return workflow_id
    
    async def _create_sequential_workflow(self, workflow_id: str, steps: List[Dict[str, Any]]) -> None:
        """Create tasks for sequential workflow execution."""
        workflow = self._active_workflows[workflow_id]
        prev_task_id = None
        
        for i, step in enumerate(steps):
            task = Task(
                id=f"{workflow_id}_step_{i}",
                type=step.get("type"),
                description=f"Workflow step {i+1}: {step.get('description', step.get('type'))}",
                parameters=step.get("parameters", {}),
                priority=step.get("priority", 5),
                dependencies=[prev_task_id] if prev_task_id else [],
                assigned_agent=step.get("agent")
            )
            
            task_id = await self.submit_task(task)
            workflow["task_ids"].append(task_id)
            prev_task_id = task_id
        
        workflow["status"] = "executing"
    
    async def _create_parallel_workflow(self, workflow_id: str, steps: List[Dict[str, Any]]) -> None:
        """Create tasks for parallel workflow execution."""
        workflow = self._active_workflows[workflow_id]
        
        for i, step in enumerate(steps):
            task = Task(
                id=f"{workflow_id}_step_{i}",
                type=step.get("type"),
                description=f"Parallel step {i+1}: {step.get('description', step.get('type'))}",
                parameters=step.get("parameters", {}),
                priority=step.get("priority", 5),
                dependencies=[],
                assigned_agent=step.get("agent")
            )
            
            task_id = await self.submit_task(task)
            workflow["task_ids"].append(task_id)
        
        workflow["status"] = "executing"
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow status information
        """
        workflow = self._active_workflows.get(workflow_id)
        if not workflow:
            return None
        
        # Update workflow status based on task statuses
        completed_tasks = 0
        failed_tasks = 0
        
        for task_id in workflow["task_ids"]:
            task = self._active_tasks.get(task_id)
            if task:
                if task.status == TaskStatus.COMPLETED:
                    completed_tasks += 1
                elif task.status == TaskStatus.FAILED:
                    failed_tasks += 1
        
        workflow["completed_steps"] = completed_tasks
        workflow["failed_steps"] = failed_tasks
        
        # Determine overall workflow status
        total_steps = len(workflow["task_ids"])
        if completed_tasks == total_steps:
            workflow["status"] = "completed"
        elif failed_tasks > 0:
            workflow["status"] = "partial_failure"
        
        return {
            "workflow_id": workflow_id,
            "name": workflow["name"],
            "status": workflow["status"],
            "total_steps": total_steps,
            "completed_steps": completed_tasks,
            "failed_steps": failed_tasks,
            "execution_mode": workflow["execution_mode"],
            "created_at": workflow["created_at"].isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.
        
        Returns:
            System status information
        """
        # Count tasks by status
        task_counts = {status.value: 0 for status in TaskStatus}
        for task in self._active_tasks.values():
            task_counts[task.status.value] += 1
        
        # Count agents by status
        agent_counts = {status.value: 0 for status in AgentStatus}
        for agent_info in self._registered_agents.values():
            agent_counts[agent_info.status.value] += 1
        
        return {
            "orchestrator_name": self.name,
            "is_running": self._is_running,
            "registered_agents": len(self._registered_agents),
            "active_tasks": len(self._active_tasks),
            "active_workflows": len(self._active_workflows),
            "task_queue_size": len(self._task_queue),
            "task_counts": task_counts,
            "agent_counts": agent_counts,
            "agent_list": list(self._registered_agents.keys())
        }
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent status information
        """
        agent_info = self._registered_agents.get(agent_name)
        agent_instance = self._agent_instances.get(agent_name)
        
        if not agent_info or not agent_instance:
            return None
        
        return {
            "name": agent_name,
            "status": agent_info.status.value,
            "capabilities": agent_info.registration.capabilities,
            "supported_task_types": agent_info.registration.supported_task_types,
            "current_tasks": len(agent_info.current_tasks),
            "max_concurrent_tasks": agent_info.registration.max_concurrent_tasks,
            "total_tasks_completed": agent_info.total_tasks_completed,
            "error_count": agent_info.error_count,
            "last_heartbeat": agent_info.last_heartbeat.isoformat(),
            "available_tools": list(agent_instance.get_available_tools().keys()) if hasattr(agent_instance, 'get_available_tools') else []
        }
    
    async def _find_suitable_agent(self, task: Task) -> Optional[str]:
        """
        Find a suitable agent for a task.
        
        Args:
            task: Task to find an agent for
            
        Returns:
            Agent name if found, None otherwise
        """
        # If task has assigned agent, check if it's available
        if task.assigned_agent:
            agent_info = self._registered_agents.get(task.assigned_agent)
            agent_instance = self._agent_instances.get(task.assigned_agent)
            
            if agent_info and agent_instance and agent_instance.can_handle_task(task):
                return task.assigned_agent
        
        # Find agents that can handle this task type
        suitable_agents = []
        for agent_name, agent_info in self._registered_agents.items():
            agent_instance = self._agent_instances.get(agent_name)
            
            if (agent_info.status == AgentStatus.HEALTHY and 
                agent_instance and 
                agent_instance.can_handle_task(task)):
                suitable_agents.append((agent_name, agent_info))
        
        if not suitable_agents:
            return None
        
        # Sort by current workload (prefer less loaded agents)
        suitable_agents.sort(key=lambda x: len(x[1].current_tasks))
        return suitable_agents[0][0]
    
    async def _execute_task(self, task: Task) -> None:
        """
        Execute a task by assigning it to a suitable agent.
        
        Args:
            task: Task to execute
        """
        try:
            # Find suitable agent
            agent_name = await self._find_suitable_agent(task)
            if not agent_name:
                self.logger.warning(f"No suitable agent found for task {task.id}")
                task.status = TaskStatus.FAILED
                task.error = "No suitable agent available"
                return
            
            # Get agent and context
            agent_instance = self._agent_instances[agent_name]
            agent_info = self._registered_agents[agent_name]
            context = self._active_contexts.get(task.id)
            
            # Update task status
            task.status = TaskStatus.RUNNING
            task.assigned_agent = agent_name
            task.execution_start = datetime.now()
            
            # Add to agent's current tasks
            agent_info.current_tasks.append(task.id)
            
            self.logger.info(f"Executing task {task.id} on agent {agent_name}")
            
            # Execute task
            result = await agent_instance.execute_task(task, context)
            
            # Update task status
            if result.success:
                task.status = TaskStatus.COMPLETED
                task.result = result.data
                agent_info.total_tasks_completed += 1
            else:
                task.status = TaskStatus.FAILED
                task.error = result.error
                agent_info.error_count += 1
            
            task.execution_end = datetime.now()
            
            # Remove from agent's current tasks
            if task.id in agent_info.current_tasks:
                agent_info.current_tasks.remove(task.id)
            
            # Store result
            self._task_results[task.id] = result
            
            self.logger.info(f"Task {task.id} completed with status: {task.status.value}")
            
        except Exception as e:
            self.logger.error(f"Error executing task {task.id}: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.execution_end = datetime.now()
            
            # Clean up agent assignment
            if task.assigned_agent:
                agent_info = self._registered_agents.get(task.assigned_agent)
                if agent_info and task.id in agent_info.current_tasks:
                    agent_info.current_tasks.remove(task.id)
                    agent_info.error_count += 1
    
    async def _task_processor_loop(self) -> None:
        """Background loop for processing tasks from the queue."""
        while self._is_running and not self._shutdown_requested:
            try:
                if self._task_queue:
                    # Get tasks that are ready to execute (dependencies satisfied)
                    ready_tasks = []
                    for task in self._task_queue[:]:
                        if self._are_dependencies_satisfied(task):
                            ready_tasks.append(task)
                            self._task_queue.remove(task)
                    
                    # Execute ready tasks
                    if ready_tasks:
                        # Limit concurrent execution
                        current_running = sum(1 for t in self._active_tasks.values() 
                                            if t.status == TaskStatus.RUNNING)
                        
                        max_concurrent = self.config["max_concurrent_tasks"]
                        available_slots = max_concurrent - current_running
                        
                        tasks_to_execute = ready_tasks[:available_slots]
                        
                        # Execute tasks concurrently
                        if tasks_to_execute:
                            await asyncio.gather(
                                *[self._execute_task(task) for task in tasks_to_execute],
                                return_exceptions=True
                            )
                
                # Wait before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in task processor loop: {e}")
                await asyncio.sleep(5)
    
    def _are_dependencies_satisfied(self, task: Task) -> bool:
        """
        Check if a task's dependencies are satisfied.
        
        Args:
            task: Task to check
            
        Returns:
            True if dependencies are satisfied
        """
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            dep_task = self._active_tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _heartbeat_loop(self) -> None:
        """Background loop for agent heartbeat monitoring."""
        while self._is_running and not self._shutdown_requested:
            try:
                current_time = datetime.now()
                
                for agent_name, agent_info in self._registered_agents.items():
                    time_since_heartbeat = (current_time - agent_info.last_heartbeat).total_seconds()
                    
                    # Update heartbeat
                    agent_info.last_heartbeat = current_time
                    
                    # Check if agent is responsive
                    if time_since_heartbeat > self.config["heartbeat_interval"] * 2:
                        if agent_info.status == AgentStatus.HEALTHY:
                            agent_info.status = AgentStatus.UNHEALTHY
                            self.logger.warning(f"Agent {agent_name} appears unresponsive")
                
                await asyncio.sleep(self.config["heartbeat_interval"])
                
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(10)
    
    async def _health_check_loop(self) -> None:
        """Background loop for system health monitoring."""
        while self._is_running and not self._shutdown_requested:
            try:
                # Monitor system health
                total_agents = len(self._registered_agents)
                healthy_agents = sum(1 for agent in self._registered_agents.values() 
                                   if agent.status == AgentStatus.HEALTHY)
                
                if total_agents > 0:
                    health_ratio = healthy_agents / total_agents
                    if health_ratio < 0.5:
                        self.logger.warning(f"System health degraded: {healthy_agents}/{total_agents} agents healthy")
                
                # Monitor task queue
                if len(self._task_queue) > 100:
                    self.logger.warning(f"Task queue is growing large: {len(self._task_queue)} tasks")
                
                # Clean up completed tasks
                await self._cleanup_old_tasks()
                
                await asyncio.sleep(self.config["health_check_interval"])
                
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_old_tasks(self) -> None:
        """Clean up old completed tasks to prevent memory buildup."""
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self._active_tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.execution_end and
                (current_time - task.execution_end).total_seconds() > 3600):  # 1 hour
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self._active_tasks[task_id]
            if task_id in self._task_results:
                del self._task_results[task_id]
            if task_id in self._active_contexts:
                del self._active_contexts[task_id]
        
        if tasks_to_remove:
            self.logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")