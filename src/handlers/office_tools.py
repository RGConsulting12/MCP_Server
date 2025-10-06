#!/usr/bin/env python3
"""
Office Productivity Tools for MCP Server
Meeting summaries, email integration, Slack, calendar, PowerPoint automation
"""

import os
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List
import requests
from .base_tool import MCPTool

class MeetingSummarizerTool(MCPTool):
    """Tool to create meeting summaries from transcripts or notes"""
    
    def __init__(self):
        super().__init__(
            name="meeting_summarizer",
            description="Generate structured meeting summaries from transcripts or notes"
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
                        "meeting_content": {
                            "type": "string",
                            "description": "Raw meeting transcript or notes"
                        },
                        "meeting_title": {
                            "type": "string",
                            "description": "Title of the meeting"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of meeting attendees"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["structured", "bullet_points", "action_items", "executive"],
                            "description": "Summary format style",
                            "default": "structured"
                        }
                    },
                    "required": ["meeting_content", "meeting_title"]
                }
            }
        }
    
    async def execute(self, meeting_content: str, meeting_title: str, 
                     attendees: List[str] = None, format: str = "structured") -> Dict[str, Any]:
        """Execute meeting summarization"""
        try:
            # Extract key information
            lines = meeting_content.split('\n')
            
            # Simple keyword extraction for action items
            action_keywords = ['action:', 'todo:', 'follow up:', 'next steps:', 'assign']
            decisions_keywords = ['decided:', 'agreed:', 'conclusion:', 'resolution:']
            
            action_items = []
            decisions = []
            key_points = []
            
            for line in lines:
                line_lower = line.lower().strip()
                if any(keyword in line_lower for keyword in action_keywords):
                    action_items.append(line.strip())
                elif any(keyword in line_lower for keyword in decisions_keywords):
                    decisions.append(line.strip())
                elif len(line.strip()) > 20:  # Substantial content
                    key_points.append(line.strip())
            
            # Generate summary based on format
            if format == "structured":
                summary = self._generate_structured_summary(
                    meeting_title, attendees, key_points, decisions, action_items
                )
            elif format == "bullet_points":
                summary = self._generate_bullet_summary(key_points, action_items)
            elif format == "action_items":
                summary = self._generate_action_summary(action_items)
            elif format == "executive":
                summary = self._generate_executive_summary(
                    meeting_title, decisions, action_items
                )
            
            self.log_call(True)
            return {
                "success": True,
                "meeting_title": meeting_title,
                "summary": summary,
                "action_items_count": len(action_items),
                "decisions_count": len(decisions),
                "format": format
            }
            
        except Exception as e:
            error_msg = f"Summarization error: {str(e)}"
            self.log_call(False, error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _generate_structured_summary(self, title, attendees, points, decisions, actions):
        """Generate structured meeting summary"""
        summary = f"# Meeting Summary: {title}\n\n"
        summary += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        
        if attendees:
            summary += f"**Attendees:** {', '.join(attendees)}\n\n"
        
        summary += "## Key Discussion Points\n"
        for i, point in enumerate(points[:5], 1):  # Top 5 points
            summary += f"{i}. {point}\n"
        
        if decisions:
            summary += "\n## Decisions Made\n"
            for decision in decisions:
                summary += f"- {decision}\n"
        
        if actions:
            summary += "\n## Action Items\n"
            for action in actions:
                summary += f"- [ ] {action}\n"
        
        return summary
    
    def _generate_bullet_summary(self, points, actions):
        """Generate bullet point summary"""
        summary = "## Meeting Highlights\n"
        for point in points[:8]:
            summary += f"• {point}\n"
        
        if actions:
            summary += "\n## Next Steps\n"
            for action in actions:
                summary += f"→ {action}\n"
        
        return summary
    
    def _generate_action_summary(self, actions):
        """Generate action-focused summary"""
        if not actions:
            return "No specific action items identified in this meeting."
        
        summary = "## Action Items Summary\n\n"
        for i, action in enumerate(actions, 1):
            summary += f"**{i}.** {action}\n"
            summary += f"   - Status: Pending\n"
            summary += f"   - Due Date: TBD\n\n"
        
        return summary
    
    def _generate_executive_summary(self, title, decisions, actions):
        """Generate executive summary"""
        summary = f"## Executive Summary: {title}\n\n"
        summary += f"**Meeting Overview:** {len(decisions)} key decisions made, "
        summary += f"{len(actions)} action items identified.\n\n"
        
        if decisions:
            summary += "**Key Outcomes:**\n"
            for decision in decisions[:3]:  # Top 3 decisions
                summary += f"- {decision}\n"
        
        if actions:
            summary += f"\n**Critical Actions:** {len(actions)} items require follow-up.\n"
        
        return summary

class EmailIntegrationTool(MCPTool):
    """Tool for email operations - reading, sending, searching"""
    
    def __init__(self):
        super().__init__(
            name="email_integration",
            description="Read, send, and search emails via IMAP/SMTP"
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
                        "operation": {
                            "type": "string",
                            "enum": ["read_recent", "send_email", "search_emails", "get_unread"],
                            "description": "Email operation to perform"
                        },
                        "email_config": {
                            "type": "object",
                            "properties": {
                                "smtp_server": {"type": "string"},
                                "imap_server": {"type": "string"},
                                "email": {"type": "string"},
                                "password": {"type": "string"},
                                "port_smtp": {"type": "integer", "default": 587},
                                "port_imap": {"type": "integer", "default": 993}
                            },
                            "description": "Email server configuration"
                        },
                        "to_email": {
                            "type": "string",
                            "description": "Recipient email (for sending)"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject (for sending)"
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body (for sending)"
                        },
                        "search_query": {
                            "type": "string",
                            "description": "Search query for emails"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Number of emails to retrieve"
                        }
                    },
                    "required": ["operation", "email_config"]
                }
            }
        }
    
    async def execute(self, operation: str, email_config: Dict, **kwargs) -> Dict[str, Any]:
        """Execute email operations"""
        try:
            if operation == "read_recent":
                return await self._read_recent_emails(email_config, kwargs.get('limit', 10))
            elif operation == "send_email":
                return await self._send_email(
                    email_config, 
                    kwargs.get('to_email'), 
                    kwargs.get('subject'), 
                    kwargs.get('body')
                )
            elif operation == "search_emails":
                return await self._search_emails(
                    email_config, 
                    kwargs.get('search_query'), 
                    kwargs.get('limit', 10)
                )
            elif operation == "get_unread":
                return await self._get_unread_emails(email_config, kwargs.get('limit', 10))
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            error_msg = f"Email operation error: {str(e)}"
            self.log_call(False, error_msg)
            return {"success": False, "error": error_msg}
    
    async def _read_recent_emails(self, config: Dict, limit: int):
        """Read recent emails"""
        # Placeholder - would implement IMAP connection
        self.log_call(True)
        return {
            "success": True,
            "operation": "read_recent",
            "emails": [
                {
                    "subject": "Weekly Team Meeting",
                    "from": "manager@company.com",
                    "date": "2024-01-15",
                    "preview": "Hi team, let's schedule our weekly sync..."
                },
                {
                    "subject": "Project Update Required",
                    "from": "project@company.com", 
                    "date": "2024-01-14",
                    "preview": "Please provide status update on current tasks..."
                }
            ],
            "count": 2,
            "note": "Demo mode - replace with actual IMAP implementation"
        }
    
    async def _send_email(self, config: Dict, to_email: str, subject: str, body: str):
        """Send email"""
        # Placeholder - would implement SMTP sending
        self.log_call(True)
        return {
            "success": True,
            "operation": "send_email",
            "to": to_email,
            "subject": subject,
            "message": "Email sent successfully (demo mode)",
            "note": "Demo mode - replace with actual SMTP implementation"
        }

