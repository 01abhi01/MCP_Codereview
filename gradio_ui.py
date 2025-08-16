#!/usr/bin/env python3
"""
Gradio Web UI for GitHub Code Review MCP Server
Interactive web interface for repository analysis
"""

import gradio as gr
import asyncio
import subprocess
import tempfile
import os
import urllib.request
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class GitHubAnalyzerUI:
    """Web UI for GitHub repository analysis"""
    
    def __init__(self):
        self.github_token = self._load_github_token()
        self.current_repos = []
        
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
    
    def discover_repositories(self, username: str) -> Tuple[str, List]:
        """Discover repositories for a GitHub user"""
        if not username.strip():
            return "❌ Please enter a GitHub username", []
            
        try:
            print(f"🔍 Discovering repositories for {username}...")
            
            # Prepare API request
            url = f'https://api.github.com/users/{username}/repos?per_page=20&sort=updated'
            headers = {}
            
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
                headers['Accept'] = 'application/vnd.github.v3+json'
            
            # Make request
            req = urllib.request.Request(url)
            for key, value in headers.items():
                req.add_header(key, value)
            
            with urllib.request.urlopen(req) as response:
                repos_data = json.loads(response.read().decode())
            
            # Process repository data
            repositories = []
            repo_choices = []
            
            for repo in repos_data:
                repo_info = {
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'description': repo['description'] or 'No description',
                    'language': repo['language'] or 'Unknown',
                    'stars': repo['stargazers_count'],
                    'updated': repo['updated_at'][:10],
                    'private': repo.get('private', False)
                }
                repositories.append(repo_info)
                
                # Just add repository name to choices
                repo_choices.append(repo_info['name'])
            
            self.current_repos = repositories
            
            # Simple summary with just repository names
            summary = f"✅ Found {len(repositories)} repositories for {username}\n\n"
            for i, repo in enumerate(repositories, 1):
                summary += f"{i}. {repo['name']}\n"
            
            return summary, repo_choices
            
        except Exception as e:
            error_msg = f"❌ Error discovering repositories: {str(e)}"
            return error_msg, []
    
    def analyze_repository(self, username: str, selected_repo: str, analysis_type: str, progress=gr.Progress()) -> str:
        """Analyze selected repository"""
        if not username.strip():
            return "❌ Please enter a GitHub username first"
            
        if not selected_repo or selected_repo == "Select a repository first":
            return "❌ Please select a repository to analyze"
        
        try:
            # Find the selected repository by name
            selected_repo_info = None
            
            for repo in self.current_repos:
                if repo['name'] == selected_repo:
                    selected_repo_info = repo
                    break
            
            if not selected_repo_info:
                return f"❌ Repository '{selected_repo}' not found in discovered repositories"
            
            full_repo_name = selected_repo_info['full_name']
            
            progress(0.1, desc="Initializing analysis...")
            
            # Start analysis
            result = self._perform_analysis(full_repo_name, analysis_type, progress)
            
            return result
            
        except Exception as e:
            return f"❌ Analysis failed: {str(e)}"
    
    def _perform_analysis(self, repo_full_name: str, analysis_type: str, progress) -> str:
        """Perform the actual repository analysis"""
        try:
            progress(0.2, desc="Cloning repository...")
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = Path(temp_dir) / "repo"
                
                # Clone repository
                clone_url = f"https://github.com/{repo_full_name}.git"
                
                result = subprocess.run([
                    'git', 'clone', '--depth', '1', clone_url, str(repo_path)
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    return f"❌ Failed to clone repository: {result.stderr}"
                
                progress(0.5, desc="Analyzing code files...")
                
                # Analyze the repository
                analysis_results = self._analyze_code_files(repo_path, analysis_type)
                
                progress(0.9, desc="Generating report...")
                
                # Format results
                report = self._format_analysis_report(repo_full_name, analysis_type, analysis_results)
                
                progress(1.0, desc="Analysis complete!")
                
                return report
                
        except subprocess.TimeoutExpired:
            return f"⏰ Analysis timeout for {repo_full_name} (>60s)"
        except Exception as e:
            return f"❌ Analysis error: {str(e)}"
    
    def _analyze_code_files(self, repo_path: Path, analysis_type: str) -> Dict:
        """Analyze code files in the repository"""
        results = {
            'total_files': 0,
            'analyzed_files': 0,
            'languages': set(),
            'security_issues': [],
            'quality_issues': [],
            'performance_issues': []
        }
        
        # File extensions to analyze
        code_extensions = {'.py', '.js', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.ts'}
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                results['total_files'] += 1
                
                if file_path.suffix in code_extensions:
                    results['analyzed_files'] += 1
                    
                    # Determine language
                    lang = self._get_language(file_path.suffix)
                    results['languages'].add(lang)
                    
                    # Analyze file
                    file_issues = self._analyze_single_file(file_path, analysis_type)
                    
                    # Collect issues
                    results['security_issues'].extend(file_issues.get('security', []))
                    results['quality_issues'].extend(file_issues.get('quality', []))
                    results['performance_issues'].extend(file_issues.get('performance', []))
        
        return results
    
    def _get_language(self, extension: str) -> str:
        """Map file extension to programming language"""
        mapping = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.cs': 'C#',
            '.php': 'PHP', '.rb': 'Ruby', '.go': 'Go'
        }
        return mapping.get(extension, 'Unknown')
    
    def _analyze_single_file(self, file_path: Path, analysis_type: str) -> Dict:
        """Analyze a single code file"""
        issues = {'security': [], 'quality': [], 'performance': []}
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Security analysis
                if analysis_type in ['security', 'full']:
                    # Check for hardcoded credentials (more specific patterns)
                    credential_patterns = [
                        ('password', 'Hardcoded password detected'),
                        ('api_key', 'Hardcoded API key detected'),
                        ('secret_key', 'Hardcoded secret key detected'),
                        ('access_token', 'Hardcoded access token detected')
                    ]
                    
                    for pattern, description in credential_patterns:
                        if pattern in line.lower() and '=' in line and not line.strip().startswith('#'):
                            # Check if it's actually a hardcoded value (not a variable assignment)
                            if any(quote in line for quote in ['"', "'"]) and not 'input(' in line.lower():
                                issues['security'].append({
                                    'file': file_path.name,
                                    'line': i,
                                    'type': 'hardcoded_credential',
                                    'description': description,
                                    'severity': 'HIGH',
                                    'code_snippet': line.strip()[:100]
                                })
                    
                    # Check for dangerous functions
                    dangerous_functions = [
                        ('eval(', 'Use of eval() function - potential code injection risk'),
                        ('exec(', 'Use of exec() function - potential code execution risk'),
                        ('system(', 'Use of system() function - potential command injection risk'),
                        ('shell_exec(', 'Use of shell_exec() function - potential command injection risk')
                    ]
                    
                    for func, description in dangerous_functions:
                        if func in line and not line.strip().startswith('#'):
                            issues['security'].append({
                                'file': file_path.name,
                                'line': i,
                                'type': 'dangerous_function',
                                'description': description,
                                'severity': 'HIGH',
                                'code_snippet': line.strip()[:100]
                            })
                
                # Quality analysis
                if analysis_type in ['quality', 'full']:
                    # Line length check
                    if len(line) > 120:
                        issues['quality'].append({
                            'file': file_path.name,
                            'line': i,
                            'type': 'line_length',
                            'description': f'Line length {len(line)} exceeds 120 characters',
                            'severity': 'LOW',
                            'code_snippet': line.strip()[:100] + '...'
                        })
                    
                    # TODO/FIXME comments
                    if any(keyword in line.upper() for keyword in ['TODO', 'FIXME', 'HACK']):
                        issues['quality'].append({
                            'file': file_path.name,
                            'line': i,
                            'type': 'todo_comment',
                            'description': 'TODO/FIXME comment found',
                            'severity': 'LOW',
                            'code_snippet': line.strip()[:100]
                        })
                
                # Performance analysis
                if analysis_type in ['performance', 'full']:
                    # Inefficient loops
                    if 'for' in line and 'range(len(' in line:
                        issues['performance'].append({
                            'file': file_path.name,
                            'line': i,
                            'type': 'inefficient_loop',
                            'description': 'Consider using enumerate() instead of range(len())',
                            'severity': 'MEDIUM',
                            'code_snippet': line.strip()[:100]
                        })
        
        except Exception:
            pass  # Skip files that can't be analyzed
        
        return issues
    
    def _format_analysis_report(self, repo_name: str, analysis_type: str, results: Dict) -> str:
        """Format the analysis results into a readable report"""
        # Calculate scores
        security_score = max(0, 100 - len(results['security_issues']) * 20)
        quality_score = max(0, 100 - len(results['quality_issues']) * 2)
        performance_score = max(0, 100 - len(results['performance_issues']) * 10)
        
        # Score indicators
        def get_indicator(score):
            return "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
        
        report = f"""# 🔍 Analysis Results for {repo_name}

## 📊 Overall Scores
- **Security**: {security_score}/100 {get_indicator(security_score)}
- **Quality**: {quality_score}/100 {get_indicator(quality_score)}
- **Performance**: {performance_score}/100 {get_indicator(performance_score)}

## 📈 Summary
- **Total Files**: {results['total_files']}
- **Analyzed Files**: {results['analyzed_files']}
- **Languages**: {', '.join(sorted(results['languages'])) if results['languages'] else 'None detected'}
- **Analysis Type**: {analysis_type.title()}

"""
        
        # Add specific analysis results
        if analysis_type in ['security', 'full']:
            report += f"## 🔒 Security Analysis ({len(results['security_issues'])} issues)\n"
            if results['security_issues']:
                for i, issue in enumerate(results['security_issues'][:10], 1):
                    report += f"\n**Issue #{i}: {issue['description']}**\n"
                    report += f"- **File**: {issue['file']} (Line {issue['line']})\n"
                    report += f"- **Severity**: {issue['severity']}\n"
                    report += f"- **Code**: `{issue['code_snippet']}`\n"
                if len(results['security_issues']) > 10:
                    report += f"\n... and {len(results['security_issues']) - 10} more security issues\n\n"
            else:
                report += "✅ No security issues detected!\n\n"
        
        if analysis_type in ['quality', 'full']:
            report += f"## 📝 Quality Analysis ({len(results['quality_issues'])} issues)\n"
            if results['quality_issues']:
                for i, issue in enumerate(results['quality_issues'][:10], 1):
                    report += f"\n**Issue #{i}: {issue['description']}**\n"
                    report += f"- **File**: {issue['file']} (Line {issue['line']})\n"
                    report += f"- **Severity**: {issue['severity']}\n"
                if len(results['quality_issues']) > 10:
                    report += f"\n... and {len(results['quality_issues']) - 10} more quality issues\n\n"
            else:
                report += "✅ No quality issues detected!\n\n"
        
        if analysis_type in ['performance', 'full']:
            report += f"## ⚡ Performance Analysis ({len(results['performance_issues'])} issues)\n"
            if results['performance_issues']:
                for i, issue in enumerate(results['performance_issues'][:10], 1):
                    report += f"\n**Issue #{i}: {issue['description']}**\n"
                    report += f"- **File**: {issue['file']} (Line {issue['line']})\n"
                    report += f"- **Severity**: {issue['severity']}\n"
                if len(results['performance_issues']) > 10:
                    report += f"\n... and {len(results['performance_issues']) - 10} more performance issues\n\n"
            else:
                report += "✅ No performance issues detected!\n\n"
        
        report += "---\n*Analysis completed via MCP GitHub Code Review Server*"
        
        return report

def create_gradio_interface():
    """Create and configure the Gradio interface"""
    analyzer = GitHubAnalyzerUI()
    
    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .main-header {
        text-align: center;
        color: #2563eb;
        margin-bottom: 2rem;
    }
    .analysis-output {
        max-height: 600px;
        overflow-y: auto;
    }
    """
    
    with gr.Blocks(css=custom_css, title="GitHub Code Review - MCP Server", theme=gr.themes.Soft()) as interface:
        gr.HTML("""
        <div class="main-header">
            <h1>🔍 GitHub Code Review MCP Server</h1>
            <p>Intelligent repository analysis with security, quality, and performance insights</p>
            <p style="font-size: 14px; color: #666; margin-top: 10px;">Powered by Abhishek Rath</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML("<h3>📦 Repository Discovery</h3>")
                
                username_input = gr.Textbox(
                    label="GitHub Username",
                    placeholder="Enter GitHub username (e.g., 01abhi01)",
                    value="01abhi01"
                )
                
                discover_btn = gr.Button("🔍 Discover Repositories", variant="primary")
                
                repo_info = gr.Markdown(
                    value="Enter a GitHub username and click 'Discover Repositories' to start",
                    label="Repository Information"
                )
                
            with gr.Column(scale=1):
                gr.HTML("<h3>⚙️ Analysis Configuration</h3>")
                
                repo_dropdown = gr.Dropdown(
                    label="Select Repository",
                    choices=["Select a repository first"],
                    value="Select a repository first",
                    interactive=True,
                    allow_custom_value=False
                )
                
                analysis_type = gr.Radio(
                    label="Analysis Type",
                    choices=[
                        ("🔒 Security Analysis", "security"),
                        ("📝 Quality Analysis", "quality"), 
                        ("⚡ Performance Analysis", "performance"),
                        ("🔍 Full Analysis", "full")
                    ],
                    value="full"
                )
                
                analyze_btn = gr.Button("🚀 Analyze Repository", variant="secondary")
        
        gr.HTML("<hr>")
        
        gr.HTML("<h3>📊 Analysis Results</h3>")
        analysis_output = gr.Markdown(
            value="Select a repository and analysis type, then click 'Analyze Repository' to see results",
            label="Analysis Report",
            elem_classes=["analysis-output"]
        )
        
        # Event handlers
        def update_repositories(username):
            summary, choices = analyzer.discover_repositories(username)
            if choices:
                return summary, gr.update(choices=choices, value=choices[0] if choices else "Select a repository first")
            else:
                return summary, gr.update(choices=["Select a repository first"], value="Select a repository first")
        
        discover_btn.click(
            fn=update_repositories,
            inputs=[username_input],
            outputs=[repo_info, repo_dropdown]
        )
        
        analyze_btn.click(
            fn=analyzer.analyze_repository,
            inputs=[username_input, repo_dropdown, analysis_type],
            outputs=[analysis_output]
        )
        
        # Add examples
        gr.HTML("""
        <div style="margin-top: 2rem; padding: 1rem; background-color: #f8fafc; border-radius: 0.5rem;">
            <h4>💡 Example Usage:</h4>
            <ol>
                <li>Enter a GitHub username (e.g., "01abhi01")</li>
                <li>Click "Discover Repositories" to see available repos</li>
                <li>Select a repository from the dropdown</li>
                <li>Choose your analysis type (Security, Quality, Performance, or Full)</li>
                <li>Click "Analyze Repository" to start the analysis</li>
            </ol>
            <p><strong>Note:</strong> Make sure you have a GitHub token configured in your .env file for private repositories.</p>
        </div>
        """)
    
    return interface

def main():
    """Launch the Gradio web interface"""
    print("🚀 Starting GitHub Code Review Web Interface...")
    
    # Create and launch interface
    interface = create_gradio_interface()
    
    interface.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        debug=True,
        show_error=True,
        inbrowser=True
    )

if __name__ == "__main__":
    main()
