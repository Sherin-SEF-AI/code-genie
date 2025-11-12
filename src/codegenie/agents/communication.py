"""
Agent communication system for inter-agent messaging and coordination.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages that can be sent between agents."""
    
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    STATUS_UPDATE = "status_update"
    BROADCAST = "broadcast"
    DIRECT_MESSAGE = "direct_message"
    ERROR_NOTIFICATION = "error_notification"


class MessagePriority(Enum):
    """Message priority levels."""
    
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """Represents a message between agents."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    sender: str = ""
    recipient: str = ""  # Empty string for broadcast messages
    message_type: MessageType = MessageType.DIRECT_MESSAGE
    priority: MessagePriority = MessagePriority.NORMAL
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    requires_response: bool = False
    response_timeout: Optional[float] = None
    correlation_id: Optional[str] = None  # For linking request/response pairs


@dataclass
class MessageHandler:
    """Handler for processing specific message types."""
    
    message_type: MessageType
    handler_func: Callable[[Message], Any]
    agent_name: str


class AgentCommunicationBus:
    """Central communication bus for agent messaging."""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}  # agent_name -> agent_instance
        self.message_handlers: Dict[str, Dict[MessageType, MessageHandler]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.broadcast_subscribers: Set[str] = set()
        self.message_history: List[Message] = []
        self.running = False
        self.processor_task: Optional[asyncio.Task] = None
        
        logger.info("Initialized AgentCommunicationBus")
    
    async def start(self) -> None:
        """Start the communication bus."""
        if self.running:
            return
        
        self.running = True
        self.processor_task = asyncio.create_task(self._process_messages())
        logger.info("Started AgentCommunicationBus")
    
    async def stop(self) -> None:
        """Stop the communication bus."""
        if not self.running:
            return
        
        self.running = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped AgentCommunicationBus")
    
    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """
        Register an agent with the communication bus.
        
        Args:
            agent_name: Name of the agent
            agent_instance: The agent instance
        """
        self.agents[agent_name] = agent_instance
        self.message_handlers[agent_name] = {}
        logger.info(f"Registered agent: {agent_name}")
    
    def unregister_agent(self, agent_name: str) -> None:
        """
        Unregister an agent from the communication bus.
        
        Args:
            agent_name: Name of the agent to unregister
        """
        self.agents.pop(agent_name, None)
        self.message_handlers.pop(agent_name, None)
        self.broadcast_subscribers.discard(agent_name)
        logger.info(f"Unregistered agent: {agent_name}")
    
    def register_message_handler(
        self,
        agent_name: str,
        message_type: MessageType,
        handler_func: Callable[[Message], Any]
    ) -> None:
        """
        Register a message handler for an agent.
        
        Args:
            agent_name: Name of the agent
            message_type: Type of message to handle
            handler_func: Function to handle the message
        """
        if agent_name not in self.message_handlers:
            self.message_handlers[agent_name] = {}
        
        handler = MessageHandler(
            message_type=message_type,
            handler_func=handler_func,
            agent_name=agent_name
        )
        
        self.message_handlers[agent_name][message_type] = handler
        logger.debug(f"Registered handler for {agent_name}: {message_type.value}")
    
    def subscribe_to_broadcasts(self, agent_name: str) -> None:
        """
        Subscribe an agent to broadcast messages.
        
        Args:
            agent_name: Name of the agent to subscribe
        """
        self.broadcast_subscribers.add(agent_name)
        logger.debug(f"Agent {agent_name} subscribed to broadcasts")
    
    def unsubscribe_from_broadcasts(self, agent_name: str) -> None:
        """
        Unsubscribe an agent from broadcast messages.
        
        Args:
            agent_name: Name of the agent to unsubscribe
        """
        self.broadcast_subscribers.discard(agent_name)
        logger.debug(f"Agent {agent_name} unsubscribed from broadcasts")
    
    async def send_message(self, message: Message) -> bool:
        """
        Send a message through the communication bus.
        
        Args:
            message: The message to send
            
        Returns:
            True if message was queued successfully, False otherwise
        """
        try:
            # Validate message
            if not message.sender:
                logger.error("Message sender cannot be empty")
                return False
            
            if message.sender not in self.agents:
                logger.error(f"Sender agent {message.sender} not registered")
                return False
            
            # For non-broadcast messages, validate recipient
            if message.message_type != MessageType.BROADCAST:
                if not message.recipient:
                    logger.error("Non-broadcast message must have a recipient")
                    return False
                
                if message.recipient not in self.agents:
                    logger.error(f"Recipient agent {message.recipient} not registered")
                    return False
            
            # Queue the message
            await self.message_queue.put(message)
            logger.debug(f"Queued message from {message.sender} to {message.recipient or 'broadcast'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def send_direct_message(
        self,
        sender: str,
        recipient: str,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_response: bool = False,
        response_timeout: Optional[float] = None
    ) -> bool:
        """
        Send a direct message between agents.
        
        Args:
            sender: Name of the sending agent
            recipient: Name of the receiving agent
            content: Message content
            priority: Message priority
            requires_response: Whether a response is required
            response_timeout: Timeout for response (if required)
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        message = Message(
            sender=sender,
            recipient=recipient,
            message_type=MessageType.DIRECT_MESSAGE,
            priority=priority,
            content=content,
            requires_response=requires_response,
            response_timeout=response_timeout
        )
        
        return await self.send_message(message)
    
    async def broadcast_message(
        self,
        sender: str,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> bool:
        """
        Broadcast a message to all subscribed agents.
        
        Args:
            sender: Name of the sending agent
            content: Message content
            priority: Message priority
            
        Returns:
            True if message was broadcast successfully, False otherwise
        """
        message = Message(
            sender=sender,
            recipient="",  # Empty for broadcast
            message_type=MessageType.BROADCAST,
            priority=priority,
            content=content
        )
        
        return await self.send_message(message)
    
    async def request_collaboration(
        self,
        sender: str,
        recipient: str,
        task_description: str,
        collaboration_type: str,
        context: Dict[str, Any] = None,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Request collaboration from another agent.
        
        Args:
            sender: Name of the requesting agent
            recipient: Name of the target agent
            task_description: Description of the task
            collaboration_type: Type of collaboration needed
            context: Additional context
            timeout: Response timeout
            
        Returns:
            Collaboration response or None if failed/timeout
        """
        content = {
            "task_description": task_description,
            "collaboration_type": collaboration_type,
            "context": context or {}
        }
        
        message = Message(
            sender=sender,
            recipient=recipient,
            message_type=MessageType.COLLABORATION_REQUEST,
            priority=MessagePriority.HIGH,
            content=content,
            requires_response=True,
            response_timeout=timeout
        )
        
        success = await self.send_message(message)
        if not success:
            return None
        
        # Wait for response
        try:
            response = await asyncio.wait_for(
                self._wait_for_response(message.id),
                timeout=timeout
            )
            return response.content if response else None
            
        except asyncio.TimeoutError:
            logger.warning(f"Collaboration request from {sender} to {recipient} timed out")
            return None
    
    async def _process_messages(self) -> None:
        """Process messages from the queue."""
        logger.info("Started message processor")
        
        while self.running:
            try:
                # Get message with timeout to allow checking running status
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                await self._handle_message(message)
                
            except asyncio.TimeoutError:
                # Normal timeout, continue loop
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: Message) -> None:
        """
        Handle a single message.
        
        Args:
            message: The message to handle
        """
        try:
            # Add to history
            self.message_history.append(message)
            
            # Handle broadcast messages
            if message.message_type == MessageType.BROADCAST:
                await self._handle_broadcast_message(message)
                return
            
            # Handle direct messages
            recipient = message.recipient
            if recipient not in self.message_handlers:
                logger.warning(f"No handlers registered for agent: {recipient}")
                return
            
            handlers = self.message_handlers[recipient]
            if message.message_type not in handlers:
                logger.warning(f"No handler for message type {message.message_type.value} in agent {recipient}")
                return
            
            # Execute handler
            handler = handlers[message.message_type]
            try:
                result = await self._execute_handler(handler.handler_func, message)
                
                # Send response if required
                if message.requires_response:
                    await self._send_response(message, result, success=True)
                    
            except Exception as e:
                logger.error(f"Handler error for {recipient}: {e}")
                
                # Send error response if required
                if message.requires_response:
                    await self._send_response(message, str(e), success=False)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _handle_broadcast_message(self, message: Message) -> None:
        """
        Handle broadcast messages.
        
        Args:
            message: The broadcast message
        """
        for subscriber in self.broadcast_subscribers:
            if subscriber == message.sender:
                continue  # Don't send to sender
            
            # Create individual message for each subscriber
            individual_message = Message(
                sender=message.sender,
                recipient=subscriber,
                message_type=message.message_type,
                priority=message.priority,
                content=message.content,
                timestamp=message.timestamp,
                correlation_id=message.id
            )
            
            await self._handle_message(individual_message)
    
    async def _execute_handler(self, handler_func: Callable, message: Message) -> Any:
        """
        Execute a message handler function.
        
        Args:
            handler_func: The handler function to execute
            message: The message to handle
            
        Returns:
            Result from the handler function
        """
        if asyncio.iscoroutinefunction(handler_func):
            return await handler_func(message)
        else:
            return handler_func(message)
    
    async def _send_response(self, original_message: Message, result: Any, success: bool) -> None:
        """
        Send a response to a message that requires one.
        
        Args:
            original_message: The original message being responded to
            result: The result to send back
            success: Whether the operation was successful
        """
        response_content = {
            "success": success,
            "result": result,
            "original_message_id": original_message.id
        }
        
        response_message = Message(
            sender=original_message.recipient,
            recipient=original_message.sender,
            message_type=MessageType.TASK_RESPONSE,
            content=response_content,
            correlation_id=original_message.id
        )
        
        await self.send_message(response_message)
    
    async def _wait_for_response(self, message_id: str) -> Optional[Message]:
        """
        Wait for a response to a specific message.
        
        Args:
            message_id: ID of the message to wait for response to
            
        Returns:
            Response message or None if not found
        """
        # This is a simplified implementation
        # In a real system, you'd want a more sophisticated response tracking mechanism
        start_time = time.time()
        timeout = 30.0  # Default timeout
        
        while time.time() - start_time < timeout:
            # Check recent messages for response
            for message in reversed(self.message_history[-100:]):  # Check last 100 messages
                if (message.correlation_id == message_id and 
                    message.message_type == MessageType.TASK_RESPONSE):
                    return message
            
            await asyncio.sleep(0.1)  # Small delay
        
        return None
    
    def get_agent_list(self) -> List[str]:
        """Get list of registered agents."""
        return list(self.agents.keys())
    
    def get_message_stats(self) -> Dict[str, Any]:
        """Get communication statistics."""
        total_messages = len(self.message_history)
        
        # Count by type
        type_counts = {}
        for message in self.message_history:
            msg_type = message.message_type.value
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        
        # Count by priority
        priority_counts = {}
        for message in self.message_history:
            priority = message.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            "total_messages": total_messages,
            "registered_agents": len(self.agents),
            "broadcast_subscribers": len(self.broadcast_subscribers),
            "message_types": type_counts,
            "message_priorities": priority_counts,
            "queue_size": self.message_queue.qsize(),
            "running": self.running
        }
    
    def clear_message_history(self, keep_recent: int = 100) -> None:
        """
        Clear message history, optionally keeping recent messages.
        
        Args:
            keep_recent: Number of recent messages to keep
        """
        if keep_recent > 0:
            self.message_history = self.message_history[-keep_recent:]
        else:
            self.message_history.clear()
        
        logger.info(f"Cleared message history, kept {len(self.message_history)} recent messages")