class SlackIntegrationTool(MCPTool):
    """Tool for Slack operations - reading messages, posting updates"""
    
    def __init__(self):
        super().__init__(
            name="slack_integration", 
            description="Read messages and post updates to Slack channels"
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
                        "operation": {
                            "type": "string",
                            "enum": ["read_messages", "post_message", "get_channels", "search_messages"],
                            "description": "Slack operation to perform"
                        },
                        "token": {
                            "type": "string",
                            "description": "Slack Bot Token"
                        },
                        "channel": {
                            "type": "string",
                            "description": "Slack channel name or ID"
                        },
                        "message": {
                            "type": "string",
                            "description": "Message to post (for posting)"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query (for searching)"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Number of messages to retrieve"
                        }
                    },
                    "required": ["operation", "token"]
                }
            }
        }
    
    async def execute(self, operation: str, token: str, **kwargs) -> Dict[str, Any]:
        """Execute Slack operations"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            if operation == "read_messages":
                return await self._read_messages(headers, kwargs.get('channel'), kwargs.get('limit', 10))
            elif operation == "post_message":
                return await self._post_message(headers, kwargs.get('channel'), kwargs.get('message'))
            elif operation == "get_channels":
                return await self._get_channels(headers)
            elif operation == "search_messages":
                return await self._search_messages(headers, kwargs.get('query'), kwargs.get('limit', 10))
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            error_msg = f"Slack operation error: {str(e)}"
            self.log_call(False, error_msg)
            return {"success": False, "error": error_msg}
    
    async def _read_messages(self, headers: Dict, channel: str, limit: int):
        """Read recent messages from channel"""
        # Placeholder - would make actual Slack API call
        self.log_call(True)
        return {
            "success": True,
            "operation": "read_messages",
            "channel": channel,
            "messages": [
                {
                    "user": "john.doe",
                    "text": "Great meeting today, thanks everyone!",
                    "timestamp": "2024-01-15T14:30:00Z"
                },
                {
                    "user": "jane.smith", 
                    "text": "Can we schedule a follow-up for next week?",
                    "timestamp": "2024-01-15T14:32:00Z"
                }
            ],
            "count": 2,
            "note": "Demo mode - replace with actual Slack API calls"
        }
    
    async def _post_message(self, headers: Dict, channel: str, message: str):
        """Post message to channel"""
        # Placeholder - would make actual Slack API call
        self.log_call(True)
        return {
            "success": True,
            "operation": "post_message",
            "channel": channel,
            "message": message,
            "result": "Message posted successfully (demo mode)",
            "note": "Demo mode - replace with actual Slack API calls"
        }

class CalendarTool(MCPTool):
    """Tool for calendar operations - creating meetings, checking availability"""
    
    def __init__(self):
        super().__init__(
            name="calendar_tool",
            description="Create meeting invites and manage calendar events"
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
                        "operation": {
                            "type": "string",
                            "enum": ["create_meeting", "check_availability", "list_events", "send_invite"],
                            "description": "Calendar operation to perform"
                        },
                        "title": {
                            "type": "string",
                            "description": "Meeting title"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Meeting start time (ISO format)"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "Meeting end time (ISO format)"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of attendee email addresses"
                        },
                        "description": {
                            "type": "string",
                            "description": "Meeting description/agenda"
                        },
                        "location": {
                            "type": "string",
                            "description": "Meeting location or video link"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute calendar operations"""
        try:
            if operation == "create_meeting":
                return await self._create_meeting(
                    kwargs.get('title'),
                    kwargs.get('start_time'),
                    kwargs.get('end_time'),
                    kwargs.get('attendees', []),
                    kwargs.get('description', ''),
                    kwargs.get('location', '')
                )
            elif operation == "send_invite":
                return await self._send_invite(
                    kwargs.get('title'),
                    kwargs.get('start_time'),
                    kwargs.get('attendees', [])
                )
            elif operation == "check_availability":
                return await self._check_availability(kwargs.get('start_time'), kwargs.get('end_time'))
            elif operation == "list_events":
                return await self._list_events()
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            error_msg = f"Calendar operation error: {str(e)}"
            self.log_call(False, error_msg)
            return {"success": False, "error": error_msg}
    
    async def _create_meeting(self, title: str, start_time: str, end_time: str, 
                            attendees: List[str], description: str, location: str):
        """Create a meeting event"""
        # Placeholder - would integrate with calendar API (Google Calendar, Outlook, etc.)
        self.log_call(True)
        
        meeting_data = {
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees,
            "description": description,
            "location": location,
            "meeting_id": f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        return {
            "success": True,
            "operation": "create_meeting",
            "meeting": meeting_data,
            "message": "Meeting created successfully (demo mode)",
            "note": "Demo mode - replace with actual calendar API integration"
        }
    
    async def _send_invite(self, title: str, start_time: str, attendees: List[str]):
        """Send meeting invitations"""
        self.log_call(True)
        return {
            "success": True,
            "operation": "send_invite",
            "title": title,
            "start_time": start_time,
            "attendees": attendees,
            "invites_sent": len(attendees),
            "message": "Invitations sent successfully (demo mode)",
            "note": "Demo mode - replace with actual email/calendar integration"
        }

class PowerPointTool(MCPTool):
    """Tool for PowerPoint automation via VBA/COM"""
    
    def __init__(self):
        super().__init__(
            name="powerpoint_tool",
            description="Create and manipulate PowerPoint presentations"
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
                        "operation": {
                            "type": "string",
                            "enum": ["create_presentation", "add_slide", "add_content", "save_presentation"],
                            "description": "PowerPoint operation to perform"
                        },
                        "title": {
                            "type": "string",
                            "description": "Presentation or slide title"
                        },
                        "content": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Content items for slides"
                        },
                        "template": {
                            "type": "string",
                            "enum": ["blank", "title_slide", "content_slide", "two_column"],
                            "description": "Slide template type",
                            "default": "blank"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path to save presentation"
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute PowerPoint operations"""
        try:
            if operation == "create_presentation":
                return await self._create_presentation(kwargs.get('title', 'New Presentation'))
            elif operation == "add_slide":
                return await self._add_slide(
                    kwargs.get('title'),
                    kwargs.get('content', []),
                    kwargs.get('template', 'blank')
                )
            elif operation == "save_presentation":
                return await self._save_presentation(kwargs.get('file_path'))
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            error_msg = f"PowerPoint operation error: {str(e)}"
            self.log_call(False, error_msg)
            return {"success": False, "error": error_msg}
    
    async def _create_presentation(self, title: str):
        """Create new PowerPoint presentation"""
        # Placeholder - would use COM automation or python-pptx
        self.log_call(True)
        return {
            "success": True,
            "operation": "create_presentation",
            "title": title,
            "presentation_id": f"ppt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "message": "Presentation created successfully (demo mode)",
            "note": "Demo mode - replace with actual PowerPoint COM automation or python-pptx"
        }
    
    async def _add_slide(self, title: str, content: List[str], template: str):
        """Add slide to presentation"""
        self.log_call(True)
        return {
            "success": True,
            "operation": "add_slide",
            "title": title,
            "content_items": len(content),
            "template": template,
            "slide_number": 1,  # Would track actual slide numbers
            "message": "Slide added successfully (demo mode)"
        }

def register_tools(server):
    """Register office productivity tools with the MCP server."""
    meeting_tool = MeetingSummarizerTool()
    email_tool = EmailIntegrationTool()
    slack_tool = SlackIntegrationTool()
    calendar_tool = CalendarTool()
    ppt_tool = PowerPointTool()

    @server.tool(name=meeting_tool.name)
    async def meeting_summarizer(meeting_content: str, meeting_title: str, 
                               attendees: list = None, format: str = "structured"):
        """Generate structured meeting summaries."""
        return await meeting_tool.execute(
            meeting_content=meeting_content, 
            meeting_title=meeting_title, 
            attendees=attendees, 
            format=format
        )

    @server.tool(name=email_tool.name)
    async def email_integration(operation: str, email_config: dict, **kwargs):
        """Email operations - reading, sending, searching."""
        return await email_tool.execute(operation=operation, email_config=email_config, **kwargs)

    @server.tool(name=slack_tool.name)
    async def slack_integration(operation: str, token: str, **kwargs):
        """Slack operations - reading messages, posting updates."""
        return await slack_tool.execute(operation=operation, token=token, **kwargs)

    @server.tool(name=calendar_tool.name)
    async def calendar_tool_func(operation: str, **kwargs):
        """Calendar operations - creating meetings, checking availability."""
        return await calendar_tool.execute(operation=operation, **kwargs)

    @server.tool(name=ppt_tool.name)
    async def powerpoint_tool(operation: str, **kwargs):
        """PowerPoint automation operations."""
        return await ppt_tool.execute(operation=operation, **kwargs)