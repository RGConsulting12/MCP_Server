#!/usr/bin/env python3
"""
Real Slack Integration using Slack Web API
"""

import os
import json
from typing import Dict, Any, List
import httpx
from .base_tool import MCPTool

class SlackRealTool(MCPTool):
    """Real Slack integration using Slack Web API"""
    
    def __init__(self):
        super().__init__(
            name="slack_real",
            description="Real Slack integration with Web API"
        )
        self.bot_token = os.getenv('SLACK_BOT_TOKEN')
        self.base_url = "https://slack.com/api"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["post_message", "read_messages", "get_channels", "upload_file"],
                            "description": "Slack operation to perform"
                        },
                        "channel": {
                            "type": "string",
                            "description": "Slack channel name or ID"
                        },
                        "message": {
                            "type": "string",
                            "description": "Message to post (for post_message)"
                        },
                        "username": {
                            "type": "string",
                            "description": "Bot username (for post_message)",
                            "default": "MCP Bot"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of messages to retrieve (for read_messages)",
                            "default": 10
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path to upload (for upload_file)"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute Slack operations"""
        try:
            headers = {
                'Authorization': f'Bearer {self.bot_token}',
                'Content-Type': 'application/json'
            }
            
            if operation == "post_message":
                return await self._post_message(headers, kwargs)
            elif operation == "read_messages":
                return await self._read_messages(headers, kwargs)
            elif operation == "get_channels":
                return await self._get_channels(headers)
            elif operation == "upload_file":
                return await self._upload_file(headers, kwargs)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            error_msg = f"Slack operation error: {str(e)}"
            self.log_call(False, error_msg)
            return {"success": False, "error": error_msg}
    
    async def _post_message(self, headers: Dict, data: Dict):
        """Post message to Slack channel"""
        url = f"{self.base_url}/chat.postMessage"
        
        payload = {
            "channel": data.get('channel'),
            "text": data.get('message'),
            "username": data.get('username', 'MCP Bot')
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            result = response.json()
            
            if result.get('ok'):
                self.log_call(True)
                return {
                    "success": True,
                    "operation": "post_message",
                    "message_ts": result.get('ts'),
                    "channel": result.get('channel')
                }
            else:
                raise Exception(f"Slack API error: {result.get('error')}")
    
    async def _read_messages(self, headers: Dict, data: Dict):
        """Read messages from Slack channel"""
        url = f"{self.base_url}/conversations.history"
        
        params = {
            "channel": data.get('channel'),
            "limit": data.get('limit', 10)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get('ok'):
                messages = []
                for msg in result.get('messages', []):
                    messages.append({
                        'text': msg.get('text', ''),
                        'user': msg.get('user', ''),
                        'timestamp': msg.get('ts', ''),
                        'type': msg.get('type', '')
                    })
                
                self.log_call(True)
                return {
                    "success": True,
                    "operation": "read_messages",
                    "messages": messages,
                    "count": len(messages)
                }
            else:
                raise Exception(f"Slack API error: {result.get('error')}")

    async def _get_channels(self, headers: Dict):
        """Get list of channels"""
        url = f"{self.base_url}/conversations.list"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            result = response.json()
            
            if result.get('ok'):
                channels = []
                for channel in result.get('channels', []):
                    channels.append({
                        'id': channel.get('id'),
                        'name': channel.get('name'),
                        'is_private': channel.get('is_private', False),
                        'is_member': channel.get('is_member', False)
                    })
                
                self.log_call(True)
                return {
                    "success": True,
                    "operation": "get_channels",
                    "channels": channels,
                    "count": len(channels)
                }
            else:
                raise Exception(f"Slack API error: {result.get('error')}")

    async def _upload_file(self, headers: Dict, data: Dict):
        """Upload file to Slack channel"""
        url = f"{self.base_url}/files.upload"
        
        file_path = data.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return {"success": False, "error": "File not found"}
        
        # For file upload, we need to use form data instead of JSON
        headers_copy = headers.copy()
        del headers_copy['Content-Type']  # Let httpx set the content type for multipart
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data_form = {
                'channels': data.get('channel', ''),
                'title': data.get('title', os.path.basename(file_path)),
                'initial_comment': data.get('comment', '')
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers_copy, files=files, data=data_form)
                result = response.json()
                
                if result.get('ok'):
                    self.log_call(True)
                    return {
                        "success": True,
                        "operation": "upload_file",
                        "file_id": result.get('file', {}).get('id'),
                        "file_url": result.get('file', {}).get('url_private')
                    }
                else:
                    raise Exception(f"Slack API error: {result.get('error')}")

def register_tools(server):
    """Register SlackRealTool with the MCP server."""
    slack_tool = SlackRealTool()

    @server.tool(name=slack_tool.name)
    async def slack_real(operation: str, **kwargs):
        """Real Slack integration with Web API."""
        return await slack_tool.execute(operation=operation, **kwargs)