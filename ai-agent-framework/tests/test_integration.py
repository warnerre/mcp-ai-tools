#!/usr/bin/env python3
"""
Integration Tests for AI Agent Framework

These tests validate the complete multi-agent system end-to-end.
They demonstrate proper integration between all components and serve
as educational examples of testing distributed systems.
"""

import asyncio
import sys
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

# Add the project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core import (
    create_framework, create_agent_registration,
    Task, TaskStatus, Context, Orchestrator, TaskRouter, ContextManager
)
from src.agents.file_agent import FileAgent
from src.agents.task_agent import TaskAgent
from src.agents.coordinator_agent import CoordinatorAgent


class TestFrameworkIntegration:
    """
    Integration tests for the complete framework.
    
    Educational Purpose:
    These tests demonstrate how to validate multi-agent systems
    and show patterns for testing distributed architectures.
    """
    
    @pytest.fixture
    async def framework_components(self):
        """Create framework components for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator, task_router, context_manager = create_framework(
                name="test_framework",
                storage_path=temp_dir
            )
            yield orchestrator, task_router, context_manager
            
            # Cleanup
            await orchestrator.stop()
    
    @pytest.fixture
    async def test_agents(self):
        """Create test agents."""
        file_agent = FileAgent()
        task_agent = TaskAgent()
        coordinator_agent = CoordinatorAgent()
        
        # Setup agents
        await file_agent.setup()
        await task_agent.setup()
        await coordinator_agent.setup()
        
        yield {
            "file_agent": file_agent,
            "task_agent": task_agent,
            "coordinator_agent": coordinator_agent
        }
        
        # Cleanup
        await file_agent.stop()
        await task_agent.stop()
        await coordinator_agent.stop()
    
    async def test_framework_creation(self, framework_components):
        """Test framework components are created correctly."""
        orchestrator, task_router, context_manager = framework_components
        
        # Verify types
        assert isinstance(orchestrator, Orchestrator)
        assert isinstance(task_router, TaskRouter)
        assert isinstance(context_manager, ContextManager)
        
        # Verify integration
        assert orchestrator._task_router is task_router
        assert orchestrator._context_manager is context_manager
        
        # Verify configuration
        assert orchestrator.name == "test_framework_orchestrator"
        assert task_router.name == "test_framework_router"
        assert context_manager.name == "test_framework_context"
    
    async def test_agent_registration(self, framework_components, test_agents):
        """Test agent registration with orchestrator."""
        orchestrator, _, _ = framework_components
        agents = test_agents
        
        # Register all agents
        for agent_name, agent in agents.items():
            success = await orchestrator.register_agent(agent)
            assert success, f"Failed to register {agent_name}"
        
        # Verify registration
        system_status = orchestrator.get_system_status()
        assert system_status["registered_agents"] == 3
        assert len(system_status["agent_list"]) == 3
        
        # Check specific agents
        for agent_name in agents.keys():
            agent_status = orchestrator.get_agent_status(agent_name)
            assert agent_status is not None
            assert agent_status["status"] == "healthy"
    
    async def test_task_routing(self, framework_components, test_agents):
        """Test intelligent task routing."""
        orchestrator, task_router, _ = framework_components
        agents = test_agents
        
        # Register agents
        agent_infos = {}
        for agent in agents.values():
            await orchestrator.register_agent(agent)
            agent_infos[agent.name] = orchestrator._registered_agents[agent.name]
        
        # Test file operation routing
        file_task = Task(
            id="test_file_task",
            type="read_file",
            description="Test file reading",
            parameters={"path": "test.txt"}
        )
        
        best_agent = task_router.find_best_agent(file_task, agent_infos)
        assert best_agent == "file_agent", "File task should route to file agent"
        
        # Test task management routing
        task_mgmt_task = Task(
            id="test_task_mgmt",
            type="create_task",
            description="Test task creation",
            parameters={"type": "test", "description": "Test task"}
        )
        
        best_agent = task_router.find_best_agent(task_mgmt_task, agent_infos)
        assert best_agent == "task_agent", "Task mgmt should route to task agent"
        
        # Test coordination routing
        coord_task = Task(
            id="test_coordination",
            type="orchestrate_workflow",
            description="Test workflow orchestration",
            parameters={"name": "test_workflow", "steps": []}
        )
        
        best_agent = task_router.find_best_agent(coord_task, agent_infos)
        assert best_agent == "coordinator_agent", "Coordination should route to coordinator"
    
    async def test_context_management(self, framework_components):
        """Test context management functionality."""
        _, _, context_manager = framework_components
        
        # Create context
        context = context_manager.create_context(
            conversation_id="test_conv_001",
            user_id="test_user",
            initial_data={"session_start": datetime.now().isoformat()}
        )
        
        assert context.conversation_id == "test_conv_001"
        assert context.user_id == "test_user"
        assert "session_start" in context.session_data
        
        # Test shared memory
        success = context_manager.set_shared_memory("test_conv_001", "test_key", "test_value")
        assert success
        
        value = context_manager.get_shared_memory("test_conv_001", "test_key")
        assert value == "test_value"
        
        # Test agent state
        success = context_manager.update_agent_state(
            "test_conv_001", 
            "file_agent", 
            {"last_action": "read_file", "status": "active"}
        )
        assert success
        
        agent_state = context_manager.get_agent_state("test_conv_001", "file_agent")
        assert agent_state["last_action"] == "read_file"
        assert agent_state["status"] == "active"
    
    async def test_end_to_end_workflow(self, framework_components, test_agents):
        """Test complete end-to-end workflow execution."""
        orchestrator, _, context_manager = framework_components
        agents = test_agents
        
        # Register all agents
        for agent in agents.values():
            await orchestrator.register_agent(agent)
        
        # Create context for workflow
        context = context_manager.create_context(
            conversation_id="workflow_test",
            user_id="test_user"
        )
        
        # Test 1: Simple file operation
        file_task = Task(
            id="workflow_step_1",
            type="create_directory",
            description="Create test directory",
            parameters={"path": "test_workflow_dir"}
        )
        
        task_id = await orchestrator.submit_task(file_task, context)
        assert task_id == file_task.id
        
        # Wait a moment for processing
        await asyncio.sleep(2)
        
        # Check task result
        result = await orchestrator.get_task_result(task_id)
        if result:
            assert result.success or "already exists" in (result.error or "")
        
        # Test 2: Task management operation
        task_creation_task = Task(
            id="workflow_step_2",
            type="create_task",
            description="Create a managed task",
            parameters={
                "type": "write_file",
                "description": "Write test file",
                "parameters": {
                    "path": "test_workflow_dir/test.txt",
                    "content": "Hello from multi-agent framework!"
                },
                "priority": 5
            }
        )
        
        task_id = await orchestrator.submit_task(task_creation_task, context)
        await asyncio.sleep(2)
        
        result = await orchestrator.get_task_result(task_id)
        if result:
            assert result.success, f"Task creation failed: {result.error}"
        
        # Test 3: System monitoring
        monitor_task = Task(
            id="workflow_step_3",
            type="monitor_system",
            description="Monitor system status",
            parameters={"scope": "full_system"}
        )
        
        task_id = await orchestrator.submit_task(monitor_task, context)
        await asyncio.sleep(2)
        
        result = await orchestrator.get_task_result(task_id)
        if result:
            assert result.success, f"Monitoring failed: {result.error}"
            assert "system_status" in result.data
    
    async def test_error_handling(self, framework_components, test_agents):
        """Test error handling and resilience."""
        orchestrator, _, _ = framework_components
        agents = test_agents
        
        # Register agents
        for agent in agents.values():
            await orchestrator.register_agent(agent)
        
        # Test 1: Invalid file operation
        invalid_task = Task(
            id="error_test_1",
            type="read_file",
            description="Try to read non-existent file",
            parameters={"path": "/invalid/path/file.txt"}
        )
        
        task_id = await orchestrator.submit_task(invalid_task)
        await asyncio.sleep(2)
        
        result = await orchestrator.get_task_result(task_id)
        if result:
            assert not result.success, "Invalid file operation should fail"
            assert result.error is not None
        
        # Test 2: Unsupported task type
        unsupported_task = Task(
            id="error_test_2",
            type="unsupported_operation",
            description="Test unsupported operation",
            parameters={}
        )
        
        task_id = await orchestrator.submit_task(unsupported_task)
        await asyncio.sleep(2)
        
        # Should fail to find suitable agent
        result = await orchestrator.get_task_result(task_id)
        if result:
            assert not result.success
    
    async def test_performance_metrics(self, framework_components):
        """Test performance monitoring and metrics."""
        orchestrator, task_router, context_manager = framework_components
        
        # Check orchestrator metrics
        system_status = orchestrator.get_system_status()
        assert "registered_agents" in system_status
        assert "active_tasks" in system_status
        assert "task_counts" in system_status
        assert "agent_counts" in system_status
        
        # Check router metrics
        routing_stats = task_router.get_routing_stats()
        assert "total_tasks_routed" in routing_stats
        assert "success_rate" in routing_stats
        assert "configuration" in routing_stats
        
        # Check context manager metrics
        context_stats = context_manager.get_context_stats()
        assert "active_contexts" in context_stats
        assert "total_memory_mb" in context_stats
        assert "contexts_created" in context_stats


class TestAgentSpecialization:
    """
    Test individual agent specializations and capabilities.
    
    Educational Purpose:
    Shows how to test individual components in a multi-agent system
    and validate agent-specific functionality.
    """
    
    @pytest.fixture
    async def file_agent(self):
        """Create and setup file agent."""
        agent = FileAgent()
        await agent.setup()
        yield agent
        await agent.stop()
    
    @pytest.fixture
    async def task_agent(self):
        """Create and setup task agent."""
        agent = TaskAgent()
        await agent.setup()
        yield agent
        await agent.stop()
    
    @pytest.fixture
    async def coordinator_agent(self):
        """Create and setup coordinator agent."""
        agent = CoordinatorAgent()
        await agent.setup()
        yield agent
        await agent.stop()
    
    async def test_file_agent_capabilities(self, file_agent):
        """Test file agent specific capabilities."""
        # Test directory listing
        list_task = Task(
            id="file_test_1",
            type="list_directory",
            description="List current directory",
            parameters={"path": "."}
        )
        
        result = await file_agent.execute_task(list_task)
        assert result.success, f"Directory listing failed: {result.error}"
        assert "directory" in result.data
        assert "file_count" in result.data
        
        # Test capability matching
        supported_types = file_agent.registration.supported_task_types
        assert "read_file" in supported_types
        assert "write_file" in supported_types
        assert "list_directory" in supported_types
        assert "analyze_directory" in supported_types
    
    async def test_task_agent_capabilities(self, task_agent):
        """Test task agent specific capabilities."""
        # Test task creation
        create_task = Task(
            id="task_test_1",
            type="create_task",
            description="Create a test task",
            parameters={
                "type": "test_operation",
                "description": "A test task for validation",
                "parameters": {"param1": "value1"},
                "priority": 5
            }
        )
        
        result = await task_agent.execute_task(create_task)
        assert result.success, f"Task creation failed: {result.error}"
        assert "task_id" in result.data
        assert "task_type" in result.data
        
        # Test capability matching
        capabilities = task_agent.registration.capabilities
        assert "task_management" in capabilities
        assert "workflow_coordination" in capabilities
        assert "task_scheduling" in capabilities
    
    async def test_coordinator_capabilities(self, coordinator_agent):
        """Test coordinator agent specific capabilities."""
        # Test system monitoring
        monitor_task = Task(
            id="coord_test_1",
            type="monitor_system",
            description="Monitor system health",
            parameters={"scope": "full_system"}
        )
        
        result = await coordinator_agent.execute_task(monitor_task)
        assert result.success, f"System monitoring failed: {result.error}"
        assert "system_status" in result.data
        assert "monitoring_scope" in result.data
        
        # Test capability matching
        capabilities = coordinator_agent.registration.capabilities
        assert "agent_coordination" in capabilities
        assert "workflow_orchestration" in capabilities
        assert "system_monitoring" in capabilities


@pytest.mark.asyncio
class TestEducationalConcepts:
    """
    Tests that validate educational concepts and learning objectives.
    
    Educational Purpose:
    These tests ensure that the framework successfully demonstrates
    key multi-agent system concepts that learners should understand.
    """
    
    async def test_mcp_client_server_pattern(self):
        """Validate MCP client-server architecture is properly implemented."""
        # Create agents (MCP clients)
        file_agent = FileAgent()
        await file_agent.setup()
        
        try:
            # Verify MCP client functionality
            available_tools = file_agent.get_available_tools()
            assert len(available_tools) > 0, "Agent should have discovered MCP tools"
            
            # Verify expected tools from file operations server
            expected_tools = ["read_file", "write_file", "list_directory", "create_directory"]
            for tool in expected_tools:
                assert tool in available_tools, f"Missing expected tool: {tool}"
            
            # Verify tool metadata
            for tool_name, tool_info in available_tools.items():
                assert "description" in tool_info
                assert "inputSchema" in tool_info
                assert "server" in tool_info
        
        finally:
            await file_agent.stop()
    
    async def test_agent_specialization_pattern(self):
        """Validate agent specialization design pattern."""
        agents = [
            (FileAgent(), "file_operations"),
            (TaskAgent(), "task_management"), 
            (CoordinatorAgent(), "agent_coordination")
        ]
        
        try:
            for agent, expected_capability in agents:
                await agent.setup()
                
                # Verify agent has specialized capabilities
                capabilities = agent.registration.capabilities
                assert expected_capability in capabilities, \
                    f"{agent.name} should have {expected_capability} capability"
                
                # Verify agent has appropriate task types
                task_types = agent.registration.supported_task_types
                assert len(task_types) > 0, f"{agent.name} should support specific task types"
                
                # Verify agent specialization (no agent should do everything)
                assert len(task_types) < 20, f"{agent.name} seems too generalized"
        
        finally:
            for agent, _ in agents:
                await agent.stop()
    
    async def test_orchestration_pattern(self):
        """Validate orchestration and coordination patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create framework (demonstrates orchestration setup)
            orchestrator, task_router, context_manager = create_framework(
                storage_path=temp_dir
            )
            
            try:
                # Verify orchestrator can manage multiple agents
                assert hasattr(orchestrator, '_registered_agents')
                assert hasattr(orchestrator, '_task_queue')
                assert hasattr(orchestrator, '_active_workflows')
                
                # Verify task router provides intelligent routing
                assert hasattr(task_router, 'find_best_agent')
                assert hasattr(task_router, 'analyze_routing_requirements')
                assert hasattr(task_router, 'get_routing_stats')
                
                # Verify context manager enables shared state
                assert hasattr(context_manager, 'create_context')
                assert hasattr(context_manager, 'set_shared_memory')
                assert hasattr(context_manager, 'update_agent_state')
                
                # Verify components work together
                assert orchestrator._task_router is task_router
                assert orchestrator._context_manager is context_manager
            
            finally:
                await orchestrator.stop()
    
    async def test_scalability_patterns(self):
        """Validate scalability and extensibility patterns."""
        # Test agent registration pattern (adding new agents)
        registration = create_agent_registration(
            name="test_agent",
            capabilities=["test_capability"],
            supported_task_types=["test_task"],
            priority=5,
            max_concurrent_tasks=2
        )
        
        # Verify registration structure supports scalability
        assert hasattr(registration, 'capabilities')
        assert hasattr(registration, 'supported_task_types')
        assert hasattr(registration, 'max_concurrent_tasks')
        assert hasattr(registration, 'priority')
        
        # Test framework supports dynamic agent addition
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator, _, _ = create_framework(storage_path=temp_dir)
            
            # Should start with no agents
            status = orchestrator.get_system_status()
            assert status["registered_agents"] == 0
            
            await orchestrator.stop()


# Educational test runner that explains concepts
def run_educational_tests():
    """
    Run integration tests with educational explanations.
    
    This function demonstrates how to structure testing for
    educational multi-agent systems.
    """
    print("🎓 AI Agent Framework - Educational Integration Tests")
    print("=" * 60)
    print()
    print("These tests validate the multi-agent framework and demonstrate:")
    print("• MCP client-server architecture patterns")
    print("• Agent specialization and capability design")
    print("• Orchestration and coordination patterns")
    print("• Task routing and load balancing")
    print("• Context management and shared state")
    print("• Error handling and system resilience")
    print("• Performance monitoring and optimization")
    print()
    
    # Run pytest with verbose output
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"
    ])


if __name__ == "__main__":
    run_educational_tests()