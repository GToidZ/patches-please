import contextlib
from fastapi import FastAPI
from git import Blob

from .config import settings
from .git import (
    GitRepositoryManager,
    list_closed_pull_requests,
    list_merged_pull_requests
)
from .game import GameSystem, setup_database

@contextlib.asynccontextmanager
async def app_lifecycle(app: FastAPI):
    setup_database()
    repo_manager = GitRepositoryManager()
    yield
    repo_manager.cleanup()

app = FastAPI(lifespan=app_lifecycle)

# -- Tests --

@app.get("/pr/{repo:path}")
def pull_requests_info(repo: str, settings: settings):
    return list_closed_pull_requests(repo, settings.gh_api_token)

@app.get("/merges/{repo:path}")
def merged_prs(repo: str, settings: settings):
    return list_merged_pull_requests(repo, settings.gh_api_token)

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

@app.get("/test/prompt/{repo:path}")
def test_generate_prompt(repo: str, settings: settings):
    """
    Test generate a prompt in game.
    """
    system = GameSystem()
    level = system.generate_new_level(repo)
    prompt = system.generate_new_prompt(level)
    return prompt.model_dump_json()