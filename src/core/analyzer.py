"""
Code analysis module for the GitHub Code Review MCP Server.

Provides comprehensive code analysis including security scanning, performance analysis,
and quality metrics for multiple programming languages.
"""

import ast
import os
import subprocess
import tempfile
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..utils import get_logger, Config
from ..utils.helpers import (
    get_file_extension,
    is_binary_file,
    calculate_complexity,
    extract_imports,
    find_security_patterns,
    detect_dependencies,
    calculate_file_hash
)


@dataclass
class AnalysisResult:
    """Result of code analysis."""
    file_path: str
    language: str
    issues: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    suggestions: List[Dict[str, Any]]
    security_score: float
    quality_score: float
    performance_score: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'file_path': self.file_path,
            'language': self.language,
            'issues': self.issues,
            'metrics': self.metrics,
            'suggestions': self.suggestions,
            'scores': {
                'security': self.security_score,
                'quality': self.quality_score,
                'performance': self.performance_score
            },
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class RepositoryAnalysis:
    """Complete repository analysis result."""
    repository: str
    total_files: int
    analyzed_files: int
    languages: Dict[str, int]
    overall_scores: Dict[str, float]
    file_results: List[AnalysisResult]
    dependencies: Dict[str, List[str]]
    summary: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'repository': self.repository,
            'total_files': self.total_files,
            'analyzed_files': self.analyzed_files,
            'languages': self.languages,
            'overall_scores': self.overall_scores,
            'file_results': [result.to_dict() for result in self.file_results],
            'dependencies': self.dependencies,
            'summary': self.summary,
            'timestamp': self.timestamp.isoformat()
        }


