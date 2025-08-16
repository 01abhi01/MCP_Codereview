#!/usr/bin/env python3
"""
Demo script for the GitHub Code Review MCP Server.

This script demonstrates the code review functionality using local file analysis
without requiring a GitHub connection.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.analyzer import CodeAnalyzer
from src.utils.config import Config
from src.utils.logger import setup_logging


def create_demo_python_file():
    """Create a demo Python file with various code issues for analysis."""
    demo_code = '''
import os
import subprocess

# Security issue: hardcoded password
password = "secret123"
api_key = "sk-1234567890abcdef"

def unsafe_function(user_input):
    # Security issue: using eval
    result = eval(user_input)
    return result

def command_execution(cmd):
    # Security issue: shell injection vulnerability
    os.system(cmd)

def poor_quality_function(a, b, c, d, e, f, g, h, i):
    # Quality issue: too many parameters
    if a > 10:
        if b < 5:
            if c == 3:
                if d != 0:
                    if e > 7:
                        if f < 2:
                            # Quality issue: deeply nested code
                            return a + b + c + d + e + f + g + h + i
    return 0

def performance_issue():
    # Performance issue: inefficient string concatenation
    result = ""
    for i in range(1000):
        result += str(i)
    return result

def main():
    print("Demo application")
    unsafe_function("1 + 1")
    command_execution("ls -la")
    poor_quality_function(1, 2, 3, 4, 5, 6, 7, 8, 9)
    performance_issue()

if __name__ == "__main__":
    main()
'''
    return demo_code


def create_demo_javascript_file():
    """Create a demo JavaScript file with code issues."""
    demo_code = '''
// Demo JavaScript file with various issues

var apiKey = "sk-1234567890abcdef";  // Security issue: hardcoded API key

function unsafeEval(userInput) {
    // Security issue: using eval
    return eval(userInput);
}

function poorQuality(a, b, c, d, e, f, g, h) {
    // Quality issue: too many parameters
    if (a == b) {  // Quality issue: should use ===
        console.log("Debug message");  // Quality issue: console.log in production
        return a + b + c + d + e + f + g + h;
    }
    return 0;
}

function performanceIssue() {
    // Performance issue: inefficient DOM query in loop
    for (let i = 0; i < 100; i++) {
        document.getElementById("myElement").innerHTML = "Value: " + i;
    }
}

function main() {
    unsafeEval("1 + 1");
    poorQuality(1, 2, 3, 4, 5, 6, 7, 8);
    performanceIssue();
}

main();
'''
    return demo_code


async def demo_analysis():
    """Demonstrate the code analysis functionality."""
    print("🚀 GitHub Code Review MCP Server - Demo Analysis")
    print("=" * 60)
    
    # Setup configuration and logging
    config = Config()
    config.LOG_LEVEL = 'INFO'
    logger_manager = setup_logging(config)
    logger = logger_manager.get_logger('demo')
    
    # Initialize analyzer
    analyzer = CodeAnalyzer(config)
    
    # Create temporary directory with demo files
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Creating demo repository in: {temp_dir}")
        
        # Create demo Python file
        python_file = os.path.join(temp_dir, "demo_app.py")
        with open(python_file, 'w') as f:
            f.write(create_demo_python_file())
        
        # Create demo JavaScript file  
        js_file = os.path.join(temp_dir, "demo_app.js")
        with open(js_file, 'w') as f:
            f.write(create_demo_javascript_file())
        
        # Create a README file
        readme_file = os.path.join(temp_dir, "README.md")
        with open(readme_file, 'w') as f:
            f.write("# Demo Repository\n\nThis is a demo repository for testing code analysis.\n")
        
        print("📝 Demo files created:")
        print(f"  - {python_file}")
        print(f"  - {js_file}")
        print(f"  - {readme_file}")
        print()
        
        # Analyze the repository
        print("🔍 Analyzing repository...")
        analysis_result = analyzer.analyze_repository(temp_dir, "demo-repository")
        
        # Display results
        print("\n📊 Analysis Results:")
        print("=" * 40)
        
        print(f"Repository: {analysis_result.repository}")
        print(f"Total Files: {analysis_result.total_files}")
        print(f"Analyzed Files: {analysis_result.analyzed_files}")
        print(f"Languages: {', '.join(analysis_result.languages.keys())}")
        print()
        
        print("📈 Overall Scores:")
        print(f"  🛡️  Security: {analysis_result.overall_scores.get('security', 0):.1f}/100")
        print(f"  ⭐ Quality: {analysis_result.overall_scores.get('quality', 0):.1f}/100")
        print(f"  🚀 Performance: {analysis_result.overall_scores.get('performance', 0):.1f}/100")
        print()
        
        # Show issues by category
        all_issues = []
        for file_result in analysis_result.file_results:
            for issue in file_result.issues:
                all_issues.append((file_result.file_path, issue))
        
        if all_issues:
            print("🚨 Issues Found:")
            
            # Group by category
            categories = {}
            for file_path, issue in all_issues:
                category = issue.get('category', 'unknown')
                if category not in categories:
                    categories[category] = []
                categories[category].append((file_path, issue))
            
            for category, issues in categories.items():
                print(f"\n{category.title()} Issues ({len(issues)}):")
                for i, (file_path, issue) in enumerate(issues[:5], 1):  # Show top 5
                    severity = issue.get('severity', 'unknown')
                    description = issue.get('description', 'Unknown issue')
                    line = issue.get('line', 'Unknown')
                    
                    severity_emoji = {
                        'high': '🔴',
                        'medium': '🟡', 
                        'low': '🟢'
                    }.get(severity, '⚪')
                    
                    file_name = os.path.basename(file_path)
                    print(f"  {i}. {severity_emoji} [{severity.upper()}] {file_name}:{line}")
                    print(f"     {description}")
                
                if len(issues) > 5:
                    print(f"     ... and {len(issues) - 5} more issues")
        
        # Show suggestions
        all_suggestions = []
        for file_result in analysis_result.file_results:
            for suggestion in file_result.suggestions:
                all_suggestions.append(suggestion)
        
        if all_suggestions:
            print(f"\n💡 Improvement Suggestions ({len(all_suggestions)}):")
            for i, suggestion in enumerate(all_suggestions[:3], 1):  # Show top 3
                priority = suggestion.get('priority', 'medium')
                description = suggestion.get('description', 'Unknown suggestion')
                
                priority_emoji = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(priority, '⚪')
                
                print(f"  {i}. {priority_emoji} [{priority.upper()}] {description}")
        
        print(f"\n📋 Summary:")
        print(f"  Total Issues: {len(all_issues)}")
        print(f"  High Priority: {len([i for _, i in all_issues if i.get('severity') == 'high'])}")
        print(f"  Security Issues: {len([i for _, i in all_issues if i.get('category') == 'security'])}")
        print(f"  Quality Issues: {len([i for _, i in all_issues if i.get('category') == 'quality'])}")
        print(f"  Performance Issues: {len([i for _, i in all_issues if i.get('category') == 'performance'])}")
        
        # Show recommendation
        high_priority_count = len([i for _, i in all_issues if i.get('severity') == 'high'])
        total_issues = len(all_issues)
        
        print(f"\n🎯 Recommendation:")
        if high_priority_count > 0:
            print(f"  ⚠️  REQUIRES ATTENTION: {high_priority_count} high-priority issues found.")
            print("     Please address security and critical quality issues before deploying.")
        elif total_issues > 10:
            print(f"  ⚠️  REVIEW RECOMMENDED: {total_issues} issues found.")
            print("     Consider addressing major issues for better code quality.")
        elif total_issues > 0:
            print(f"  ✅ GOOD WITH MINOR FIXES: {total_issues} minor issues found.")
            print("     Code is generally good with some room for improvement.")
        else:
            print("  ✅ EXCELLENT: No issues found. Great code quality!")
        
        print("\n" + "=" * 60)
        print("✨ Demo completed successfully!")
        print("\nTo use with real GitHub repositories:")
        print("1. Get a GitHub Personal Access Token from: https://github.com/settings/tokens")
        print("2. Set GITHUB_TOKEN in your .env file")
        print("3. Run: python run.py --analyze owner/repository-name")


def main():
    """Main entry point for the demo."""
    print("GitHub Code Review MCP Server - Demo Mode")
    print("This demo shows the code analysis capabilities without requiring GitHub access.\n")
    
    try:
        asyncio.run(demo_analysis())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Handle Windows event loop policy
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    main()
