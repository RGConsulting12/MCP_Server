#!/usr/bin/env python3
"""
Enhanced Visual Web Dashboard for MCP Server
Now includes Office Productivity Tools
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
import json
import sys
import os
from datetime import datetime
from typing import Dict, List

# Add src to path for tool imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import all tools
from handlers.file_tools import FileReaderTool, FileWriterTool
from handlers.data_tools import CalculatorTool, JSONProcessorTool
from handlers.office_tools import (
    MeetingSummarizerTool, EmailIntegrationTool, 
    SlackIntegrationTool, CalendarTool, PowerPointTool
)

app = FastAPI(title="MCP Server Dashboard")

# Store server activity
server_logs = []
tool_calls = []
server_stats = {
    "start_time": datetime.now(),
    "total_requests": 0,
    "active_tools": 0
}

# Initialize all tools
tools = {
    "file_reader": FileReaderTool(),
    "file_writer": FileWriterTool(),
    "calculator": CalculatorTool(),
    "json_processor": JSONProcessorTool(),
    "meeting_summarizer": MeetingSummarizerTool(),
    "email_integration": EmailIntegrationTool(),
    "slack_integration": SlackIntegrationTool(),
    "calendar_tool": CalendarTool(),
    "powerpoint_tool": PowerPointTool()
}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Enhanced dashboard with all tools"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Server Dashboard - Office Edition</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            .header {{ background: rgba(255,255,255,0.95); color: #2c3e50; padding: 30px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }}
            .stat-card {{ background: rgba(255,255,255,0.95); padding: 25px; border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); text-align: center; }}
            .stat-value {{ font-size: 2.5em; font-weight: bold; color: #3498db; margin-bottom: 10px; }}
            .stat-label {{ color: #7f8c8d; font-weight: 500; }}
            .tools-section {{ background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .tool-categories {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; }}
            .tool-category {{ background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #3498db; }}
            .category-title {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; margin-bottom: 15px; }}
            .tool-buttons {{ display: flex; flex-wrap: wrap; gap: 10px; }}
            .btn {{ background: linear-gradient(45deg, #3498db, #2980b9); color: white; padding: 12px 20px; border: none; border-radius: 25px; cursor: pointer; font-weight: 500; transition: all 0.3s; }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4); }}
            .btn-office {{ background: linear-gradient(45deg, #e74c3c, #c0392b); }}
            .btn-data {{ background: linear-gradient(45deg, #f39c12, #e67e22); }}
            .btn-file {{ background: linear-gradient(45deg, #27ae60, #229954); }}
            .logs {{ background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }}
            .log-entry {{ padding: 12px; border-bottom: 1px solid #ecf0f1; border-left: 3px solid #3498db; margin-bottom: 8px; background: #f8f9fa; }}
            .success {{ color: #27ae60; font-weight: bold; }}
            .error {{ color: #e74c3c; font-weight: bold; }}
            .test-result {{ margin-top: 20px; padding: 15px; border-radius: 8px; }}
            .result-success {{ background: #d5f4e6; border: 1px solid #27ae60; color: #1e7e34; }}
            .result-error {{ background: #f8d7da; border: 1px solid #e74c3c; color: #721c24; }}
        </style>
        <script>
            async function testTool(toolName, params = {{}}) {{
                const resultDiv = document.getElementById('test-result');
                resultDiv.innerHTML = '<div style="color: #3498db;">🔄 Testing ' + toolName + '...</div>';
                
                try {{
                    const response = await fetch('/test-tool/' + toolName, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(params)
                    }});
                    const data = await response.json();
                    
                    if (data.success) {{
                        resultDiv.innerHTML = '<div class="test-result result-success">✅ ' + data.message + '</div>';
                    }} else {{
                        resultDiv.innerHTML = '<div class="test-result result-error">❌ ' + data.error + '</div>';
                    }}
                    
                    setTimeout(() => location.reload(), 3000);
                }} catch (error) {{
                    resultDiv.innerHTML = '<div class="test-result result-error">❌ Error: ' + error + '</div>';
                }}
            }}
            
            // Auto-refresh every 10 seconds
            setTimeout(() => location.reload(), 10000);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 MCP Server Dashboard - Office Edition</h1>
                <p>Visual interface for Model Context Protocol server with Office Productivity Tools</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{len(server_logs)}</div>
                    <div class="stat-label">Server Events</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(tool_calls)}</div>
                    <div class="stat-label">Tool Executions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(tools)}</div>
                    <div class="stat-label">Available Tools</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{(datetime.now() - server_stats['start_time']).seconds}s</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>
            
            <div class="tools-section">
                <h3>🛠️ Interactive Tool Testing</h3>
                <div class="tool-categories">
                    
                    <div class="tool-category">
                        <div class="category-title">📁 File Operations</div>
                        <div class="tool-buttons">
                            <button class="btn btn-file" onclick="testTool('file_reader')">📖 Read File</button>
                            <button class="btn btn-file" onclick="testTool('file_writer')">✍️ Write File</button>
                        </div>
                    </div>
                    
                    <div class="tool-category">
                        <div class="category-title">🔢 Data Processing</div>
                        <div class="tool-buttons">
                            <button class="btn btn-data" onclick="testTool('calculator')">🧮 Calculator</button>
                            <button class="btn btn-data" onclick="testTool('json_processor')">📊 JSON Processor</button>
                        </div>
                    </div>
                    
                    <div class="tool-category">
                        <div class="category-title">🏢 Office Productivity</div>
                        <div class="tool-buttons">
                            <button class="btn btn-office" onclick="testTool('meeting_summarizer')">📝 Meeting Summary</button>
                            <button class="btn btn-office" onclick="testTool('email_integration')">📧 Email Tools</button>
                            <button class="btn btn-office" onclick="testTool('slack_integration')">💬 Slack Tools</button>
                        </div>
                    </div>
                    
                    <div class="tool-category">
                        <div class="category-title">📅 Calendar & Presentations</div>
                        <div class="tool-buttons">
                            <button class="btn btn-office" onclick="testTool('calendar_tool')">📅 Calendar</button>
                            <button class="btn btn-office" onclick="testTool('powerpoint_tool')">📊 PowerPoint</button>
                        </div>
                    </div>
                    
                </div>
                <div id="test-result"></div>
            </div>
            
            <div class="logs">
                <h3>📋 Live Activity Feed</h3>
                <div style="max-height: 400px; overflow-y: auto;">
    """
    
    # Add recent logs
    recent_logs = server_logs[-15:]  # Show last 15 logs
    for log in reversed(recent_logs):
        html_content += f'<div class="log-entry">[{log["time"]}] {log["message"]}</div>'
    
    if not recent_logs:
        html_content += '<div class="log-entry">🎯 Ready for testing! Click any tool button above.</div>'
    
    html_content += """
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/test-tool/{tool_name}")
async def test_tool_advanced(tool_name: str):
    """Advanced tool testing with actual tool execution"""
    server_stats['total_requests'] += 1
    
    # Log the tool call
    log_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": f"🧪 Testing {tool_name}"
    }
    server_logs.append(log_entry)
    tool_calls.append({"tool": tool_name, "time": datetime.now()})
    
    try:
        if tool_name not in tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        tool = tools[tool_name]
        
        # Execute tool with sample parameters
        if tool_name == "file_reader":
            result = await tool.execute(file_path=__file__)  # Read this dashboard file
        elif tool_name == "file_writer":
            result = await tool.execute(
                file_path="/tmp/mcp_test.txt", 
                content="Hello from MCP Dashboard!"
            )
        elif tool_name == "calculator":
            result = await tool.execute(expression="(10 + 5) * 2")
        elif tool_name == "json_processor":
            result = await tool.execute(
                json_data='{"tools": 9, "status": "active"}', 
                operation="validate"
            )
        elif tool_name == "meeting_summarizer":
            result = await tool.execute(
                meeting_content="John: Let's review the project. Sarah: We're on track. Action: Update docs by Friday.",
                meeting_title="Quick Sync",
                format="structured"
            )
        elif tool_name == "email_integration":
            result = await tool.execute(
                operation="read_recent",
                email_config={"smtp_server": "demo", "email": "demo@test.com", "password": "demo"}
            )
        elif tool_name == "slack_integration":
            result = await tool.execute(
                operation="read_messages",
                token="demo_token",
                channel="general"
            )
        elif tool_name == "calendar_tool":
            result = await tool.execute(
                operation="create_meeting",
                title="MCP Demo Meeting",
                start_time=datetime.now().isoformat(),
                attendees=["demo@test.com"]
            )
        elif tool_name == "powerpoint_tool":
            result = await tool.execute(
                operation="create_presentation",
                title="MCP Server Demo"
            )
        else:
            result = {"success": False, "error": "Unknown tool"}
        
        # Log result
        if result.get('success'):
            log_entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "message": f"✅ {tool_name} executed successfully"
            }
            server_logs.append(log_entry)
            return {"success": True, "message": f"{tool_name} working perfectly! Check logs for details."}
        else:
            log_entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "message": f"❌ {tool_name} failed: {result.get('error', 'Unknown error')}"
            }
            server_logs.append(log_entry)
            return {"success": False, "error": result.get('error', 'Tool execution failed')}
            
    except Exception as e:
        error_msg = f"Tool execution error: {str(e)}"
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": f"❌ {tool_name} crashed: {error_msg}"
        }
        server_logs.append(log_entry)
        return {"success": False, "error": error_msg}

@app.get("/api/stats")
async def get_stats():
    """API endpoint for server statistics"""
    return {
        "logs": len(server_logs),
        "tool_calls": len(tool_calls),
        "uptime": (datetime.now() - server_stats['start_time']).seconds,
        "total_requests": server_stats['total_requests'],
        "available_tools": list(tools.keys())
    }

def start_dashboard(port: int = 8090):
    """Start the enhanced web dashboard"""
    print(f"🌐 Starting Enhanced MCP Server Dashboard at http://localhost:{port}")
    print(f"📊 Available Tools: {len(tools)}")
    print(f"🏢 Office Tools: meeting_summarizer, email_integration, slack_integration, calendar_tool, powerpoint_tool")
    
    # Add startup log
    server_logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": f"🚀 Enhanced MCP Dashboard started with {len(tools)} tools"
    })
    
    uvicorn.run(app, host="localhost", port=port)

if __name__ == "__main__":
    start_dashboard()
