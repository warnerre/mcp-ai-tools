#!/usr/bin/env python3
"""
Context Manager - Core Framework Component

The context manager maintains shared state and memory across multi-agent interactions.
This demonstrates how to build context-aware systems where agents can share information,
maintain conversation state, and coordinate through shared memory.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

from .types import Context, Task, AgentInfo


class ContextManager:
    """
    Manages shared context and memory for multi-agent coordination.
    
    The context manager provides:
    - Conversation context persistence
    - Shared memory management
    - Cross-agent state coordination
    - Context-based task routing
    - Memory optimization and cleanup
    """
    
    def __init__(self, name: str = "context_manager", storage_path: Optional[str] = None):
        self.name = name
        self.logger = self._setup_logging()
        
        # Storage configuration
        self.storage_path = Path(storage_path) if storage_path else Path("data/contexts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Active contexts
        self._active_contexts: Dict[str, Context] = {}
        self._context_indexes: Dict[str, Set[str]] = {
            "user_id": {},
            "conversation_id": {},
            "agent_states": {}
        }
        
        # Configuration
        self.config = {
            "max_contexts": 1000,
            "context_ttl_hours": 24,
            "auto_cleanup_interval": 3600,  # 1 hour
            "max_memory_size_mb": 100,
            "enable_persistence": True,
            "enable_context_sharing": True,
            "memory_compression": True
        }
        
        # Context statistics
        self.stats = {
            "contexts_created": 0,
            "contexts_loaded": 0,
            "contexts_expired": 0,
            "memory_operations": 0,
            "context_merges": 0
        }
        
        # Last cleanup time
        self._last_cleanup = datetime.now()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup context manager logging."""
        logger = logging.getLogger(f"context_manager.{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - ContextManager - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def create_context(self, conversation_id: str, user_id: str, 
                      initial_data: Optional[Dict[str, Any]] = None) -> Context:
        """
        Create a new context for conversation tracking.
        
        Args:
            conversation_id: Unique conversation identifier
            user_id: User identifier
            initial_data: Initial context data
            
        Returns:
            Created context
        """
        # Check if context already exists
        if conversation_id in self._active_contexts:
            self.logger.warning(f"Context {conversation_id} already exists, returning existing")
            return self._active_contexts[conversation_id]
        
        # Create new context
        context = Context(
            conversation_id=conversation_id,
            user_id=user_id,
            session_data=initial_data or {},
            shared_memory={},
            active_tasks=[],
            agent_states={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store context
        self._active_contexts[conversation_id] = context
        self._update_indexes(context)
        
        # Persist if enabled
        if self.config["enable_persistence"]:
            self._persist_context(context)
        
        self.stats["contexts_created"] += 1
        self.logger.info(f"Created new context: {conversation_id} for user: {user_id}")
        
        return context
    
    def get_context(self, conversation_id: str) -> Optional[Context]:
        """
        Retrieve a context by conversation ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Context if found, None otherwise
        """
        # Check active contexts first
        if conversation_id in self._active_contexts:
            context = self._active_contexts[conversation_id]
            self._touch_context(context)
            return context
        
        # Try loading from persistence
        if self.config["enable_persistence"]:
            context = self._load_context(conversation_id)
            if context:
                self._active_contexts[conversation_id] = context
                self._update_indexes(context)
                self.stats["contexts_loaded"] += 1
                self.logger.info(f"Loaded context from persistence: {conversation_id}")
                return context
        
        return None
    
    def update_context(self, conversation_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update context data.
        
        Args:
            conversation_id: Conversation identifier
            updates: Data to update
            
        Returns:
            True if successful
        """
        context = self.get_context(conversation_id)
        if not context:
            self.logger.warning(f"Context not found for update: {conversation_id}")
            return False
        
        # Update session data
        if "session_data" in updates:
            context.session_data.update(updates["session_data"])
        
        # Update shared memory
        if "shared_memory" in updates:
            context.shared_memory.update(updates["shared_memory"])
        
        # Update agent states
        if "agent_states" in updates:
            context.agent_states.update(updates["agent_states"])
        
        # Update active tasks
        if "active_tasks" in updates:
            new_tasks = updates["active_tasks"]
            if isinstance(new_tasks, list):
                context.active_tasks.extend(new_tasks)
            else:
                context.active_tasks.append(new_tasks)
        
        # Touch context
        self._touch_context(context)
        
        # Persist changes
        if self.config["enable_persistence"]:
            self._persist_context(context)
        
        self.logger.debug(f"Updated context: {conversation_id}")
        return True
    
    def set_shared_memory(self, conversation_id: str, key: str, value: Any) -> bool:
        """
        Set a value in shared memory.
        
        Args:
            conversation_id: Conversation identifier
            key: Memory key
            value: Value to store
            
        Returns:
            True if successful
        """
        context = self.get_context(conversation_id)
        if not context:
            return False
        
        context.shared_memory[key] = value
        self._touch_context(context)
        
        if self.config["enable_persistence"]:
            self._persist_context(context)
        
        self.stats["memory_operations"] += 1
        self.logger.debug(f"Set shared memory {key} in context {conversation_id}")
        return True
    
    def get_shared_memory(self, conversation_id: str, key: str) -> Any:
        """
        Get a value from shared memory.
        
        Args:
            conversation_id: Conversation identifier
            key: Memory key
            
        Returns:
            Value if found, None otherwise
        """
        context = self.get_context(conversation_id)
        if not context:
            return None
        
        value = context.shared_memory.get(key)
        self.stats["memory_operations"] += 1
        return value
    
    def update_agent_state(self, conversation_id: str, agent_name: str, 
                          agent_state: Dict[str, Any]) -> bool:
        """
        Update agent state within a context.
        
        Args:
            conversation_id: Conversation identifier
            agent_name: Name of the agent
            agent_state: Agent state data
            
        Returns:
            True if successful
        """
        context = self.get_context(conversation_id)
        if not context:
            return False
        
        if agent_name not in context.agent_states:
            context.agent_states[agent_name] = {}
        
        context.agent_states[agent_name].update(agent_state)
        self._touch_context(context)
        
        if self.config["enable_persistence"]:
            self._persist_context(context)
        
        self.logger.debug(f"Updated agent state for {agent_name} in context {conversation_id}")
        return True
    
    def get_agent_state(self, conversation_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get agent state from context.
        
        Args:
            conversation_id: Conversation identifier
            agent_name: Name of the agent
            
        Returns:
            Agent state if found
        """
        context = self.get_context(conversation_id)
        if not context:
            return None
        
        return context.agent_states.get(agent_name)
    
    def add_task_to_context(self, conversation_id: str, task: Task) -> bool:
        """
        Add a task to context's active tasks.
        
        Args:
            conversation_id: Conversation identifier
            task: Task to add
            
        Returns:
            True if successful
        """
        context = self.get_context(conversation_id)
        if not context:
            return False
        
        # Add task if not already present
        if task not in context.active_tasks:
            context.active_tasks.append(task)
            self._touch_context(context)
            
            if self.config["enable_persistence"]:
                self._persist_context(context)
            
            self.logger.debug(f"Added task {task.id} to context {conversation_id}")
        
        return True
    
    def remove_task_from_context(self, conversation_id: str, task_id: str) -> bool:
        """
        Remove a task from context's active tasks.
        
        Args:
            conversation_id: Conversation identifier
            task_id: Task identifier
            
        Returns:
            True if successful
        """
        context = self.get_context(conversation_id)
        if not context:
            return False
        
        # Remove task
        context.active_tasks = [t for t in context.active_tasks if t.id != task_id]
        self._touch_context(context)
        
        if self.config["enable_persistence"]:
            self._persist_context(context)
        
        self.logger.debug(f"Removed task {task_id} from context {conversation_id}")
        return True
    
    def merge_contexts(self, target_conversation_id: str, 
                      source_conversation_id: str) -> bool:
        """
        Merge two contexts together.
        
        Args:
            target_conversation_id: Target context ID
            source_conversation_id: Source context ID
            
        Returns:
            True if successful
        """
        if not self.config["enable_context_sharing"]:
            self.logger.warning("Context sharing is disabled")
            return False
        
        target_context = self.get_context(target_conversation_id)
        source_context = self.get_context(source_conversation_id)
        
        if not target_context or not source_context:
            self.logger.warning(f"Cannot merge contexts - target: {target_context is not None}, "
                              f"source: {source_context is not None}")
            return False
        
        # Merge session data
        target_context.session_data.update(source_context.session_data)
        
        # Merge shared memory
        target_context.shared_memory.update(source_context.shared_memory)
        
        # Merge agent states
        for agent_name, agent_state in source_context.agent_states.items():
            if agent_name in target_context.agent_states:
                target_context.agent_states[agent_name].update(agent_state)
            else:
                target_context.agent_states[agent_name] = agent_state.copy()
        
        # Merge active tasks (avoid duplicates)
        existing_task_ids = {t.id for t in target_context.active_tasks}
        for task in source_context.active_tasks:
            if task.id not in existing_task_ids:
                target_context.active_tasks.append(task)
        
        self._touch_context(target_context)
        
        if self.config["enable_persistence"]:
            self._persist_context(target_context)
        
        self.stats["context_merges"] += 1
        self.logger.info(f"Merged context {source_conversation_id} into {target_conversation_id}")
        
        return True
    
    def find_contexts_by_user(self, user_id: str) -> List[Context]:
        """
        Find all contexts for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of contexts for the user
        """
        contexts = []
        
        # Search active contexts
        for context in self._active_contexts.values():
            if context.user_id == user_id:
                contexts.append(context)
        
        # Search persisted contexts if needed
        if self.config["enable_persistence"]:
            contexts.extend(self._find_persisted_contexts_by_user(user_id))
        
        return contexts
    
    def find_contexts_with_agent(self, agent_name: str) -> List[Context]:
        """
        Find all contexts that have state for a specific agent.
        
        Args:
            agent_name: Agent name
            
        Returns:
            List of contexts with agent state
        """
        contexts = []
        
        for context in self._active_contexts.values():
            if agent_name in context.agent_states:
                contexts.append(context)
        
        return contexts
    
    def cleanup_expired_contexts(self) -> int:
        """
        Clean up expired contexts to free memory.
        
        Returns:
            Number of contexts cleaned up
        """
        if not self._should_cleanup():
            return 0
        
        current_time = datetime.now()
        ttl = timedelta(hours=self.config["context_ttl_hours"])
        expired_contexts = []
        
        # Find expired contexts
        for conversation_id, context in self._active_contexts.items():
            if current_time - context.updated_at > ttl:
                expired_contexts.append(conversation_id)
        
        # Remove expired contexts
        for conversation_id in expired_contexts:
            context = self._active_contexts.pop(conversation_id)
            self._remove_from_indexes(context)
            
            # Archive to persistence if enabled
            if self.config["enable_persistence"]:
                self._archive_context(context)
        
        self.stats["contexts_expired"] += len(expired_contexts)
        self._last_cleanup = current_time
        
        if expired_contexts:
            self.logger.info(f"Cleaned up {len(expired_contexts)} expired contexts")
        
        return len(expired_contexts)
    
    def get_context_stats(self) -> Dict[str, Any]:
        """
        Get context manager statistics.
        
        Returns:
            Statistics dictionary
        """
        # Calculate memory usage
        total_memory = 0
        for context in self._active_contexts.values():
            total_memory += self._estimate_context_memory(context)
        
        return {
            "active_contexts": len(self._active_contexts),
            "total_memory_mb": total_memory / (1024 * 1024),
            "contexts_created": self.stats["contexts_created"],
            "contexts_loaded": self.stats["contexts_loaded"],
            "contexts_expired": self.stats["contexts_expired"],
            "memory_operations": self.stats["memory_operations"],
            "context_merges": self.stats["context_merges"],
            "last_cleanup": self._last_cleanup.isoformat(),
            "config": self.config.copy()
        }
    
    def _touch_context(self, context: Context) -> None:
        """Update context timestamp."""
        context.updated_at = datetime.now()
    
    def _update_indexes(self, context: Context) -> None:
        """Update context indexes for fast lookup."""
        conversation_id = context.conversation_id
        
        # User ID index
        if context.user_id not in self._context_indexes["user_id"]:
            self._context_indexes["user_id"][context.user_id] = set()
        self._context_indexes["user_id"][context.user_id].add(conversation_id)
        
        # Agent states index
        for agent_name in context.agent_states:
            if agent_name not in self._context_indexes["agent_states"]:
                self._context_indexes["agent_states"][agent_name] = set()
            self._context_indexes["agent_states"][agent_name].add(conversation_id)
    
    def _remove_from_indexes(self, context: Context) -> None:
        """Remove context from indexes."""
        conversation_id = context.conversation_id
        
        # User ID index
        if context.user_id in self._context_indexes["user_id"]:
            self._context_indexes["user_id"][context.user_id].discard(conversation_id)
            if not self._context_indexes["user_id"][context.user_id]:
                del self._context_indexes["user_id"][context.user_id]
        
        # Agent states index
        for agent_name in context.agent_states:
            if agent_name in self._context_indexes["agent_states"]:
                self._context_indexes["agent_states"][agent_name].discard(conversation_id)
                if not self._context_indexes["agent_states"][agent_name]:
                    del self._context_indexes["agent_states"][agent_name]
    
    def _should_cleanup(self) -> bool:
        """Check if cleanup should be performed."""
        time_since_cleanup = (datetime.now() - self._last_cleanup).total_seconds()
        return time_since_cleanup >= self.config["auto_cleanup_interval"]
    
    def _estimate_context_memory(self, context: Context) -> int:
        """Estimate memory usage of a context in bytes."""
        try:
            # Convert context to JSON to estimate size
            context_dict = {
                "conversation_id": context.conversation_id,
                "user_id": context.user_id,
                "session_data": context.session_data,
                "shared_memory": context.shared_memory,
                "agent_states": context.agent_states,
                # Skip active_tasks as they might be large objects
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat()
            }
            return len(json.dumps(context_dict, default=str))
        except Exception:
            return 1024  # Default estimate
    
    def _persist_context(self, context: Context) -> bool:
        """Persist context to storage."""
        try:
            context_file = self.storage_path / f"{context.conversation_id}.json"
            
            # Convert context to serializable format
            context_data = {
                "conversation_id": context.conversation_id,
                "user_id": context.user_id,
                "session_data": context.session_data,
                "shared_memory": context.shared_memory,
                "agent_states": context.agent_states,
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat(),
                # Serialize tasks separately to handle complex objects
                "task_ids": [task.id for task in context.active_tasks]
            }
            
            with open(context_file, 'w') as f:
                json.dump(context_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to persist context {context.conversation_id}: {e}")
            return False
    
    def _load_context(self, conversation_id: str) -> Optional[Context]:
        """Load context from storage."""
        try:
            context_file = self.storage_path / f"{conversation_id}.json"
            if not context_file.exists():
                return None
            
            with open(context_file, 'r') as f:
                context_data = json.load(f)
            
            # Reconstruct context
            context = Context(
                conversation_id=context_data["conversation_id"],
                user_id=context_data["user_id"],
                session_data=context_data.get("session_data", {}),
                shared_memory=context_data.get("shared_memory", {}),
                active_tasks=[],  # Tasks will be loaded separately if needed
                agent_states=context_data.get("agent_states", {}),
                created_at=datetime.fromisoformat(context_data["created_at"]),
                updated_at=datetime.fromisoformat(context_data["updated_at"])
            )
            
            return context
        except Exception as e:
            self.logger.error(f"Failed to load context {conversation_id}: {e}")
            return None
    
    def _archive_context(self, context: Context) -> bool:
        """Archive expired context."""
        try:
            archive_dir = self.storage_path / "archived"
            archive_dir.mkdir(exist_ok=True)
            
            context_file = self.storage_path / f"{context.conversation_id}.json"
            archive_file = archive_dir / f"{context.conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            if context_file.exists():
                context_file.rename(archive_file)
                return True
        except Exception as e:
            self.logger.error(f"Failed to archive context {context.conversation_id}: {e}")
        
        return False
    
    def _find_persisted_contexts_by_user(self, user_id: str) -> List[Context]:
        """Find persisted contexts for a user."""
        contexts = []
        
        try:
            for context_file in self.storage_path.glob("*.json"):
                if context_file.name.startswith("archived"):
                    continue
                
                try:
                    with open(context_file, 'r') as f:
                        context_data = json.load(f)
                    
                    if context_data.get("user_id") == user_id:
                        context = self._load_context(context_data["conversation_id"])
                        if context:
                            contexts.append(context)
                except Exception:
                    continue
        except Exception as e:
            self.logger.error(f"Failed to search persisted contexts: {e}")
        
        return contexts