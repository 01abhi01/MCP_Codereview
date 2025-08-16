# Dynamic GitHub Code Review MCP Server

A Python-based Model Context Protocol server that provides comprehensive code review capabilities for any GitHub repository. Dynamically fetches repositories from https://github.com/01abhi01 and supports configurable code scanning.

## Features

🔍 **Dynamic Repository Support**
- Automatically discover repositories from GitHub user/organization
- Configure any repository for code review
- Support for multiple programming languages

🛠️ **Smart Code Analysis**
- Language-specific analysis (Python, JavaScript, Java, Go, etc.)
- Security vulnerability detection  
- Performance optimization suggestions
- Code quality assessment

🤖 **AI-Powered Reviews**
- Intelligent code pattern recognition
- Automated pull request analysis
- Context-aware feedback generation
- Best practices recommendations

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements-minimal.txt
```

### 2. Configure GitHub Access
```bash
# Create .env file with your GitHub token
echo "GITHUB_TOKEN=your_github_token_here" > .env
echo "GITHUB_USERNAME=01abhi01" >> .env
```

### 3. Test the Analysis
```bash
# Test with a sample repository
python run.py --analyze 01abhi01/MovieRecommend --type security

# Run comprehensive analysis
python run.py --analyze 01abhi01/MovieRecommend --type full

# Quality-focused analysis
python run.py --analyze 01abhi01/MovieRecommend --type quality
```

### 4. Run as MCP Server
```bash
python src/main.py
```

## Example Usage & Testing

### Command Line Analysis Examples

```bash
# Security analysis of a repository
python run.py --analyze 01abhi01/MovieRecommend --type security
# Output: Security score, vulnerability detection, dependency scanning

# Performance analysis
python run.py --analyze 01abhi01/MovieRecommend --type performance
# Output: Performance bottlenecks, optimization suggestions

# Code quality assessment
python run.py --analyze 01abhi01/MovieRecommend --type quality
# Output: Code style issues, maintainability metrics, best practice violations

# Full comprehensive analysis
python run.py --analyze 01abhi01/MovieRecommend --type full
# Output: Complete analysis with all categories combined
```

### Demo Script Examples

```bash
# Run the interactive demo
python demo.py

# Expected output:
# 🔍 Analyzing Sample Python Code...
# ✅ Security Analysis: Found 0 critical issues
# ✅ Quality Analysis: Found 6 style issues  
# ✅ Performance Analysis: Found 0 performance issues
# 📊 Overall Scores: Security: 100/100, Quality: 85/100, Performance: 100/100
```

### MCP Server Integration Examples

Once the server is running, you can use these MCP tools:

```json
{
  "name": "discover_repositories",
  "description": "Discover all repositories for a GitHub user",
  "inputSchema": {
    "type": "object",
    "properties": {
      "username": {"type": "string", "description": "GitHub username"}
    }
  }
}
```

```json
{
  "name": "analyze_repository", 
  "description": "Perform comprehensive code analysis",
  "inputSchema": {
    "type": "object",
    "properties": {
      "repository": {"type": "string", "description": "Repository name (owner/repo)"},
      "analysis_type": {"type": "string", "enum": ["security", "quality", "performance", "full"]}
    }
  }
}
```

### Python API Examples

```python
import asyncio
from src.core.github_client import GitHubClient
from src.core.repository_manager import RepositoryManager
from src.core.analyzer import CodeAnalyzer
from src.utils.config import Config

async def analyze_repository_example():
    """Example: Analyze a repository programmatically"""
    config = Config()
    github_client = GitHubClient(config)
    await github_client.initialize()
    
    repo_manager = RepositoryManager(github_client, config)
    analyzer = CodeAnalyzer(config)
    
    # Clone and analyze repository
    local_path = await repo_manager.clone_repository("01abhi01/MovieRecommend")
    results = await analyzer.analyze_repository(local_path)
    
    print(f"Security Score: {results['scores']['security']}/100")
    print(f"Quality Score: {results['scores']['quality']}/100") 
    print(f"Performance Score: {results['scores']['performance']}/100")
    
    await github_client.close()

# Run the example
asyncio.run(analyze_repository_example())
```

### Testing Your Setup

```bash
# 1. Test GitHub authentication
python -c "
import asyncio
from src.core.github_client import GitHubClient
from src.utils.config import Config

async def test_auth():
    config = Config()
    client = GitHubClient(config)
    await client.initialize()
    print('✅ GitHub authentication successful')
    await client.close()

asyncio.run(test_auth())
"

# 2. Test repository discovery
python -c "
import asyncio
from src.core.github_client import GitHubClient
from src.utils.config import Config

