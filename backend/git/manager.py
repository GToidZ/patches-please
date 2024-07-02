import shutil, os, stat, httpx

from typing import Dict
from pathlib import Path
from logging import Logger, getLogger
from re import match

from git import Repo
from git import Repo as GitPythonRepository
from pydriller import Repository as PyDrillerRepository


class RepositoryAccessor:

    path: os.PathLike = ""
    __gitpython_instance: GitPythonRepository = None
    __pydriller_instance: PyDrillerRepository = None

    def __init__(self, path: os.PathLike):
        self.path = path

    def gitpython(self):
        if not self.__gitpython_instance:
            try:
                self.__gitpython_instance = GitPythonRepository(self.path)
            except:
                raise RuntimeError(f"Error while creating a GitPython instance at {self.path}")
        return self.__gitpython_instance

    def pydriller(self):
        if not self.__pydriller_instance:
            try:
                self.__pydriller_instance = PyDrillerRepository(str(self.path))
            except:
                raise RuntimeError(f"Error while creating a PyDriller instance at {self.path}")
        return self.__pydriller_instance

    def close(self):
        if self.__gitpython_instance:
            self.__gitpython_instance.git.clear_cache()
            self.__gitpython_instance.close()

        # we can ignore PyDriller instance since it manages to close the repository
        # on its own.

        # if self.__pydriller_instance:
        #    self.__pydriller_instance.git.clear()


class GitRepositoryManager:

    root_dir = Path("repos")
    repos: Dict[str, Path] = dict()
    active_repos: Dict[str, RepositoryAccessor] = dict()
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
            for repo in self.active_repos.values():
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
    def _get_repository_path(self, repo: str) -> Path:
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
    def get_repository(self, repo: str) -> RepositoryAccessor:
        if repo not in self.active_repos:
            ref = self._get_repository_path(repo)
            ret_repo = RepositoryAccessor(ref)
            self.active_repos[repo] = ret_repo
            return ret_repo
        return self.active_repos[repo]
