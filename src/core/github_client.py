"""
GitHub API Client for dynamic repository access and management.

Supports both GitHub Personal Access Tokens and GitHub App authentication.
Provides comprehensive GitHub API operations for code review and analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from github import Github, Auth, GithubException
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.GithubException import GithubException


class GitHubClient:
    """Enhanced GitHub API client with dynamic repository support."""
    
    def __init__(self, config):
        """Initialize GitHub client with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.github: Optional[Github] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = 5000
        
    async def initialize(self):
        """Initialize GitHub authentication and client."""
        try:
            self.logger.info("🔐 Initializing GitHub authentication...")
            
            # Try GitHub App authentication first
            if (self.config.GITHUB_APP_ID and 
                self.config.GITHUB_APP_PRIVATE_KEY_PATH and 
                self.config.GITHUB_APP_INSTALLATION_ID):
                
                self.logger.info("Using GitHub App authentication")
                await self._init_github_app()
                
            elif self.config.GITHUB_TOKEN:
                self.logger.info("Using Personal Access Token authentication")
                await self._init_personal_token()
                
            else:
                raise ValueError(
                    "No GitHub authentication configured. "
                    "Set GITHUB_TOKEN or GitHub App credentials."
                )
            
            # Test authentication
            await self._test_authentication()
            
            # Initialize HTTP session for additional API calls
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "Authorization": f"token {self._get_token()}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "DynamicGitHubCodeReview/1.0"
                }
            )
            
            self.logger.info("✅ GitHub client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ GitHub client initialization failed: {e}")
            raise
    
    async def _init_github_app(self):
        """Initialize GitHub App authentication."""
        # TODO: Implement GitHub App authentication
        # This would require additional libraries for JWT token generation
        raise NotImplementedError("GitHub App authentication not yet implemented")
    
    async def _init_personal_token(self):
        """Initialize Personal Access Token authentication."""
        auth = Auth.Token(self.config.GITHUB_TOKEN)
        self.github = Github(auth=auth)
    
    async def _test_authentication(self):
        """Test GitHub authentication and get user info."""
        try:
            user = self.github.get_user()
            self.logger.info(f"🔗 Authenticated as: {user.login}")
            
            # Set a default rate limit for now
            self.rate_limit_remaining = 5000
            self.logger.info(f"📊 API rate limit: assumed 5000/5000")
            
        except GithubException as e:
            raise Exception(f"GitHub authentication test failed: {e}")
    
    def _get_token(self) -> str:
        """Get the current authentication token."""
        return self.config.GITHUB_TOKEN
    
    async def get_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Get all repositories for a specific user."""
        try:
            self.logger.info(f"📦 Fetching repositories for user: {username}")
            
            user = self.github.get_user(username)
            repositories = []
            
            # Get repositories with pagination
            for repo in user.get_repos(type='all', sort='updated'):
                # Apply filters
                if not self.config.INCLUDE_FORKS and repo.fork:
                    continue
                    
                if not self.config.INCLUDE_PRIVATE_REPOS and repo.private:
                    continue
                
                repo_data = {
                    'id': repo.id,
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'language': repo.language,
                    'default_branch': repo.default_branch,
                    'private': repo.private,
                    'fork': repo.fork,
                    'archived': repo.archived,
                    'disabled': repo.disabled,
                    'size': repo.size,
                    'stargazers_count': repo.stargazers_count,
                    'watchers_count': repo.watchers_count,
                    'forks_count': repo.forks_count,
                    'open_issues_count': repo.open_issues_count,
                    'topics': repo.get_topics(),
                    'created_at': repo.created_at.isoformat() if repo.created_at else None,
                    'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
                    'pushed_at': repo.pushed_at.isoformat() if repo.pushed_at else None,
                    'clone_url': repo.clone_url,
                    'html_url': repo.html_url,
                    'api_url': repo.url
                }
                
                repositories.append(repo_data)
                
                # Respect rate limits
                if len(repositories) >= self.config.MAX_REPOSITORIES:
                    break
                    
                # Add small delay to avoid rate limiting
                await asyncio.sleep(self.config.REQUEST_DELAY)
            
            self.logger.info(f"✅ Found {len(repositories)} repositories")
            return repositories
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to fetch repositories: {e}")
            raise
    
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get detailed information about a specific repository."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            return {
                'id': repository.id,
                'name': repository.name,
                'full_name': repository.full_name,
                'description': repository.description,
                'language': repository.language,
                'languages': await self._get_repository_languages(owner, repo),
                'default_branch': repository.default_branch,
                'private': repository.private,
                'size': repository.size,
                'stargazers_count': repository.stargazers_count,
                'forks_count': repository.forks_count,
                'open_issues_count': repository.open_issues_count,
                'topics': repository.get_topics(),
                'license': repository.license.name if repository.license else None,
                'created_at': repository.created_at.isoformat(),
                'updated_at': repository.updated_at.isoformat(),
                'clone_url': repository.clone_url,
                'html_url': repository.html_url
            }
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to get repository {owner}/{repo}: {e}")
            raise
    
    async def _get_repository_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Get programming languages used in the repository."""
        if not self.session:
            return {}
            
        try:
            async with self.session.get(
                f"https://api.github.com/repos/{owner}/{repo}/languages"
            ) as response:
                if response.status == 200:
                    return await response.json()
                return {}
        except Exception as e:
            self.logger.warning(f"Failed to get languages for {owner}/{repo}: {e}")
            return {}
    
    async def get_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """Get pull requests for a repository."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull_requests = []
            
            for pr in repository.get_pulls(state=state):
                pr_data = {
                    'number': pr.number,
                    'title': pr.title,
                    'body': pr.body,
                    'state': pr.state,
                    'user': {
                        'login': pr.user.login,
                        'avatar_url': pr.user.avatar_url
                    },
                    'head': {
                        'ref': pr.head.ref,
                        'sha': pr.head.sha
                    },
                    'base': {
                        'ref': pr.base.ref,
                        'sha': pr.base.sha
                    },
                    'created_at': pr.created_at.isoformat(),
                    'updated_at': pr.updated_at.isoformat(),
                    'mergeable': pr.mergeable,
                    'additions': pr.additions,
                    'deletions': pr.deletions,
                    'changed_files': pr.changed_files,
                    'html_url': pr.html_url
                }
                pull_requests.append(pr_data)
            
            return pull_requests
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to get pull requests for {owner}/{repo}: {e}")
            raise
    
    async def get_file_content(self, owner: str, repo: str, path: str, ref: str = None) -> str:
        """Get content of a specific file from the repository."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            if ref:
                file_content = repository.get_contents(path, ref=ref)
            else:
                file_content = repository.get_contents(path)
            
            if file_content.encoding == 'base64':
                import base64
                return base64.b64decode(file_content.content).decode('utf-8')
            else:
                return file_content.decoded_content.decode('utf-8')
                
        except GithubException as e:
            self.logger.error(f"❌ Failed to get file content {owner}/{repo}:{path}: {e}")
            raise
    
    async def get_repository_tree(self, owner: str, repo: str, ref: str = None) -> List[Dict[str, Any]]:
        """Get the file tree of a repository."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            if ref is None:
                ref = repository.default_branch
                
            tree = repository.get_git_tree(ref, recursive=True)
            
            files = []
            for element in tree.tree:
                if element.type == 'blob':  # Files only, not directories
                    files.append({
                        'path': element.path,
                        'size': element.size,
                        'sha': element.sha,
                        'type': element.type,
                        'url': element.url
                    })
            
            return files
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to get repository tree {owner}/{repo}: {e}")
            raise
    
    async def create_pull_request_review(self, owner: str, repo: str, pr_number: int, 
                                       body: str, event: str = "COMMENT") -> Dict[str, Any]:
        """Create a review on a pull request."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            
            review = pr.create_review(body=body, event=event)
            
            return {
                'id': review.id,
                'user': review.user.login,
                'body': review.body,
                'state': review.state,
                'html_url': review.html_url,
                'submitted_at': review.submitted_at.isoformat() if review.submitted_at else None
            }
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to create review for {owner}/{repo}#{pr_number}: {e}")
            raise

    async def get_repository_info(self, repository: str) -> Dict[str, Any]:
        """Get detailed information about a repository."""
        try:
            self.logger.info(f"📋 Getting repository info for: {repository}")
            
            repo = self.github.get_repo(repository)
            
            return {
                'id': repo.id,
                'name': repo.name,
                'full_name': repo.full_name,
                'owner': repo.owner.login,
                'private': repo.private,
                'html_url': repo.html_url,
                'clone_url': repo.clone_url,
                'ssh_url': repo.ssh_url,
                'description': repo.description,
                'language': repo.language,
                'size': repo.size,
                'default_branch': repo.default_branch,
                'open_issues_count': repo.open_issues_count,
                'forks_count': repo.forks_count,
                'stargazers_count': repo.stargazers_count,
                'watchers_count': repo.watchers_count,
                'created_at': repo.created_at.isoformat() if repo.created_at else None,
                'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
                'pushed_at': repo.pushed_at.isoformat() if repo.pushed_at else None,
                'fork': repo.fork,
                'archived': repo.archived,
                'disabled': repo.disabled,
                'topics': repo.get_topics() if hasattr(repo, 'get_topics') else [],
                'license': repo.license.name if repo.license else None,
                'has_issues': repo.has_issues,
                'has_projects': repo.has_projects,
                'has_wiki': repo.has_wiki,
                'has_pages': repo.has_pages,
                'has_downloads': repo.has_downloads
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get repository info for {repository}: {e}")
            raise
    
    async def close(self):
        """Close the GitHub client and cleanup resources."""
        if self.session:
            await self.session.close()
        self.logger.info("👋 GitHub client closed")
