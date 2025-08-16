"""
Logging configuration and utilities for the GitHub Code Review MCP Server.

Provides structured logging with configurable output formats and destinations.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_obj.update(record.extra)
        
        return json.dumps(log_obj)


class CodeReviewLogger:
    """Logger configuration for the GitHub Code Review MCP Server."""
    
    def __init__(self, config):
        """Initialize logging configuration."""
        self.config = config
        self.logger = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration based on config."""
        # Create main logger
        self.logger = logging.getLogger('github_code_review')
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Format based on log level
        if self.config.LOG_LEVEL == 'DEBUG':
            console_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
            )
        else:
            console_format = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler (if enabled)
        if self.config.ENABLE_FILE_LOGGING:
            self._setup_file_logging()
        
        # Suppress verbose third-party loggers
        self._suppress_third_party_logs()
    
    def _setup_file_logging(self):
        """Setup file logging with rotation."""
        log_file = Path(self.config.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler (10MB max, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Use JSON format for file logs for better parsing
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)
    
    def _suppress_third_party_logs(self):
        """Suppress verbose third-party library logs."""
        # Suppress GitHub library debug logs
        logging.getLogger('github').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('aiohttp').setLevel(logging.WARNING)
        
        # Only show errors from these libraries unless we're in debug mode
        if self.config.LOG_LEVEL != 'DEBUG':
            logging.getLogger('asyncio').setLevel(logging.ERROR)
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance."""
        if name:
            return logging.getLogger(f'github_code_review.{name}')
        return self.logger
    
    def log_analysis_start(self, repository: str, analysis_type: str):
        """Log the start of a code analysis."""
        self.logger.info(
            f"Starting {analysis_type} analysis for repository: {repository}",
            extra={
                'event_type': 'analysis_start',
                'repository': repository,
                'analysis_type': analysis_type
            }
        )
    
    def log_analysis_complete(self, repository: str, analysis_type: str, 
                            duration: float, issues_found: int):
        """Log the completion of a code analysis."""
        self.logger.info(
            f"Completed {analysis_type} analysis for {repository} "
            f"in {duration:.2f}s - Found {issues_found} issues",
            extra={
                'event_type': 'analysis_complete',
                'repository': repository,
                'analysis_type': analysis_type,
                'duration': duration,
                'issues_found': issues_found
            }
        )
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, 
                    duration: float):
        """Log GitHub API calls."""
        self.logger.debug(
            f"GitHub API {method} {endpoint} - {status_code} ({duration:.3f}s)",
            extra={
                'event_type': 'api_call',
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'duration': duration
            }
        )
    
    def log_rate_limit(self, remaining: int, reset_time: int):
        """Log rate limit information."""
        if remaining < 100:
            self.logger.warning(
                f"GitHub API rate limit low: {remaining} requests remaining "
                f"(resets at {datetime.fromtimestamp(reset_time)})",
                extra={
                    'event_type': 'rate_limit_warning',
                    'remaining': remaining,
                    'reset_time': reset_time
                }
            )
    
    def log_error(self, message: str, error: Exception = None, **kwargs):
        """Log an error with optional exception details."""
        extra = {'event_type': 'error'}
        extra.update(kwargs)
        
        if error:
            self.logger.error(f"{message}: {str(error)}", exc_info=error, extra=extra)
        else:
            self.logger.error(message, extra=extra)
    
    def log_repository_discovered(self, repository: str, language: str, 
                                 framework: Optional[str] = None):
        """Log repository discovery."""
        message = f"Discovered repository: {repository} ({language}"
        if framework:
            message += f", {framework}"
        message += ")"
        
        self.logger.info(
            message,
            extra={
                'event_type': 'repository_discovered',
                'repository': repository,
                'language': language,
                'framework': framework
            }
        )
    
    def log_mcp_request(self, method: str, resource: str, params: dict = None):
        """Log MCP protocol requests."""
        self.logger.debug(
            f"MCP Request: {method} {resource}",
            extra={
                'event_type': 'mcp_request',
                'method': method,
                'resource': resource,
                'params': params or {}
            }
        )
    
    def log_security_issue(self, repository: str, file_path: str, 
                          issue_type: str, severity: str, description: str):
        """Log security issues found during analysis."""
        self.logger.warning(
            f"Security issue in {repository}/{file_path}: {issue_type} ({severity}) - {description}",
            extra={
                'event_type': 'security_issue',
                'repository': repository,
                'file_path': file_path,
                'issue_type': issue_type,
                'severity': severity,
                'description': description
            }
        )
    
    def log_performance_issue(self, repository: str, file_path: str,
                             issue_type: str, description: str, suggestion: str = None):
        """Log performance issues found during analysis."""
        message = f"Performance issue in {repository}/{file_path}: {issue_type} - {description}"
        if suggestion:
            message += f" | Suggestion: {suggestion}"
        
        self.logger.info(
            message,
            extra={
                'event_type': 'performance_issue',
                'repository': repository,
                'file_path': file_path,
                'issue_type': issue_type,
                'description': description,
                'suggestion': suggestion
            }
        )


# Global logger instance
_logger_instance: Optional[CodeReviewLogger] = None


def setup_logging(config) -> CodeReviewLogger:
    """Setup global logging configuration."""
    global _logger_instance
    _logger_instance = CodeReviewLogger(config)
    return _logger_instance


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    if _logger_instance is None:
        raise RuntimeError("Logging not initialized. Call setup_logging() first.")
    return _logger_instance.get_logger(name)


def log_analysis_start(repository: str, analysis_type: str):
    """Log the start of a code analysis."""
    if _logger_instance:
        _logger_instance.log_analysis_start(repository, analysis_type)


def log_analysis_complete(repository: str, analysis_type: str, 
                         duration: float, issues_found: int):
    """Log the completion of a code analysis."""
    if _logger_instance:
        _logger_instance.log_analysis_complete(repository, analysis_type, duration, issues_found)


def log_error(message: str, error: Exception = None, **kwargs):
    """Log an error with optional exception details."""
    if _logger_instance:
        _logger_instance.log_error(message, error, **kwargs)