async def test_discovery():
    config = Config()
    client = GitHubClient(config)
    await client.initialize()
    repos = await client.get_user_repositories('01abhi01')
    print(f'✅ Found {len(repos)} repositories')
    await client.close()

asyncio.run(test_discovery())
"

# 3. Test code analysis engine
python -c "
from src.core.analyzer import CodeAnalyzer
from src.utils.config import Config

config = Config()
analyzer = CodeAnalyzer(config)
result = analyzer.analyze_code('print(\"hello world\")', 'python', 'test.py')
print(f'✅ Analysis engine working: {len(result)} issues found')
"
```

## Configuration Examples

### Basic Configuration (.env)
```bash
# Minimal setup
GITHUB_TOKEN=github_pat_your_token_here
GITHUB_USERNAME=01abhi01
LOG_LEVEL=INFO
```

### Advanced Configuration (.env)
```bash
# GitHub Authentication
GITHUB_TOKEN=github_pat_your_token_here

# Target Configuration  
GITHUB_USERNAME=01abhi01
DEFAULT_BRANCH=main

# Repository Settings
MAX_REPOSITORIES=20
INCLUDE_PRIVATE_REPOS=false
INCLUDE_FORKS=false

# Analysis Configuration
MAX_FILE_SIZE=1048576
ANALYSIS_TIMEOUT=300
ENABLE_SECURITY_SCAN=true
ENABLE_PERFORMANCE_SCAN=true
ENABLE_DEPENDENCY_SCAN=true

# Supported Languages
SUPPORTED_LANGUAGES=python,javascript,typescript,java,go,rust,cpp,csharp,php,ruby

# Code Review Settings
REVIEW_DEPTH=comprehensive
FOCUS_AREAS=security,performance,maintainability,style
AUTO_SUGGEST_FIXES=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/github_code_review.log
ENABLE_FILE_LOGGING=true

# MCP Server Configuration
MCP_SERVER_NAME=dynamic-github-code-review
MCP_SERVER_VERSION=1.0.0

# Cache Configuration
ENABLE_CACHING=true
CACHE_DURATION=3600
CACHE_DIR=./cache
```

## Dynamic Repository Configuration

The server automatically discovers and configures repositories from:
- **User**: https://github.com/01abhi01
- **All public repositories**
- **Accessible private repositories** (with proper authentication)

### Supported Repository Types
- Python projects (Django, Flask, FastAPI, etc.)
- JavaScript/Node.js applications
- Java/Spring applications
- Go applications
- Any GitHub repository with code

## Expected Analysis Results

### Sample Output for MovieRecommend Repository:
```
=== Analysis Results for 01abhi01/MovieRecommend ===
Overall Scores:
  Security: 100.0/100
  Quality: 74.0/100
  Performance: 100.0/100

Summary:
  Total Files: 16
  Analyzed Files: 9
  Languages: python

Top Issues (quality):
  1. [LOW] app.py: Line length 123 exceeds 120 characters
  2. [LOW] app.py: Line length 262 exceeds 120 characters
  3. [MEDIUM] Missing docstrings in function definitions
  4. [LOW] Inconsistent variable naming conventions
```

## Architecture

```
src/
├── main.py                    # MCP server entry point
├── core/
│   ├── github_client.py       # GitHub API integration
│   ├── repository_manager.py  # Dynamic repo management
│   └── analyzer.py            # Code analysis engine
├── tools/
│   └── __init__.py            # MCP tools implementation
├── utils/
│   ├── config.py              # Configuration management
│   └── logging_setup.py       # Logging configuration
├── resources/
│   └── __init__.py            # MCP resources
└── prompts/
    └── __init__.py            # MCP prompts
```

## Technology Stack

- **Python 3.8+**
- **Model Context Protocol (MCP)**
- **PyGithub** - GitHub API integration
- **AST Analysis** - Python code parsing
- **Tree-sitter** - Multi-language parsing
- **Bandit** - Security analysis
- **Subprocess** - Git operations

## Troubleshooting

### Common Issues

1. **Authentication Error**
```bash
# Verify token is valid
python -c "import os; print('GITHUB_TOKEN' in os.environ)"
# Should output: True
```

2. **Repository Not Found**
```bash
# Check if repository exists and is accessible
python run.py --analyze 01abhi01/MovieRecommend --type security
# Should show analysis results, not 404 error
```

3. **Git Clone Errors**
```bash
# Ensure git is installed and in PATH
git --version
# Should show git version
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test: `python demo.py`
4. Commit changes: `git commit -am 'Add feature'`
5. Push to branch: `git push origin feature-name`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review the example usage patterns
