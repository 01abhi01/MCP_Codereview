#!/usr/bin/env python3
"""
Dynamic MCP Server - Discovers repositories and asks user to choose
"""

import asyncio
import subprocess
import tempfile
import ast
import re
import requests
import os
from pathlib import Path

class DynamicGitHubAnalyzer:
    """Dynamically discover and analyze GitHub repositories"""
    
    def __init__(self):
        self.github_token = self._load_github_token()
        self.username = "01abhi01"  # Default, can be changed
    
    def _load_github_token(self):
        """Load GitHub token from environment or .env file"""
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            env_file = Path('.env')
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        if line.startswith('GITHUB_TOKEN='):
                            token = line.split('=', 1)[1].strip()
                            break
        return token
    
    async def discover_repositories(self, username=None):
        """Discover repositories for a GitHub user"""
        username = username or self.username
        
        print(f"🔍 **Discovering repositories for {username}...**")
        
        if not self.github_token:
            print("❌ No GitHub token found. Using public API (limited).")
            return await self._discover_public_repos(username)
        
        return await self._discover_with_token(username)
    
    async def _discover_with_token(self, username):
        """Discover repositories using GitHub token"""
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            url = f'https://api.github.com/users/{username}/repos'
            
            # Make the request
            import urllib.request
            req = urllib.request.Request(url)
            for key, value in headers.items():
                req.add_header(key, value)
            
            with urllib.request.urlopen(req) as response:
                import json
                repos_data = json.loads(response.read().decode())
            
            repositories = []
            for repo in repos_data:
                repositories.append({
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'description': repo['description'] or 'No description',
                    'language': repo['language'] or 'Unknown',
                    'stars': repo['stargazers_count'],
                    'updated': repo['updated_at'][:10],  # Just date
                    'private': repo['private']
                })
            
            return repositories
            
        except Exception as e:
            print(f"❌ Error discovering repositories: {e}")
            return []
    
    async def _discover_public_repos(self, username):
        """Fallback: discover public repositories without token"""
        try:
            url = f'https://api.github.com/users/{username}/repos'
            
            import urllib.request
            with urllib.request.urlopen(url) as response:
                import json
                repos_data = json.loads(response.read().decode())
            
            repositories = []
            for repo in repos_data[:10]:  # Limit to 10 for public API
                repositories.append({
                    'name': repo['name'],
                    'full_name': repo['full_name'], 
                    'description': repo['description'] or 'No description',
                    'language': repo['language'] or 'Unknown',
                    'stars': repo['stargazers_count'],
                    'updated': repo['updated_at'][:10]
                })
            
            return repositories
            
        except Exception as e:
            print(f"❌ Error discovering public repositories: {e}")
            return []
    
    def display_repositories(self, repositories):
        """Display repositories and let user choose"""
        if not repositories:
            print("❌ No repositories found!")
            return None
        
        print(f"\n📦 **Found {len(repositories)} repositories:**\n")
        
        for i, repo in enumerate(repositories, 1):
            private_indicator = "🔒" if repo.get('private') else "🌐"
            print(f"{i:2d}. {private_indicator} **{repo['name']}** ({repo['language']})")
            print(f"     {repo['description'][:60]}{'...' if len(repo['description']) > 60 else ''}")
            print(f"     ⭐ {repo['stars']} stars • Updated: {repo['updated']}")
            print()
        
        return repositories
    
    def get_user_choice(self, repositories):
        """Get user's repository choice"""
        while True:
            try:
                print(f"🎯 **Choose a repository to analyze (1-{len(repositories)}) or 'q' to quit:**")
                choice = input("➤ ").strip().lower()
                
                if choice == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(repositories):
                    return repositories[index]
                else:
                    print(f"❌ Please enter a number between 1 and {len(repositories)}")
                    
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
    
    def get_analysis_type(self):
        """Get analysis type from user"""
        analysis_types = {
            '1': ('security', 'Security vulnerability scanning'),
            '2': ('quality', 'Code quality and style analysis'),
            '3': ('performance', 'Performance optimization suggestions'),
            '4': ('full', 'Complete comprehensive analysis')
        }
        
        print("\n🔍 **Choose analysis type:**")
        for key, (name, desc) in analysis_types.items():
            print(f"{key}. **{name.title()}** - {desc}")
        
        while True:
            try:
                choice = input("\n➤ Enter choice (1-4): ").strip()
                if choice in analysis_types:
                    return analysis_types[choice][0]
                else:
                    print("❌ Please enter 1, 2, 3, or 4")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
    
    async def analyze_repository_real(self, repository_info, analysis_type):
        """Actually clone and analyze a repository"""
        repo_name = repository_info['full_name']
        
        print(f"\n🔍 **ANALYZING: {repo_name}**")
        print(f"📊 **Analysis Type:** {analysis_type}")
        print("="*50)
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = Path(temp_dir) / "repo"
                
                # Clone repository
                print("📥 Cloning repository...")
                clone_url = f"https://github.com/{repo_name}.git"
                
                result = subprocess.run([
                    'git', 'clone', '--depth', '1', clone_url, str(repo_path)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    return f"❌ Clone failed: {result.stderr}"
                
                print("✅ Repository cloned successfully")
                print("🔍 Analyzing code files...")
                
                # Analyze the code
                return self._analyze_code_files(repo_path, analysis_type)
                
        except Exception as e:
            return f"❌ Analysis failed: {str(e)}"
    
    def _analyze_code_files(self, repo_path: Path, analysis_type):
        """Analyze code files based on analysis type"""
        results = {
            'total_files': 0,
            'analyzed_files': 0, 
            'languages': set(),
            'security_issues': [],
            'quality_issues': [],
            'performance_issues': []
        }
        
        # Find code files
        code_extensions = {'.py', '.js', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go'}
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                results['total_files'] += 1
                
                if file_path.suffix in code_extensions:
                    results['analyzed_files'] += 1
                    
                    # Determine language
                    lang = self._get_language(file_path.suffix)
                    results['languages'].add(lang)
                    
                    # Analyze file based on type
                    file_issues = self._analyze_file_by_type(file_path, analysis_type)
                    
                    # Collect issues
                    results['security_issues'].extend(file_issues.get('security', []))
                    results['quality_issues'].extend(file_issues.get('quality', []))
                    results['performance_issues'].extend(file_issues.get('performance', []))
        
        return self._format_results(results, analysis_type)
    
    def _get_language(self, extension):
        """Map file extension to language"""
        mapping = {
            '.py': 'Python', '.js': 'JavaScript', '.java': 'Java',
            '.cpp': 'C++', '.c': 'C', '.cs': 'C#', 
            '.php': 'PHP', '.rb': 'Ruby', '.go': 'Go'
        }
        return mapping.get(extension, 'Unknown')
    
    def _analyze_file_by_type(self, file_path: Path, analysis_type):
        """Analyze file based on requested analysis type"""
        issues = {'security': [], 'quality': [], 'performance': []}
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Security analysis
                if analysis_type in ['security', 'full']:
                    if any(word in line.lower() for word in ['password', 'secret', 'key']) and '=' in line:
                        issues['security'].append({
                            'file': file_path.name,
                            'line': i,
                            'type': 'hardcoded_credential',
                            'description': 'Possible hardcoded credential',
                            'severity': 'HIGH'
                        })
                    
                    if 'eval(' in line or 'exec(' in line:
                        issues['security'].append({
                            'file': file_path.name,
                            'line': i,
                            'type': 'code_injection',
                            'description': 'Dangerous eval/exec usage',
                            'severity': 'HIGH'
                        })
                
                # Quality analysis
                if analysis_type in ['quality', 'full']:
                    if len(line) > 120:
                        issues['quality'].append({
                            'file': file_path.name,
                            'line': i,
                            'type': 'line_length',
                            'description': f'Line length {len(line)} exceeds 120 characters',
                            'severity': 'LOW'
                        })
                
                # Performance analysis
                if analysis_type in ['performance', 'full']:
                    if 'for' in line and 'in' in line and 'range(len(' in line:
                        issues['performance'].append({
                            'file': file_path.name,
                            'line': i,
                            'type': 'inefficient_loop',
                            'description': 'Consider using enumerate() instead of range(len())',
                            'severity': 'MEDIUM'
                        })
        
        except Exception:
            pass  # Skip files that can't be read
        
        return issues
    
    def _format_results(self, results, analysis_type):
        """Format analysis results based on type"""
        security_score = max(0, 100 - len(results['security_issues']) * 20)
        quality_score = max(0, 100 - len(results['quality_issues']) * 2) 
        performance_score = max(0, 100 - len(results['performance_issues']) * 10)
        
        report = f"""
✅ **ANALYSIS COMPLETE**

📊 **Scores:**
- Security: {security_score}/100 {'✅' if security_score >= 90 else '⚠️' if security_score >= 70 else '❌'}
- Quality: {quality_score}/100 {'✅' if quality_score >= 90 else '⚠️' if quality_score >= 70 else '❌'}
- Performance: {performance_score}/100 {'✅' if performance_score >= 90 else '⚠️' if performance_score >= 70 else '❌'}

📈 **Summary:**
- Total Files: {results['total_files']}
- Analyzed Files: {results['analyzed_files']}
- Languages: {', '.join(sorted(results['languages']))}
"""
        
        # Add specific analysis results
        if analysis_type in ['security', 'full'] and results['security_issues']:
            report += f"\n🔒 **Security Issues ({len(results['security_issues'])}):**\n"
            for issue in results['security_issues'][:5]:
                report += f"  • [{issue['severity']}] {issue['file']}:{issue['line']} - {issue['description']}\n"
        
        if analysis_type in ['quality', 'full'] and results['quality_issues']:
            report += f"\n📝 **Quality Issues ({len(results['quality_issues'])}):**\n"
            for issue in results['quality_issues'][:5]:
                report += f"  • [{issue['severity']}] {issue['file']}:{issue['line']} - {issue['description']}\n"
            if len(results['quality_issues']) > 5:
                report += f"  ... and {len(results['quality_issues']) - 5} more quality issues\n"
        
        if analysis_type in ['performance', 'full'] and results['performance_issues']:
            report += f"\n⚡ **Performance Issues ({len(results['performance_issues'])}):**\n"
            for issue in results['performance_issues'][:5]:
                report += f"  • [{issue['severity']}] {issue['file']}:{issue['line']} - {issue['description']}\n"
        
        return report


async def main():
    """Interactive main function"""
    analyzer = DynamicGitHubAnalyzer()
    
    print("🚀 **DYNAMIC GITHUB CODE REVIEW**")
    print("="*50)
    
    try:
        # Discover repositories
        repositories = await analyzer.discover_repositories()
        
        if not repositories:
            print("❌ No repositories found!")
            return
        
        # Display and get user choice
        analyzer.display_repositories(repositories)
        chosen_repo = analyzer.get_user_choice(repositories)
        
        if not chosen_repo:
            print("👋 Analysis cancelled!")
            return
        
        # Get analysis type
        analysis_type = analyzer.get_analysis_type()
        
        if not analysis_type:
            print("👋 Analysis cancelled!")
            return
        
        # Perform analysis
        result = await analyzer.analyze_repository_real(chosen_repo, analysis_type)
        print(result)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
