"""
Configuration management for the GitHub Code Review MCP Server.

Loads configuration from environment variables with sensible defaults.
"""

import os
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration class for the MCP server."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration from environment variables."""
        # Load environment variables from .env file
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from common locations
            for env_path in ['.env', '.env.local', '../.env']:
                if Path(env_path).exists():
                    load_dotenv(env_path)
                    break
        
        # GitHub Authentication
        self.GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
        self.GITHUB_APP_ID = os.getenv('GITHUB_APP_ID')
        self.GITHUB_APP_PRIVATE_KEY_PATH = os.getenv('GITHUB_APP_PRIVATE_KEY_PATH')
        self.GITHUB_APP_INSTALLATION_ID = os.getenv('GITHUB_APP_INSTALLATION_ID')
        
        # Target Configuration
        self.GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', '01abhi01')
        self.DEFAULT_BRANCH = os.getenv('DEFAULT_BRANCH', 'main')
        
        # Repository Settings
        self.MAX_REPOSITORIES = int(os.getenv('MAX_REPOSITORIES', '50'))
        self.INCLUDE_PRIVATE_REPOS = os.getenv('INCLUDE_PRIVATE_REPOS', 'false').lower() == 'true'
        self.INCLUDE_FORKS = os.getenv('INCLUDE_FORKS', 'false').lower() == 'true'
        
        # Analysis Configuration
        self.MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '1048576'))  # 1MB
        self.ANALYSIS_TIMEOUT = int(os.getenv('ANALYSIS_TIMEOUT', '300'))  # 5 minutes
        self.ENABLE_SECURITY_SCAN = os.getenv('ENABLE_SECURITY_SCAN', 'true').lower() == 'true'
        self.ENABLE_PERFORMANCE_SCAN = os.getenv('ENABLE_PERFORMANCE_SCAN', 'true').lower() == 'true'
        self.ENABLE_DEPENDENCY_SCAN = os.getenv('ENABLE_DEPENDENCY_SCAN', 'true').lower() == 'true'
        
        # Supported Languages
        self.SUPPORTED_LANGUAGES = os.getenv(
            'SUPPORTED_LANGUAGES', 
            'python,javascript,typescript,java,go,rust,cpp,csharp,php,ruby'
        )
        
        # Code Review Settings
        self.REVIEW_DEPTH = os.getenv('REVIEW_DEPTH', 'comprehensive')
        self.FOCUS_AREAS = os.getenv('FOCUS_AREAS', 'security,performance,maintainability,style')
        self.AUTO_SUGGEST_FIXES = os.getenv('AUTO_SUGGEST_FIXES', 'true').lower() == 'true'
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.LOG_FILE = os.getenv('LOG_FILE', './logs/github_code_review.log')
        self.ENABLE_FILE_LOGGING = os.getenv('ENABLE_FILE_LOGGING', 'true').lower() == 'true'
        
        # MCP Server Configuration
        self.MCP_SERVER_NAME = os.getenv('MCP_SERVER_NAME', 'dynamic-github-code-review')
        self.MCP_SERVER_VERSION = os.getenv('MCP_SERVER_VERSION', '1.0.0')
        self.SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
        self.SERVER_PORT = int(os.getenv('SERVER_PORT', '8000'))
        
        # API Configuration
        self.GITHUB_API_RATE_LIMIT = int(os.getenv('GITHUB_API_RATE_LIMIT', '5000'))
        self.REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '0.1'))
        
        # Cache Configuration
        self.ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        self.CACHE_DURATION = int(os.getenv('CACHE_DURATION', '3600'))  # 1 hour
        self.CACHE_DIR = os.getenv('CACHE_DIR', './cache')
        
        # Analysis Exclusions
        self.EXCLUDE_PATTERNS = os.getenv(
            'EXCLUDE_PATTERNS',
            '__pycache__,*.pyc,node_modules,*.log,*.tmp,.git,.vscode,.idea'
        ).split(',')
        
        self.EXCLUDE_DIRECTORIES = os.getenv(
            'EXCLUDE_DIRECTORIES',
            'venv,env,.venv,dist,build'
        ).split(',')
        
        # Security Settings
        self.MASK_SENSITIVE_DATA = os.getenv('MASK_SENSITIVE_DATA', 'true').lower() == 'true'
        self.SANITIZE_OUTPUT = os.getenv('SANITIZE_OUTPUT', 'true').lower() == 'true'
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration and raise errors for missing required values."""
        if not self.GITHUB_TOKEN and not (
            self.GITHUB_APP_ID and 
            self.GITHUB_APP_PRIVATE_KEY_PATH and 
            self.GITHUB_APP_INSTALLATION_ID
        ):
            raise ValueError(
                "GitHub authentication not configured. "
                "Set GITHUB_TOKEN or GitHub App credentials (GITHUB_APP_ID, "
                "GITHUB_APP_PRIVATE_KEY_PATH, GITHUB_APP_INSTALLATION_ID)."
            )
        
        if not self.GITHUB_USERNAME:
            raise ValueError("GITHUB_USERNAME is required")
        
        # Ensure required directories exist
        Path(self.CACHE_DIR).mkdir(parents=True, exist_ok=True)
        
        if self.ENABLE_FILE_LOGGING:
            Path(self.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return [lang.strip().lower() for lang in self.SUPPORTED_LANGUAGES.split(',')]
    
    def get_focus_areas(self) -> List[str]:
        """Get list of code review focus areas."""
        return [area.strip().lower() for area in self.FOCUS_AREAS.split(',')]
    
    def is_file_excluded(self, file_path: str) -> bool:
        """Check if a file should be excluded from analysis."""
        import fnmatch
        
        # Check exclude patterns
        for pattern in self.EXCLUDE_PATTERNS:
            if fnmatch.fnmatch(file_path, pattern.strip()):
                return True
        
        # Check exclude directories
        path_parts = Path(file_path).parts
        for exclude_dir in self.EXCLUDE_DIRECTORIES:
            if exclude_dir.strip() in path_parts:
                return True
        
        return False
    
    def __repr__(self):
        """String representation of configuration (excluding sensitive data)."""
        safe_attrs = {
            'GITHUB_USERNAME': self.GITHUB_USERNAME,
            'MCP_SERVER_NAME': self.MCP_SERVER_NAME,
            'MCP_SERVER_VERSION': self.MCP_SERVER_VERSION,
            'SUPPORTED_LANGUAGES': self.SUPPORTED_LANGUAGES,
            'LOG_LEVEL': self.LOG_LEVEL,
            'MAX_REPOSITORIES': self.MAX_REPOSITORIES,
            'ENABLE_SECURITY_SCAN': self.ENABLE_SECURITY_SCAN,
            'ENABLE_PERFORMANCE_SCAN': self.ENABLE_PERFORMANCE_SCAN
        }
        
        return f"Config({', '.join(f'{k}={v}' for k, v in safe_attrs.items())})"
