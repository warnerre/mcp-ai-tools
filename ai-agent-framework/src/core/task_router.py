#!/usr/bin/env python3
"""
Task Router - Core Framework Component

The task router analyzes incoming tasks and intelligently routes them to the most
suitable agents based on capabilities, current workload, and task requirements.
This demonstrates intelligent task distribution patterns in multi-agent systems.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime

from .types import Task, AgentInfo, AgentStatus, TaskStatus


class TaskRouter:
    """
    Intelligent task routing system for multi-agent coordination.
    
    The router provides:
    - Capability-based agent matching
    - Load balancing and workload distribution
    - Priority-based task scheduling
    - Dependency analysis and resolution
    - Performance optimization routing
    """
    
    def __init__(self, name: str = "task_router"):
        self.name = name
        self.logger = self._setup_logging()
        
        # Routing configuration
        self.config = {
            "max_agent_workload_ratio": 0.8,  # Don't overload agents
            "priority_weight": 0.4,           # How much priority matters
            "workload_weight": 0.3,           # How much current load matters
            "capability_weight": 0.3,         # How much capability match matters
            "enable_load_balancing": True,
            "enable_priority_boosting": True,
            "dependency_timeout": 300         # Max wait for dependencies (seconds)
        }
        
        # Routing statistics
        self.stats = {
            "total_routed": 0,
            "successful_matches": 0,
            "failed_matches": 0,
            "load_balanced_routes": 0,
            "priority_boosted_routes": 0
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup router logging."""
        logger = logging.getLogger(f"task_router.{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - TaskRouter - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def find_best_agent(self, task: Task, available_agents: Dict[str, AgentInfo]) -> Optional[str]:
        """
        Find the best agent for a given task.
        
        Args:
            task: Task to route
            available_agents: Dictionary of available agents
            
        Returns:
            Name of best agent, or None if no suitable agent found
        """
        self.stats["total_routed"] += 1
        
        # If task has assigned agent, check if it's available and capable
        if task.assigned_agent:
            if self._can_agent_handle_task(task.assigned_agent, task, available_agents):
                self.stats["successful_matches"] += 1
                self.logger.info(f"Task {task.id} routed to assigned agent: {task.assigned_agent}")
                return task.assigned_agent
            else:
                self.logger.warning(f"Assigned agent {task.assigned_agent} cannot handle task {task.id}")
        
        # Find all capable agents
        capable_agents = self._find_capable_agents(task, available_agents)
        if not capable_agents:
            self.stats["failed_matches"] += 1
            self.logger.warning(f"No capable agents found for task {task.id} (type: {task.type})")
            return None
        
        # Score and rank agents
        scored_agents = self._score_agents(task, capable_agents, available_agents)
        if not scored_agents:
            self.stats["failed_matches"] += 1
            return None
        
        # Select best agent
        best_agent = scored_agents[0][0]  # First element is agent name
        self.stats["successful_matches"] += 1
        
        self.logger.info(f"Task {task.id} routed to best agent: {best_agent} (score: {scored_agents[0][1]:.2f})")
        return best_agent
    
    def _can_agent_handle_task(self, agent_name: str, task: Task, 
                              available_agents: Dict[str, AgentInfo]) -> bool:
        """
        Check if a specific agent can handle a task.
        
        Args:
            agent_name: Name of the agent
            task: Task to check
            available_agents: Available agents
            
        Returns:
            True if agent can handle the task
        """
        agent_info = available_agents.get(agent_name)
        if not agent_info:
            return False
        
        # Check agent health
        if agent_info.status != AgentStatus.HEALTHY:
            return False
        
        # Check task type support
        if task.type not in agent_info.registration.supported_task_types:
            return False
        
        # Check workload capacity
        current_load = len(agent_info.current_tasks)
        max_load = agent_info.registration.max_concurrent_tasks
        
        if current_load >= max_load:
            return False
        
        # Check workload ratio
        load_ratio = current_load / max_load if max_load > 0 else 1.0
        if load_ratio >= self.config["max_agent_workload_ratio"]:
            return False
        
        return True
    
    def _find_capable_agents(self, task: Task, 
                           available_agents: Dict[str, AgentInfo]) -> List[str]:
        """
        Find all agents capable of handling a task.
        
        Args:
            task: Task to find agents for
            available_agents: Available agents
            
        Returns:
            List of capable agent names
        """
        capable_agents = []
        
        for agent_name, agent_info in available_agents.items():
            if self._can_agent_handle_task(agent_name, task, available_agents):
                capable_agents.append(agent_name)
        
        return capable_agents
    
    def _score_agents(self, task: Task, capable_agents: List[str], 
                     available_agents: Dict[str, AgentInfo]) -> List[Tuple[str, float]]:
        """
        Score and rank capable agents for task assignment.
        
        Args:
            task: Task to score agents for
            capable_agents: List of capable agent names
            available_agents: Available agents
            
        Returns:
            List of (agent_name, score) tuples, sorted by score (highest first)
        """
        scored_agents = []
        
        for agent_name in capable_agents:
            agent_info = available_agents[agent_name]
            score = self._calculate_agent_score(task, agent_name, agent_info)
            scored_agents.append((agent_name, score))
        
        # Sort by score (highest first)
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return scored_agents
    
    def _calculate_agent_score(self, task: Task, agent_name: str, 
                             agent_info: AgentInfo) -> float:
        """
        Calculate a score for how well an agent matches a task.
        
        Args:
            task: Task to score
            agent_name: Name of the agent
            agent_info: Agent information
            
        Returns:
            Score (0.0 to 1.0, higher is better)
        """
        scores = {}
        
        # 1. Capability match score
        capability_score = self._calculate_capability_score(task, agent_info)
        scores["capability"] = capability_score
        
        # 2. Workload score (lower load = higher score)
        workload_score = self._calculate_workload_score(agent_info)
        scores["workload"] = workload_score
        
        # 3. Priority score (agent priority vs task priority)
        priority_score = self._calculate_priority_score(task, agent_info)
        scores["priority"] = priority_score
        
        # 4. Performance score (based on past performance)
        performance_score = self._calculate_performance_score(agent_info)
        scores["performance"] = performance_score
        
        # Weighted combination
        weights = {
            "capability": self.config["capability_weight"],
            "workload": self.config["workload_weight"], 
            "priority": self.config["priority_weight"],
            "performance": 0.1  # Small weight for performance
        }
        
        total_score = sum(scores[key] * weights[key] for key in scores)
        
        # Normalize to 0-1 range
        max_possible = sum(weights.values())
        normalized_score = total_score / max_possible if max_possible > 0 else 0.0
        
        self.logger.debug(f"Agent {agent_name} score for task {task.id}: {normalized_score:.3f} "
                         f"(cap:{scores['capability']:.2f}, load:{scores['workload']:.2f}, "
                         f"pri:{scores['priority']:.2f}, perf:{scores['performance']:.2f})")
        
        return normalized_score
    
    def _calculate_capability_score(self, task: Task, agent_info: AgentInfo) -> float:
        """Calculate how well agent capabilities match task requirements."""
        registration = agent_info.registration
        
        # Basic task type support (required)
        if task.type not in registration.supported_task_types:
            return 0.0
        
        # Check for exact capability match
        task_capabilities = self._extract_task_capabilities(task)
        agent_capabilities = set(registration.capabilities)
        
        if not task_capabilities:
            return 0.8  # Default good score if no specific capabilities needed
        
        # Calculate overlap
        matched_capabilities = task_capabilities.intersection(agent_capabilities)
        if not task_capabilities:
            return 0.8
        
        overlap_ratio = len(matched_capabilities) / len(task_capabilities)
        
        # Bonus for exact matches
        if overlap_ratio == 1.0:
            return 1.0
        elif overlap_ratio >= 0.5:
            return 0.6 + (overlap_ratio * 0.4)  # Scale 0.6-1.0
        else:
            return overlap_ratio * 0.6  # Scale 0.0-0.6
    
    def _extract_task_capabilities(self, task: Task) -> Set[str]:
        """Extract required capabilities from task type and parameters."""
        # Map task types to required capabilities
        capability_mapping = {
            "read_file": {"file_operations"},
            "write_file": {"file_operations"},
            "list_directory": {"file_operations", "directory_operations"},
            "analyze_directory": {"file_operations", "file_analysis"},
            "search_files": {"file_operations", "file_search"},
            "backup_files": {"file_operations", "batch_operations"},
            "create_task": {"task_management"},
            "manage_workflow": {"workflow_coordination", "task_management"},
            "schedule_tasks": {"task_scheduling"},
            "monitor_progress": {"task_monitoring"},
            "orchestrate_workflow": {"workflow_orchestration", "agent_coordination"},
            "coordinate_agents": {"agent_coordination", "multi_agent_communication"},
            "allocate_resources": {"resource_allocation"},
            "resolve_conflicts": {"conflict_resolution"},
            "handle_emergencies": {"error_recovery", "system_monitoring"}
        }
        
        return capability_mapping.get(task.type, set())
    
    def _calculate_workload_score(self, agent_info: AgentInfo) -> float:
        """Calculate score based on current agent workload (lower load = higher score)."""
        current_load = len(agent_info.current_tasks)
        max_load = agent_info.registration.max_concurrent_tasks
        
        if max_load <= 0:
            return 0.0
        
        load_ratio = current_load / max_load
        
        # Invert the ratio (lower load = higher score)
        workload_score = 1.0 - load_ratio
        
        # Apply load balancing bonus if enabled
        if self.config["enable_load_balancing"] and load_ratio < 0.5:
            workload_score += 0.1  # Bonus for underutilized agents
            self.stats["load_balanced_routes"] += 1
        
        return min(workload_score, 1.0)
    
    def _calculate_priority_score(self, task: Task, agent_info: AgentInfo) -> float:
        """Calculate score based on task and agent priorities."""
        task_priority = task.priority if hasattr(task, 'priority') else 5
        agent_priority = agent_info.registration.priority
        
        # Normalize priorities to 0-1 scale (assuming 1-10 range)
        task_priority_norm = (task_priority - 1) / 9 if task_priority >= 1 else 0.5
        agent_priority_norm = (agent_priority - 1) / 9 if agent_priority >= 1 else 0.5
        
        # Higher priority agents should get higher priority tasks
        if task_priority >= 7 and agent_priority >= 7:  # Both high priority
            priority_score = 1.0
            if self.config["enable_priority_boosting"]:
                self.stats["priority_boosted_routes"] += 1
        elif task_priority <= 3 and agent_priority <= 3:  # Both low priority
            priority_score = 0.8
        else:
            # Calculate compatibility between task and agent priority
            priority_diff = abs(task_priority_norm - agent_priority_norm)
            priority_score = 1.0 - priority_diff
        
        return max(priority_score, 0.0)
    
    def _calculate_performance_score(self, agent_info: AgentInfo) -> float:
        """Calculate score based on agent's historical performance."""
        total_completed = agent_info.total_tasks_completed
        error_count = agent_info.error_count
        
        if total_completed == 0:
            return 0.5  # Neutral score for new agents
        
        # Calculate success rate
        success_rate = (total_completed - error_count) / total_completed
        success_rate = max(success_rate, 0.0)
        
        # Weight by experience (more completed tasks = higher confidence)
        experience_weight = min(total_completed / 100, 1.0)  # Cap at 100 tasks
        
        performance_score = (success_rate * 0.8) + (experience_weight * 0.2)
        return min(performance_score, 1.0)
    
    def analyze_routing_requirements(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Analyze a batch of tasks to understand routing requirements.
        
        Args:
            tasks: List of tasks to analyze
            
        Returns:
            Analysis report with routing recommendations
        """
        analysis = {
            "total_tasks": len(tasks),
            "task_types": {},
            "priority_distribution": {},
            "capability_requirements": set(),
            "estimated_agents_needed": 0,
            "potential_bottlenecks": []
        }
        
        # Analyze task types
        for task in tasks:
            task_type = task.type
            analysis["task_types"][task_type] = analysis["task_types"].get(task_type, 0) + 1
            
            # Collect required capabilities
            capabilities = self._extract_task_capabilities(task)
            analysis["capability_requirements"].update(capabilities)
            
            # Analyze priority distribution
            priority = getattr(task, 'priority', 5)
            analysis["priority_distribution"][priority] = analysis["priority_distribution"].get(priority, 0) + 1
        
        # Estimate agent requirements
        max_concurrent_per_type = {}
        for task_type, count in analysis["task_types"].items():
            # Assume average agent can handle 2 concurrent tasks of same type
            max_concurrent_per_type[task_type] = max(1, count // 2)
        
        analysis["estimated_agents_needed"] = sum(max_concurrent_per_type.values())
        
        # Identify potential bottlenecks
        total_tasks = len(tasks)
        for task_type, count in analysis["task_types"].items():
            if count / total_tasks > 0.3:  # More than 30% of tasks are same type
                analysis["potential_bottlenecks"].append({
                    "type": "task_type_concentration",
                    "task_type": task_type,
                    "percentage": (count / total_tasks) * 100
                })
        
        # Convert set to list for JSON serialization
        analysis["capability_requirements"] = list(analysis["capability_requirements"])
        
        return analysis
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get routing statistics and performance metrics.
        
        Returns:
            Dictionary with routing statistics
        """
        total_routed = self.stats["total_routed"]
        
        return {
            "total_tasks_routed": total_routed,
            "successful_matches": self.stats["successful_matches"],
            "failed_matches": self.stats["failed_matches"],
            "success_rate": (self.stats["successful_matches"] / total_routed) if total_routed > 0 else 0.0,
            "load_balanced_routes": self.stats["load_balanced_routes"],
            "priority_boosted_routes": self.stats["priority_boosted_routes"],
            "configuration": self.config.copy()
        }
    
    def optimize_routing_config(self, performance_data: Dict[str, Any]) -> None:
        """
        Optimize routing configuration based on performance data.
        
        Args:
            performance_data: Historical performance metrics
        """
        # Adjust weights based on system performance
        success_rate = performance_data.get("success_rate", 0.0)
        avg_response_time = performance_data.get("avg_response_time", 0.0)
        agent_utilization = performance_data.get("agent_utilization", 0.0)
        
        # If success rate is low, increase capability weight
        if success_rate < 0.8:
            self.config["capability_weight"] = min(0.5, self.config["capability_weight"] + 0.1)
            self.logger.info("Increased capability weight due to low success rate")
        
        # If response time is high, increase workload weight
        if avg_response_time > 10.0:  # seconds
            self.config["workload_weight"] = min(0.5, self.config["workload_weight"] + 0.1)
            self.logger.info("Increased workload weight due to high response time")
        
        # If utilization is low, decrease max workload ratio
        if agent_utilization < 0.3:
            self.config["max_agent_workload_ratio"] = max(0.5, self.config["max_agent_workload_ratio"] - 0.1)
            self.logger.info("Decreased max workload ratio due to low utilization")
        
        # Normalize weights to ensure they sum to 1.0
        total_weight = (self.config["capability_weight"] + 
                       self.config["workload_weight"] + 
                       self.config["priority_weight"])
        
        if total_weight > 0:
            self.config["capability_weight"] /= total_weight
            self.config["workload_weight"] /= total_weight
            self.config["priority_weight"] /= total_weight
    
    def validate_routing_decision(self, task: Task, selected_agent: str, 
                                available_agents: Dict[str, AgentInfo]) -> Dict[str, Any]:
        """
        Validate a routing decision and provide detailed analysis.
        
        Args:
            task: Task that was routed
            selected_agent: Agent that was selected
            available_agents: Available agents at time of routing
            
        Returns:
            Validation report
        """
        validation = {
            "task_id": task.id,
            "selected_agent": selected_agent,
            "is_valid": False,
            "validation_details": {},
            "alternative_agents": [],
            "routing_rationale": ""
        }
        
        agent_info = available_agents.get(selected_agent)
        if not agent_info:
            validation["validation_details"]["error"] = f"Selected agent '{selected_agent}' not found"
            return validation
        
        # Validate agent can handle task
        can_handle = self._can_agent_handle_task(selected_agent, task, available_agents)
        validation["is_valid"] = can_handle
        
        if can_handle:
            # Calculate why this agent was selected
            score = self._calculate_agent_score(task, selected_agent, agent_info)
            validation["routing_rationale"] = f"Selected based on score: {score:.3f}"
            
            # Find alternative agents for comparison
            capable_agents = self._find_capable_agents(task, available_agents)
            scored_agents = self._score_agents(task, capable_agents, available_agents)
            
            validation["alternative_agents"] = [
                {"agent": agent, "score": score} 
                for agent, score in scored_agents[:3]  # Top 3 alternatives
                if agent != selected_agent
            ]
        else:
            validation["validation_details"]["error"] = "Selected agent cannot handle the task"
            
            # Provide reasons why it failed
            if agent_info.status != AgentStatus.HEALTHY:
                validation["validation_details"]["health_issue"] = f"Agent status: {agent_info.status.value}"
            
            if task.type not in agent_info.registration.supported_task_types:
                validation["validation_details"]["capability_mismatch"] = f"Task type '{task.type}' not supported"
            
            current_load = len(agent_info.current_tasks)
            max_load = agent_info.registration.max_concurrent_tasks
            if current_load >= max_load:
                validation["validation_details"]["capacity_exceeded"] = f"Agent at capacity: {current_load}/{max_load}"
        
        return validation