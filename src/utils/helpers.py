"""
Helper utilities for the GitHub Code Review MCP Server.

Contains various utility functions for file handling, code analysis, and data processing.
"""

import re
import os
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
import ast
import tokenize
import io


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file system usage."""
    # Remove or replace invalid characters
    invalid_chars = r'<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and periods
    filename = filename.strip(' .')
    
    # Ensure it's not empty
    if not filename:
        filename = 'untitled'
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def get_file_extension(file_path: str) -> str:
    """Get the file extension in lowercase."""
    return Path(file_path).suffix.lower()


def is_binary_file(file_path: str) -> bool:
    """Check if a file is binary."""
    try:
        # Check MIME type first
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and not mime_type.startswith('text'):
            return True
        
        # Read a small chunk and check for null bytes
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return True
        
        return False
    except (OSError, IOError):
        return True


def calculate_complexity(file_path: str, language: str = None) -> Dict[str, int]:
    """Calculate code complexity metrics."""
    complexity = {
        'lines_of_code': 0,
        'blank_lines': 0,
        'comment_lines': 0,
        'cyclomatic_complexity': 0,
        'functions': 0,
        'classes': 0
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        complexity['lines_of_code'] = len(lines)
        
        # Count blank lines and comments based on language
        if not language:
            language = _detect_language_from_extension(file_path)
        
        comment_patterns = _get_comment_patterns(language)
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                complexity['blank_lines'] += 1
            elif any(stripped.startswith(pattern) for pattern in comment_patterns):
                complexity['comment_lines'] += 1
        
        # Language-specific complexity analysis
        if language == 'python':
            complexity.update(_analyze_python_complexity(content))
        elif language in ['javascript', 'typescript']:
            complexity.update(_analyze_js_complexity(content))
        
        return complexity
    
    except Exception:
        return complexity


def _detect_language_from_extension(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext = get_file_extension(file_path)
    
    language_map = {
        '.py': 'python',
        '.js': 'javascript', 
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.sql': 'sql',
        '.sh': 'bash',
        '.ps1': 'powershell'
    }
    
    return language_map.get(ext, 'unknown')


def _get_comment_patterns(language: str) -> List[str]:
    """Get comment patterns for a programming language."""
    patterns = {
        'python': ['#'],
        'javascript': ['//', '/*'],
        'typescript': ['//', '/*'],
        'java': ['//', '/*'],
        'go': ['//', '/*'],
        'rust': ['//', '/*'],
        'cpp': ['//', '/*'],
        'c': ['//', '/*'],
        'csharp': ['//', '/*'],
        'php': ['//', '/*', '#'],
        'ruby': ['#'],
        'swift': ['//', '/*'],
        'kotlin': ['//', '/*'],
        'scala': ['//', '/*'],
        'r': ['#'],
        'sql': ['--', '/*'],
        'bash': ['#'],
        'powershell': ['#']
    }
    
    return patterns.get(language, ['#', '//'])


def _analyze_python_complexity(content: str) -> Dict[str, int]:
    """Analyze Python-specific complexity metrics."""
    metrics = {'cyclomatic_complexity': 0, 'functions': 0, 'classes': 0}
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics['functions'] += 1
                # Count decision points for cyclomatic complexity
                metrics['cyclomatic_complexity'] += _count_decision_points(node)
            elif isinstance(node, ast.ClassDef):
                metrics['classes'] += 1
    
    except SyntaxError:
        pass
    
    return metrics


def _analyze_js_complexity(content: str) -> Dict[str, int]:
    """Analyze JavaScript/TypeScript complexity metrics."""
    metrics = {'cyclomatic_complexity': 0, 'functions': 0, 'classes': 0}
    
    # Simple regex-based analysis for JS/TS
    function_patterns = [
        r'function\s+\w+',
        r'const\s+\w+\s*=\s*\(',
        r'let\s+\w+\s*=\s*\(',
        r'var\s+\w+\s*=\s*\(',
        r'=>',
        r'async\s+function'
    ]
    
    class_patterns = [r'class\s+\w+']
    
    decision_patterns = [
        r'\bif\s*\(',
        r'\belse\s+if\s*\(',
        r'\bwhile\s*\(',
        r'\bfor\s*\(',
        r'\bswitch\s*\(',
        r'\bcase\s+',
        r'\bcatch\s*\(',
        r'\?\s*.*\s*:'  # ternary operator
    ]
    
    for pattern in function_patterns:
        metrics['functions'] += len(re.findall(pattern, content, re.IGNORECASE))
    
    for pattern in class_patterns:
        metrics['classes'] += len(re.findall(pattern, content, re.IGNORECASE))
    
    for pattern in decision_patterns:
        metrics['cyclomatic_complexity'] += len(re.findall(pattern, content, re.IGNORECASE))
    
    return metrics


def _count_decision_points(node: ast.AST) -> int:
    """Count decision points in an AST node for cyclomatic complexity."""
    count = 1  # Base complexity
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            count += 1
        elif isinstance(child, ast.ExceptHandler):
            count += 1
        elif isinstance(child, ast.comprehension):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += len(child.values) - 1
    
    return count


def extract_imports(file_path: str, language: str = None) -> List[Dict[str, str]]:
    """Extract import statements from a source file."""
    imports = []
    
    if not language:
        language = _detect_language_from_extension(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if language == 'python':
            imports = _extract_python_imports(content)
        elif language in ['javascript', 'typescript']:
            imports = _extract_js_imports(content)
        elif language == 'java':
            imports = _extract_java_imports(content)
        elif language == 'go':
            imports = _extract_go_imports(content)
    
    except Exception:
        pass
    
    return imports


def _extract_python_imports(content: str) -> List[Dict[str, str]]:
    """Extract Python import statements."""
    imports = []
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'type': 'from_import',
                        'module': module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
    
    except SyntaxError:
        pass
    
    return imports


def _extract_js_imports(content: str) -> List[Dict[str, str]]:
    """Extract JavaScript/TypeScript import statements."""
    imports = []
    
    # ES6 imports
    import_patterns = [
        r'import\s+(\*\s+as\s+\w+|\w+|\{[^}]+\})\s+from\s+[\'"]([^\'"]+)[\'"]',
        r'import\s+[\'"]([^\'"]+)[\'"]',
        r'const\s+(\w+|\{[^}]+\})\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
    ]
    
    for i, line in enumerate(content.split('\n'), 1):
        for pattern in import_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                if len(match) == 2:
                    imports.append({
                        'type': 'import',
                        'name': match[0],
                        'module': match[1],
                        'line': i
                    })
                else:
                    imports.append({
                        'type': 'import',
                        'module': match[0],
                        'line': i
                    })
    
    return imports


def _extract_java_imports(content: str) -> List[Dict[str, str]]:
    """Extract Java import statements."""
    imports = []
    
    import_pattern = r'import\s+(static\s+)?([a-zA-Z_][a-zA-Z0-9_.]*(?:\.\*)?);'
    
    for i, line in enumerate(content.split('\n'), 1):
        matches = re.findall(import_pattern, line)
        for match in matches:
            imports.append({
                'type': 'static_import' if match[0] else 'import',
                'module': match[1],
                'line': i
            })
    
    return imports


def _extract_go_imports(content: str) -> List[Dict[str, str]]:
    """Extract Go import statements."""
    imports = []
    
    # Single import
    single_pattern = r'import\s+"([^"]+)"'
    # Block import
    block_pattern = r'import\s*\(\s*((?:[^)]+\n?)*)\s*\)'
    
    for i, line in enumerate(content.split('\n'), 1):
        # Single imports
        matches = re.findall(single_pattern, line)
        for match in matches:
            imports.append({
                'type': 'import',
                'module': match,
                'line': i
            })
    
    # Block imports
    block_matches = re.findall(block_pattern, content, re.MULTILINE)
    for block in block_matches:
        for line in block.split('\n'):
            line = line.strip()
            if line and line.startswith('"') and line.endswith('"'):
                imports.append({
                    'type': 'import',
                    'module': line.strip('"'),
                    'line': 0  # Block import, line number not specific
                })
    
    return imports


def find_security_patterns(file_path: str, language: str = None) -> List[Dict[str, str]]:
    """Find potential security issues in source code."""
    issues = []
    
    if not language:
        language = _detect_language_from_extension(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Common security patterns across languages
        common_patterns = [
            {
                'pattern': r'password\s*=\s*[\'"][^\'"]+[\'"]',
                'type': 'hardcoded_password',
                'severity': 'high',
                'description': 'Hardcoded password found'
            },
            {
                'pattern': r'api[_-]?key\s*=\s*[\'"][^\'"]+[\'"]',
                'type': 'hardcoded_api_key',
                'severity': 'high',
                'description': 'Hardcoded API key found'
            },
            {
                'pattern': r'secret\s*=\s*[\'"][^\'"]+[\'"]',
                'type': 'hardcoded_secret',
                'severity': 'high',
                'description': 'Hardcoded secret found'
            },
            {
                'pattern': r'token\s*=\s*[\'"][^\'"]+[\'"]',
                'type': 'hardcoded_token',
                'severity': 'medium',
                'description': 'Hardcoded token found'
            }
        ]
        
        # Language-specific patterns
        if language == 'python':
            common_patterns.extend(_get_python_security_patterns())
        elif language in ['javascript', 'typescript']:
            common_patterns.extend(_get_js_security_patterns())
        elif language == 'sql':
            common_patterns.extend(_get_sql_security_patterns())
        
        # Search for patterns
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern_info in common_patterns:
                if re.search(pattern_info['pattern'], line, re.IGNORECASE):
                    issues.append({
                        'type': pattern_info['type'],
                        'severity': pattern_info['severity'],
                        'description': pattern_info['description'],
                        'line': i,
                        'code': line.strip()
                    })
    
    except Exception:
        pass
    
    return issues


def _get_python_security_patterns() -> List[Dict[str, str]]:
    """Get Python-specific security patterns."""
    return [
        {
            'pattern': r'eval\s*\(',
            'type': 'dangerous_eval',
            'severity': 'high',
            'description': 'Use of eval() can lead to code injection'
        },
        {
            'pattern': r'exec\s*\(',
            'type': 'dangerous_exec',
            'severity': 'high',
            'description': 'Use of exec() can lead to code injection'
        },
        {
            'pattern': r'os\.system\s*\(',
            'type': 'command_injection',
            'severity': 'high',
            'description': 'Use of os.system() can lead to command injection'
        },
        {
            'pattern': r'subprocess\.call\s*\([^)]*shell\s*=\s*True',
            'type': 'shell_injection',
            'severity': 'high',
            'description': 'subprocess with shell=True can lead to shell injection'
        },
        {
            'pattern': r'pickle\.loads?\s*\(',
            'type': 'unsafe_deserialization',
            'severity': 'high',
            'description': 'Pickle deserialization can execute arbitrary code'
        }
    ]


def _get_js_security_patterns() -> List[Dict[str, str]]:
    """Get JavaScript/TypeScript-specific security patterns."""
    return [
        {
            'pattern': r'eval\s*\(',
            'type': 'dangerous_eval',
            'severity': 'high',
            'description': 'Use of eval() can lead to code injection'
        },
        {
            'pattern': r'innerHTML\s*=',
            'type': 'xss_risk',
            'severity': 'medium',
            'description': 'innerHTML assignment can lead to XSS'
        },
        {
            'pattern': r'document\.write\s*\(',
            'type': 'xss_risk',
            'severity': 'medium',
            'description': 'document.write() can lead to XSS'
        },
        {
            'pattern': r'new\s+Function\s*\(',
            'type': 'dynamic_function',
            'severity': 'medium',
            'description': 'Dynamic function creation can be dangerous'
        }
    ]


def _get_sql_security_patterns() -> List[Dict[str, str]]:
    """Get SQL-specific security patterns."""
    return [
        {
            'pattern': r'[\'"].*\+.*[\'"]',
            'type': 'sql_injection',
            'severity': 'high',
            'description': 'Potential SQL injection via string concatenation'
        },
        {
            'pattern': r'execute\s*\(\s*[\'"][^\'\"]*%[^\'\"]*[\'"]',
            'type': 'sql_injection',
            'severity': 'high',
            'description': 'Potential SQL injection via string formatting'
        }
    ]


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except (OSError, IOError):
        return ""


def detect_dependencies(file_path: str, language: str = None) -> Dict[str, List[str]]:
    """Detect dependencies and package requirements from source files."""
    dependencies = {'direct': [], 'dev': [], 'optional': []}
    
    if not language:
        language = _detect_language_from_extension(file_path)
    
    try:
        filename = os.path.basename(file_path)
        
        # Check for dependency files
        if filename in ['requirements.txt', 'requirements-dev.txt', 'requirements.in']:
            dependencies = _parse_python_requirements(file_path)
        elif filename == 'package.json':
            dependencies = _parse_package_json(file_path)
        elif filename == 'Pipfile':
            dependencies = _parse_pipfile(file_path)
        elif filename == 'poetry.lock' or filename == 'pyproject.toml':
            dependencies = _parse_poetry_file(file_path)
        elif filename in ['go.mod', 'go.sum']:
            dependencies = _parse_go_mod(file_path)
        elif filename == 'Cargo.toml':
            dependencies = _parse_cargo_toml(file_path)
    
    except Exception:
        pass
    
    return dependencies


def _parse_python_requirements(file_path: str) -> Dict[str, List[str]]:
    """Parse Python requirements.txt file."""
    dependencies = {'direct': [], 'dev': [], 'optional': []}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Remove version specifiers for just the package name
                    package = re.split(r'[><=!]', line)[0].strip()
                    if package:
                        dependencies['direct'].append(package)
    except Exception:
        pass
    
    return dependencies


def _parse_package_json(file_path: str) -> Dict[str, List[str]]:
    """Parse Node.js package.json file."""
    import json
    
    dependencies = {'direct': [], 'dev': [], 'optional': []}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'dependencies' in data:
            dependencies['direct'] = list(data['dependencies'].keys())
        
        if 'devDependencies' in data:
            dependencies['dev'] = list(data['devDependencies'].keys())
        
        if 'optionalDependencies' in data:
            dependencies['optional'] = list(data['optionalDependencies'].keys())
    
    except Exception:
        pass
    
    return dependencies


def _parse_pipfile(file_path: str) -> Dict[str, List[str]]:
    """Parse Python Pipfile."""
    dependencies = {'direct': [], 'dev': [], 'optional': []}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple parsing - look for [packages] and [dev-packages] sections
        in_packages = False
        in_dev_packages = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line == '[packages]':
                in_packages = True
                in_dev_packages = False
                continue
            elif line == '[dev-packages]':
                in_packages = False
                in_dev_packages = True
                continue
            elif line.startswith('['):
                in_packages = False
                in_dev_packages = False
                continue
            
            if line and '=' in line and not line.startswith('#'):
                package = line.split('=')[0].strip().strip('"\'')
                if in_packages:
                    dependencies['direct'].append(package)
                elif in_dev_packages:
                    dependencies['dev'].append(package)
    
    except Exception:
        pass
    
    return dependencies


def _parse_poetry_file(file_path: str) -> Dict[str, List[str]]:
    """Parse Python Poetry pyproject.toml file."""
    dependencies = {'direct': [], 'dev': [], 'optional': []}
    
    try:
        # Try to import tomllib (Python 3.11+) or fallback to tomli
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                # If no TOML library is available, skip parsing
                return dependencies
        
        with open(file_path, 'rb') as f:
            data = tomllib.load(f)
        
        if 'tool' in data and 'poetry' in data['tool']:
            poetry_data = data['tool']['poetry']
            
            if 'dependencies' in poetry_data:
                for dep in poetry_data['dependencies']:
                    if dep != 'python':  # Skip Python version requirement
                        dependencies['direct'].append(dep)
            
            if 'group' in poetry_data and 'dev' in poetry_data['group']:
                if 'dependencies' in poetry_data['group']['dev']:
                    dependencies['dev'] = list(poetry_data['group']['dev']['dependencies'].keys())
    
    except Exception:
        pass
    
    return dependencies


def _parse_go_mod(file_path: str) -> Dict[str, List[str]]:
    """Parse Go go.mod file."""
    dependencies = {'direct': [], 'dev': [], 'optional': []}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for require statements
        require_pattern = r'require\s+([^\s]+)'
        matches = re.findall(require_pattern, content)
        
        for match in matches:
            if not match.startswith('('):
                dependencies['direct'].append(match.split()[0])
    
    except Exception:
        pass
    
    return dependencies


def _parse_cargo_toml(file_path: str) -> Dict[str, List[str]]:
    """Parse Rust Cargo.toml file."""
    dependencies = {'direct': [], 'dev': [], 'optional': []}
    
    try:
        # Try to import tomllib (Python 3.11+) or fallback to tomli
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                # If no TOML library is available, skip parsing
                return dependencies
        
        with open(file_path, 'rb') as f:
            data = tomllib.load(f)
        
        if 'dependencies' in data:
            dependencies['direct'] = list(data['dependencies'].keys())
        
        if 'dev-dependencies' in data:
            dependencies['dev'] = list(data['dev-dependencies'].keys())
    
    except Exception:
        pass
    
    return dependencies
