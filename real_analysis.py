#!/usr/bin/env python3
"""
Real GitHub Analysis - Working Version
"""

import os
import subprocess
import tempfile
import ast
import re
from pathlib import Path

class RealGitHubAnalyzer:
    """Actually analyze GitHub repositories"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            # Try to load from .env file
            env_file = Path('.env')
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        if line.startswith('GITHUB_TOKEN='):
                            self.github_token = line.split('=', 1)[1].strip()
                            break
    
    async def analyze_repository_real(self, repository: str):
        """Actually clone and analyze a repository"""
        try:
            print(f"🔍 **REAL ANALYSIS** of {repository}")
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = Path(temp_dir) / "repo"
                
                # Clone repository
                print("📥 Cloning repository...")
                clone_url = f"https://github.com/{repository}.git"
                
                result = subprocess.run([
                    'git', 'clone', '--depth', '1', clone_url, str(repo_path)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    return f"❌ Clone failed: {result.stderr}"
                
                print("✅ Repository cloned successfully")
                
                # Analyze the code
                return self._analyze_code_files(repo_path)
                
        except Exception as e:
            return f"❌ Analysis failed: {str(e)}"
    
    def _analyze_code_files(self, repo_path: Path):
        """Analyze code files for real issues"""
        results = {
            'total_files': 0,
            'analyzed_files': 0,
            'languages': set(),
            'security_issues': [],
            'quality_issues': [],
            'file_analysis': {}
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
                    
                    # Analyze file
                    file_issues = self._analyze_file(file_path)
                    results['file_analysis'][str(file_path.relative_to(repo_path))] = file_issues
                    
                    # Collect issues
                    results['security_issues'].extend(file_issues['security'])
                    results['quality_issues'].extend(file_issues['quality'])
        
        return self._format_results(results)
    
    def _get_language(self, extension):
        """Map file extension to language"""
        mapping = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go'
        }
        return mapping.get(extension, 'Unknown')
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single file for issues"""
        issues = {'security': [], 'quality': []}
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Security checks
                if 'password' in line.lower() and '=' in line:
                    issues['security'].append({
                        'line': i,
                        'type': 'hardcoded_credential',
                        'description': 'Possible hardcoded password',
                        'severity': 'HIGH'
                    })
                
                if 'sql' in line.lower() and ('+' in line or 'format' in line):
                    issues['security'].append({
                        'line': i, 
                        'type': 'sql_injection',
                        'description': 'Potential SQL injection vulnerability',
                        'severity': 'HIGH'
                    })
                
                if 'eval(' in line or 'exec(' in line:
                    issues['security'].append({
                        'line': i,
                        'type': 'code_injection', 
                        'description': 'Dangerous eval/exec usage',
                        'severity': 'HIGH'
                    })
                
                # Quality checks
                if len(line) > 120:
                    issues['quality'].append({
                        'line': i,
                        'type': 'line_length',
                        'description': f'Line length {len(line)} exceeds 120 characters',
                        'severity': 'LOW'
                    })
                
                if line.strip().startswith('TODO') or line.strip().startswith('FIXME'):
                    issues['quality'].append({
                        'line': i,
                        'type': 'todo_comment',
                        'description': 'TODO/FIXME comment found',
                        'severity': 'LOW'
                    })
        
        except Exception as e:
            issues['quality'].append({
                'line': 0,
                'type': 'file_error',
                'description': f'Could not analyze file: {str(e)}',
                'severity': 'MEDIUM'
            })
        
        return issues
    
    def _format_results(self, results):
        """Format analysis results"""
        security_score = max(0, 100 - len(results['security_issues']) * 10)
        quality_score = max(0, 100 - len(results['quality_issues']) * 2)
        
        total_issues = len(results['security_issues']) + len(results['quality_issues'])
        
        report = f"""
🔍 **REAL ANALYSIS RESULTS**

📊 **Overall Scores:**
- Security: {security_score}/100 {'✅' if security_score >= 90 else '⚠️' if security_score >= 70 else '❌'}
- Quality: {quality_score}/100 {'✅' if quality_score >= 90 else '⚠️' if quality_score >= 70 else '❌'}

📈 **Summary:**
- Total Files: {results['total_files']}
- Analyzed Files: {results['analyzed_files']}  
- Languages: {', '.join(sorted(results['languages']))}
- Total Issues Found: {total_issues}

🔒 **Security Issues:** {len(results['security_issues'])}
"""
        
        # Add security issues
        for issue in results['security_issues'][:5]:  # Show top 5
            report += f"  • [{issue['severity']}] Line {issue['line']}: {issue['description']}\n"
        
        report += f"\n📝 **Quality Issues:** {len(results['quality_issues'])}\n"
        
        # Add quality issues  
        for issue in results['quality_issues'][:5]:  # Show top 5
            report += f"  • [{issue['severity']}] Line {issue['line']}: {issue['description']}\n"
        
        if len(results['quality_issues']) > 5:
            report += f"  ... and {len(results['quality_issues']) - 5} more quality issues\n"
        
        return report


async def main():
    """Test real analysis"""
    analyzer = RealGitHubAnalyzer()
    
    print("🎯 **TESTING REAL GITHUB ANALYSIS**")
    print("="*50)
    
    result = await analyzer.analyze_repository_real("01abhi01/MovieRecommend")
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
