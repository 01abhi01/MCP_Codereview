#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.github_client import GitHubClient
from src.utils.config import Config

async def main():
    config = Config()
    github_client = GitHubClient(config)
    await github_client.initialize()
    
    try:
        repos = await github_client.get_user_repositories('01abhi01')
        print(f'Found {len(repos)} repositories for 01abhi01:')
        for i, repo in enumerate(repos[:10], 1):  # Show first 10
            print(f'  {i}. {repo["full_name"]} ({repo["language"] or "Unknown"}) - {(repo["description"] or "No description")[:50]}')
        
        if len(repos) > 10:
            print(f'  ... and {len(repos) - 10} more repositories')
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        await github_client.close()

if __name__ == "__main__":
    asyncio.run(main())
