import contextlib
import itertools
from fastapi import FastAPI
from git import Blob

from .config import settings
from .git import GitRepositoryManager
from .git.github import list_closed_pull_requests

@contextlib.asynccontextmanager
async def app_lifecycle(app: FastAPI):
    repo_manager = GitRepositoryManager()
    yield
    repo_manager.cleanup()

app = FastAPI(lifespan=app_lifecycle)


# -- Tests --

@app.get("/pr/{repo:path}")
def pull_requests_info(repo: str, settings: settings):
    return list_closed_pull_requests(repo, settings.gh_api_token)

@app.get("/ls/{repo:path}")
def show_tree_repo(repo: str, settings: settings):
    """
    Show an entire tree (dir) of the repo from root.
    """
    repo_manager = GitRepositoryManager()
    repo_obj = repo_manager.get_repository(repo=repo).gitpython()
    master_tree = repo_obj.tree(repo_obj.heads[0])
    resp = []
    for obj in master_tree.list_traverse():
        resp.append(f"{obj.path} ||| type: {obj.type}")
    return resp

@app.get("/readme/{repo:path}")
def show_readme(repo: str, settings: settings):
    """
    Show contents of README.md file in repo.
    """
    repo_manager = GitRepositoryManager()
    repo_obj = repo_manager.get_repository(repo=repo).gitpython()
    master_tree = repo_obj.tree(repo_obj.heads[0])
    
    try:
        readme: Blob = master_tree.join("README.md")
        return readme.data_stream.read()
    except:
        return "No README.md"

@app.get("/commits/{repo:path}")
def list_commits_pydriller(repo: str, settings: settings):
    """
    List commits using PyDriller.
    """
    repo_manager = GitRepositoryManager()
    repo_obj = repo_manager.get_repository(repo=repo).pydriller()
    resp = []
    for c in repo_obj.traverse_commits():
        resp.append({
            "title": c.msg,
            "when": c.committer_date
        })
    return resp
