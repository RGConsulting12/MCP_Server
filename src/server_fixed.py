#!/usr/bin/env python3
"""MCP Server Implementation (Fixed)"""

import asyncio
import logging
import sys
import importlib
import pkgutil
import handlers
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServer:
    """Model Context Protocol Server"""
    
    def __init__(self, environment: str = "dev"):
        self.environment = environment
        self.server = Server(name="mcp-server")
        self.registered_tools = {}
        logger.info(f"Initializing MCP Server in {environment} mode")

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
                            self.register_tool(tool_instance)
                            logger.info(f"✅ Registered tool: {tool_instance.name}")
                        except Exception as e:
                            logger.warning(f"⚠️  Could not instantiate {attr_name}: {e}")
                            
            except Exception as e:
                logger.error(f"❌ Error loading module {module_name}: {e}")

    def register_tool(self, tool_instance):
        """Register a single tool instance"""
        self.registered_tools[tool_instance.name] = tool_instance
        
        # Create MCP Tool object
        schema = tool_instance.get_schema()
        mcp_tool = Tool(
            name=tool_instance.name,
            description=tool_instance.description,
            inputSchema=schema.get("function", {}).get("parameters", {})
        )
        
        # Register with server (this is the correct MCP way)
        @self.server.call_tool()
        async def handle_tool_call(name: str, arguments: dict):
            if name == tool_instance.name:
                return [TextContent(
                    type="text",
                    text=str(await tool_instance.execute(**arguments))
                )]
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    def list_tools(self):
        """List all registered tools"""
        return list(self.registered_tools.keys())

    async def run(self):
        """Run the MCP server"""
        self.register_all_tools()
        
        logger.info(f"Starting MCP Server with {len(self.registered_tools)} tools...")
        for tool_name in self.registered_tools:
            logger.info(f"  - {tool_name}")
        
        async with self.server.stdio_server() as (r, w):
            await self.server.run(r, w, InitializationOptions(
                server_name="mcp-server",
                server_version="1.0.0"
            ))

        logger.info("MCP Server terminated.")

def main():
    """Main entry point"""
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"
    mcp_server = MCPServer(environment)
    asyncio.run(mcp_server.run())

if __name__ == "__main__":
    main()
