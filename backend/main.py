import contextlib
from fastapi import FastAPI
from git import Blob

from .config import settings
from .git import list_closed_pull_requests, GitRepositoryManager

@contextlib.asynccontextmanager
async def app_lifecycle(app: FastAPI):
    repo_manager = GitRepositoryManager()
    yield
    repo_manager.cleanup()

app = FastAPI(lifespan=app_lifecycle)

""" @app.get("/commits")
def commits_info(n: int = 10):
    res = {}
    commits = get_n_commits(n)
    for c in commits:
        res[c.hash] = {
            "msg": c.msg,
            "insertions": c.insertions,
            "deletions": c.deletions,
            "modified": c.lines,
            "files": [f.filename for f in c.modified_files],
            "datetime": c.committer_date,
            "timezone": c.committer_timezone
        }
    return res """

@app.get("/pr/{repo:path}")
def pull_requests_info(repo: str, settings: settings):
    return list_closed_pull_requests(repo, settings.gh_api_token)

@app.get("/ls/{repo:path}")
def show_tree_repo(repo: str, settings: settings):
    """
    Show an entire tree (dir) of the repo from root.
    """
    repo_manager = GitRepositoryManager()
    repo_obj = repo_manager.get_repo_gitpython(repo=repo)
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
    repo_obj = repo_manager.get_repo_gitpython(repo=repo)
    master_tree = repo_obj.tree(repo_obj.heads[0])
    
    try:
        readme: Blob = master_tree.join("README.md")
        return readme.data_stream.read()
    except:
        return "No README.md"
