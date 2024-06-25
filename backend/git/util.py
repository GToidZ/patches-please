from pydriller import Repository, Git, Commit
from typing import List
from re import match

import itertools
import httpx

_GH_API_URL = "https://api.github.com"


def get_repository(repo_name: str) -> Repository:
    return Repository(f"https://github.com/{repo_name}.git",
                      only_modifications_with_file_types=[".py"])

def list_closed_pull_requests(repo_name: str, token: str):
    # TODO: implement caching.
    # Sends a GET request to GitHub API, /repos/{owner}/{repo}/pulls
    if not isinstance(repo_name, str):
        raise TypeError(f"Name of the repository {repo_name} is not a string.")
    if not match(r'^[\w.\-]+\/[\w.\-]+$', repo_name):
        raise ValueError(f"Name of the repository {repo_name} is not in 'owner/name' format.")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    r = httpx.get(f"{_GH_API_URL}/repos/{repo_name}/pulls?state=closed", headers=headers)
    if r.status_code != httpx.codes.OK:
        raise RuntimeError(f"Cannot obtain pull requests from GitHub repository, {repo_name}.")
    return r.json()

""" TODO: Use GitPython instead of PyDriller.

    The problems right now are:
    - PyDriller does not support usage of trees. (File listing of repository.)
    - PyDriller Git class requires local repository instead of remote repository,
    so their functionality on automatic repository cloning isn't supported.
    - PyDriller does not provide a way to directly access Repo class from GitPython,
    so it is not possible to call any external methods that are not from PyDriller.

    To fix them:
    - Use GitPython directly instead.
    - The GitPython library provides all types of objects including Blobs.
    - Blobs are a unit of file in a repository. It also provides `data_stream` property,
    use it to read file contents.
    - GitPython provides a method to easily clone remote repository, however it doesn't provide
    automatic deletion after usage. (requires manual implementation)

    Drawbacks:
    - GitPython does not have Delta Maintainability Model, but we can still hook the repository from
    GitPython up to PyDriller, so it's fixable.
    - There are less abstraction in GitPython, which requires intensive research.
"""

# -- Playground --

def get_n_commits(n: int) -> List[Commit]:
    return itertools.islice(get_repository("").traverse_commits(), n)
