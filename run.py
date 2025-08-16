#!/usr/bin/env python3
"""
Startup script for the Dynamic GitHub Code Review MCP Server.

This script can be used to run the MCP server in different modes:
- Development mode with debug logging
- Production mode with optimized settings
- CLI mode for direct repository analysis
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import DynamicGitHubCodeReviewServer
from src.utils.config import Config
from src.utils.logger import setup_logging


async def run_server(debug: bool = False):
    """Run the MCP server."""
    # Override log level for debug mode
    if debug:
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    server = DynamicGitHubCodeReviewServer()
    
    try:
        await server.setup()
        await server.server.run()
    except KeyboardInterrupt:
        print("Server interrupted by user")
    except Exception as e:
        print(f"Server error: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        await server.cleanup()


async def analyze_repository(repository: str, analysis_type: str = "full"):
    """Analyze a specific repository directly."""
    config = Config()
    logger_manager = setup_logging(config)
    logger = logger_manager.get_logger('cli')
    
    try:
        from src.core.github_client import GitHubClient
        from src.core.repository_manager import RepositoryManager
        from src.core.analyzer import CodeAnalyzer
        
        # Initialize components
        github_client = GitHubClient(config)
        await github_client.initialize()
        
        repo_manager = RepositoryManager(github_client, config)
        analyzer = CodeAnalyzer(config)
        
        # Clone and analyze repository
        logger.info(f"Analyzing repository: {repository}")
        local_path = await repo_manager.clone_repository(repository)
        
        analysis_result = analyzer.analyze_repository(local_path, repository)
        
        # Print results
        print(f"\n=== Analysis Results for {repository} ===")
        print(f"Overall Scores:")
        print(f"  Security: {analysis_result.overall_scores.get('security', 0):.1f}/100")
        print(f"  Quality: {analysis_result.overall_scores.get('quality', 0):.1f}/100")
        print(f"  Performance: {analysis_result.overall_scores.get('performance', 0):.1f}/100")
        
        print(f"\nSummary:")
        print(f"  Total Files: {analysis_result.total_files}")
        print(f"  Analyzed Files: {analysis_result.analyzed_files}")
        print(f"  Languages: {', '.join(analysis_result.languages.keys())}")
        
        # Show top issues
        all_issues = []
        for file_result in analysis_result.file_results:
            for issue in file_result.issues:
                if analysis_type == "full" or issue.get('category') == analysis_type:
                    all_issues.append((file_result.file_path, issue))
        
        if all_issues:
            print(f"\nTop Issues ({analysis_type}):")
            for i, (file_path, issue) in enumerate(all_issues[:10]):
                severity = issue.get('severity', 'unknown')
                description = issue.get('description', 'Unknown issue')
                print(f"  {i+1}. [{severity.upper()}] {file_path}: {description}")
        
        await github_client.close()
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if config.LOG_LEVEL == 'DEBUG':
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dynamic GitHub Code Review MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                                    # Run MCP server
  python run.py --debug                            # Run with debug logging
  python run.py --analyze 01abhi01/repo-name      # Analyze specific repository
  python run.py --analyze 01abhi01/repo-name --type security  # Security analysis only
        """
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--analyze',
        metavar='REPOSITORY',
        help='Analyze a specific repository (owner/repo format)'
    )
    
    parser.add_argument(
        '--type',
        choices=['full', 'security', 'quality', 'performance'],
        default='full',
        help='Type of analysis to perform (default: full)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Dynamic GitHub Code Review MCP Server 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Handle Windows event loop policy
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    if args.analyze:
        # CLI analysis mode
        asyncio.run(analyze_repository(args.analyze, args.type))
    else:
        # MCP server mode
        asyncio.run(run_server(args.debug))


if __name__ == "__main__":
    main()
