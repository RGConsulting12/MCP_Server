#!/usr/bin/env python3
"""
Simplified Air-Gapped MCP Server for Local Use
"""

import asyncio
import logging
import sys
import importlib
import pkgutil
from typing import Dict, Any, List
import handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleToolRegistry:
    """Simple tool registry for air-gapped operation"""
    
    def __init__(self):
        self.tools = {}
        self.tool_schemas = {}
    
    def register_tool(self, tool_instance):
        """Register a tool instance"""
        self.tools[tool_instance.name] = tool_instance
        self.tool_schemas[tool_instance.name] = tool_instance.get_schema()
        logger.info(f"✅ Registered tool: {tool_instance.name}")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools"""
        return [
            {
                "name": name,
                "description": tool.description,
                "schema": self.tool_schemas[name]
            }
            for name, tool in self.tools.items()
        ]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name"""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        try:
            return await self.tools[tool_name].execute(**kwargs)
        except Exception as e:
            return {"success": False, "error": f"Tool execution error: {str(e)}"}

class AirGappedMCPServer:
    """Air-gapped MCP Server for local operation"""
    
    def __init__(self, environment: str = "dev"):
        self.environment = environment
        self.registry = SimpleToolRegistry()
        logger.info(f"Initializing Air-Gapped MCP Server in {environment} mode")

    def register_all_tools(self):
        """Auto-discover and register all tools in the handlers directory."""
        for _, module_name, _ in pkgutil.iter_modules(handlers.__path__):
            if module_name in ["__init__", "base_tool"]:
                continue
            
            try:
                module = importlib.import_module(f"handlers.{module_name}")
                
                # Look for tool classes that inherit from MCPTool
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        hasattr(attr, '__bases__') and 
                        any('MCPTool' in str(base) for base in attr.__bases__)):
                        
                        try:
                            tool_instance = attr()
                            self.registry.register_tool(tool_instance)
                        except Exception as e:
                            logger.warning(f"⚠️  Could not instantiate {attr_name}: {e}")
                            
            except Exception as e:
                logger.error(f"❌ Error loading module {module_name}: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools"""
        return self.registry.list_tools()
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool"""
        return await self.registry.execute_tool(tool_name, **kwargs)
    
    def print_summary(self):
        """Print server summary"""
        tools = self.list_tools()
        print(f"\n🚀 Air-Gapped MCP Server Ready!")
        print(f"📊 Environment: {self.environment}")
        print(f"🔧 Registered Tools: {len(tools)}")
        
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
        
        print(f"\n💡 This server works completely offline with local tools only.")
        print(f"🔒 No external API calls will be made.")

def main():
    """Main entry point for air-gapped server"""
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"
    server = AirGappedMCPServer(environment)
    server.register_all_tools()
    server.print_summary()
    
    # For testing, you can add interactive mode here
    print(f"\n🧪 Server initialized successfully!")
    return server

if __name__ == "__main__":
    server = main()
