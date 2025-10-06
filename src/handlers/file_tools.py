#!/usr/bin/env python3
"""
File Operation Tools for MCP Server
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from .base_tool import MCPTool

class FileReaderTool(MCPTool):
    """Tool to read file contents"""
    
    def __init__(self):
        super().__init__(
            name="file_reader",
            description="Read contents of a text file"
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
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "Maximum number of lines to read (optional)",
                            "default": 100
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
    
    async def execute(self, file_path: str, max_lines: int = 100) -> Dict[str, Any]:
        """Execute file reading"""
        try:
            if not os.path.exists(file_path):
                self.log_call(False, f"File not found: {file_path}")
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:max_lines]
                content = ''.join(lines)
            
            self.log_call(True)
            return {
                "success": True,
                "content": content,
                "lines_read": len(lines),
                "file_size": os.path.getsize(file_path)
            }
            
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.log_call(False, error_msg)
            return {
                "success": False,
                "error": error_msg
            }

class FileWriterTool(MCPTool):
    """Tool to write content to files"""
    
    def __init__(self):
        super().__init__(
            name="file_writer",
            description="Write content to a text file"
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
                        "file_path": {
                            "type": "string",
                            "description": "Path where to write the file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        },
                        "append": {
                            "type": "boolean",
                            "description": "Whether to append to existing file",
                            "default": False
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        }
    
    async def execute(self, file_path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """Execute file writing"""
        try:
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            self.log_call(True)
            return {
                "success": True,
                "message": f"Successfully {'appended to' if append else 'wrote'} {file_path}",
                "bytes_written": len(content.encode('utf-8'))
            }
            
        except Exception as e:
            error_msg = f"Error writing file: {str(e)}"
            self.log_call(False, error_msg)
            return {
                "success": False,
                "error": error_msg
            }

def register_tools(server):
    """Register FileReaderTool and FileWriterTool with the MCP server."""
    reader_tool = FileReaderTool()
    writer_tool = FileWriterTool()

    @server.tool(name=reader_tool.name)
    async def file_reader(file_path: str, max_lines: int = 100):
        """Read file contents (delegates to FileReaderTool)."""
        return await reader_tool.execute(file_path=file_path, max_lines=max_lines)

    @server.tool(name=writer_tool.name)
    async def file_writer(file_path: str, content: str, append: bool = False):
        """Write content to a file (delegates to FileWriterTool)."""
        return await writer_tool.execute(file_path=file_path, content=content, append=append)

