import shutil, os, stat, httpx

from typing import Dict, Union
from pathlib import Path
from logging import Logger, getLogger
from re import match

from git import Repo
from git import Repo as GitPythonRepository
from pydriller import Repository as PyDrillerRepository

class GitRepositoryManager:

    root_dir = Path("repos")
    repos: Dict[str, Path] = dict()
    active_repos: Dict[str, Union[GitPythonRepository, PyDrillerRepository]] = dict()
    logger: Logger = getLogger("RepoManager")

    def __new__(cls) -> "GitRepositoryManager":
        if not hasattr(cls, "instance"):
            cls.instance = super(GitRepositoryManager, cls).__new__(cls)
            cls.instance.__prepare()
        return cls.instance
    
    def __prepare(self):
        # Check if the temporary root directory exists,
        self.logger.debug("Preparing Git repository manager...")
        if self.cleanup(): self.logger.debug("Outdated temporary directory was removed!")
        self.root_dir.mkdir()

    def cleanup(self):
        if self.active_repos:
            # TODO: Make it compatible with PyDriller
            for repo in self.active_repos.values():
                repo.git.clear_cache()
                repo.close()
        if self.root_dir.exists():
            for root, dirs, files in os.walk(self.root_dir):
                for dir in dirs:
                    os.chmod(os.path.join(root, dir), stat.S_IRWXU)
                for file in files:
                    os.chmod(os.path.join(root, file), stat.S_IRWXU)
            shutil.rmtree(self.root_dir)
            return True
        return False

    """
    The `repo` argument of functions below this comment
    corresponds to regex pattern of 'owner/name'
    """
    def __repo_str_constraint(fn):
        def wrapper(self, repo: str, *args, **kwargs):
            if not match(r'^[\w.\-]+\/[\w.\-]+$', repo):
                raise ValueError(f"'{repo}' repository is not in 'owner/name' format.")
            return fn(self, repo, *args, **kwargs)
        return wrapper

    @__repo_str_constraint
    def _get_repository(self, repo: str) -> Path:
        if not repo in self.repos:
            self.__clone_repository(repo)
        return self.repos[repo]

    @__repo_str_constraint
    def __clone_repository(self, repo: str):
        gh_url = f"https://github.com/{repo}"
        if (httpx.get(gh_url)).status_code != httpx.codes.OK:
            raise ValueError(f"Repository does not exist on GitHub.")
        
        ref_path = self.root_dir.joinpath(repo)
        if not ref_path.exists():
            Repo.clone_from(f"{gh_url}.git", to_path=ref_path)
        
        self.repos[repo] = ref_path.absolute()

    @__repo_str_constraint
    def get_repo_gitpython(self, repo: str) -> GitPythonRepository:
        if repo not in self.active_repos:
            ref = self._get_repository(repo)
            ret_repo = GitPythonRepository(ref)
            self.active_repos[repo] = ret_repo
            return ret_repo
        return self.active_repos[repo]

    @__repo_str_constraint
    def get_repo_pydriller(self, repo: str) -> PyDrillerRepository:
        # TODO: Hook this to GitPython Repository so we can use the Delta Maintainability Model
        ref = self._get_repository(repo)
        return PyDrillerRepository(ref)
