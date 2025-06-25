#!/usr/bin/env python3
"""
Task Agent Implementation

Specialized agent for task lifecycle management and workflow coordination.
This agent connects to the task management MCP server and provides
intelligent task handling capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.base_agent import BaseAgent
from src.core.types import (
    Task, TaskResult, Context, AgentRegistration, MCPServerConfig
)


class TaskAgent(BaseAgent):
    """
    Specialized agent for task management and workflow coordination.
    
    Capabilities:
    - Task creation and lifecycle management
    - Workflow planning and execution
    - Task scheduling and prioritization
    - Dependency tracking and resolution
    - Agent workload monitoring
    - Task analytics and reporting
    """
    
    def __init__(self):
        registration = AgentRegistration(
            name="task_agent",
            capabilities=[
                "task_management",
                "workflow_coordination",
                "task_scheduling",
                "task_monitoring",
                "dependency_resolution",
                "workload_balancing"
            ],
            supported_task_types=[
                "create_task",
                "manage_workflow",
                "schedule_tasks",
                "monitor_progress",
                "balance_workload",
                "analyze_performance",
                "coordinate_dependencies",
                "generate_reports"
            ],
            priority=8,
            max_concurrent_tasks=5,
            config={
                "max_workflow_depth": 10,
                "default_timeout": 300,
                "retry_attempts": 3,
                "priority_levels": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        )
        
        super().__init__("task_agent", registration)
        
        # Task management state
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
    
    async def setup(self) -> bool:
        """Setup the task agent by connecting to required servers."""
        try:
            # Connect to task management server
            task_server_config = MCPServerConfig(
                name="task_management_server",
                transport_type="stdio",
                command="python",
                args=["src/servers/task_management_server.py"],
                tools=[
                    "create_task", "get_task", "update_task_status", "list_tasks",
                    "get_next_task", "register_agent", "get_task_history", "get_agent_workload"
                ],
                resources=["task_queue", "task_history", "agent_registry"]
            )
            
            success = await self.connect_to_server(task_server_config)
            if not success:
                self.logger.error("Failed to connect to task management server")
                return False
            
            # Register self with task management system
            await self.call_tool("register_agent", {
                "name": self.name,
                "capabilities": self.registration.capabilities,
                "max_concurrent_tasks": self.registration.max_concurrent_tasks
            })
            
            await self.start()
            self.logger.info("Task Agent setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Task Agent setup failed: {e}")
            return False
    
    def _can_handle_task_specific(self, task: Task) -> bool:
        """Check if this agent can handle the specific task."""
        return task.type in self.registration.supported_task_types
    
    async def _execute_task_specific(self, task: Task, context: Optional[Context]) -> Dict[str, Any]:
        """Execute task-specific operations."""
        
        if task.type == "create_task":
            return await self._handle_create_task(task)
        elif task.type == "manage_workflow":
            return await self._handle_manage_workflow(task)
        elif task.type == "schedule_tasks":
            return await self._handle_schedule_tasks(task)
        elif task.type == "monitor_progress":
            return await self._handle_monitor_progress(task)
        elif task.type == "balance_workload":
            return await self._handle_balance_workload(task)
        elif task.type == "analyze_performance":
            return await self._handle_analyze_performance(task)
        elif task.type == "coordinate_dependencies":
            return await self._handle_coordinate_dependencies(task)
        elif task.type == "generate_reports":
            return await self._handle_generate_reports(task)
        else:
            raise ValueError(f"Unsupported task type: {task.type}")
    
    async def _handle_create_task(self, task: Task) -> Dict[str, Any]:
        """Create a new task in the system."""
        task_type = task.parameters.get("type")
        description = task.parameters.get("description")
        parameters = task.parameters.get("parameters", {})
        priority = task.parameters.get("priority", 5)
        dependencies = task.parameters.get("dependencies", [])
        deadline = task.parameters.get("deadline")
        assigned_agent = task.parameters.get("assigned_agent")
        
        if not task_type or not description:
            raise ValueError("Task type and description are required")
        
        self.logger.info(f"Creating task: {task_type} - {description}")
        
        # Create task using MCP tool
        result = await self.call_tool("create_task", {
            "type": task_type,
            "description": description,
            "parameters": parameters,
            "priority": priority,
            "dependencies": dependencies,
            "deadline": deadline,
            "assigned_agent": assigned_agent
        })
        
        # Parse the result to extract task ID
        result_text = result.content[0].text
        import json
        try:
            # Extract JSON from the result text
            json_start = result_text.find('{')
            if json_start != -1:
                json_text = result_text[json_start:]
                task_info = json.loads(json_text)
                task_id = task_info.get("task_id")
            else:
                task_id = "unknown"
        except Exception:
            task_id = "unknown"
        
        return {
            "task_id": task_id,
            "task_type": task_type,
            "description": description,
            "priority": priority,
            "status": "created",
            "result": result_text
        }
    
    async def _handle_manage_workflow(self, task: Task) -> Dict[str, Any]:
        """Manage a multi-step workflow."""
        workflow_id = task.parameters.get("workflow_id")
        workflow_steps = task.parameters.get("steps", [])
        execution_mode = task.parameters.get("execution_mode", "sequential")
        
        if not workflow_id or not workflow_steps:
            raise ValueError("Workflow ID and steps are required")
        
        self.logger.info(f"Managing workflow: {workflow_id} with {len(workflow_steps)} steps")
        
        # Store workflow state
        self._active_workflows[workflow_id] = {
            "steps": workflow_steps,
            "execution_mode": execution_mode,
            "status": "planning",
            "created_tasks": [],
            "completed_tasks": [],
            "failed_tasks": []
        }
        
        created_tasks = []
        
        if execution_mode == "sequential":
            # Create tasks with dependencies
            prev_task_id = None
            for i, step in enumerate(workflow_steps):
                dependencies = [prev_task_id] if prev_task_id else []
                
                create_result = await self.call_tool("create_task", {
                    "type": step.get("type"),
                    "description": step.get("description"),
                    "parameters": step.get("parameters", {}),
                    "priority": step.get("priority", 5),
                    "dependencies": dependencies
                })
                
                # Extract task ID from result
                result_text = create_result.content[0].text
                try:
                    import json
                    json_start = result_text.find('{')
                    if json_start != -1:
                        task_info = json.loads(result_text[json_start:])
                        task_id = task_info.get("task_id")
                        created_tasks.append(task_id)
                        prev_task_id = task_id
                except Exception:
                    self.logger.warning(f"Could not extract task ID from step {i}")
        
        elif execution_mode == "parallel":
            # Create all tasks without dependencies
            for step in workflow_steps:
                create_result = await self.call_tool("create_task", {
                    "type": step.get("type"),
                    "description": step.get("description"),
                    "parameters": step.get("parameters", {}),
                    "priority": step.get("priority", 5),
                    "dependencies": []
                })
                
                # Extract task ID
                result_text = create_result.content[0].text
                try:
                    import json
                    json_start = result_text.find('{')
                    if json_start != -1:
                        task_info = json.loads(result_text[json_start:])
                        task_id = task_info.get("task_id")
                        created_tasks.append(task_id)
                except Exception:
                    continue
        
        # Update workflow state
        self._active_workflows[workflow_id]["created_tasks"] = created_tasks
        self._active_workflows[workflow_id]["status"] = "executing"
        
        return {
            "workflow_id": workflow_id,
            "execution_mode": execution_mode,
            "total_steps": len(workflow_steps),
            "created_tasks": created_tasks,
            "status": "executing"
        }
    
    async def _handle_schedule_tasks(self, task: Task) -> Dict[str, Any]:
        """Schedule tasks based on priority and dependencies."""
        scheduling_strategy = task.parameters.get("strategy", "priority_first")
        max_concurrent = task.parameters.get("max_concurrent", 10)
        agent_filter = task.parameters.get("agent_filter")
        
        self.logger.info(f"Scheduling tasks using {scheduling_strategy} strategy")
        
        # Get pending tasks
        result = await self.call_tool("list_tasks", {
            "status": "pending",
            "limit": 100
        })
        
        # Parse tasks from result
        result_text = result.content[0].text
        tasks_data = []
        
        try:
            import json
            # Extract JSON array from result
            json_start = result_text.find('[')
            if json_start != -1:
                json_text = result_text[json_start:]
                tasks_data = json.loads(json_text)
        except Exception:
            self.logger.warning("Could not parse tasks from result")
        
        # Apply scheduling strategy
        scheduled_tasks = []
        
        if scheduling_strategy == "priority_first":
            # Sort by priority (highest first)
            sorted_tasks = sorted(tasks_data, key=lambda t: t.get("priority", 5), reverse=True)
            scheduled_tasks = sorted_tasks[:max_concurrent]
        
        elif scheduling_strategy == "fifo":
            # First In, First Out
            sorted_tasks = sorted(tasks_data, key=lambda t: t.get("created_at", ""))
            scheduled_tasks = sorted_tasks[:max_concurrent]
        
        elif scheduling_strategy == "deadline_first":
            # Sort by deadline (earliest first)
            deadline_tasks = [t for t in tasks_data if t.get("deadline")]
            sorted_tasks = sorted(deadline_tasks, key=lambda t: t.get("deadline", ""))
            scheduled_tasks = sorted_tasks[:max_concurrent]
        
        return {
            "scheduling_strategy": scheduling_strategy,
            "total_pending_tasks": len(tasks_data),
            "scheduled_tasks": len(scheduled_tasks),
            "max_concurrent": max_concurrent,
            "scheduled_task_ids": [t.get("id") for t in scheduled_tasks]
        }
    
    async def _handle_monitor_progress(self, task: Task) -> Dict[str, Any]:
        """Monitor progress of tasks and workflows."""
        monitor_target = task.parameters.get("target", "all")  # "all", "workflow_id", "agent_name"
        target_id = task.parameters.get("target_id")
        
        self.logger.info(f"Monitoring progress for target: {monitor_target}")
        
        progress_data = {}
        
        if monitor_target == "all":
            # Get overall system progress
            for status in ["pending", "running", "completed", "failed"]:
                result = await self.call_tool("list_tasks", {
                    "status": status,
                    "limit": 1000
                })
                
                # Count tasks in this status
                result_text = result.content[0].text
                if "Found" in result_text:
                    try:
                        count = int(result_text.split("Found ")[1].split(" tasks")[0])
                        progress_data[status] = count
                    except Exception:
                        progress_data[status] = 0
                else:
                    progress_data[status] = 0
        
        elif monitor_target == "workflow" and target_id:
            # Monitor specific workflow
            if target_id in self._active_workflows:
                workflow = self._active_workflows[target_id]
                progress_data = {
                    "workflow_id": target_id,
                    "total_tasks": len(workflow["created_tasks"]),
                    "status": workflow["status"],
                    "completed_tasks": len(workflow["completed_tasks"]),
                    "failed_tasks": len(workflow["failed_tasks"])
                }
        
        elif monitor_target == "agent" and target_id:
            # Monitor specific agent workload
            result = await self.call_tool("get_agent_workload", {
                "agent_name": target_id
            })
            
            result_text = result.content[0].text
            try:
                import json
                json_start = result_text.find('{')
                if json_start != -1:
                    agent_data = json.loads(result_text[json_start:])
                    progress_data = agent_data
            except Exception:
                progress_data = {"error": "Could not parse agent data"}
        
        return {
            "monitor_target": monitor_target,
            "target_id": target_id,
            "progress_data": progress_data,
            "timestamp": task.created_at.isoformat() if hasattr(task, 'created_at') else None
        }
    
    async def _handle_balance_workload(self, task: Task) -> Dict[str, Any]:
        """Balance workload across available agents."""
        rebalance_strategy = task.parameters.get("strategy", "even_distribution")
        force_rebalance = task.parameters.get("force_rebalance", False)
        
        self.logger.info(f"Balancing workload using {rebalance_strategy} strategy")
        
        # Get current agent workloads
        workload_result = await self.call_tool("get_agent_workload", {})
        workload_text = workload_result.content[0].text
        
        agents_data = []
        try:
            import json
            json_start = workload_text.find('[')
            if json_start != -1:
                agents_data = json.loads(workload_text[json_start:])
        except Exception:
            self.logger.warning("Could not parse agent workload data")
        
        # Get pending tasks
        pending_result = await self.call_tool("list_tasks", {
            "status": "pending",
            "limit": 100
        })
        
        pending_text = pending_result.content[0].text
        pending_tasks = []
        try:
            import json
            json_start = pending_text.find('[')
            if json_start != -1:
                pending_tasks = json.loads(pending_text[json_start:])
        except Exception:
            pass
        
        # Calculate workload balance
        total_agents = len(agents_data)
        total_tasks = len(pending_tasks)
        
        if total_agents == 0:
            return {
                "strategy": rebalance_strategy,
                "status": "no_agents_available",
                "total_pending_tasks": total_tasks
            }
        
        # Simple even distribution strategy
        if rebalance_strategy == "even_distribution":
            tasks_per_agent = total_tasks // total_agents
            assignments = {}
            
            for i, agent in enumerate(agents_data):
                agent_name = agent.get("name")
                if agent_name:
                    start_idx = i * tasks_per_agent
                    end_idx = start_idx + tasks_per_agent
                    if i == total_agents - 1:  # Last agent gets remaining tasks
                        end_idx = total_tasks
                    
                    assigned_tasks = pending_tasks[start_idx:end_idx]
                    assignments[agent_name] = [t.get("id") for t in assigned_tasks]
        
        return {
            "strategy": rebalance_strategy,
            "total_agents": total_agents,
            "total_pending_tasks": total_tasks,
            "assignments": assignments if 'assignments' in locals() else {},
            "status": "completed"
        }
    
    async def _handle_analyze_performance(self, task: Task) -> Dict[str, Any]:
        """Analyze task execution performance."""
        analysis_period = task.parameters.get("period", "last_24_hours")
        metrics = task.parameters.get("metrics", ["completion_rate", "avg_execution_time", "error_rate"])
        
        self.logger.info(f"Analyzing performance for period: {analysis_period}")
        
        # Get completed tasks for analysis
        completed_result = await self.call_tool("list_tasks", {
            "status": "completed",
            "limit": 1000
        })
        
        failed_result = await self.call_tool("list_tasks", {
            "status": "failed",
            "limit": 1000
        })
        
        # Parse results
        completed_text = completed_result.content[0].text
        failed_text = failed_result.content[0].text
        
        completed_count = 0
        failed_count = 0
        
        # Extract counts from results
        if "Found" in completed_text:
            try:
                completed_count = int(completed_text.split("Found ")[1].split(" tasks")[0])
            except Exception:
                pass
        
        if "Found" in failed_text:
            try:
                failed_count = int(failed_text.split("Found ")[1].split(" tasks")[0])
            except Exception:
                pass
        
        # Calculate metrics
        total_tasks = completed_count + failed_count
        completion_rate = (completed_count / total_tasks) if total_tasks > 0 else 0
        error_rate = (failed_count / total_tasks) if total_tasks > 0 else 0
        
        performance_metrics = {
            "period": analysis_period,
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "completion_rate": completion_rate,
            "error_rate": error_rate,
            "avg_execution_time": "unknown"  # Would need more detailed task data
        }
        
        # Add requested metrics
        filtered_metrics = {}
        for metric in metrics:
            if metric in performance_metrics:
                filtered_metrics[metric] = performance_metrics[metric]
        
        return {
            "analysis_period": analysis_period,
            "requested_metrics": metrics,
            "performance_data": filtered_metrics,
            "summary": f"Analyzed {total_tasks} tasks with {completion_rate:.2%} completion rate"
        }
    
    async def _handle_coordinate_dependencies(self, task: Task) -> Dict[str, Any]:
        """Coordinate task dependencies and resolve conflicts."""
        dependency_strategy = task.parameters.get("strategy", "check_and_resolve")
        auto_resolve = task.parameters.get("auto_resolve", True)
        
        self.logger.info("Coordinating task dependencies")
        
        # Get all pending tasks to check dependencies
        pending_result = await self.call_tool("list_tasks", {
            "status": "pending",
            "limit": 1000
        })
        
        # For this example, we'll return a summary of dependency coordination
        # In a real implementation, this would involve complex dependency resolution
        
        return {
            "strategy": dependency_strategy,
            "auto_resolve": auto_resolve,
            "dependency_analysis": {
                "checked_tasks": "pending_tasks",
                "conflicts_found": 0,
                "resolutions_applied": 0
            },
            "status": "completed"
        }
    
    async def _handle_generate_reports(self, task: Task) -> Dict[str, Any]:
        """Generate task management reports."""
        report_type = task.parameters.get("type", "summary")
        period = task.parameters.get("period", "last_24_hours")
        include_details = task.parameters.get("include_details", False)
        
        self.logger.info(f"Generating {report_type} report for {period}")
        
        # Get data for different statuses
        status_counts = {}
        for status in ["pending", "running", "completed", "failed", "cancelled"]:
            result = await self.call_tool("list_tasks", {
                "status": status,
                "limit": 1000
            })
            
            result_text = result.content[0].text
            if "Found" in result_text:
                try:
                    count = int(result_text.split("Found ")[1].split(" tasks")[0])
                    status_counts[status] = count
                except Exception:
                    status_counts[status] = 0
            else:
                status_counts[status] = 0
        
        # Get agent workload summary
        workload_result = await self.call_tool("get_agent_workload", {})
        workload_text = workload_result.content[0].text
        
        agent_summary = {}
        try:
            import json
            json_start = workload_text.find('[')
            if json_start != -1:
                agents_data = json.loads(workload_text[json_start:])
                agent_summary = {
                    "total_agents": len(agents_data),
                    "active_agents": len([a for a in agents_data if a.get("status") == "online"])
                }
        except Exception:
            agent_summary = {"total_agents": 0, "active_agents": 0}
        
        report_data = {
            "report_type": report_type,
            "period": period,
            "generated_at": task.created_at.isoformat() if hasattr(task, 'created_at') else None,
            "task_summary": status_counts,
            "agent_summary": agent_summary,
            "total_tasks": sum(status_counts.values())
        }
        
        if include_details:
            report_data["details"] = {
                "completion_rate": status_counts["completed"] / sum(status_counts.values()) if sum(status_counts.values()) > 0 else 0,
                "error_rate": status_counts["failed"] / sum(status_counts.values()) if sum(status_counts.values()) > 0 else 0,
                "active_workflows": len(self._active_workflows)
            }
        
        return report_data
    
    def _get_tools_used_in_task(self, task: Task) -> List[str]:
        """Return tools used for specific task types."""
        tool_mapping = {
            "create_task": ["create_task"],
            "manage_workflow": ["create_task", "list_tasks"],
            "schedule_tasks": ["list_tasks"],
            "monitor_progress": ["list_tasks", "get_agent_workload"],
            "balance_workload": ["get_agent_workload", "list_tasks"],
            "analyze_performance": ["list_tasks"],
            "coordinate_dependencies": ["list_tasks"],
            "generate_reports": ["list_tasks", "get_agent_workload"]
        }
        return tool_mapping.get(task.type, [])