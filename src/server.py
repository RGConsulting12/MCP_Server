#!/usr/bin/env python3
"""MCP Server Implementation (Extended)"""

import asyncio
import logging
import sys
import importlib
import pkgutil
import handlers
from mcp.server import Server
from mcp.server.models import InitializationOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPServer:
    """Model Context Protocol Server"""
    
    def __init__(self, environment: str = "dev"):
        self.environment = environment
        self.server = Server(name="mcp-server")
        self.registered_tools = {}
        logger.info(f"Initializing MCP Server in {environment} mode")
        
        # Add tool decorator to server
        self.server.tool = self.tool_decorator

    def tool_decorator(self, name: str):
        """Decorator to register tools"""
        def decorator(func):
            self.registered_tools[name] = func
            return func
        return decorator

    def register_all_tools(self):
        """Auto-discover and register all tools in the handlers directory."""
        for _, module_name, _ in pkgutil.iter_modules(handlers.__path__):
            if module_name == "__init__":
                continue
            try:
                module = importlib.import_module(f"handlers.{module_name}")
                if hasattr(module, "register_tools"):
                    module.register_tools(self.server)
                    logger.info(f"✅ Registered tools from {module_name}")
                else:
                    logger.warning(f"⚠️  {module_name} has no register_tools()")
            except Exception as e:
                logger.error(f"❌ Error registering {module_name}: {e}")

    def list_tools(self):
        """List all registered tools"""
        return list(self.registered_tools.keys())

    async def run(self):
        """Run the MCP server"""
        self.register_all_tools()
        
        logger.info(f"Starting MCP Server with {len(self.registered_tools)} tools...")
        for tool_name in self.registered_tools:
            logger.info(f"  - {tool_name}")

        logger.info("MCP Server event loop ready (air-gapped mode)")
        # For air-gapped mode, we don't need the full MCP protocol
        # Just keep the server running for local tool access
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("MCP Server terminated by user.")

def main():
    """Main entry point"""
    environment = sys.argv[1] if len(sys.argv) > 1 else "dev"
    mcp_server = MCPServer(environment)
    asyncio.run(mcp_server.run())

if __name__ == "__main__":
    main()

