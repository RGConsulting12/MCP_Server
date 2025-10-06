#!/usr/bin/env python3
"""
Base Tool Class for MCP Server
All tools inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class MCPTool(ABC):
    """Base class for all MCP tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.call_count = 0
        self.last_called = None
        self.errors = []
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return the tool's JSON schema"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    def log_call(self, success: bool = True, error: str = None):
        """Log tool usage"""
        self.call_count += 1
        self.last_called = datetime.now()
        if not success and error:
            self.errors.append({
                "time": self.last_called,
                "error": error
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        return {
            "name": self.name,
            "call_count": self.call_count,
            "last_called": self.last_called.isoformat() if self.last_called else None,
            "error_count": len(self.errors),
            "recent_errors": self.errors[-3:] if self.errors else []
        }