class CodeAnalyzer:
    """Main code analyzer for multiple programming languages."""
    
    def __init__(self, config: Config):
        """Initialize the code analyzer."""
        self.config = config
        self.logger = get_logger('analyzer')
        self.supported_languages = self._get_supported_languages()
        self.analyzers = self._setup_analyzers()
    
    def _get_supported_languages(self) -> Dict[str, List[str]]:
        """Get supported languages and their file extensions."""
        return {
            'python': ['.py', '.pyw'],
            'javascript': ['.js', '.jsx', '.mjs'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'cpp': ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.h'],
            'c': ['.c', '.h'],
            'csharp': ['.cs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'swift': ['.swift'],
            'kotlin': ['.kt'],
            'scala': ['.scala'],
            'r': ['.r', '.R'],
            'sql': ['.sql'],
            'bash': ['.sh'],
            'powershell': ['.ps1'],
            'yaml': ['.yml', '.yaml'],
            'json': ['.json'],
            'xml': ['.xml'],
            'html': ['.html', '.htm'],
            'css': ['.css'],
            'scss': ['.scss'],
            'less': ['.less']
        }
    
    def _setup_analyzers(self) -> Dict[str, Any]:
        """Setup language-specific analyzers."""
        analyzers = {}
        
        # Check for available tools
        if self._tool_available('bandit'):
            analyzers['python_security'] = 'bandit'
        
        if self._tool_available('pylint'):
            analyzers['python_quality'] = 'pylint'
        
        if self._tool_available('flake8'):
            analyzers['python_style'] = 'flake8'
        
        if self._tool_available('eslint'):
            analyzers['js_quality'] = 'eslint'
        
        if self._tool_available('jshint'):
            analyzers['js_lint'] = 'jshint'
        
        if self._tool_available('checkstyle'):
            analyzers['java_style'] = 'checkstyle'
        
        if self._tool_available('spotbugs'):
            analyzers['java_bugs'] = 'spotbugs'
        
        if self._tool_available('gofmt'):
            analyzers['go_format'] = 'gofmt'
        
        if self._tool_available('golint'):
            analyzers['go_lint'] = 'golint'
        
        if self._tool_available('ansible-lint'):
            analyzers['ansible_lint'] = 'ansible-lint'
        
        if self._tool_available('yamllint'):
            analyzers['yaml_lint'] = 'yamllint'
        
        return analyzers
    
    def _tool_available(self, tool_name: str) -> bool:
        """Check if a command-line tool is available."""
        try:
            subprocess.run([tool_name, '--version'], 
                         capture_output=True, timeout=5)
            return True
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def analyze_repository(self, repo_path: str, repository_name: str) -> RepositoryAnalysis:
        """Analyze an entire repository."""
        self.logger.info(f"Starting repository analysis: {repository_name}")
        
        start_time = datetime.now()
        
        # Discover files
        all_files = self._discover_files(repo_path)
        
        # Filter analyzable files
        analyzable_files = [f for f in all_files if self._is_analyzable(f)]
        
        self.logger.info(f"Found {len(all_files)} total files, {len(analyzable_files)} analyzable")
        
        # Analyze files
        file_results = []
        languages = {}
        
        for file_path in analyzable_files:
            if len(file_results) >= 100:  # Limit for performance
                self.logger.warning("Reached file analysis limit (100 files)")
                break
            
            try:
                result = self.analyze_file(file_path)
                if result:
                    file_results.append(result)
                    lang = result.language
                    languages[lang] = languages.get(lang, 0) + 1
            except Exception as e:
                self.logger.error(f"Error analyzing {file_path}: {e}")
        
        # Calculate overall scores
        overall_scores = self._calculate_overall_scores(file_results)
        
        # Detect dependencies
        dependencies = self._analyze_dependencies(repo_path)
        
        # Generate summary
        summary = self._generate_summary(file_results, languages, dependencies)
        
        analysis = RepositoryAnalysis(
            repository=repository_name,
            total_files=len(all_files),
            analyzed_files=len(file_results),
            languages=languages,
            overall_scores=overall_scores,
            file_results=file_results,
            dependencies=dependencies,
            summary=summary,
            timestamp=datetime.now()
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Repository analysis completed in {duration:.2f}s")
        
        return analysis
    
    def analyze_file(self, file_path: str) -> Optional[AnalysisResult]:
        """Analyze a single file."""
        if not os.path.exists(file_path) or is_binary_file(file_path):
            return None
        
        # Check file size
        if os.path.getsize(file_path) > self.config.MAX_FILE_SIZE:
            self.logger.warning(f"Skipping large file: {file_path}")
            return None
        
        # Detect language
        language = self._detect_language(file_path)
        if not language:
            return None
        
        self.logger.debug(f"Analyzing {file_path} as {language}")
        
        try:
            # Basic metrics
            metrics = calculate_complexity(file_path, language)
            metrics['file_size'] = os.path.getsize(file_path)
            metrics['file_hash'] = calculate_file_hash(file_path)
            
            # Security analysis
            security_issues = self._analyze_security(file_path, language)
            
            # Quality analysis
            quality_issues = self._analyze_quality(file_path, language)
            
            # Performance analysis
            performance_issues = self._analyze_performance(file_path, language)
            
            # Combine all issues
            all_issues = security_issues + quality_issues + performance_issues
            
            # Calculate scores
            security_score = self._calculate_security_score(security_issues, metrics)
            quality_score = self._calculate_quality_score(quality_issues, metrics)
            performance_score = self._calculate_performance_score(performance_issues, metrics)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(all_issues, metrics, language)
            
            return AnalysisResult(
                file_path=file_path,
                language=language,
                issues=all_issues,
                metrics=metrics,
                suggestions=suggestions,
                security_score=security_score,
                quality_score=quality_score,
                performance_score=performance_score,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _discover_files(self, repo_path: str) -> List[str]:
        """Discover all files in a repository."""
        files = []
        
        for root, dirs, filenames in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self.config.is_file_excluded(d)]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if not self.config.is_file_excluded(file_path):
                    files.append(file_path)
        
        return files
    
    def _is_analyzable(self, file_path: str) -> bool:
        """Check if a file can be analyzed."""
        if is_binary_file(file_path):
            return False
        
        ext = get_file_extension(file_path)
        
        # Check if extension is supported
        for language, extensions in self.supported_languages.items():
            if ext in extensions:
                return True
        
        return False
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect the programming language of a file."""
        ext = get_file_extension(file_path)
        
        for language, extensions in self.supported_languages.items():
            if ext in extensions:
                return language
        
        return None
    
    def _analyze_security(self, file_path: str, language: str) -> List[Dict[str, Any]]:
        """Analyze file for security issues."""
        issues = []
        
        # Pattern-based security analysis
        pattern_issues = find_security_patterns(file_path, language)
        for issue in pattern_issues:
            issues.append({
                'category': 'security',
                'type': issue['type'],
                'severity': issue['severity'],
                'description': issue['description'],
                'line': issue['line'],
                'code': issue.get('code', ''),
                'tool': 'pattern_analysis'
            })
        
        # Tool-based analysis
        if language == 'python' and 'python_security' in self.analyzers:
            tool_issues = self._run_bandit(file_path)
            issues.extend(tool_issues)
        elif language == 'yaml':
            yaml_security_issues = self._analyze_yaml_security(file_path)
            issues.extend(yaml_security_issues)
            
            # Run additional YAML tools if available
            if 'ansible_lint' in self.analyzers and self._is_ansible_file(file_path, open(file_path).read()):
                ansible_issues = self._run_ansible_lint(file_path)
                issues.extend(ansible_issues)
        
        return issues
    
    def _analyze_quality(self, file_path: str, language: str) -> List[Dict[str, Any]]:
        """Analyze file for quality issues."""
        issues = []
        
        # Language-specific quality analysis
        if language == 'python':
            issues.extend(self._analyze_python_quality(file_path))
        elif language in ['javascript', 'typescript']:
            issues.extend(self._analyze_js_quality(file_path))
        elif language == 'java':
            issues.extend(self._analyze_java_quality(file_path))
        elif language == 'yaml':
            issues.extend(self._analyze_yaml_quality(file_path))
            
            # Run YAML linting tools if available
            if 'yaml_lint' in self.analyzers:
                yaml_issues = self._run_yamllint(file_path)
                issues.extend(yaml_issues)
        
        return issues
    
    def _analyze_performance(self, file_path: str, language: str) -> List[Dict[str, Any]]:
        """Analyze file for performance issues."""
        issues = []
        
        # Language-specific performance analysis
        if language == 'python':
            issues.extend(self._analyze_python_performance(file_path))
        elif language in ['javascript', 'typescript']:
            issues.extend(self._analyze_js_performance(file_path))
        elif language == 'yaml':
            issues.extend(self._analyze_yaml_performance(file_path))
        
        return issues
    
    def _run_bandit(self, file_path: str) -> List[Dict[str, Any]]:
        """Run bandit security analysis on Python file."""
        issues = []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_output = temp_file.name
            
            cmd = ['bandit', '-f', 'json', '-o', temp_output, file_path]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if os.path.exists(temp_output):
                with open(temp_output, 'r') as f:
                    bandit_output = json.load(f)
                
                for result_item in bandit_output.get('results', []):
                    issues.append({
                        'category': 'security',
                        'type': result_item.get('test_id', 'unknown'),
                        'severity': result_item.get('issue_severity', 'medium').lower(),
                        'description': result_item.get('issue_text', ''),
                        'line': result_item.get('line_number', 0),
                        'code': result_item.get('code', ''),
                        'tool': 'bandit',
                        'confidence': result_item.get('issue_confidence', 'medium').lower()
                    })
                
                os.unlink(temp_output)
        
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            self.logger.warning(f"Bandit analysis failed for {file_path}: {e}")
        
        return issues
    
    def _run_ansible_lint(self, file_path: str) -> List[Dict[str, Any]]:
        """Run ansible-lint on Ansible YAML files."""
        issues = []
        
        try:
            cmd = ['ansible-lint', '-f', 'json', file_path]
            result = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
            
            if result.returncode != 0 and result.stdout:
                try:
                    lint_output = json.loads(result.stdout)
                    for issue in lint_output:
                        issues.append({
                            'category': 'quality',
                            'type': f"ansible_lint_{issue.get('tag', 'unknown')}",
                            'severity': self._map_ansible_lint_severity(issue.get('level', 'warning')),
                            'description': issue.get('message', 'Ansible lint issue'),
                            'line': issue.get('linenumber', 0),
                            'code': '',
                            'tool': 'ansible-lint',
                            'rule': issue.get('tag', '')
                        })
                except json.JSONDecodeError:
                    # Fallback to parsing text output
                    for line in result.stdout.split('\n'):
                        if ':' in line and any(severity in line.lower() for severity in ['error', 'warning']):
                            issues.append({
                                'category': 'quality',
                                'type': 'ansible_lint_issue',
                                'severity': 'medium',
                                'description': line.strip(),
                                'line': 0,
                                'code': '',
                                'tool': 'ansible-lint'
                            })
        
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.warning(f"Ansible-lint analysis failed for {file_path}: {e}")
        
        return issues
    
    def _run_yamllint(self, file_path: str) -> List[Dict[str, Any]]:
        """Run yamllint on YAML files."""
        issues = []
        
        try:
            cmd = ['yamllint', '-f', 'json', file_path]
            result = subprocess.run(cmd, capture_output=True, timeout=30, text=True)
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            issue = json.loads(line)
                            issues.append({
                                'category': 'quality',
                                'type': f"yaml_lint_{issue.get('type', 'unknown')}",
                                'severity': self._map_yamllint_severity(issue.get('level', 'warning')),
                                'description': issue.get('desc', 'YAML lint issue'),
                                'line': issue.get('line', 0),
                                'code': '',
                                'tool': 'yamllint',
                                'rule': issue.get('rule', '')
                            })
                        except json.JSONDecodeError:
                            continue
        
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.warning(f"Yamllint analysis failed for {file_path}: {e}")
        
        return issues
    
    def _map_ansible_lint_severity(self, level: str) -> str:
        """Map ansible-lint severity levels to our standard levels."""
        mapping = {
            'very_high': 'high',
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
            'very_low': 'low',
            'info': 'low'
        }
        return mapping.get(level.lower(), 'medium')
    
    def _map_yamllint_severity(self, level: str) -> str:
        """Map yamllint severity levels to our standard levels."""
        mapping = {
            'error': 'high',
            'warning': 'medium',
            'info': 'low'
        }
        return mapping.get(level.lower(), 'medium')
    
    def _analyze_python_quality(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze Python file for quality issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # AST-based analysis
            try:
                tree = ast.parse(content)
                
                # Check for common quality issues
                for node in ast.walk(tree):
                    # Too many arguments
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if len(node.args.args) > 7:
                            issues.append({
                                'category': 'quality',
                                'type': 'too_many_arguments',
                                'severity': 'medium',
                                'description': f'Function has {len(node.args.args)} arguments (max recommended: 7)',
                                'line': node.lineno,
                                'tool': 'ast_analysis'
                            })
                    
                    # Long line length (simple check)
                    if hasattr(node, 'lineno'):
                        line = content.split('\n')[node.lineno - 1] if node.lineno <= len(content.split('\n')) else ''
                        if len(line) > 120:
                            issues.append({
                                'category': 'quality',
                                'type': 'long_line',
                                'severity': 'low',
                                'description': f'Line length {len(line)} exceeds 120 characters',
                                'line': node.lineno,
                                'tool': 'ast_analysis'
                            })
            
            except SyntaxError as e:
                issues.append({
                    'category': 'quality',
                    'type': 'syntax_error',
                    'severity': 'high',
                    'description': f'Syntax error: {str(e)}',
                    'line': e.lineno or 0,
                    'tool': 'ast_analysis'
                })
        
        except Exception as e:
            self.logger.warning(f"Python quality analysis failed for {file_path}: {e}")
        
        return issues
    
    def _analyze_js_quality(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze JavaScript/TypeScript file for quality issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for console.log statements
                if re.search(r'console\.(log|debug|info|warn|error)', line):
                    issues.append({
                        'category': 'quality',
                        'type': 'console_statement',
                        'severity': 'low',
                        'description': 'Console statement found (should be removed in production)',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'pattern_analysis'
                    })
                
                # Check for var usage (prefer let/const)
                if re.search(r'\bvar\s+\w+', line):
                    issues.append({
                        'category': 'quality',
                        'type': 'var_usage',
                        'severity': 'medium',
                        'description': 'Use of var (prefer let/const)',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'pattern_analysis'
                    })
                
                # Check for == usage (prefer ===)
                if re.search(r'[^=!]==[^=]', line):
                    issues.append({
                        'category': 'quality',
                        'type': 'loose_equality',
                        'severity': 'medium',
                        'description': 'Use of == (prefer === for strict equality)',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'pattern_analysis'
                    })
        
        except Exception as e:
            self.logger.warning(f"JavaScript quality analysis failed for {file_path}: {e}")
        
        return issues
    
    def _analyze_java_quality(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze Java file for quality issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for System.out.println
                if 'System.out.println' in line:
                    issues.append({
                        'category': 'quality',
                        'type': 'system_out_println',
                        'severity': 'low',
                        'description': 'System.out.println found (use logging instead)',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'pattern_analysis'
                    })
                
                # Check for empty catch blocks
                if re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', line):
                    issues.append({
                        'category': 'quality',
                        'type': 'empty_catch',
                        'severity': 'high',
                        'description': 'Empty catch block (should handle or log exception)',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'pattern_analysis'
                    })
        
        except Exception as e:
            self.logger.warning(f"Java quality analysis failed for {file_path}: {e}")
        
        return issues
    
    def _analyze_python_performance(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze Python file for performance issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for string concatenation in loops
                if '+=' in line and any(keyword in line for keyword in ['for ', 'while ']):
                    issues.append({
                        'category': 'performance',
                        'type': 'string_concatenation_in_loop',
                        'severity': 'medium',
                        'description': 'String concatenation in loop (consider using join() or list)',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'pattern_analysis'
                    })
                
                # Check for list comprehension opportunities
                if re.search(r'for\s+\w+\s+in\s+.*:\s*\w+\.append\(', line):
                    issues.append({
                        'category': 'performance',
                        'type': 'list_comprehension_opportunity',
                        'severity': 'low',
                        'description': 'Consider using list comprehension for better performance',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'pattern_analysis'
                    })
        
        except Exception as e:
            self.logger.warning(f"Python performance analysis failed for {file_path}: {e}")
        
        return issues
    
    def _analyze_js_performance(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze JavaScript/TypeScript file for performance issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for inefficient DOM queries
                if re.search(r'document\.getElementById|document\.querySelector', line):
                    if 'for' in line or 'while' in line:
                        issues.append({
                            'category': 'performance',
                            'type': 'dom_query_in_loop',
                            'severity': 'medium',
                            'description': 'DOM query in loop (cache the result outside loop)',
                            'line': i,
                            'code': line.strip(),
                            'tool': 'pattern_analysis'
                        })
                
                # Check for inefficient array methods
                if re.search(r'\.indexOf\(.*\)\s*[><!]=?\s*-?1', line):
                    issues.append({
                        'category': 'performance',
                        'type': 'inefficient_array_search',
                        'severity': 'low',
                        'description': 'Consider using .includes() instead of .indexOf() for existence check',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'pattern_analysis'
                    })
        
        except Exception as e:
            self.logger.warning(f"JavaScript performance analysis failed for {file_path}: {e}")
        
        return issues
    
    def _analyze_yaml_security(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze YAML file for security issues, especially Ansible-specific ones."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            is_ansible = self._is_ansible_file(file_path, content)
            
            for i, line in enumerate(lines, 1):
                # General YAML security issues
                
                # Check for hardcoded secrets
                if re.search(r'(password|secret|key|token|api_key):\s*["\']?[a-zA-Z0-9_\-+=\/]{8,}["\']?', line, re.IGNORECASE):
                    issues.append({
                        'category': 'security',
                        'type': 'hardcoded_secret',
                        'severity': 'high',
                        'description': 'Hardcoded secret or credential detected',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'yaml_security_analysis'
                    })
                
                # Check for URLs with credentials
                if re.search(r'https?://[^:]+:[^@]+@', line):
                    issues.append({
                        'category': 'security',
                        'type': 'url_with_credentials',
                        'severity': 'high',
                        'description': 'URL contains embedded credentials',
                        'line': i,
                        'code': line.strip(),
                        'tool': 'yaml_security_analysis'
                    })
                
                # Ansible-specific security checks
                if is_ansible:
                    # Check for shell commands with user input
                    if re.search(r'(shell|command):', line):
                        if '{{' in line and any(unsafe in line.lower() for unsafe in ['user_input', 'ansible_user', 'item']):
                            issues.append({
                                'category': 'security',
                                'type': 'ansible_shell_injection',
                                'severity': 'high',
                                'description': 'Potential shell injection via unescaped user input',
                                'line': i,
                                'code': line.strip(),
                                'tool': 'ansible_security_analysis'
                            })
                    
                    # Check for privilege escalation without become
                    if re.search(r'(shell|command):.*sudo', line) and 'become:' not in content:
                        issues.append({
                            'category': 'security',
                            'type': 'ansible_unsafe_sudo',
                            'severity': 'medium',
                            'description': 'Use become instead of sudo in shell commands',
                            'line': i,
                            'code': line.strip(),
                            'tool': 'ansible_security_analysis'
                        })
                    
                    # Check for file permissions issues
                    if 'mode:' in line:
                        mode_match = re.search(r'mode:\s*["\']?(\d+)["\']?', line)
                        if mode_match:
                            mode = mode_match.group(1)
                            if len(mode) == 3 and mode.endswith('7'):  # World writable
                                issues.append({
                                    'category': 'security',
                                    'type': 'ansible_world_writable',
                                    'severity': 'medium',
                                    'description': 'File/directory is world-writable, consider restricting permissions',
                                    'line': i,
                                    'code': line.strip(),
                                    'tool': 'ansible_security_analysis'
                                })
                    
                    # Check for unsafe file operations
                    if 'src:' in line and '{{' in line:
                        if not re.search(r'\|\s*quote', line):  # No quote filter
                            issues.append({
                                'category': 'security',
                                'type': 'ansible_unquoted_src',
                                'severity': 'medium',
                                'description': 'Use quote filter for dynamic file paths to prevent injection',
                                'line': i,
                                'code': line.strip(),
                                'tool': 'ansible_security_analysis'
                            })
                    
                    # Check for debug tasks that might leak sensitive info
                    if 'debug:' in line and ('var:' in line or 'msg:' in line):
                        if any(sensitive in line.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                            issues.append({
                                'category': 'security',
                                'type': 'ansible_debug_sensitive',
                                'severity': 'medium',
                                'description': 'Debug statement might expose sensitive information',
                                'line': i,
                                'code': line.strip(),
                                'tool': 'ansible_security_analysis'
                            })
                    
                    # Check for missing no_log on sensitive tasks
                    if any(module in line for module in ['user:', 'mysql_user:', 'postgresql_user:']):
                        if 'password' in line and 'no_log:' not in content[max(0, content.rfind('\n', 0, content.find(line))):content.find(line) + len(line) + 200]:
                            issues.append({
                                'category': 'security',
                                'type': 'ansible_missing_no_log',
                                'severity': 'high',
                                'description': 'Tasks with passwords should use no_log: true',
                                'line': i,
                                'code': line.strip(),
                                'tool': 'ansible_security_analysis'
                            })
        
        except Exception as e:
            self.logger.warning(f"YAML security analysis failed for {file_path}: {e}")
        
        return issues
    
    def _analyze_yaml_quality(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze YAML file for quality and Ansible-specific issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            is_ansible = self._is_ansible_file(file_path, content)
            
            for i, line in enumerate(lines, 1):
                # Basic YAML quality checks
                
                # Check for tabs (YAML should use spaces)
                if '\t' in line:
                    issues.append({
                        'category': 'quality',
                        'type': 'yaml_tabs',
                        'severity': 'medium',
                        'description': 'YAML files should use spaces, not tabs for indentation',
                        'line': i,
                        'code': line.rstrip(),
                        'tool': 'yaml_analysis'
                    })
                
                # Check for trailing whitespace
                if line.rstrip() != line and line.strip():
                    issues.append({
                        'category': 'quality',
                        'type': 'trailing_whitespace',
                        'severity': 'low',
                        'description': 'Remove trailing whitespace',
                        'line': i,
                        'code': line.rstrip(),
                        'tool': 'yaml_analysis'
                    })
                
                # Check for inconsistent indentation (not multiple of 2)
                if line.strip() and line.startswith(' '):
                    indent_level = len(line) - len(line.lstrip())
                    if indent_level % 2 != 0:
                        issues.append({
                            'category': 'quality',
                            'type': 'inconsistent_indentation',
                            'severity': 'medium',
                            'description': 'YAML indentation should be consistent (multiples of 2 spaces)',
                            'line': i,
                            'code': line.rstrip(),
                            'tool': 'yaml_analysis'
                        })
                
                # Ansible-specific quality checks
                if is_ansible:
                    issues.extend(self._analyze_ansible_quality_line(line, i))
            
            # Check overall YAML structure
            if is_ansible:
                issues.extend(self._analyze_ansible_structure(content, file_path))
            
        except Exception as e:
            self.logger.warning(f"YAML quality analysis failed for {file_path}: {e}")
        
        return issues
    
    def _analyze_yaml_performance(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze YAML file for performance issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            is_ansible = self._is_ansible_file(file_path, content)
            
            if is_ansible:
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for inefficient Ansible patterns
                    
                    # Using shell/command when modules exist
                    if re.search(r'shell:|command:', line):
                        if any(cmd in line.lower() for cmd in ['apt ', 'yum ', 'pip ', 'git clone', 'systemctl']):
                            issues.append({
                                'category': 'performance',
                                'type': 'ansible_inefficient_module',
                                'severity': 'medium',
                                'description': 'Consider using specific Ansible modules instead of shell/command',
                                'line': i,
                                'code': line.strip(),
                                'tool': 'ansible_analysis'
                            })
                    
                    # Missing when conditions for optimization
                    if 'register:' in line and i < len(lines) - 5:
                        next_lines = lines[i:i+5]
                        if not any('when:' in next_line for next_line in next_lines):
                            issues.append({
                                'category': 'performance',
                                'type': 'ansible_missing_when',
                                'severity': 'low',
                                'description': 'Consider adding when conditions to skip unnecessary tasks',
                                'line': i,
                                'code': line.strip(),
                                'tool': 'ansible_analysis'
                            })
                    
                    # Inefficient loops
                    if 'with_items:' in line:
                        issues.append({
                            'category': 'performance',
                            'type': 'ansible_deprecated_loop',
                            'severity': 'medium',
                            'description': 'with_items is deprecated, use loop instead',
                            'line': i,
                            'code': line.strip(),
                            'tool': 'ansible_analysis'
                        })
        
        except Exception as e:
            self.logger.warning(f"YAML performance analysis failed for {file_path}: {e}")
        
        return issues
    
    def _is_ansible_file(self, file_path: str, content: str) -> bool:
        """Determine if a YAML file is an Ansible playbook/role."""
        filename = os.path.basename(file_path).lower()
        
        # Check filename patterns
        ansible_filenames = [
            'playbook.yml', 'playbook.yaml', 'site.yml', 'site.yaml',
            'main.yml', 'main.yaml'
        ]
        
        if filename in ansible_filenames:
            return True
        
        # Check for Ansible-specific keywords in content
        ansible_keywords = [
            'hosts:', 'tasks:', 'handlers:', 'vars:', 'roles:', 
            'playbook:', 'become:', 'gather_facts:', 'ansible_',
            'with_items:', 'when:', 'notify:', 'register:'
        ]
        
        keyword_count = sum(1 for keyword in ansible_keywords if keyword in content)
        return keyword_count >= 3
    
    def _analyze_ansible_quality_line(self, line: str, line_num: int) -> List[Dict[str, Any]]:
        """Analyze a single line for Ansible-specific quality issues."""
        issues = []
        
        # Check for deprecated syntax
        deprecated_patterns = [
            (r'include:', 'Use include_tasks or import_tasks instead of include'),
            (r'sudo:', 'Use become instead of sudo'),
            (r'sudo_user:', 'Use become_user instead of sudo_user'),
            (r'always_run:', 'Use check_mode instead of always_run')
        ]
        
        for pattern, message in deprecated_patterns:
            if re.search(pattern, line):
                issues.append({
                    'category': 'quality',
                    'type': 'ansible_deprecated_syntax',
                    'severity': 'medium',
                    'description': message,
                    'line': line_num,
                    'code': line.strip(),
                    'tool': 'ansible_analysis'
                })
        
        # Check for missing quotes around strings with variables
        if '{{' in line and '}}' in line:
            # Variable interpolation should be quoted
            if re.search(r':\s*{{.*}}', line) and not re.search(r':\s*["\']{{.*}}["\']', line):
                issues.append({
                    'category': 'quality',
                    'type': 'ansible_unquoted_variables',
                    'severity': 'medium',
                    'description': 'Variables should be quoted to prevent YAML parsing issues',
                    'line': line_num,
                    'code': line.strip(),
                    'tool': 'ansible_analysis'
                })
        
        # Check for hardcoded values that should be variables
        if re.search(r'(password|secret|key|token):\s*["\']?[a-zA-Z0-9]+["\']?', line, re.IGNORECASE):
            issues.append({
                'category': 'security',
                'type': 'ansible_hardcoded_secret',
                'severity': 'high',
                'description': 'Avoid hardcoding secrets, use vault or variables',
                'line': line_num,
                'code': line.strip(),
                'tool': 'ansible_analysis'
            })
        
        return issues
    
    def _analyze_ansible_structure(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze overall Ansible file structure."""
        issues = []
        
        # Check for missing essential sections
        if 'hosts:' in content and 'tasks:' not in content and 'roles:' not in content:
            issues.append({
                'category': 'quality',
                'type': 'ansible_missing_tasks',
                'severity': 'high',
                'description': 'Playbook should have either tasks or roles section',
                'line': 1,
                'code': '',
                'tool': 'ansible_analysis'
            })
        
        # Check for overly complex playbooks
        task_count = content.count('- name:')
        if task_count > 50:
            issues.append({
                'category': 'quality',
                'type': 'ansible_complex_playbook',
                'severity': 'medium',
                'description': f'Playbook has {task_count} tasks, consider breaking into roles',
                'line': 1,
                'code': '',
                'tool': 'ansible_analysis'
            })
        
        # Check for missing documentation
        if '- name:' in content and 'description:' not in content and '# ' not in content:
            issues.append({
                'category': 'quality',
                'type': 'ansible_missing_documentation',
                'severity': 'low',
                'description': 'Consider adding comments or description for better maintainability',
                'line': 1,
                'code': '',
                'tool': 'ansible_analysis'
            })
        
        return issues
    
    def _calculate_security_score(self, issues: List[Dict[str, Any]], metrics: Dict[str, Any]) -> float:
        """Calculate security score (0-100)."""
        if not issues:
            return 100.0
        
        penalty = 0
        for issue in issues:
            if issue.get('category') == 'security':
                severity = issue.get('severity', 'medium')
                if severity == 'high':
                    penalty += 20
                elif severity == 'medium':
                    penalty += 10
                else:  # low
                    penalty += 5
        
        score = max(0, 100 - penalty)
        return score
    
    def _calculate_quality_score(self, issues: List[Dict[str, Any]], metrics: Dict[str, Any]) -> float:
        """Calculate quality score (0-100)."""
        base_score = 100.0
        
        # Penalties for quality issues
        quality_issues = [i for i in issues if i.get('category') == 'quality']
        penalty = 0
        
        for issue in quality_issues:
            severity = issue.get('severity', 'medium')
            if severity == 'high':
                penalty += 15
            elif severity == 'medium':
                penalty += 8
            else:  # low
                penalty += 3
        
        # Additional penalties based on metrics
        complexity = metrics.get('cyclomatic_complexity', 0)
        if complexity > 10:
            penalty += min(20, complexity - 10)
        
        lines_of_code = metrics.get('lines_of_code', 0)
        if lines_of_code > 500:
            penalty += min(10, (lines_of_code - 500) // 100)
        
        score = max(0, base_score - penalty)
        return score
    
    def _calculate_performance_score(self, issues: List[Dict[str, Any]], metrics: Dict[str, Any]) -> float:
        """Calculate performance score (0-100)."""
        base_score = 100.0
        
        # Penalties for performance issues
        performance_issues = [i for i in issues if i.get('category') == 'performance']
        penalty = 0
        
        for issue in performance_issues:
            severity = issue.get('severity', 'medium')
            if severity == 'high':
                penalty += 20
            elif severity == 'medium':
                penalty += 12
            else:  # low
                penalty += 5
        
        score = max(0, base_score - penalty)
        return score
    
    def _generate_suggestions(self, issues: List[Dict[str, Any]], 
                           metrics: Dict[str, Any], language: str) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on analysis."""
        suggestions = []
        
        # Group issues by type
        issue_types = {}
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        # Generate suggestions based on common issues
        if 'hardcoded_password' in issue_types or 'hardcoded_api_key' in issue_types:
            suggestions.append({
                'type': 'security',
                'priority': 'high',
                'description': 'Use environment variables or secure configuration files for secrets',
                'category': 'best_practices'
            })
        
        if metrics.get('cyclomatic_complexity', 0) > 15:
            suggestions.append({
                'type': 'refactoring',
                'priority': 'medium',
                'description': 'Consider breaking down complex functions into smaller, more manageable pieces',
                'category': 'maintainability'
            })
        
        if language == 'python':
            if 'console_statement' in issue_types:
                suggestions.append({
                    'type': 'quality',
                    'priority': 'low',
                    'description': 'Replace print statements with proper logging',
                    'category': 'best_practices'
                })
        
        elif language in ['javascript', 'typescript']:
            if 'var_usage' in issue_types:
                suggestions.append({
                    'type': 'modernization',
                    'priority': 'medium',
                    'description': 'Replace var with let/const for better scoping and immutability',
                    'category': 'modern_syntax'
                })
        
        return suggestions
    
    def _calculate_overall_scores(self, file_results: List[AnalysisResult]) -> Dict[str, float]:
        """Calculate overall repository scores."""
        if not file_results:
            return {'security': 0.0, 'quality': 0.0, 'performance': 0.0}
        
        security_scores = [r.security_score for r in file_results]
        quality_scores = [r.quality_score for r in file_results]
        performance_scores = [r.performance_score for r in file_results]
        
        return {
            'security': sum(security_scores) / len(security_scores),
            'quality': sum(quality_scores) / len(quality_scores),
            'performance': sum(performance_scores) / len(performance_scores)
        }
    
    def _analyze_dependencies(self, repo_path: str) -> Dict[str, List[str]]:
        """Analyze repository dependencies."""
        dependencies = {'direct': [], 'dev': [], 'optional': []}
        
        # Common dependency files
        dep_files = [
            'requirements.txt', 'requirements-dev.txt', 'Pipfile',
            'pyproject.toml', 'package.json', 'go.mod', 'Cargo.toml',
            'pom.xml', 'build.gradle', 'composer.json'
        ]
        
        for dep_file in dep_files:
            file_path = os.path.join(repo_path, dep_file)
            if os.path.exists(file_path):
                file_deps = detect_dependencies(file_path)
                for key in dependencies:
                    dependencies[key].extend(file_deps.get(key, []))
        
        # Remove duplicates
        for key in dependencies:
            dependencies[key] = list(set(dependencies[key]))
        
        return dependencies
    
    def _generate_summary(self, file_results: List[AnalysisResult], 
                         languages: Dict[str, int], 
                         dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate analysis summary."""
        total_issues = sum(len(r.issues) for r in file_results)
        
        # Count issues by category
        security_issues = sum(1 for r in file_results for i in r.issues if i.get('category') == 'security')
        quality_issues = sum(1 for r in file_results for i in r.issues if i.get('category') == 'quality')
        performance_issues = sum(1 for r in file_results for i in r.issues if i.get('category') == 'performance')
        
        # Count issues by severity
        high_severity = sum(1 for r in file_results for i in r.issues if i.get('severity') == 'high')
        medium_severity = sum(1 for r in file_results for i in r.issues if i.get('severity') == 'medium')
        low_severity = sum(1 for r in file_results for i in r.issues if i.get('severity') == 'low')
        
        return {
            'total_issues': total_issues,
            'issues_by_category': {
                'security': security_issues,
                'quality': quality_issues,
                'performance': performance_issues
            },
            'issues_by_severity': {
                'high': high_severity,
                'medium': medium_severity,
                'low': low_severity
            },
            'languages_detected': list(languages.keys()),
            'most_common_language': max(languages.items(), key=lambda x: x[1])[0] if languages else 'unknown',
            'total_dependencies': sum(len(deps) for deps in dependencies.values()),
            'has_security_issues': security_issues > 0,
            'requires_attention': high_severity > 0 or security_issues > 5
        }
