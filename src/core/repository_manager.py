"""
Dynamic Repository Manager

Handles discovery, configuration, and management of GitHub repositories
for code review and analysis. Supports dynamic repository selection
and multi-repository operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path


@dataclass
class RepositoryConfig:
    """Configuration for a specific repository."""
    owner: str
    name: str
    full_name: str
    language: str
    default_branch: str
    enabled: bool = True
    analysis_config: Dict[str, Any] = None
    last_analyzed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.analysis_config is None:
            self.analysis_config = {}


class RepositoryManager:
    """Manages dynamic repository discovery and configuration."""
    
    def __init__(self, github_client, config):
        """Initialize repository manager."""
        self.github_client = github_client
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Repository storage
        self.repositories: Dict[str, RepositoryConfig] = {}
        self.config_file = Path("./cache/repositories.json")
        
        # Ensure cache directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing configuration
        self._load_repository_config()
    
    async def discover_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Discover all repositories for a GitHub user."""
        try:
            self.logger.info(f"🔍 Discovering repositories for user: {username}")
            
            # Get repositories from GitHub
            repositories = await self.github_client.get_user_repositories(username)
            
            # Filter by supported languages
            filtered_repos = []
            supported_languages = set(
                lang.strip().lower() 
                for lang in self.config.SUPPORTED_LANGUAGES.split(',')
            )
            
            for repo in repositories:
                repo_language = (repo.get('language') or '').lower()
                
                # Include if language is supported or if no language filter
                if (not supported_languages or 
                    repo_language in supported_languages or
                    'all' in supported_languages):
                    
                    filtered_repos.append(repo)
                    
                    # Auto-configure repository
                    await self._auto_configure_repository(repo)
            
            self.logger.info(f"✅ Discovered {len(filtered_repos)} repositories")
            return filtered_repos
            
        except Exception as e:
            self.logger.error(f"❌ Repository discovery failed: {e}")
            raise
    
    async def _auto_configure_repository(self, repo_data: Dict[str, Any]):
        """Automatically configure a discovered repository."""
        try:
            repo_config = RepositoryConfig(
                owner=repo_data['full_name'].split('/')[0],
                name=repo_data['name'],
                full_name=repo_data['full_name'],
                language=repo_data.get('language', 'unknown'),
                default_branch=repo_data.get('default_branch', 'main'),
                enabled=True,
                analysis_config=self._get_default_analysis_config(repo_data)
            )
            
            self.repositories[repo_config.full_name] = repo_config
            self.logger.debug(f"📝 Auto-configured repository: {repo_config.full_name}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to auto-configure repository {repo_data.get('full_name')}: {e}")
    
    def _get_default_analysis_config(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get default analysis configuration based on repository characteristics."""
        language = (repo_data.get('language') or '').lower()
        
        config = {
            'security_scan': self.config.ENABLE_SECURITY_SCAN,
            'performance_scan': self.config.ENABLE_PERFORMANCE_SCAN,
            'dependency_scan': self.config.ENABLE_DEPENDENCY_SCAN,
            'code_quality_scan': True,
            'focus_areas': self.config.FOCUS_AREAS.split(','),
            'auto_suggest_fixes': self.config.AUTO_SUGGEST_FIXES
        }
        
        # Language-specific configurations
        if language == 'python':
            config.update({
                'tools': ['pylint', 'bandit', 'safety', 'mypy'],
                'frameworks': self._detect_python_frameworks(repo_data),
                'check_requirements': True,
                'check_setup_py': True
            })
        elif language == 'javascript':
            config.update({
                'tools': ['eslint', 'npm-audit', 'jshint'],
                'frameworks': self._detect_js_frameworks(repo_data),
                'check_package_json': True,
                'check_node_modules': True
            })
        elif language == 'java':
            config.update({
                'tools': ['spotbugs', 'pmd', 'checkstyle'],
                'frameworks': self._detect_java_frameworks(repo_data),
                'check_maven': True,
                'check_gradle': True
            })
        elif language == 'go':
            config.update({
                'tools': ['go-vet', 'golint', 'gosec'],
                'check_go_mod': True,
                'check_go_sum': True
            })
        
        return config
    
    def _detect_python_frameworks(self, repo_data: Dict[str, Any]) -> List[str]:
        """Detect Python frameworks based on repository characteristics."""
        frameworks = []
        
        # Check topics and description for framework indicators
        topics = repo_data.get('topics', [])
        description = (repo_data.get('description') or '').lower()
        
        framework_indicators = {
            'django': ['django', 'web', 'webapp'],
            'flask': ['flask', 'microservice', 'api'],
            'fastapi': ['fastapi', 'api', 'async'],
            'streamlit': ['streamlit', 'dashboard', 'visualization'],
            'langchain': ['langchain', 'llm', 'ai', 'chatbot'],
            'tensorflow': ['tensorflow', 'ml', 'machine-learning'],
            'pytorch': ['pytorch', 'deep-learning', 'neural']
        }
        
        for framework, indicators in framework_indicators.items():
            if (framework in description or 
                any(indicator in description for indicator in indicators) or
                any(indicator in topics for indicator in indicators)):
                frameworks.append(framework)
        
        return frameworks
    
    def _detect_js_frameworks(self, repo_data: Dict[str, Any]) -> List[str]:
        """Detect JavaScript frameworks."""
        frameworks = []
        topics = repo_data.get('topics', [])
        description = (repo_data.get('description') or '').lower()
        
        js_frameworks = ['react', 'vue', 'angular', 'node', 'express', 'next']
        
        for framework in js_frameworks:
            if framework in description or framework in topics:
                frameworks.append(framework)
        
        return frameworks
    
    def _detect_java_frameworks(self, repo_data: Dict[str, Any]) -> List[str]:
        """Detect Java frameworks."""
        frameworks = []
        topics = repo_data.get('topics', [])
        description = (repo_data.get('description') or '').lower()
        
        java_frameworks = ['spring', 'springboot', 'hibernate', 'maven', 'gradle']
        
        for framework in java_frameworks:
            if framework in description or framework in topics:
                frameworks.append(framework)
        
        return frameworks
    
    async def get_repository_config(self, full_name: str) -> Optional[RepositoryConfig]:
        """Get configuration for a specific repository."""
        return self.repositories.get(full_name)
    
    async def configure_repository(self, full_name: str, config: Dict[str, Any]) -> bool:
        """Configure a specific repository."""
        try:
            if full_name in self.repositories:
                repo_config = self.repositories[full_name]
                repo_config.analysis_config.update(config)
                repo_config.enabled = config.get('enabled', repo_config.enabled)
                
                self._save_repository_config()
                self.logger.info(f"✅ Updated configuration for {full_name}")
                return True
            else:
                self.logger.warning(f"⚠️ Repository {full_name} not found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to configure repository {full_name}: {e}")
            return False
    
    async def get_enabled_repositories(self) -> List[RepositoryConfig]:
        """Get all enabled repositories."""
        return [repo for repo in self.repositories.values() if repo.enabled]
    
    async def get_repositories_by_language(self, language: str) -> List[RepositoryConfig]:
        """Get repositories filtered by programming language."""
        return [
            repo for repo in self.repositories.values() 
            if repo.language.lower() == language.lower() and repo.enabled
        ]
    
    async def get_repository_summary(self) -> Dict[str, Any]:
        """Get summary of all configured repositories."""
        total_repos = len(self.repositories)
        enabled_repos = len([r for r in self.repositories.values() if r.enabled])
        
        languages = {}
        for repo in self.repositories.values():
            lang = repo.language or 'unknown'
            languages[lang] = languages.get(lang, 0) + 1
        
        return {
            'total_repositories': total_repos,
            'enabled_repositories': enabled_repos,
            'disabled_repositories': total_repos - enabled_repos,
            'languages': languages,
            'last_discovery': datetime.now().isoformat()
        }
    
    def _load_repository_config(self):
        """Load repository configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                for repo_data in data:
                    repo_config = RepositoryConfig(
                        owner=repo_data['owner'],
                        name=repo_data['name'],
                        full_name=repo_data['full_name'],
                        language=repo_data['language'],
                        default_branch=repo_data['default_branch'],
                        enabled=repo_data.get('enabled', True),
                        analysis_config=repo_data.get('analysis_config', {}),
                        last_analyzed=datetime.fromisoformat(repo_data['last_analyzed']) if repo_data.get('last_analyzed') else None
                    )
                    self.repositories[repo_config.full_name] = repo_config
                
                self.logger.info(f"📂 Loaded {len(self.repositories)} repository configurations")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to load repository config: {e}")
    
    def _save_repository_config(self):
        """Save repository configuration to file."""
        try:
            data = []
            for repo in self.repositories.values():
                data.append({
                    'owner': repo.owner,
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'language': repo.language,
                    'default_branch': repo.default_branch,
                    'enabled': repo.enabled,
                    'analysis_config': repo.analysis_config,
                    'last_analyzed': repo.last_analyzed.isoformat() if repo.last_analyzed else None
                })
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.debug("💾 Saved repository configuration")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save repository config: {e}")
    
    async def refresh_repository_data(self, full_name: str) -> bool:
        """Refresh repository data from GitHub."""
        try:
            owner, name = full_name.split('/')
            repo_data = await self.github_client.get_repository(owner, name)
            
            if full_name in self.repositories:
                repo_config = self.repositories[full_name]
                # Update with fresh data from GitHub
                repo_config.language = repo_data.get('language', repo_config.language)
                repo_config.default_branch = repo_data.get('default_branch', repo_config.default_branch)
                
                self._save_repository_config()
                self.logger.info(f"🔄 Refreshed data for {full_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to refresh repository data for {full_name}: {e}")
            return False

    async def clone_repository(self, repository: str, branch: str = None) -> str:
        """
        Clone a repository to local storage for analysis.
        
        Args:
            repository: Repository name in format 'owner/repo'
            branch: Optional branch name, defaults to repository's default branch
            
        Returns:
            Local path to cloned repository
        """
        import os
        import tempfile
        import subprocess
        from pathlib import Path
        
        try:
            # Create a temporary directory for cloning
            clone_dir = Path(tempfile.mkdtemp(prefix=f"repo_{repository.replace('/', '_')}_"))
            
            # Get repository info to determine clone URL and default branch
            owner, repo_name = repository.split('/')
            repo_data = await self.github_client.get_repository_info(repository)
            
            clone_url = repo_data.get('clone_url')
            if not clone_url:
                # Fallback to HTTPS URL
                clone_url = f"https://github.com/{repository}.git"
            
            # Use specified branch or repository default
            target_branch = branch or repo_data.get('default_branch', 'main')
            
            # Clone the repository
            self.logger.info(f"📥 Cloning {repository} (branch: {target_branch}) to {clone_dir}")
            
            # Use git command to clone
            cmd = [
                'git', 'clone', 
                '--depth', '1',  # Shallow clone for faster operation
                '--branch', target_branch,
                clone_url,
                str(clone_dir)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            self.logger.info(f"✅ Successfully cloned {repository} to {clone_dir}")
            return str(clone_dir)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to clone repository {repository}: {e}")
            raise Exception(f"Repository clone failed: {e}")
