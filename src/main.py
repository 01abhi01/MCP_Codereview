"""
Main entry point for the Dynamic GitHub Code Review MCP Server.

This server provides comprehensive code review capabilities for GitHub repositories
with dynamic repository discovery and multi-language support.
"""

import asyncio
import logging
from typing import Any, Sequence
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp import Resource, Tool
from mcp.types import TextContent, ImageContent, EmbeddedResource

from utils import Config, setup_logging
from core.github_client import GitHubClient
from core.repository_manager import RepositoryManager
from core.analyzer import CodeAnalyzer
from tools import GitHubCodeReviewTools


class DynamicGitHubCodeReviewServer:
    """Dynamic GitHub Code Review MCP Server."""
    
    def __init__(self):
        """Initialize the server."""
        # Load configuration
        self.config = Config()
        
        # Setup logging
        self.logger_manager = setup_logging(self.config)
        self.logger = self.logger_manager.get_logger('main')
        
        # Initialize MCP server
        self.server = Server("dynamic-github-code-review")
        
        # Initialize components (will be done in setup)
        self.github_client = None
        self.repo_manager = None
        self.analyzer = None
        self.tools = None
        
        # Setup MCP handlers
        self._setup_mcp_handlers()
        
        self.logger.info("GitHub Code Review MCP Server initialized")
    
    def _setup_mcp_handlers(self):
        """Setup MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            if self.tools:
                return self.tools.tools
            return []
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
            """Handle tool calls."""
            if self.tools:
                return await self.tools.call_tool(name, arguments)
            return [TextContent(type="text", text="Tools not initialized")]
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """List available resources."""
            resources = []
            
            # Dynamic repository resources
            if self.repo_manager:
                repos = await self.repo_manager.get_configured_repositories()
                for repo_name, repo_config in repos.items():
                    resources.append(Resource(
                        uri=f"github://repository/{repo_name}",
                        name=f"Repository: {repo_name}",
                        description=f"{repo_config.get('language', 'Unknown')} repository"
                    ))
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read resource content."""
            try:
                if uri.startswith("github://repository/"):
                    repo_name = uri.replace("github://repository/", "")
                    
                    if self.repo_manager:
                        local_path = await self.repo_manager.get_local_path(repo_name)
                        if local_path:
                            # Return repository analysis summary
                            analysis = self.analyzer.analyze_repository(local_path, repo_name)
                            return f"Repository Analysis for {repo_name}:\n{analysis.to_dict()}"
                    
                    return f"Repository {repo_name} not found or not cloned"
                
                return f"Unknown resource: {uri}"
            
            except Exception as e:
                return f"Error reading resource {uri}: {str(e)}"
        
        @self.server.list_prompts()
        async def handle_list_prompts():
            """List available prompts."""
            return [
                {
                    "name": "code_review",
                    "description": "Generate a comprehensive code review for a repository",
                    "arguments": [
                        {
                            "name": "repository",
                            "description": "Repository name (owner/repo format)",
                            "required": True
                        },
                        {
                            "name": "focus_areas",
                            "description": "Comma-separated focus areas (security,quality,performance)",
                            "required": False
                        }
                    ]
                },
                {
                    "name": "security_analysis",
                    "description": "Generate a security analysis report for a repository", 
                    "arguments": [
                        {
                            "name": "repository", 
                            "description": "Repository name (owner/repo format)",
                            "required": True
                        }
                    ]
                },
                {
                    "name": "improvement_suggestions",
                    "description": "Generate improvement suggestions for a repository",
                    "arguments": [
                        {
                            "name": "repository",
                            "description": "Repository name (owner/repo format)", 
                            "required": True
                        },
                        {
                            "name": "focus_area",
                            "description": "Specific area to focus on (security,performance,maintainability)",
                            "required": False
                        }
                    ]
                }
            ]
        
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: dict):
            """Handle prompt requests."""
            try:
                if name == "code_review":
                    repository = arguments.get("repository")
                    focus_areas = arguments.get("focus_areas", "security,quality,performance").split(",")
                    
                    if not repository:
                        return "Error: Repository parameter is required"
                    
                    # Generate code review prompt
                    return await self._generate_code_review_prompt(repository, focus_areas)
                
                elif name == "security_analysis":
                    repository = arguments.get("repository")
                    
                    if not repository:
                        return "Error: Repository parameter is required"
                    
                    return await self._generate_security_analysis_prompt(repository)
                
                elif name == "improvement_suggestions":
                    repository = arguments.get("repository")
                    focus_area = arguments.get("focus_area")
                    
                    if not repository:
                        return "Error: Repository parameter is required"
                    
                    return await self._generate_improvement_suggestions_prompt(repository, focus_area)
                
                return f"Unknown prompt: {name}"
            
            except Exception as e:
                return f"Error generating prompt {name}: {str(e)}"
    
    async def setup(self):
        """Setup server components."""
        try:
            self.logger.info("Setting up server components...")
            
            # Initialize GitHub client
            self.github_client = GitHubClient(self.config)
            await self.github_client.initialize()
            
            # Initialize repository manager
            self.repo_manager = RepositoryManager(self.config, self.github_client)
            
            # Initialize code analyzer
            self.analyzer = CodeAnalyzer(self.config)
            
            # Initialize tools
            self.tools = GitHubCodeReviewTools(
                self.config, 
                self.github_client, 
                self.repo_manager, 
                self.analyzer
            )
            
            # Discover repositories on startup
            await self._discover_initial_repositories()
            
            self.logger.info("Server components setup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to setup server components: {e}")
            raise
    
    async def _discover_initial_repositories(self):
        """Discover initial repositories for the configured user."""
        try:
            self.logger.info(f"Discovering repositories for user: {self.config.GITHUB_USERNAME}")
            
            repositories = await self.github_client.get_user_repositories(
                self.config.GITHUB_USERNAME,
                include_private=self.config.INCLUDE_PRIVATE_REPOS,
                include_forks=self.config.INCLUDE_FORKS,
                max_repos=self.config.MAX_REPOSITORIES
            )
            
            await self.repo_manager.update_repositories(repositories)
            
            self.logger.info(f"Discovered {len(repositories)} repositories")
            
            # Log repository details
            for repo in repositories[:5]:  # Log first 5 repos
                self.logger.info(
                    f"Repository: {repo['full_name']} "
                    f"({repo.get('language', 'Unknown')}) - "
                    f"{repo.get('stargazers_count', 0)} stars"
                )
            
            if len(repositories) > 5:
                self.logger.info(f"... and {len(repositories) - 5} more repositories")
        
        except Exception as e:
            self.logger.error(f"Failed to discover initial repositories: {e}")
    
    async def _generate_code_review_prompt(self, repository: str, focus_areas: list) -> str:
        """Generate a code review prompt."""
        try:
            # Ensure repository is analyzed
            local_path = await self.repo_manager.get_local_path(repository)
            if not local_path:
                local_path = await self.repo_manager.clone_repository(repository)
            
            analysis = self.analyzer.analyze_repository(local_path, repository)
            
            prompt = f"""# Code Review for {repository}

## Repository Overview
- **Languages**: {', '.join(analysis.languages.keys())}
- **Files Analyzed**: {analysis.analyzed_files}/{analysis.total_files}
- **Overall Scores**: Security: {analysis.overall_scores.get('security', 0):.1f}/100, Quality: {analysis.overall_scores.get('quality', 0):.1f}/100, Performance: {analysis.overall_scores.get('performance', 0):.1f}/100

## Focus Areas
{', '.join(focus_areas)}

## Analysis Summary
{analysis.summary}

## Key Issues Found
"""
            
            # Add top issues by focus areas
            for focus_area in focus_areas:
                focus_issues = []
                for file_result in analysis.file_results:
                    for issue in file_result.issues:
                        if issue.get('category') == focus_area.strip() and issue.get('severity') in ['high', 'medium']:
                            focus_issues.append(f"- **{file_result.file_path}**: {issue.get('description', 'Unknown issue')}")
                
                if focus_issues:
                    prompt += f"\n### {focus_area.title()} Issues\n"
                    prompt += '\n'.join(focus_issues[:10])  # Top 10 issues
                    prompt += "\n"
            
            prompt += f"""
## Recommendations
Based on this analysis, please provide a comprehensive code review focusing on the {', '.join(focus_areas)} areas. 
Include specific recommendations for improvement and highlight any critical issues that need immediate attention.
"""
            
            return prompt
        
        except Exception as e:
            return f"Error generating code review prompt: {str(e)}"
    
    async def _generate_security_analysis_prompt(self, repository: str) -> str:
        """Generate a security analysis prompt."""
        try:
            local_path = await self.repo_manager.get_local_path(repository)
            if not local_path:
                local_path = await self.repo_manager.clone_repository(repository)
            
            analysis = self.analyzer.analyze_repository(local_path, repository)
            
            # Extract security issues
            security_issues = []
            for file_result in analysis.file_results:
                for issue in file_result.issues:
                    if issue.get('category') == 'security':
                        security_issues.append({
                            'file': file_result.file_path,
                            'issue': issue
                        })
            
            prompt = f"""# Security Analysis for {repository}

## Security Score: {analysis.overall_scores.get('security', 0):.1f}/100

## Security Issues Found: {len(security_issues)}

### High Priority Security Issues
"""
            
            high_priority = [issue for issue in security_issues if issue['issue'].get('severity') == 'high']
            for issue_data in high_priority[:10]:
                prompt += f"- **{issue_data['file']}** (Line {issue_data['issue'].get('line', 'Unknown')}): {issue_data['issue'].get('description', 'Unknown issue')}\n"
            
            prompt += f"""
### Dependencies
{analysis.dependencies}

## Request
Please provide a comprehensive security assessment of this repository. Focus on:
1. Critical security vulnerabilities that need immediate attention
2. Security best practices that should be implemented
3. Dependency security recommendations
4. Overall security posture and improvements needed
"""
            
            return prompt
        
        except Exception as e:
            return f"Error generating security analysis prompt: {str(e)}"
    
    async def _generate_improvement_suggestions_prompt(self, repository: str, focus_area: str = None) -> str:
        """Generate improvement suggestions prompt."""
        try:
            local_path = await self.repo_manager.get_local_path(repository)
            if not local_path:
                local_path = await self.repo_manager.clone_repository(repository)
            
            analysis = self.analyzer.analyze_repository(local_path, repository)
            
            # Collect suggestions
            all_suggestions = []
            for file_result in analysis.file_results:
                for suggestion in file_result.suggestions:
                    if not focus_area or suggestion.get('type') == focus_area:
                        all_suggestions.append({
                            'file': file_result.file_path,
                            'suggestion': suggestion
                        })
            
            prompt = f"""# Improvement Suggestions for {repository}

## Current Scores
- Security: {analysis.overall_scores.get('security', 0):.1f}/100
- Quality: {analysis.overall_scores.get('quality', 0):.1f}/100  
- Performance: {analysis.overall_scores.get('performance', 0):.1f}/100

## Focus Area: {focus_area or 'All Areas'}

## Key Metrics
- Languages: {', '.join(analysis.languages.keys())}
- Total Files: {analysis.total_files}
- Files with Issues: {len([f for f in analysis.file_results if f.issues])}

## Improvement Opportunities
"""
            
            # Group suggestions by priority
            high_priority = [s for s in all_suggestions if s['suggestion'].get('priority') == 'high']
            medium_priority = [s for s in all_suggestions if s['suggestion'].get('priority') == 'medium']
            
            if high_priority:
                prompt += "### High Priority\n"
                for item in high_priority[:5]:
                    prompt += f"- **{item['file']}**: {item['suggestion'].get('description', 'Unknown suggestion')}\n"
            
            if medium_priority:
                prompt += "\n### Medium Priority\n"
                for item in medium_priority[:5]:
                    prompt += f"- **{item['file']}**: {item['suggestion'].get('description', 'Unknown suggestion')}\n"
            
            prompt += f"""
## Request
Based on this analysis, please provide actionable improvement recommendations for this repository. 
Focus on {focus_area if focus_area else 'overall code quality, security, and performance'}. 
Prioritize suggestions that will have the most impact on code quality and maintainability.
"""
            
            return prompt
        
        except Exception as e:
            return f"Error generating improvement suggestions prompt: {str(e)}"
    
    async def cleanup(self):
        """Cleanup server resources."""
        try:
            if self.github_client:
                await self.github_client.close()
            
            if self.repo_manager:
                await self.repo_manager.cleanup()
            
            self.logger.info("Server cleanup complete")
        
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """Main entry point."""
    server_instance = DynamicGitHubCodeReviewServer()
    
    try:
        await server_instance.setup()
        
        # Run the server
        await server_instance.server.run()
    
    except KeyboardInterrupt:
        server_instance.logger.info("Server interrupted by user")
    
    except Exception as e:
        server_instance.logger.error(f"Server error: {e}")
        raise
    
    finally:
        await server_instance.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
