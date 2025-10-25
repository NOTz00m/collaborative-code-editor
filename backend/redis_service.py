"""
Redis pub/sub service for broadcasting messages across multiple server instances.
"""
import json
import asyncio
from typing import Callable, Optional, Dict, Any
import redis.asyncio as redis
from config import settings


class RedisPubSub:
    """
    Redis pub/sub service for scalable message broadcasting.
    Allows multiple backend instances to communicate.
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.listeners: Dict[str, Callable] = {}
        self._running = False
    
    async def connect(self) -> None:
        """Connect to Redis server."""
        try:
            self.redis_client = await redis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            print(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        self._running = False
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        print("Disconnected from Redis")
    
    async def subscribe(self, channel: str, handler: Callable) -> None:
        """
        Subscribe to a channel with a message handler.
        
        Args:
            channel: Channel name to subscribe to
            handler: Async function to handle messages
        """
        if not self.pubsub:
            raise RuntimeError("Not connected to Redis")
        
        await self.pubsub.subscribe(channel)
        self.listeners[channel] = handler
        print(f"Subscribed to channel: {channel}")
    
    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel."""
        if not self.pubsub:
            return
        
        await self.pubsub.unsubscribe(channel)
        self.listeners.pop(channel, None)
        print(f"Unsubscribed from channel: {channel}")
    
    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name to publish to
            message: Message data (will be JSON serialized)
        """
        if not self.redis_client:
            raise RuntimeError("Not connected to Redis")
        
        try:
            message_str = json.dumps(message)
            await self.redis_client.publish(channel, message_str)
        except Exception as e:
            print(f"Error publishing message: {e}")
    
    async def listen(self) -> None:
        """
        Listen for messages on subscribed channels.
        This should run as a background task.
        """
        if not self.pubsub:
            raise RuntimeError("Not connected to Redis")
        
        self._running = True
        print("Started listening for Redis messages")
        
        try:
            async for message in self.pubsub.listen():
                if not self._running:
                    break
                
                if message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    handler = self.listeners.get(channel)
                    if handler:
                        try:
                            parsed_data = json.loads(data)
                            await handler(channel, parsed_data)
                        except json.JSONDecodeError:
                            print(f"Invalid JSON in message from {channel}")
                        except Exception as e:
                            print(f"Error handling message from {channel}: {e}")
        except asyncio.CancelledError:
            print("Redis listener cancelled")
        except Exception as e:
            print(f"Error in Redis listener: {e}")
    
    async def store_document(self, room_id: str, content: str) -> None:
        """Store document content in Redis."""
        if not self.redis_client:
            return
        
        try:
            key = f"document:{room_id}"
            await self.redis_client.set(key, content, ex=86400)  # 24 hour expiry
        except Exception as e:
            print(f"Error storing document: {e}")
    
    async def get_document(self, room_id: str) -> Optional[str]:
        """Retrieve document content from Redis."""
        if not self.redis_client:
            return None
        
        try:
            key = f"document:{room_id}"
            content = await self.redis_client.get(key)
            return content
        except Exception as e:
            print(f"Error retrieving document: {e}")
            return None


# Global Redis pub/sub instance
redis_pubsub = RedisPubSub()
