#!/usr/bin/env python3
"""
Coordinator Agent Implementation

Master orchestration agent that coordinates multi-agent workflows and manages
the overall system. This agent uses both task management and communication
servers to orchestrate complex multi-agent operations.
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


class CoordinatorAgent(BaseAgent):
    """
    Master coordination agent for multi-agent orchestration.
    
    Capabilities:
    - Multi-agent workflow orchestration
    - Agent coordination and communication
    - Resource allocation and conflict resolution
    - System-wide monitoring and control
    - Complex workflow management
    - Error recovery and fault tolerance
    """
    
    def __init__(self):
        registration = AgentRegistration(
            name="coordinator_agent",
            capabilities=[
                "agent_coordination",
                "workflow_orchestration",
                "resource_allocation",
                "conflict_resolution",
                "system_monitoring",
                "error_recovery",
                "multi_agent_communication"
            ],
            supported_task_types=[
                "orchestrate_workflow",
                "coordinate_agents",
                "allocate_resources",
                "resolve_conflicts",
                "monitor_system",
                "handle_emergencies",
                "manage_communications",
                "execute_complex_workflow"
            ],
            priority=10,  # Highest priority
            max_concurrent_tasks=1,  # Focus on one major coordination at a time
            config={
                "coordination_timeout": 60,
                "max_agents_per_task": 5,
                "conflict_resolution_strategy": "priority_based",
                "communication_channels": ["main", "alerts", "coordination"]
            }
        )
        
        super().__init__("coordinator_agent", registration)
        
        # Coordination state
        self._active_orchestrations: Dict[str, Dict[str, Any]] = {}
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
        self._resource_allocations: Dict[str, Dict[str, Any]] = {}
        self._communication_channels: List[str] = []
    
    async def setup(self) -> bool:
        """Setup the coordinator agent by connecting to all required servers."""
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
            
            # Connect to communication server
            comm_server_config = MCPServerConfig(
                name="communication_server",
                transport_type="stdio",
                command="python",
                args=["src/servers/communication_server.py"],
                tools=[
                    "send_message", "broadcast_message", "get_messages", "create_channel",
                    "join_channel", "leave_channel", "list_channels", "mark_message_read"
                ],
                resources=["message_queue", "channels", "communication_stats"]
            )
            
            success = await self.connect_to_server(comm_server_config)
            if not success:
                self.logger.error("Failed to connect to communication server")
                return False
            
            # Register self with systems
            await self.call_tool("register_agent", {
                "name": self.name,
                "capabilities": self.registration.capabilities,
                "max_concurrent_tasks": self.registration.max_concurrent_tasks
            })
            
            # Create coordination channels
            for channel_name in self.registration.config["communication_channels"]:
                try:
                    await self.call_tool("create_channel", {
                        "name": channel_name,
                        "description": f"Coordination channel: {channel_name}",
                        "created_by": self.name
                    })
                    self._communication_channels.append(channel_name)
                except Exception:
                    # Channel might already exist
                    self._communication_channels.append(channel_name)
            
            await self.start()
            self.logger.info("Coordinator Agent setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Coordinator Agent setup failed: {e}")
            return False
    
    def _can_handle_task_specific(self, task: Task) -> bool:
        """Check if this agent can handle the specific task."""
        return task.type in self.registration.supported_task_types
    
    async def _execute_task_specific(self, task: Task, context: Optional[Context]) -> Dict[str, Any]:
        """Execute coordination-specific tasks."""
        
        if task.type == "orchestrate_workflow":
            return await self._handle_orchestrate_workflow(task)
        elif task.type == "coordinate_agents":
            return await self._handle_coordinate_agents(task)
        elif task.type == "allocate_resources":
            return await self._handle_allocate_resources(task)
        elif task.type == "resolve_conflicts":
            return await self._handle_resolve_conflicts(task)
        elif task.type == "monitor_system":
            return await self._handle_monitor_system(task)
        elif task.type == "handle_emergencies":
            return await self._handle_emergencies(task)
        elif task.type == "manage_communications":
            return await self._handle_manage_communications(task)
        elif task.type == "execute_complex_workflow":
            return await self._handle_execute_complex_workflow(task)
        else:
            raise ValueError(f"Unsupported task type: {task.type}")
    
    async def _handle_orchestrate_workflow(self, task: Task) -> Dict[str, Any]:
        """Orchestrate a complex multi-agent workflow."""
        workflow_name = task.parameters.get("name")
        workflow_steps = task.parameters.get("steps", [])
        coordination_strategy = task.parameters.get("strategy", "sequential")
        timeout = task.parameters.get("timeout", 300)
        
        if not workflow_name or not workflow_steps:
            raise ValueError("Workflow name and steps are required")
        
        self.logger.info(f"Orchestrating workflow: {workflow_name} with {len(workflow_steps)} steps")
        
        # Create orchestration record
        orchestration_id = f"orch_{workflow_name}_{task.id}"
        self._active_orchestrations[orchestration_id] = {
            "workflow_name": workflow_name,
            "steps": workflow_steps,
            "strategy": coordination_strategy,
            "status": "initializing",
            "created_tasks": [],
            "completed_steps": [],
            "failed_steps": [],
            "participating_agents": set()
        }
        
        # Announce workflow start
        await self.call_tool("broadcast_message", {
            "from_agent": self.name,
            "channel": "coordination",
            "message_type": "announcement",
            "subject": f"Workflow Started: {workflow_name}",
            "content": f"Coordinator is starting workflow '{workflow_name}' with {len(workflow_steps)} steps using {coordination_strategy} strategy."
        })
        
        created_tasks = []
        step_results = []
        
        if coordination_strategy == "sequential":
            # Execute steps sequentially with coordination
            prev_task_id = None
            
            for i, step in enumerate(workflow_steps):
                step_name = step.get("name", f"step_{i+1}")
                step_agent = step.get("agent")
                step_type = step.get("type")
                step_params = step.get("parameters", {})
                
                self.logger.info(f"Creating step {i+1}/{len(workflow_steps)}: {step_name}")
                
                # Create task with dependencies
                dependencies = [prev_task_id] if prev_task_id else []
                
                # Notify agents about upcoming work
                if step_agent:
                    await self.call_tool("send_message", {
                        "from_agent": self.name,
                        "to_agent": step_agent,
                        "message_type": "notification",
                        "subject": f"Upcoming Task: {step_name}",
                        "content": f"You will be assigned task '{step_name}' of type '{step_type}' shortly."
                    })
                
                # Create the task
                create_result = await self.call_tool("create_task", {
                    "type": step_type,
                    "description": f"Workflow step: {step_name}",
                    "parameters": step_params,
                    "priority": step.get("priority", 7),
                    "dependencies": dependencies,
                    "assigned_agent": step_agent
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
                        prev_task_id = task_id
                        
                        if step_agent:
                            self._active_orchestrations[orchestration_id]["participating_agents"].add(step_agent)
                        
                        step_results.append({
                            "step": step_name,
                            "task_id": task_id,
                            "agent": step_agent,
                            "status": "created"
                        })
                except Exception as e:
                    self.logger.error(f"Failed to create task for step {step_name}: {e}")
                    step_results.append({
                        "step": step_name,
                        "error": str(e),
                        "status": "failed"
                    })
        
        elif coordination_strategy == "parallel":
            # Execute steps in parallel with coordination
            for i, step in enumerate(workflow_steps):
                step_name = step.get("name", f"step_{i+1}")
                step_agent = step.get("agent")
                step_type = step.get("type")
                step_params = step.get("parameters", {})
                
                # Notify agent
                if step_agent:
                    await self.call_tool("send_message", {
                        "from_agent": self.name,
                        "to_agent": step_agent,
                        "message_type": "request",
                        "subject": f"Parallel Task: {step_name}",
                        "content": f"Starting parallel execution of task '{step_name}'"
                    })
                
                # Create task
                create_result = await self.call_tool("create_task", {
                    "type": step_type,
                    "description": f"Parallel workflow step: {step_name}",
                    "parameters": step_params,
                    "priority": step.get("priority", 6),
                    "dependencies": [],
                    "assigned_agent": step_agent
                })
                
                # Process result
                result_text = create_result.content[0].text
                try:
                    import json
                    json_start = result_text.find('{')
                    if json_start != -1:
                        task_info = json.loads(result_text[json_start:])
                        task_id = task_info.get("task_id")
                        created_tasks.append(task_id)
                        
                        if step_agent:
                            self._active_orchestrations[orchestration_id]["participating_agents"].add(step_agent)
                        
                        step_results.append({
                            "step": step_name,
                            "task_id": task_id,
                            "agent": step_agent,
                            "status": "created"
                        })
                except Exception:
                    step_results.append({
                        "step": step_name,
                        "status": "failed"
                    })
        
        # Update orchestration state
        self._active_orchestrations[orchestration_id]["created_tasks"] = created_tasks
        self._active_orchestrations[orchestration_id]["status"] = "executing"
        
        # Send summary to coordination channel
        await self.call_tool("broadcast_message", {
            "from_agent": self.name,
            "channel": "coordination",
            "message_type": "info",
            "subject": f"Workflow Status: {workflow_name}",
            "content": f"Created {len(created_tasks)} tasks for workflow '{workflow_name}'. Participating agents: {list(self._active_orchestrations[orchestration_id]['participating_agents'])}"
        })
        
        return {
            "orchestration_id": orchestration_id,
            "workflow_name": workflow_name,
            "coordination_strategy": coordination_strategy,
            "total_steps": len(workflow_steps),
            "created_tasks": created_tasks,
            "step_results": step_results,
            "participating_agents": list(self._active_orchestrations[orchestration_id]["participating_agents"]),
            "status": "executing"
        }
    
    async def _handle_coordinate_agents(self, task: Task) -> Dict[str, Any]:
        """Coordinate interaction between multiple agents."""
        coordination_type = task.parameters.get("type", "workload_balance")
        target_agents = task.parameters.get("agents", [])
        coordination_goal = task.parameters.get("goal")
        
        self.logger.info(f"Coordinating agents: {target_agents} for {coordination_type}")
        
        # Get current agent workloads
        workload_result = await self.call_tool("get_agent_workload", {})
        workload_text = workload_result.content[0].text
        
        coordination_actions = []
        
        if coordination_type == "workload_balance":
            # Balance workload between agents
            try:
                import json
                json_start = workload_text.find('[')
                if json_start != -1:
                    agents_data = json.loads(workload_text[json_start:])
                    
                    # Find overloaded and underloaded agents
                    overloaded = []
                    underloaded = []
                    
                    for agent in agents_data:
                        if agent.get("name") in target_agents:
                            current_tasks = agent.get("current_tasks", 0)
                            max_tasks = agent.get("max_concurrent_tasks", 1)
                            
                            if current_tasks >= max_tasks:
                                overloaded.append(agent.get("name"))
                            elif current_tasks < max_tasks / 2:
                                underloaded.append(agent.get("name"))
                    
                    # Send coordination messages
                    for agent in overloaded:
                        await self.call_tool("send_message", {
                            "from_agent": self.name,
                            "to_agent": agent,
                            "message_type": "alert",
                            "subject": "Workload Alert",
                            "content": "Your current workload is at capacity. Consider delegating or requesting assistance."
                        })
                        coordination_actions.append(f"Notified {agent} of high workload")
                    
                    for agent in underloaded:
                        await self.call_tool("send_message", {
                            "from_agent": self.name,
                            "to_agent": agent,
                            "message_type": "request",
                            "subject": "Available for Work",
                            "content": "You have available capacity. Ready to take on additional tasks."
                        })
                        coordination_actions.append(f"Notified {agent} of available capacity")
            
            except Exception as e:
                coordination_actions.append(f"Error analyzing workload: {e}")
        
        elif coordination_type == "emergency_response":
            # Coordinate emergency response
            for agent in target_agents:
                await self.call_tool("send_message", {
                    "from_agent": self.name,
                    "to_agent": agent,
                    "message_type": "alert",
                    "subject": "Emergency Coordination",
                    "content": f"Emergency coordination required. Goal: {coordination_goal}"
                })
                coordination_actions.append(f"Sent emergency alert to {agent}")
        
        elif coordination_type == "resource_sharing":
            # Coordinate resource sharing
            await self.call_tool("broadcast_message", {
                "from_agent": self.name,
                "target_agents": target_agents,
                "message_type": "coordination",
                "subject": "Resource Coordination",
                "content": f"Coordinating resource sharing for: {coordination_goal}"
            })
            coordination_actions.append("Initiated resource sharing coordination")
        
        return {
            "coordination_type": coordination_type,
            "target_agents": target_agents,
            "coordination_goal": coordination_goal,
            "actions_taken": coordination_actions,
            "status": "completed"
        }
    
    async def _handle_allocate_resources(self, task: Task) -> Dict[str, Any]:
        """Allocate resources to agents and tasks."""
        resource_type = task.parameters.get("resource_type", "task_capacity")
        allocation_strategy = task.parameters.get("strategy", "fair_share")
        requestors = task.parameters.get("requestors", [])
        
        self.logger.info(f"Allocating {resource_type} using {allocation_strategy} strategy")
        
        allocation_plan = {}
        
        if resource_type == "task_capacity":
            # Allocate task execution capacity
            total_capacity = 100  # Example total capacity
            
            if allocation_strategy == "fair_share":
                capacity_per_agent = total_capacity // len(requestors) if requestors else 0
                for agent in requestors:
                    allocation_plan[agent] = capacity_per_agent
            
            elif allocation_strategy == "priority_based":
                # Get agent priorities and allocate accordingly
                high_priority_agents = requestors[:len(requestors)//2]
                low_priority_agents = requestors[len(requestors)//2:]
                
                for agent in high_priority_agents:
                    allocation_plan[agent] = 60  # Higher allocation
                for agent in low_priority_agents:
                    allocation_plan[agent] = 40  # Lower allocation
        
        # Store allocation
        allocation_id = f"alloc_{resource_type}_{task.id}"
        self._resource_allocations[allocation_id] = {
            "resource_type": resource_type,
            "strategy": allocation_strategy,
            "plan": allocation_plan,
            "timestamp": task.created_at.isoformat() if hasattr(task, 'created_at') else None
        }
        
        # Notify agents of their allocations
        for agent, allocation in allocation_plan.items():
            await self.call_tool("send_message", {
                "from_agent": self.name,
                "to_agent": agent,
                "message_type": "notification",
                "subject": f"Resource Allocation: {resource_type}",
                "content": f"You have been allocated {allocation} units of {resource_type}"
            })
        
        return {
            "allocation_id": allocation_id,
            "resource_type": resource_type,
            "allocation_strategy": allocation_strategy,
            "allocation_plan": allocation_plan,
            "total_requestors": len(requestors),
            "status": "completed"
        }
    
    async def _handle_resolve_conflicts(self, task: Task) -> Dict[str, Any]:
        """Resolve conflicts between agents or tasks."""
        conflict_type = task.parameters.get("type", "resource_conflict")
        involved_parties = task.parameters.get("parties", [])
        resolution_strategy = task.parameters.get("strategy", "mediation")
        
        self.logger.info(f"Resolving {conflict_type} involving {involved_parties}")
        
        resolution_actions = []
        
        if conflict_type == "resource_conflict":
            # Resolve resource conflicts
            if resolution_strategy == "mediation":
                # Send mediation message to all parties
                await self.call_tool("broadcast_message", {
                    "from_agent": self.name,
                    "target_agents": involved_parties,
                    "message_type": "coordination",
                    "subject": "Conflict Resolution - Mediation",
                    "content": "Coordinator is mediating resource conflict. Please pause conflicting operations and await resolution."
                })
                resolution_actions.append("Initiated mediation process")
                
                # Implement simple resolution: alternate access
                for i, party in enumerate(involved_parties):
                    priority = len(involved_parties) - i  # First party gets highest priority
                    await self.call_tool("send_message", {
                        "from_agent": self.name,
                        "to_agent": party,
                        "message_type": "notification",
                        "subject": "Conflict Resolution",
                        "content": f"Your priority for resource access is {priority}. Please coordinate accordingly."
                    })
                    resolution_actions.append(f"Assigned priority {priority} to {party}")
        
        elif conflict_type == "task_dependency":
            # Resolve task dependency conflicts
            await self.call_tool("broadcast_message", {
                "from_agent": self.name,
                "target_agents": involved_parties,
                "message_type": "alert",
                "subject": "Dependency Conflict Resolution",
                "content": "Task dependency conflict detected. Coordinator is resolving execution order."
            })
            resolution_actions.append("Notified parties of dependency resolution")
        
        return {
            "conflict_type": conflict_type,
            "involved_parties": involved_parties,
            "resolution_strategy": resolution_strategy,
            "resolution_actions": resolution_actions,
            "status": "resolved"
        }
    
    async def _handle_monitor_system(self, task: Task) -> Dict[str, Any]:
        """Monitor overall system health and performance."""
        monitoring_scope = task.parameters.get("scope", "full_system")
        monitoring_duration = task.parameters.get("duration", 60)
        alert_thresholds = task.parameters.get("thresholds", {})
        
        self.logger.info(f"Monitoring system with scope: {monitoring_scope}")
        
        # Get system status
        system_status = {}
        
        # Monitor task queue
        for status in ["pending", "running", "completed", "failed"]:
            result = await self.call_tool("list_tasks", {
                "status": status,
                "limit": 1000
            })
            
            result_text = result.content[0].text
            if "Found" in result_text:
                try:
                    count = int(result_text.split("Found ")[1].split(" tasks")[0])
                    system_status[f"tasks_{status}"] = count
                except Exception:
                    system_status[f"tasks_{status}"] = 0
        
        # Monitor agent health
        workload_result = await self.call_tool("get_agent_workload", {})
        agent_count = 0
        try:
            workload_text = workload_result.content[0].text
            import json
            json_start = workload_text.find('[')
            if json_start != -1:
                agents_data = json.loads(workload_text[json_start:])
                agent_count = len(agents_data)
                system_status["total_agents"] = agent_count
                system_status["active_agents"] = len([a for a in agents_data if a.get("status") == "online"])
        except Exception:
            system_status["total_agents"] = 0
            system_status["active_agents"] = 0
        
        # Check alert thresholds
        alerts = []
        if alert_thresholds:
            for metric, threshold in alert_thresholds.items():
                if metric in system_status and system_status[metric] > threshold:
                    alert_msg = f"Alert: {metric} ({system_status[metric]}) exceeds threshold ({threshold})"
                    alerts.append(alert_msg)
                    
                    # Send alert
                    await self.call_tool("broadcast_message", {
                        "from_agent": self.name,
                        "channel": "alerts",
                        "message_type": "alert",
                        "subject": f"System Alert: {metric}",
                        "content": alert_msg
                    })
        
        return {
            "monitoring_scope": monitoring_scope,
            "system_status": system_status,
            "alerts": alerts,
            "monitoring_timestamp": task.created_at.isoformat() if hasattr(task, 'created_at') else None,
            "health_status": "healthy" if not alerts else "alerts_detected"
        }
    
    async def _handle_emergencies(self, task: Task) -> Dict[str, Any]:
        """Handle emergency situations requiring immediate coordination."""
        emergency_type = task.parameters.get("type")
        severity = task.parameters.get("severity", "medium")
        affected_systems = task.parameters.get("affected_systems", [])
        
        self.logger.error(f"Handling emergency: {emergency_type} (severity: {severity})")
        
        emergency_actions = []
        
        # Broadcast emergency alert
        await self.call_tool("broadcast_message", {
            "from_agent": self.name,
            "channel": "alerts",
            "message_type": "alert",
            "subject": f"EMERGENCY: {emergency_type}",
            "content": f"Emergency situation detected. Type: {emergency_type}, Severity: {severity}. All agents please standby for instructions.",
            "priority": 10
        })
        emergency_actions.append("Broadcast emergency alert")
        
        if severity == "critical":
            # For critical emergencies, halt non-essential operations
            await self.call_tool("broadcast_message", {
                "from_agent": self.name,
                "channel": "coordination",
                "message_type": "alert",
                "subject": "CRITICAL EMERGENCY - HALT OPERATIONS",
                "content": "Critical emergency detected. Please halt all non-essential operations immediately.",
                "priority": 10
            })
            emergency_actions.append("Ordered halt of non-essential operations")
        
        # Activate emergency protocols
        emergency_actions.append("Emergency protocols activated")
        
        return {
            "emergency_type": emergency_type,
            "severity": severity,
            "affected_systems": affected_systems,
            "emergency_actions": emergency_actions,
            "status": "emergency_protocols_active",
            "timestamp": task.created_at.isoformat() if hasattr(task, 'created_at') else None
        }
    
    async def _handle_manage_communications(self, task: Task) -> Dict[str, Any]:
        """Manage system-wide communications."""
        action = task.parameters.get("action", "status_check")
        channel = task.parameters.get("channel")
        message_filters = task.parameters.get("filters", {})
        
        self.logger.info(f"Managing communications: {action}")
        
        communication_results = {}
        
        if action == "status_check":
            # Check communication system status
            channels_result = await self.call_tool("list_channels", {})
            communication_results["channels"] = channels_result.content[0].text
            
            # Check messages
            messages_result = await self.call_tool("get_messages", {
                "agent_name": self.name,
                "status": "all",
                "limit": 10
            })
            communication_results["recent_messages"] = "Retrieved recent messages"
        
        elif action == "broadcast_status":
            # Broadcast system status
            await self.call_tool("broadcast_message", {
                "from_agent": self.name,
                "channel": "main",
                "message_type": "info",
                "subject": "System Status Update",
                "content": f"Coordinator reporting: System operational. Active orchestrations: {len(self._active_orchestrations)}"
            })
            communication_results["broadcast_sent"] = True
        
        elif action == "clean_channels":
            # Clean up communication channels
            communication_results["cleanup_actions"] = "Channel cleanup initiated"
        
        return {
            "action": action,
            "channel": channel,
            "communication_results": communication_results,
            "active_channels": len(self._communication_channels),
            "status": "completed"
        }
    
    async def _handle_execute_complex_workflow(self, task: Task) -> Dict[str, Any]:
        """Execute a complex workflow involving multiple agents and coordination points."""
        workflow_definition = task.parameters.get("workflow")
        coordination_points = task.parameters.get("coordination_points", [])
        failure_handling = task.parameters.get("failure_handling", "retry")
        
        if not workflow_definition:
            raise ValueError("Workflow definition is required")
        
        workflow_name = workflow_definition.get("name")
        phases = workflow_definition.get("phases", [])
        
        self.logger.info(f"Executing complex workflow: {workflow_name} with {len(phases)} phases")
        
        # Create workflow execution record
        execution_id = f"complex_{workflow_name}_{task.id}"
        execution_state = {
            "workflow_name": workflow_name,
            "phases": phases,
            "coordination_points": coordination_points,
            "status": "initializing",
            "current_phase": 0,
            "completed_phases": [],
            "failed_phases": [],
            "phase_results": {}
        }
        
        # Execute each phase
        for i, phase in enumerate(phases):
            phase_name = phase.get("name", f"phase_{i+1}")
            phase_type = phase.get("type", "sequential")
            phase_steps = phase.get("steps", [])
            
            self.logger.info(f"Executing phase {i+1}/{len(phases)}: {phase_name}")
            
            # Check for coordination point
            if i in coordination_points:
                await self.call_tool("broadcast_message", {
                    "from_agent": self.name,
                    "channel": "coordination",
                    "message_type": "coordination",
                    "subject": f"Coordination Point: {phase_name}",
                    "content": f"Reached coordination point before phase '{phase_name}'. All agents synchronize."
                })
            
            # Execute phase using orchestrate_workflow logic
            phase_result = await self._handle_orchestrate_workflow(Task(
                id=f"{task.id}_phase_{i}",
                type="orchestrate_workflow",
                description=f"Phase {phase_name} of complex workflow",
                parameters={
                    "name": phase_name,
                    "steps": phase_steps,
                    "strategy": phase_type
                }
            ))
            
            execution_state["phase_results"][phase_name] = phase_result
            
            if phase_result.get("status") == "executing":
                execution_state["completed_phases"].append(phase_name)
            else:
                execution_state["failed_phases"].append(phase_name)
                if failure_handling == "abort":
                    break
        
        execution_state["status"] = "completed" if not execution_state["failed_phases"] else "partial_failure"
        
        # Final coordination message
        await self.call_tool("broadcast_message", {
            "from_agent": self.name,
            "channel": "coordination",
            "message_type": "announcement",
            "subject": f"Complex Workflow Complete: {workflow_name}",
            "content": f"Workflow '{workflow_name}' execution finished. Status: {execution_state['status']}"
        })
        
        return {
            "execution_id": execution_id,
            "workflow_name": workflow_name,
            "total_phases": len(phases),
            "completed_phases": len(execution_state["completed_phases"]),
            "failed_phases": len(execution_state["failed_phases"]),
            "execution_status": execution_state["status"],
            "phase_results": execution_state["phase_results"]
        }
    
    def _get_tools_used_in_task(self, task: Task) -> List[str]:
        """Return tools used for specific task types."""
        tool_mapping = {
            "orchestrate_workflow": ["create_task", "broadcast_message", "send_message"],
            "coordinate_agents": ["get_agent_workload", "send_message", "broadcast_message"],
            "allocate_resources": ["send_message"],
            "resolve_conflicts": ["broadcast_message", "send_message"],
            "monitor_system": ["list_tasks", "get_agent_workload", "broadcast_message"],
            "handle_emergencies": ["broadcast_message"],
            "manage_communications": ["list_channels", "get_messages", "broadcast_message"],
            "execute_complex_workflow": ["create_task", "broadcast_message", "send_message"]
        }
        return tool_mapping.get(task.type, [])