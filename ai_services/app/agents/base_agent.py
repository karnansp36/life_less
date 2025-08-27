from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

class BaseAgent(ABC):
    def __init__(self, name: str, role: str, expertise: List[str]):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.memory = {}
        self.active = True
    
    @abstractmethod
    async def process_request(
        self, 
        request: Dict[str, Any], 
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process a request and return response"""
        pass
    
    async def can_handle(self, request: Dict[str, Any]) -> bool:
        """Determine if this agent can handle the request"""
        request_type = request.get('type', '')
        return request_type in self.expertise
    
    def update_memory(self, key: str, value: Any):
        """Update agent's memory"""
        self.memory[key] = {
            'value': value,
            'timestamp': datetime.now()
        }
    
    def get_memory(self, key: str) -> Optional[Any]:
        """Retrieve from agent's memory"""
        memory_item = self.memory.get(key)
        return memory_item['value'] if memory_item else None