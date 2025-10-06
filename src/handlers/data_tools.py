#!/usr/bin/env python3
"""
Data Processing Tools for MCP Server
"""

import json
import csv
from typing import Dict, Any, List
from .base_tool import MCPTool

class CalculatorTool(MCPTool):
    """Tool for mathematical calculations"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations"
        )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3')"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    
    async def execute(self, expression: str) -> Dict[str, Any]:
        """Execute calculation"""
        try:
            # Basic safety check - only allow certain characters
            allowed_chars = set('0123456789+-*/()., ')
            if not all(c in allowed_chars for c in expression):
                self.log_call(False, "Invalid characters in expression")
                return {
                    "success": False,
                    "error": "Expression contains invalid characters"
                }
            
            result = eval(expression)
            self.log_call(True)
            return {
                "success": True,
                "expression": expression,
                "result": result
            }
            
        except Exception as e:
            error_msg = f"Calculation error: {str(e)}"
            self.log_call(False, error_msg)
            return {
                "success": False,
                "error": error_msg
            }

class JSONProcessorTool(MCPTool):
    """Tool for JSON data processing"""
    
    def __init__(self):
        super().__init__(
            name="json_processor",
            description="Process and manipulate JSON data"
        )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "json_data": {
                            "type": "string",
                            "description": "JSON string to process"
                        },
                        "operation": {
                            "type": "string",
                            "enum": ["validate", "format", "extract_keys", "count_items"],
                            "description": "Operation to perform on JSON data"
                        },
                        "key_path": {
                            "type": "string",
                            "description": "Dot notation path for key extraction (e.g., 'user.name')",
                            "default": ""
                        }
                    },
                    "required": ["json_data", "operation"]
                }
            }
        }
    
    async def execute(self, json_data: str, operation: str, key_path: str = "") -> Dict[str, Any]:
        """Execute JSON processing"""
        try:
            # Parse JSON
            data = json.loads(json_data)
            
            if operation == "validate":
                result = {"valid": True, "message": "JSON is valid"}
            
            elif operation == "format":
                result = {"formatted": json.dumps(data, indent=2)}
            
            elif operation == "extract_keys":
                if isinstance(data, dict):
                    result = {"keys": list(data.keys())}
                else:
                    result = {"keys": [], "message": "Data is not a dictionary"}
            
            elif operation == "count_items":
                if isinstance(data, dict):
                    result = {"count": len(data), "type": "dictionary"}
                elif isinstance(data, list):
                    result = {"count": len(data), "type": "list"}
                else:
                    result = {"count": 1, "type": type(data).__name__}
            
            else:
                result = {"error": f"Unknown operation: {operation}"}
            
            self.log_call(True)
            return {
                "success": True,
                "operation": operation,
                "result": result
            }
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {str(e)}"
            self.log_call(False, error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            self.log_call(False, error_msg)
            return {
                "success": False,
                "error": error_msg
            }

def register_tools(server):
    """Register data processing tools with the MCP server."""
    calc_tool = CalculatorTool()
    json_tool = JSONProcessorTool()

    @server.tool(name=calc_tool.name)
    async def calculator(expression: str):
        """Perform mathematical calculations."""
        return await calc_tool.execute(expression=expression)

    @server.tool(name=json_tool.name)
    async def json_processor(json_data: str, operation: str, key_path: str = ""):
        """Process and manipulate JSON data."""
        return await json_tool.execute(json_data=json_data, operation=operation, key_path=key_path)