#!/usr/bin/env python3
"""
MCP Server Runner - Fixed import version
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import MCP components
from mcp.server import Server
from mcp import Resource, Tool
from mcp.types import TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server

# Import our modules
from src.utils.config import Config
from src.utils.logger import setup_logging
from src.core.github_client import GitHubClient
from src.core.repository_manager import RepositoryManager
from src.core.analyzer import CodeAnalyzer


class GitHubCodeReviewMCPServer:
    """MCP Server for GitHub Code Review"""
    
    def __init__(self):
        self.server = Server("dynamic-github-code-review")
        self.config = Config()
        self.logger = setup_logging(self.config)
        
        # Initialize components
        self.github_client = None
        self.repo_manager = None
        self.analyzer = None
        
        # Register handlers
        self._register_tools()
        self._register_resources()
        self._register_prompts()
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="analyze_repository",
                    description="Analyze a GitHub repository for security, quality, and performance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repository": {
                                "type": "string",
                                "description": "Repository name in format 'owner/repo'"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["security", "quality", "performance", "full"],
                                "description": "Type of analysis to perform"
                            }
                        },
                        "required": ["repository", "analysis_type"]
                    }
                ),
                Tool(
                    name="discover_repositories",
                    description="Discover all repositories for a GitHub user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "GitHub username to discover repositories for"
                            }
                        },
                        "required": ["username"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls"""
            try:
                if not self.github_client:
                    await self._initialize_clients()
                
                if name == "analyze_repository":
                    return await self._analyze_repository(
                        arguments["repository"], 
                        arguments["analysis_type"]
                    )
                elif name == "discover_repositories":
                    return await self._discover_repositories(arguments["username"])
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                self.logger.error(f"Tool call failed: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _register_resources(self):
        """Register MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            return [
                Resource(
                    uri="github://repositories",
                    name="GitHub Repositories",
                    description="Available GitHub repositories for analysis",
                    mimeType="application/json"
                )
            ]
    
    def _register_prompts(self):
        """Register MCP prompts"""
        
        @self.server.list_prompts()
        async def list_prompts() -> list:
            return [
                {
                    "name": "code_review",
                    "description": "Generate a comprehensive code review",
                    "arguments": [
                        {"name": "repository", "description": "Repository to review", "required": True}
                    ]
                }
            ]
    
    async def _initialize_clients(self):
        """Initialize GitHub client and related components"""
        self.github_client = GitHubClient(self.config)
        await self.github_client.initialize()
        
        self.repo_manager = RepositoryManager(self.github_client, self.config)
        self.analyzer = CodeAnalyzer(self.config)
        
        self.logger.info("✅ MCP Server clients initialized")
    
    async def _analyze_repository(self, repository: str, analysis_type: str) -> list[TextContent]:
        """Analyze a repository"""
        try:
            self.logger.info(f"🔍 MCP: Analyzing {repository} (type: {analysis_type})")
            
            # Clone repository
            local_path = await self.repo_manager.clone_repository(repository)
            
            # Analyze
            results = await self.analyzer.analyze_repository(local_path, analysis_type)
            
            # Format results
            analysis_text = f"""
🔍 **Analysis Results for {repository}**

**Overall Scores:**
- Security: {results['scores']['security']}/100
- Quality: {results['scores']['quality']}/100  
- Performance: {results['scores']['performance']}/100

**Summary:**
- Total Files: {results['summary']['total_files']}
- Analyzed Files: {results['summary']['analyzed_files']}
- Languages: {', '.join(results['summary']['languages'])}

**Top Issues ({analysis_type}):**
"""
            
            # Add top issues
            for i, issue in enumerate(results['issues'][:10], 1):
                analysis_text += f"  {i}. [{issue['severity']}] {issue['file']}: {issue['description']}\n"
            
            return [TextContent(type="text", text=analysis_text)]
            
        except Exception as e:
            self.logger.error(f"Repository analysis failed: {e}")
            return [TextContent(type="text", text=f"❌ Analysis failed: {str(e)}")]
    
    async def _discover_repositories(self, username: str) -> list[TextContent]:
        """Discover repositories for a user"""
        try:
            self.logger.info(f"📦 MCP: Discovering repositories for {username}")
            
            repos = await self.github_client.get_user_repositories(username)
            
            repo_text = f"📦 **Found {len(repos)} repositories for {username}:**\n\n"
            
            for repo in repos[:10]:  # Show first 10
                repo_text += f"• **{repo['full_name']}** ({repo['language'] or 'Unknown'})\n"
                repo_text += f"  {repo['description'] or 'No description'}\n"
                repo_text += f"  ⭐ {repo['stargazers_count']} stars\n\n"
            
            if len(repos) > 10:
                repo_text += f"... and {len(repos) - 10} more repositories\n"
            
            return [TextContent(type="text", text=repo_text)]
            
        except Exception as e:
            self.logger.error(f"Repository discovery failed: {e}")
            return [TextContent(type="text", text=f"❌ Discovery failed: {str(e)}")]
    
    async def run(self):
        """Run the MCP server"""
        self.logger.info("🚀 Starting GitHub Code Review MCP Server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="GitHub Code Review MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run server
    server = GitHubCodeReviewMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
