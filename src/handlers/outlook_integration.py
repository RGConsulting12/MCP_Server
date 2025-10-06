#!/usr/bin/env python3
"""
Real Microsoft Outlook Integration
Uses Microsoft Graph API for email and calendar
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
from .base_tool import MCPTool

class OutlookIntegrationTool(MCPTool):
    """Real Outlook integration using Microsoft Graph API"""
    
    def __init__(self):
        super().__init__(
            name="outlook_integration",
            description="Real Microsoft Outlook email and calendar integration"
        )
        self.client_id = os.getenv('OUTLOOK_CLIENT_ID')
        self.client_secret = os.getenv('OUTLOOK_CLIENT_SECRET') 
        self.tenant_id = os.getenv('OUTLOOK_TENANT_ID')
        self.access_token = None
        
    async def _get_access_token(self) -> str:
        """Get OAuth2 access token for Microsoft Graph"""
        if self.access_token:
            return self.access_token
            
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                return self.access_token
            else:
                raise Exception(f"Failed to get access token: {response.text}")
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute Outlook operations"""
        try:
            token = await self._get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            if operation == "read_emails":
                return await self._read_emails(headers, kwargs.get('folder', 'inbox'), kwargs.get('limit', 10))
            elif operation == "send_email":
                return await self._send_email(headers, kwargs)
            elif operation == "create_meeting":
                return await self._create_meeting(headers, kwargs)
            elif operation == "get_calendar_events":
                return await self._get_calendar_events(headers, kwargs.get('days_ahead', 7))
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            error_msg = f"Outlook operation error: {str(e)}"
            self.log_call(False, error_msg)
            return {"success": False, "error": error_msg}
    
    async def _read_emails(self, headers: Dict, folder: str, limit: int):
        """Read emails from Outlook"""
        url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder}/messages"
        params = {'$top': limit, '$select': 'subject,from,receivedDateTime,bodyPreview'}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                emails = []
                for email in data.get('value', []):
                    emails.append({
                        'subject': email.get('subject', ''),
                        'from': email.get('from', {}).get('emailAddress', {}).get('address', ''),
                        'received': email.get('receivedDateTime', ''),
                        'preview': email.get('bodyPreview', '')[:200]
                    })
                
                self.log_call(True)
                return {
                    "success": True,
                    "operation": "read_emails",
                    "emails": emails,
                    "count": len(emails)
                }
            else:
                raise Exception(f"Failed to read emails: {response.text}")
    
    async def _send_email(self, headers: Dict, email_data: Dict):
        """Send email via Outlook"""
        url = "https://graph.microsoft.com/v1.0/me/sendMail"
        
        message = {
            "message": {
                "subject": email_data.get('subject', ''),
                "body": {
                    "contentType": "Text",
                    "content": email_data.get('body', '')
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": recipient
                        }
                    } for recipient in email_data.get('to', [])
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=message)
            if response.status_code == 202:
                self.log_call(True)
                return {
                    "success": True,
                    "operation": "send_email",
                    "message": "Email sent successfully"
                }
            else:
                raise Exception(f"Failed to send email: {response.text}")
    
    async def _create_meeting(self, headers: Dict, meeting_data: Dict):
        """Create calendar meeting in Outlook"""
        url = "https://graph.microsoft.com/v1.0/me/events"
        
        event = {
            "subject": meeting_data.get('title', ''),
            "body": {
                "contentType": "HTML",
                "content": meeting_data.get('description', '')
            },
            "start": {
                "dateTime": meeting_data.get('start_time'),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": meeting_data.get('end_time'),
                "timeZone": "UTC"
            },
            "attendees": [
                {
                    "emailAddress": {
                        "address": attendee,
                        "name": attendee
                    },
                    "type": "required"
                } for attendee in meeting_data.get('attendees', [])
            ]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=event)
            if response.status_code == 201:
                event_data = response.json()
                self.log_call(True)
                return {
                    "success": True,
                    "operation": "create_meeting",
                    "event_id": event_data.get('id'),
                    "web_link": event_data.get('webLink'),
                    "message": "Meeting created successfully"
                }
            else:
                raise Exception(f"Failed to create meeting: {response.text}")

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
                                "enum": ["read_emails", "send_email", "create_meeting", "get_calendar_events"],
                                "description": "Outlook operation to perform"
                            },
                            "folder": {
                                "type": "string",
                                "description": "Email folder (for read_emails)",
                                "default": "inbox"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of items to retrieve",
                                "default": 10
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject (for send_email)"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body (for send_email)"
                            },
                            "to": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Recipients (for send_email)"
                            },
                            "title": {
                                "type": "string",
                                "description": "Meeting title (for create_meeting)"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Meeting start time ISO format (for create_meeting)"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "Meeting end time ISO format (for create_meeting)"
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Meeting attendees (for create_meeting)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Meeting description (for create_meeting)"
                            },
                            "days_ahead": {
                                "type": "integer",
                                "description": "Days ahead to get events (for get_calendar_events)",
                                "default": 7
                            }
                        },
                        "required": ["operation"]
                    }
                }
            }

def register_tools(server):
    """Register OutlookIntegrationTool with the MCP server."""
    outlook_tool = OutlookIntegrationTool()

    @server.tool(name=outlook_tool.name)
    async def outlook_integration(operation: str, **kwargs):
        """Microsoft Outlook integration."""
        return await outlook_tool.execute(operation=operation, **kwargs)