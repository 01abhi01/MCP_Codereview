"""
GitHub Code Review MCP Server

A comprehensive Model Context Protocol server for dynamic GitHub repository
analysis and code review. Supports multi-language code analysis with 
security, quality, and performance insights.
"""

__version__ = "1.0.0"
__author__ = "GitHub Code Review Team"
__license__ = "MIT"

from .main import DynamicGitHubCodeReviewServer

__all__ = ['DynamicGitHubCodeReviewServer']
