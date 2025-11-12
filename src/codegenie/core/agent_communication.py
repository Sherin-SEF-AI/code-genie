"""
Agent Communication Bus for inter-agent messaging and coordination.

This module provides:
- Message passing between agents
- Event broadcasting
- Request-response patterns
- Agent discovery and registration
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime
from enum import Enum
from uuid import uuid4


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in the system."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    EVENT = "event"


class MessagePriority(Enum):
    """Priority levels for messages."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """Represents a message between agents."""
    id: str = field(default_factory=lambda: str(uuid4()))
    message_type: MessageType = MessageType.NOTIFICATION
    sender: str = ""
    recipient: Optional[str] = None  # None for broadcast
    content: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None  # For request-response correlation
    requires_response: bool = False
    response_timeout: float = 30.0


@dataclass
class AgentRegistration:
    """Registration information for an agent."""
    agent_name: str
    capabilities: List[str]
    status: str
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.now)


class AgentCommunicationBus:
    """
    Central communication bus for inter-agent messaging.
    """
    
    def __init__(self):
        """Initialize the communication bus."""
        self.registered_agents: Dict[str, AgentRegistration] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.broadcast_handlers: List[Callable] = []
        self.message_history: List[Message] = []
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
        logger.info("Initialized AgentCommunicationBus")
    
    def register_agent(
        self,
        agent_name: str,
        capabilities: List[str],
        status: str = "active",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register an agent with the communication bus.
        
        Args:
            agent_name: Name of the agent
            capabilities: List of agent capabilities
            status: Current status of the agent
            metadata: Additional metadata
            
        Returns:
            True if registration successful
        """
        if agent_name in self.registered_agents:
            logger.warning(f"Agent {agent_name} already registered, updating registration")
        
        registration = AgentRegistration(
            agent_name=agent_name,
            capabilities=capabilities,
            status=status,
            metadata=metadata or {}
        )
        
        self.registered_agents[agent_name] = registration
        self.message_queues[agent_name] = asyncio.Queue()
        self.message_handlers[agent_name] = []
        
        logger.info(f"Registered agent: {agent_name} with capabilities: {capabilities}")
        return True
    
    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from the communication bus.
        
        Args:
            agent_name: Name of the agent to unregister
            
        Returns:
            True if unregistration successful
        """
        if agent_name not in self.registered_agents:
            logger.warning(f"Agent {agent_name} not registered")
            return False
        
        del self.registered_agents[agent_name]
        del self.message_queues[agent_name]
        del self.message_handlers[agent_name]
        
        logger.info(f"Unregistered agent: {agent_name}")
        return True
    
    def discover_agents(
        self,
        capability: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[AgentRegistration]:
        """
        Discover agents based on criteria.
        
        Args:
            capability: Optional capability to filter by
            status: Optional status to filter by
            
        Returns:
            List of matching agent registrations
        """
        agents = list(self.registered_agents.values())
        
        if capability:
            agents = [
                agent for agent in agents
                if capability in agent.capabilities
            ]
        
        if status:
            agents = [
                agent for agent in agents
                if agent.status == status
            ]
        
        return agents
    
    async def send_message(
        self,
        sender: str,
        recipient: str,
        content: Dict[str, Any],
        message_type: MessageType = MessageType.NOTIFICATION,
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_response: bool = False,
        response_timeout: float = 30.0
    ) -> Optional[Message]:
        """
        Send a message to another agent.
        
        Args:
            sender: Name of sending agent
            recipient: Name of receiving agent
            content: Message content
            message_type: Type of message
            priority: Message priority
            requires_response: Whether a response is required
            response_timeout: Timeout for response in seconds
            
        Returns:
            Response message if requires_response is True, None otherwise
        """
        if recipient not in self.registered_agents:
            logger.error(f"Recipient agent {recipient} not registered")
            return None
        
        message = Message(
            message_type=message_type,
            sender=sender,
            recipient=recipient,
            content=content,
            priority=priority,
            requires_response=requires_response,
            response_timeout=response_timeout
        )
        
        # Store in history
        self.message_history.append(message)
        
        # If response required, create future
        if requires_response:
            future = asyncio.Future()
            self.pending_responses[message.id] = future
        
        # Deliver message
        await self.message_queues[recipient].put(message)
        
        logger.debug(f"Message sent from {sender} to {recipient}: {message.id}")
        
        # Wait for response if required
        if requires_response:
            try:
                response = await asyncio.wait_for(future, timeout=response_timeout)
                return response
            except asyncio.TimeoutError:
                logger.warning(f"Response timeout for message {message.id}")
                del self.pending_responses[message.id]
                return None
        
        return None
    
    async def send_response(
        self,
        original_message: Message,
        sender: str,
        content: Dict[str, Any]
    ) -> bool:
        """
        Send a response to a message.
        
        Args:
            original_message: The message being responded to
            sender: Name of responding agent
            content: Response content
            
        Returns:
            True if response sent successfully
        """
        response = Message(
            message_type=MessageType.RESPONSE,
            sender=sender,
            recipient=original_message.sender,
            content=content,
            correlation_id=original_message.id
        )
        
        # Store in history
        self.message_history.append(response)
        
        # Resolve pending response future if exists
        if original_message.id in self.pending_responses:
            future = self.pending_responses[original_message.id]
            if not future.done():
                future.set_result(response)
            del self.pending_responses[original_message.id]
        
        logger.debug(f"Response sent from {sender} to {original_message.sender}")
        return True
    
    async def broadcast_message(
        self,
        sender: str,
        content: Dict[str, Any],
        exclude_sender: bool = True
    ) -> int:
        """
        Broadcast a message to all registered agents.
        
        Args:
            sender: Name of sending agent
            content: Message content
            exclude_sender: Whether to exclude sender from broadcast
            
        Returns:
            Number of agents message was sent to
        """
        message = Message(
            message_type=MessageType.BROADCAST,
            sender=sender,
            recipient=None,
            content=content
        )
        
        # Store in history
        self.message_history.append(message)
        
        # Send to all agents
        count = 0
        for agent_name in self.registered_agents.keys():
            if exclude_sender and agent_name == sender:
                continue
            
            await self.message_queues[agent_name].put(message)
            count += 1
        
        # Notify broadcast handlers
        for handler in self.broadcast_handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Error in broadcast handler: {e}")
        
        logger.debug(f"Broadcast from {sender} sent to {count} agents")
        return count
    
    async def receive_message(
        self,
        agent_name: str,
        timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        Receive a message for an agent.
        
        Args:
            agent_name: Name of the agent
            timeout: Optional timeout in seconds
            
        Returns:
            Message if available, None if timeout
        """
        if agent_name not in self.message_queues:
            logger.error(f"Agent {agent_name} not registered")
            return None
        
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self.message_queues[agent_name].get(),
                    timeout=timeout
                )
            else:
                message = await self.message_queues[agent_name].get()
            
            # Call message handlers
            if agent_name in self.message_handlers:
                for handler in self.message_handlers[agent_name]:
                    try:
                        await handler(message)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
            
            return message
            
        except asyncio.TimeoutError:
            return None
    
    def register_message_handler(
        self,
        agent_name: str,
        handler: Callable
    ) -> bool:
        """
        Register a message handler for an agent.
        
        Args:
            agent_name: Name of the agent
            handler: Handler function
            
        Returns:
            True if registered successfully
        """
        if agent_name not in self.message_handlers:
            logger.error(f"Agent {agent_name} not registered")
            return False
        
        self.message_handlers[agent_name].append(handler)
        logger.debug(f"Registered message handler for {agent_name}")
        return True
    
    def register_broadcast_handler(self, handler: Callable) -> None:
        """
        Register a handler for broadcast messages.
        
        Args:
            handler: Handler function
        """
        self.broadcast_handlers.append(handler)
        logger.debug("Registered broadcast handler")
    
    def get_message_history(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Message]:
        """
        Get message history.
        
        Args:
            agent_name: Optional agent name to filter by
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        messages = self.message_history
        
        if agent_name:
            messages = [
                msg for msg in messages
                if msg.sender == agent_name or msg.recipient == agent_name
            ]
        
        return messages[-limit:]
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Status dictionary or None if not found
        """
        if agent_name not in self.registered_agents:
            return None
        
        registration = self.registered_agents[agent_name]
        queue_size = self.message_queues[agent_name].qsize()
        
        return {
            'name': agent_name,
            'capabilities': registration.capabilities,
            'status': registration.status,
            'registered_at': registration.registered_at,
            'pending_messages': queue_size,
            'metadata': registration.metadata
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.
        
        Returns:
            System status dictionary
        """
        return {
            'total_agents': len(self.registered_agents),
            'active_agents': len([
                a for a in self.registered_agents.values()
                if a.status == 'active'
            ]),
            'total_messages': len(self.message_history),
            'pending_responses': len(self.pending_responses),
            'agents': list(self.registered_agents.keys())
        }


class AgentCoordinatorEnhanced:
    """
    Enhanced agent coordinator with communication bus integration.
    """
    
    def __init__(self, communication_bus: AgentCommunicationBus):
        """
        Initialize enhanced coordinator.
        
        Args:
            communication_bus: Communication bus instance
        """
        self.communication_bus = communication_bus
        self.agents: Dict[str, Any] = {}  # Agent instances
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_name
        
        logger.info("Initialized AgentCoordinatorEnhanced")
    
    def register_agent_instance(
        self,
        agent: Any,
        capabilities: List[str]
    ) -> bool:
        """
        Register an agent instance with the coordinator.
        
        Args:
            agent: Agent instance
            capabilities: List of capabilities
            
        Returns:
            True if registered successfully
        """
        agent_name = agent.name
        self.agents[agent_name] = agent
        
        # Register with communication bus
        return self.communication_bus.register_agent(
            agent_name,
            capabilities,
            status="active"
        )
    
    async def delegate_task(
        self,
        task: Any,
        required_capability: Optional[str] = None
    ) -> Optional[str]:
        """
        Delegate a task to an appropriate agent.
        
        Args:
            task: Task to delegate
            required_capability: Optional required capability
            
        Returns:
            Name of assigned agent or None
        """
        # Discover suitable agents
        suitable_agents = self.communication_bus.discover_agents(
            capability=required_capability,
            status="active"
        )
        
        if not suitable_agents:
            logger.warning(f"No suitable agents found for capability: {required_capability}")
            return None
        
        # Select best agent (simple: first available)
        selected_agent = suitable_agents[0].agent_name
        
        # Send task assignment message
        await self.communication_bus.send_message(
            sender="coordinator",
            recipient=selected_agent,
            content={
                'action': 'assign_task',
                'task': task
            },
            message_type=MessageType.REQUEST
        )
        
        self.task_assignments[task.id] = selected_agent
        
        logger.info(f"Delegated task {task.id} to agent {selected_agent}")
        return selected_agent
    
    async def request_collaboration(
        self,
        requesting_agent: str,
        target_agent: str,
        collaboration_type: str,
        context: Dict[str, Any]
    ) -> Optional[Message]:
        """
        Request collaboration between agents.
        
        Args:
            requesting_agent: Name of requesting agent
            target_agent: Name of target agent
            collaboration_type: Type of collaboration
            context: Collaboration context
            
        Returns:
            Response message or None
        """
        response = await self.communication_bus.send_message(
            sender=requesting_agent,
            recipient=target_agent,
            content={
                'action': 'collaboration_request',
                'collaboration_type': collaboration_type,
                'context': context
            },
            message_type=MessageType.REQUEST,
            requires_response=True,
            response_timeout=60.0
        )
        
        return response
    
    async def broadcast_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> int:
        """
        Broadcast an event to all agents.
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Number of agents notified
        """
        return await self.communication_bus.broadcast_message(
            sender="coordinator",
            content={
                'event_type': event_type,
                'event_data': event_data
            }
        )
    
    def get_coordination_status(self) -> Dict[str, Any]:
        """Get coordination status."""
        return {
            'registered_agents': len(self.agents),
            'active_tasks': len(self.task_assignments),
            'system_status': self.communication_bus.get_system_status()
        }
