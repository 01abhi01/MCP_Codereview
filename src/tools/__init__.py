"""
MCP Tools implementation for the GitHub Code Review MCP Server.

Provides tools for repository discovery, analysis, and code review operations.
"""

from typing import Dict, List, Any, Optional
import json
import os
import tempfile
import shutil
from pathlib import Path

from mcp import Tool, Resource
from mcp.types import TextContent, ImageContent, EmbeddedResource

from ..utils import get_logger, Config
from ..core.github_client import GitHubClient
from ..core.repository_manager import RepositoryManager
from ..core.analyzer import CodeAnalyzer


class GitHubCodeReviewTools:
    """MCP tools for GitHub code review functionality."""
    
    def __init__(self, config: Config, github_client: GitHubClient, 
                 repo_manager: RepositoryManager, analyzer: CodeAnalyzer):
        """Initialize the tools."""
        self.config = config
        self.github_client = github_client
        self.repo_manager = repo_manager
        self.analyzer = analyzer
        self.logger = get_logger('tools')
        
        # Tool definitions
        self.tools = self._define_tools()
    
    def _define_tools(self) -> List[Tool]:
        """Define all available MCP tools."""
        return [
            Tool(
                name="discover_repositories",
                description="Discover repositories for the configured GitHub user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_private": {
                            "type": "boolean",
                            "description": "Include private repositories",
                            "default": False
                        },
                        "include_forks": {
                            "type": "boolean", 
                            "description": "Include forked repositories",
                            "default": False
                        },
                        "language_filter": {
                            "type": "string",
                            "description": "Filter by programming language (optional)"
                        },
                        "max_repos": {
                            "type": "integer",
                            "description": "Maximum number of repositories to return",
                            "default": 20
                        }
                    }
                }
            ),
            Tool(
                name="clone_repository",
                description="Clone a repository for analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name (owner/repo format)"
                        },
                        "branch": {
                            "type": "string", 
                            "description": "Branch to clone",
                            "default": "main"
                        }
                    },
                    "required": ["repository"]
                }
            ),
            Tool(
                name="analyze_repository",
                description="Perform comprehensive code analysis on a repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name (owner/repo format)"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["full", "security", "quality", "performance"],
                            "description": "Type of analysis to perform",
                            "default": "full"
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "Glob pattern to filter files (optional)"
                        }
                    },
                    "required": ["repository"]
                }
            ),
            Tool(
                name="analyze_file",
                description="Analyze a specific file in a repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name (owner/repo format)"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file within the repository"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["full", "security", "quality", "performance"],
                            "description": "Type of analysis to perform",
                            "default": "full"
                        }
                    },
                    "required": ["repository", "file_path"]
                }
            ),
            Tool(
                name="review_pull_request",
                description="Review a pull request and provide feedback",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name (owner/repo format)"
                        },
                        "pull_request_number": {
                            "type": "integer",
                            "description": "Pull request number"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Areas to focus on (security, performance, style, etc.)"
                        }
                    },
                    "required": ["repository", "pull_request_number"]
                }
            ),
            Tool(
                name="generate_security_report",
                description="Generate a comprehensive security report for a repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name (owner/repo format)"
                        },
                        "include_dependencies": {
                            "type": "boolean",
                            "description": "Include dependency vulnerability scan",
                            "default": True
                        }
                    },
                    "required": ["repository"]
                }
            ),
            Tool(
                name="compare_repositories",
                description="Compare code quality metrics between repositories",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repositories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of repositories to compare (owner/repo format)"
                        },
                        "metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Metrics to compare (security, quality, performance)"
                        }
                    },
                    "required": ["repositories"]
                }
            ),
            Tool(
                name="get_repository_info",
                description="Get detailed information about a repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name (owner/repo format)"
                        }
                    },
                    "required": ["repository"]
                }
            ),
            Tool(
                name="get_file_content",
                description="Get the content of a specific file from a repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name (owner/repo format)"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file within the repository"
                        },
                        "branch": {
                            "type": "string",
                            "description": "Branch name",
                            "default": "main"
                        }
                    },
                    "required": ["repository", "file_path"]
                }
            ),
            Tool(
                name="suggest_improvements",
                description="Generate improvement suggestions for a repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name (owner/repo format)"
                        },
                        "focus_area": {
                            "type": "string",
                            "enum": ["security", "performance", "maintainability", "testing", "documentation"],
                            "description": "Area to focus improvement suggestions on"
                        }
                    },
                    "required": ["repository"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent | EmbeddedResource]:
        """Call a tool with the given arguments."""
        self.logger.info(f"Calling tool: {name} with arguments: {arguments}")
        
        try:
            if name == "discover_repositories":
                return await self._discover_repositories(**arguments)
            elif name == "clone_repository":
                return await self._clone_repository(**arguments)
            elif name == "analyze_repository":
                return await self._analyze_repository(**arguments)
            elif name == "analyze_file":
                return await self._analyze_file(**arguments)
            elif name == "review_pull_request":
                return await self._review_pull_request(**arguments)
            elif name == "generate_security_report":
                return await self._generate_security_report(**arguments)
            elif name == "compare_repositories":
                return await self._compare_repositories(**arguments)
            elif name == "get_repository_info":
                return await self._get_repository_info(**arguments)
            elif name == "get_file_content":
                return await self._get_file_content(**arguments)
            elif name == "suggest_improvements":
                return await self._suggest_improvements(**arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        except Exception as e:
            self.logger.error(f"Error calling tool {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _discover_repositories(self, include_private: bool = False, 
                                   include_forks: bool = False,
                                   language_filter: Optional[str] = None,
                                   max_repos: int = 20) -> List[TextContent]:
        """Discover repositories for the configured GitHub user."""
        try:
            repositories = await self.github_client.get_user_repositories(
                self.config.GITHUB_USERNAME,
                include_private=include_private,
                include_forks=include_forks,
                max_repos=max_repos
            )
            
            # Filter by language if specified
            if language_filter:
                repositories = [repo for repo in repositories 
                              if repo.get('language', '').lower() == language_filter.lower()]
            
            # Update repository manager
            await self.repo_manager.update_repositories(repositories)
            
            # Format response
            result = {
                "total_repositories": len(repositories),
                "repositories": []
            }
            
            for repo in repositories:
                result["repositories"].append({
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description", ""),
                    "language": repo.get("language", "Unknown"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "updated_at": repo.get("updated_at", ""),
                    "private": repo.get("private", False),
                    "fork": repo.get("fork", False),
                    "url": repo.get("html_url", "")
                })
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error discovering repositories: {str(e)}")]
    
    async def _clone_repository(self, repository: str, branch: str = "main") -> List[TextContent]:
        """Clone a repository for analysis."""
        try:
            # Clone repository using repository manager
            local_path = await self.repo_manager.clone_repository(repository, branch)
            
            # Get repository info
            repo_info = await self.github_client.get_repository(repository)
            
            result = {
                "repository": repository,
                "branch": branch,
                "local_path": local_path,
                "status": "cloned",
                "info": {
                    "language": repo_info.get("language", "Unknown"),
                    "size": repo_info.get("size", 0),
                    "default_branch": repo_info.get("default_branch", "main"),
                    "created_at": repo_info.get("created_at", ""),
                    "updated_at": repo_info.get("updated_at", "")
                }
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error cloning repository: {str(e)}")]
    
    async def _analyze_repository(self, repository: str, analysis_type: str = "full",
                                 file_pattern: Optional[str] = None) -> List[TextContent]:
        """Perform comprehensive code analysis on a repository."""
        try:
            # Ensure repository is cloned
            local_path = await self.repo_manager.get_local_path(repository)
            if not local_path or not os.path.exists(local_path):
                local_path = await self.repo_manager.clone_repository(repository)
            
            # Perform analysis
            analysis_result = self.analyzer.analyze_repository(local_path, repository)
            
            # Filter results based on analysis type
            if analysis_type != "full":
                filtered_results = []
                for file_result in analysis_result.file_results:
                    filtered_issues = [
                        issue for issue in file_result.issues
                        if issue.get('category') == analysis_type
                    ]
                    if filtered_issues:
                        file_result.issues = filtered_issues
                        filtered_results.append(file_result)
                analysis_result.file_results = filtered_results
            
            # Generate summary
            summary = {
                "repository": repository,
                "analysis_type": analysis_type,
                "timestamp": analysis_result.timestamp.isoformat(),
                "summary": analysis_result.summary,
                "overall_scores": analysis_result.overall_scores,
                "languages": analysis_result.languages,
                "total_files": analysis_result.total_files,
                "analyzed_files": analysis_result.analyzed_files,
                "key_findings": self._extract_key_findings(analysis_result)
            }
            
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing repository: {str(e)}")]
    
    async def _analyze_file(self, repository: str, file_path: str, 
                          analysis_type: str = "full") -> List[TextContent]:
        """Analyze a specific file in a repository."""
        try:
            # Ensure repository is cloned
            local_path = await self.repo_manager.get_local_path(repository)
            if not local_path or not os.path.exists(local_path):
                local_path = await self.repo_manager.clone_repository(repository)
            
            # Construct full file path
            full_file_path = os.path.join(local_path, file_path)
            
            if not os.path.exists(full_file_path):
                return [TextContent(type="text", text=f"File not found: {file_path}")]
            
            # Analyze file
            result = self.analyzer.analyze_file(full_file_path)
            
            if not result:
                return [TextContent(type="text", text=f"Unable to analyze file: {file_path}")]
            
            # Filter issues based on analysis type
            if analysis_type != "full":
                result.issues = [
                    issue for issue in result.issues
                    if issue.get('category') == analysis_type
                ]
            
            # Format response
            response = {
                "repository": repository,
                "file_path": file_path,
                "analysis_type": analysis_type,
                "language": result.language,
                "metrics": result.metrics,
                "scores": {
                    "security": result.security_score,
                    "quality": result.quality_score,
                    "performance": result.performance_score
                },
                "issues": result.issues,
                "suggestions": result.suggestions,
                "timestamp": result.timestamp.isoformat()
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing file: {str(e)}")]
    
    async def _review_pull_request(self, repository: str, pull_request_number: int,
                                  focus_areas: Optional[List[str]] = None) -> List[TextContent]:
        """Review a pull request and provide feedback."""
        try:
            # Get pull request details
            pr_data = await self.github_client.get_pull_request(repository, pull_request_number)
            
            # Get changed files
            changed_files = await self.github_client.get_pull_request_files(repository, pull_request_number)
            
            # Ensure repository is cloned
            local_path = await self.repo_manager.get_local_path(repository)
            if not local_path or not os.path.exists(local_path):
                local_path = await self.repo_manager.clone_repository(repository)
            
            # Analyze changed files
            file_analyses = []
            for file_info in changed_files:
                file_path = os.path.join(local_path, file_info['filename'])
                if os.path.exists(file_path):
                    analysis = self.analyzer.analyze_file(file_path)
                    if analysis:
                        # Filter by focus areas if specified
                        if focus_areas:
                            analysis.issues = [
                                issue for issue in analysis.issues
                                if issue.get('category') in focus_areas
                            ]
                        
                        file_analyses.append({
                            "file": file_info['filename'],
                            "status": file_info['status'],
                            "additions": file_info.get('additions', 0),
                            "deletions": file_info.get('deletions', 0),
                            "analysis": analysis.to_dict()
                        })
            
            # Generate review summary
            total_issues = sum(len(fa['analysis']['issues']) for fa in file_analyses)
            high_priority_issues = sum(
                1 for fa in file_analyses 
                for issue in fa['analysis']['issues']
                if issue.get('severity') == 'high'
            )
            
            review_summary = {
                "repository": repository,
                "pull_request": pull_request_number,
                "title": pr_data.get('title', ''),
                "description": pr_data.get('body', ''),
                "author": pr_data.get('user', {}).get('login', ''),
                "base_branch": pr_data.get('base', {}).get('ref', ''),
                "head_branch": pr_data.get('head', {}).get('ref', ''),
                "files_changed": len(changed_files),
                "files_analyzed": len(file_analyses),
                "total_issues": total_issues,
                "high_priority_issues": high_priority_issues,
                "focus_areas": focus_areas or ["security", "quality", "performance"],
                "file_analyses": file_analyses,
                "recommendation": self._generate_pr_recommendation(file_analyses, total_issues, high_priority_issues)
            }
            
            return [TextContent(type="text", text=json.dumps(review_summary, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error reviewing pull request: {str(e)}")]
    
    async def _generate_security_report(self, repository: str, 
                                      include_dependencies: bool = True) -> List[TextContent]:
        """Generate a comprehensive security report for a repository."""
        try:
            # Ensure repository is cloned
            local_path = await self.repo_manager.get_local_path(repository)
            if not local_path or not os.path.exists(local_path):
                local_path = await self.repo_manager.clone_repository(repository)
            
            # Perform security-focused analysis
            analysis_result = self.analyzer.analyze_repository(local_path, repository)
            
            # Extract security issues
            security_issues = []
            for file_result in analysis_result.file_results:
                file_security_issues = [
                    issue for issue in file_result.issues
                    if issue.get('category') == 'security'
                ]
                if file_security_issues:
                    security_issues.append({
                        "file": file_result.file_path,
                        "issues": file_security_issues,
                        "security_score": file_result.security_score
                    })
            
            # Security statistics
            total_security_issues = sum(len(file['issues']) for file in security_issues)
            high_severity_count = sum(
                1 for file in security_issues 
                for issue in file['issues']
                if issue.get('severity') == 'high'
            )
            
            # Generate security recommendations
            recommendations = self._generate_security_recommendations(security_issues)
            
            report = {
                "repository": repository,
                "report_type": "security",
                "timestamp": analysis_result.timestamp.isoformat(),
                "overall_security_score": analysis_result.overall_scores.get('security', 0),
                "summary": {
                    "total_files_analyzed": analysis_result.analyzed_files,
                    "files_with_security_issues": len(security_issues),
                    "total_security_issues": total_security_issues,
                    "high_severity_issues": high_severity_count,
                    "risk_level": self._calculate_risk_level(analysis_result.overall_scores.get('security', 0))
                },
                "security_issues": security_issues,
                "dependencies": analysis_result.dependencies if include_dependencies else {},
                "recommendations": recommendations
            }
            
            return [TextContent(type="text", text=json.dumps(report, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error generating security report: {str(e)}")]
    
    async def _compare_repositories(self, repositories: List[str], 
                                  metrics: Optional[List[str]] = None) -> List[TextContent]:
        """Compare code quality metrics between repositories."""
        try:
            if not metrics:
                metrics = ["security", "quality", "performance"]
            
            comparison_data = {
                "repositories": repositories,
                "metrics": metrics,
                "comparison_results": [],
                "summary": {}
            }
            
            repo_analyses = []
            
            # Analyze each repository
            for repo in repositories:
                try:
                    # Ensure repository is cloned
                    local_path = await self.repo_manager.get_local_path(repo)
                    if not local_path or not os.path.exists(local_path):
                        local_path = await self.repo_manager.clone_repository(repo)
                    
                    # Analyze repository
                    analysis = self.analyzer.analyze_repository(local_path, repo)
                    
                    repo_data = {
                        "repository": repo,
                        "overall_scores": analysis.overall_scores,
                        "languages": analysis.languages,
                        "total_files": analysis.total_files,
                        "analyzed_files": analysis.analyzed_files,
                        "summary": analysis.summary
                    }
                    
                    repo_analyses.append(repo_data)
                    comparison_data["comparison_results"].append(repo_data)
                
                except Exception as e:
                    self.logger.error(f"Error analyzing repository {repo}: {e}")
                    comparison_data["comparison_results"].append({
                        "repository": repo,
                        "error": str(e)
                    })
            
            # Generate comparison summary
            if repo_analyses:
                comparison_data["summary"] = self._generate_comparison_summary(repo_analyses, metrics)
            
            return [TextContent(type="text", text=json.dumps(comparison_data, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error comparing repositories: {str(e)}")]
    
    async def _get_repository_info(self, repository: str) -> List[TextContent]:
        """Get detailed information about a repository."""
        try:
            # Get repository data from GitHub
            repo_data = await self.github_client.get_repository(repository)
            
            # Get additional statistics
            languages = await self.github_client.get_repository_languages(repository)
            contributors = await self.github_client.get_repository_contributors(repository)
            
            # Check if we have local analysis data
            local_path = await self.repo_manager.get_local_path(repository)
            analysis_data = None
            
            if local_path and os.path.exists(local_path):
                try:
                    analysis_result = self.analyzer.analyze_repository(local_path, repository)
                    analysis_data = {
                        "overall_scores": analysis_result.overall_scores,
                        "summary": analysis_result.summary,
                        "last_analyzed": analysis_result.timestamp.isoformat()
                    }
                except Exception as e:
                    self.logger.warning(f"Could not get analysis data: {e}")
            
            info = {
                "repository": repository,
                "basic_info": {
                    "name": repo_data.get("name", ""),
                    "full_name": repo_data.get("full_name", ""),
                    "description": repo_data.get("description", ""),
                    "private": repo_data.get("private", False),
                    "fork": repo_data.get("fork", False),
                    "created_at": repo_data.get("created_at", ""),
                    "updated_at": repo_data.get("updated_at", ""),
                    "pushed_at": repo_data.get("pushed_at", ""),
                    "size": repo_data.get("size", 0),
                    "default_branch": repo_data.get("default_branch", "main"),
                    "url": repo_data.get("html_url", "")
                },
                "statistics": {
                    "stars": repo_data.get("stargazers_count", 0),
                    "watchers": repo_data.get("watchers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "open_issues": repo_data.get("open_issues_count", 0),
                    "contributors": len(contributors) if contributors else 0
                },
                "languages": languages,
                "analysis": analysis_data
            }
            
            return [TextContent(type="text", text=json.dumps(info, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting repository info: {str(e)}")]
    
    async def _get_file_content(self, repository: str, file_path: str, 
                              branch: str = "main") -> List[TextContent]:
        """Get the content of a specific file from a repository."""
        try:
            # Try to get from local clone first
            local_path = await self.repo_manager.get_local_path(repository)
            
            if local_path and os.path.exists(local_path):
                full_file_path = os.path.join(local_path, file_path)
                if os.path.exists(full_file_path):
                    with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    result = {
                        "repository": repository,
                        "file_path": file_path,
                        "branch": branch,
                        "source": "local",
                        "content": content,
                        "size": len(content),
                        "lines": len(content.split('\n'))
                    }
                    
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
            # Fallback to GitHub API
            file_data = await self.github_client.get_file_content(repository, file_path, branch)
            
            result = {
                "repository": repository,
                "file_path": file_path,
                "branch": branch,
                "source": "github_api",
                "content": file_data.get("content", ""),
                "size": file_data.get("size", 0),
                "sha": file_data.get("sha", ""),
                "encoding": file_data.get("encoding", "")
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting file content: {str(e)}")]
    
    async def _suggest_improvements(self, repository: str, 
                                  focus_area: Optional[str] = None) -> List[TextContent]:
        """Generate improvement suggestions for a repository."""
        try:
            # Ensure repository is cloned
            local_path = await self.repo_manager.get_local_path(repository)
            if not local_path or not os.path.exists(local_path):
                local_path = await self.repo_manager.clone_repository(repository)
            
            # Analyze repository
            analysis_result = self.analyzer.analyze_repository(local_path, repository)
            
            # Collect all suggestions
            all_suggestions = []
            for file_result in analysis_result.file_results:
                for suggestion in file_result.suggestions:
                    if not focus_area or suggestion.get('type') == focus_area:
                        all_suggestions.append({
                            "file": file_result.file_path,
                            "suggestion": suggestion
                        })
            
            # Generate repository-level suggestions
            repo_suggestions = self._generate_repository_suggestions(analysis_result, focus_area)
            
            suggestions_report = {
                "repository": repository,
                "focus_area": focus_area or "all",
                "timestamp": analysis_result.timestamp.isoformat(),
                "overall_scores": analysis_result.overall_scores,
                "file_suggestions": all_suggestions,
                "repository_suggestions": repo_suggestions,
                "priority_actions": self._prioritize_suggestions(all_suggestions + repo_suggestions)
            }
            
            return [TextContent(type="text", text=json.dumps(suggestions_report, indent=2))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error generating suggestions: {str(e)}")]
    
    def _extract_key_findings(self, analysis_result) -> List[Dict[str, Any]]:
        """Extract key findings from analysis result."""
        findings = []
        
        # High-severity security issues
        security_issues = sum(
            1 for file_result in analysis_result.file_results
            for issue in file_result.issues
            if issue.get('category') == 'security' and issue.get('severity') == 'high'
        )
        
        if security_issues > 0:
            findings.append({
                "type": "security",
                "severity": "high",
                "count": security_issues,
                "description": f"Found {security_issues} high-severity security issues"
            })
        
        # Overall quality score
        quality_score = analysis_result.overall_scores.get('quality', 0)
        if quality_score < 60:
            findings.append({
                "type": "quality",
                "severity": "medium",
                "score": quality_score,
                "description": f"Code quality score is low ({quality_score:.1f}/100)"
            })
        
        # Performance issues
        performance_issues = sum(
            1 for file_result in analysis_result.file_results
            for issue in file_result.issues
            if issue.get('category') == 'performance'
        )
        
        if performance_issues > 5:
            findings.append({
                "type": "performance",
                "severity": "medium",
                "count": performance_issues,
                "description": f"Found {performance_issues} performance optimization opportunities"
            })
        
        return findings
    
    def _generate_pr_recommendation(self, file_analyses: List[Dict], 
                                  total_issues: int, high_priority_issues: int) -> str:
        """Generate a recommendation for a pull request."""
        if high_priority_issues > 0:
            return f"⚠️  REQUIRES ATTENTION: {high_priority_issues} high-priority issues found. Please address security and critical quality issues before merging."
        elif total_issues > 10:
            return f"⚠️  REVIEW RECOMMENDED: {total_issues} issues found. Consider addressing major issues before merging."
        elif total_issues > 0:
            return f"✅ APPROVE WITH MINOR FIXES: {total_issues} minor issues found. Safe to merge with follow-up improvements."
        else:
            return "✅ APPROVED: No issues found. Safe to merge."
    
    def _generate_security_recommendations(self, security_issues: List[Dict]) -> List[Dict[str, str]]:
        """Generate security recommendations based on found issues."""
        recommendations = []
        
        # Analyze issue types
        issue_types = {}
        for file_data in security_issues:
            for issue in file_data['issues']:
                issue_type = issue.get('type', 'unknown')
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        # Generate recommendations based on common issues
        if 'hardcoded_password' in issue_types or 'hardcoded_api_key' in issue_types:
            recommendations.append({
                "priority": "high",
                "category": "secrets_management",
                "title": "Implement Proper Secrets Management",
                "description": "Use environment variables, secret management services, or encrypted configuration files instead of hardcoding sensitive information."
            })
        
        if 'dangerous_eval' in issue_types or 'command_injection' in issue_types:
            recommendations.append({
                "priority": "high",
                "category": "code_injection",
                "title": "Prevent Code Injection Vulnerabilities",
                "description": "Avoid using eval(), exec(), or system() with user input. Use safer alternatives and input validation."
            })
        
        if not recommendations:
            recommendations.append({
                "priority": "medium",
                "category": "continuous_security",
                "title": "Maintain Security Best Practices",
                "description": "Continue following security best practices and consider implementing automated security scanning in your CI/CD pipeline."
            })
        
        return recommendations
    
    def _calculate_risk_level(self, security_score: float) -> str:
        """Calculate risk level based on security score."""
        if security_score >= 80:
            return "low"
        elif security_score >= 60:
            return "medium"
        elif security_score >= 40:
            return "high"
        else:
            return "critical"
    
    def _generate_comparison_summary(self, repo_analyses: List[Dict], 
                                   metrics: List[str]) -> Dict[str, Any]:
        """Generate comparison summary for multiple repositories."""
        summary = {
            "best_performers": {},
            "average_scores": {},
            "recommendations": []
        }
        
        # Calculate averages and find best performers
        for metric in metrics:
            scores = [repo['overall_scores'].get(metric, 0) for repo in repo_analyses]
            if scores:
                summary["average_scores"][metric] = sum(scores) / len(scores)
                best_repo = max(repo_analyses, key=lambda x: x['overall_scores'].get(metric, 0))
                summary["best_performers"][metric] = {
                    "repository": best_repo['repository'],
                    "score": best_repo['overall_scores'].get(metric, 0)
                }
        
        # Generate recommendations
        lowest_avg_metric = min(summary["average_scores"].items(), key=lambda x: x[1])
        summary["recommendations"].append({
            "focus_area": lowest_avg_metric[0],
            "average_score": lowest_avg_metric[1],
            "suggestion": f"Consider improving {lowest_avg_metric[0]} across all repositories"
        })
        
        return summary
    
    def _generate_repository_suggestions(self, analysis_result, focus_area: Optional[str]) -> List[Dict[str, Any]]:
        """Generate repository-level improvement suggestions."""
        suggestions = []
        
        # Based on overall scores
        if analysis_result.overall_scores.get('security', 100) < 70:
            suggestions.append({
                "type": "security",
                "priority": "high",
                "category": "repository",
                "description": "Implement comprehensive security review process and automated security scanning"
            })
        
        if analysis_result.overall_scores.get('quality', 100) < 60:
            suggestions.append({
                "type": "quality",
                "priority": "medium", 
                "category": "repository",
                "description": "Establish code review guidelines and quality gates in CI/CD pipeline"
            })
        
        # Based on repository structure
        if analysis_result.analyzed_files > 200:
            suggestions.append({
                "type": "maintainability",
                "priority": "medium",
                "category": "repository",
                "description": "Consider modularizing large codebase into smaller, focused components"
            })
        
        # Filter by focus area if specified
        if focus_area:
            suggestions = [s for s in suggestions if s.get('type') == focus_area]
        
        return suggestions
    
    def _prioritize_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize suggestions by importance and impact."""
        priority_order = {"high": 3, "medium": 2, "low": 1}
        
        # Sort by priority and type
        sorted_suggestions = sorted(
            suggestions,
            key=lambda x: (
                priority_order.get(x.get('priority', 'low'), 1),
                x.get('type', 'unknown')
            ),
            reverse=True
        )
        
        return sorted_suggestions[:10]  # Return top 10 priority actions
