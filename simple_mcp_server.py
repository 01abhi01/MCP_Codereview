#!/usr/bin/env python3
"""
Simple MCP Server for GitHub Code Review Demo
"""

import asyncio
import sys
import os
import json
import subprocess
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# MCP imports
from mcp.server import Server
from mcp import Resource, Tool
from mcp.types import TextContent
from mcp.server.stdio import stdio_server


class SimpleGitHubMCPServer:
    """Simple MCP Server for demonstration"""
    
    def __init__(self):
        self.server = Server("github-code-review")
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="analyze_repository",
                    description="Analyze a GitHub repository for security, quality, and performance issues",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "Repository name in format 'owner/repo' (e.g., '01abhi01/MovieRecommend')"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["security", "quality", "performance", "full"],
                                "description": "Type of analysis to perform",
                                "default": "full"
                            }
                        },
                        "required": ["repository"]
                    }
                ),
                Tool(
                    name="list_repositories",
                    description="List available repositories for analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "GitHub username (defaults to '01abhi01')",
                                "default": "01abhi01"
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls"""
            try:
                if name == "analyze_repository":
                    repository = arguments.get("repository", "01abhi01/MovieRecommend")
                    analysis_type = arguments.get("analysis_type", "full")
                    return await self._analyze_repository(repository, analysis_type)
                
                elif name == "list_repositories":
                    username = arguments.get("username", "01abhi01")
                    return await self._list_repositories(username)
                
                else:
                    return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
                    
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
    
    def _register_resources(self):
        """Register MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            return [
                Resource(
                    uri="github://repositories/01abhi01",
                    name="01abhi01 Repositories",
                    description="GitHub repositories for user 01abhi01",
                    mimeType="application/json"
                )
            ]
    
    async def _analyze_repository(self, repository: str, analysis_type: str) -> list[TextContent]:
        """Analyze a repository using the command-line tool"""
        try:
            print(f"🔍 Analyzing {repository} with type {analysis_type}")
            
            # Use the existing run.py command-line tool
            cmd = [
                sys.executable, "run.py", 
                "--analyze", repository, 
                "--type", analysis_type
            ]
            
            # Run the analysis
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.path.dirname(os.path.abspath(__file__)),
                timeout=120
            )
            
            if result.returncode == 0:
                # Parse the output
                output = result.stdout
                
                analysis_text = f"""
🔍 **MCP Analysis Results for {repository}**

**Analysis Type:** {analysis_type}

{output}

---
*Analysis completed via MCP tool call*
"""
                return [TextContent(type="text", text=analysis_text)]
            else:
                error_msg = f"❌ Analysis failed for {repository}\n\nError: {result.stderr}\n\nOutput: {result.stdout}"
                return [TextContent(type="text", text=error_msg)]
            
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text=f"⏰ Analysis timeout for {repository} (>120s)")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Analysis error: {str(e)}")]
    
    async def _list_repositories(self, username: str) -> list[TextContent]:
        """List repositories for a user"""
        try:
            # For demo, return some known repositories
            if username == "01abhi01":
                repo_list = """
📦 **Available Repositories for 01abhi01:**

• **01abhi01/MovieRecommend** (Python)
  Movie recommendation system
  ⭐ Recently analyzed - Good security, needs style improvements

• **01abhi01/MCP_Codereview** (Python)  
  This MCP server project for GitHub code review
  ⭐ Active development

*To analyze any repository, use:*
`analyze_repository("01abhi01/MovieRecommend", "security")`
"""
            else:
                repo_list = f"""
📦 **Repository Discovery:**

Username: {username}

*Note: Configure your GitHub token in .env to access other users' repositories*

Available analysis types:
- `security`: Security vulnerability scanning
- `quality`: Code quality and style analysis  
- `performance`: Performance optimization suggestions
- `full`: Comprehensive analysis (all types)
"""
            
            return [TextContent(type="text", text=repo_list)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Repository listing error: {str(e)}")]
    
    async def run(self):
        """Run the MCP server"""
        print("🚀 Starting GitHub Code Review MCP Server...")
        print("📡 Waiting for MCP client connections...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = SimpleGitHubMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
