from re import match

import hishel, httpx
#from hishel_sqla._sync import SQLAlchemyStorage

from ...config import get_settings

_GH_API_URL = "https://api.github.com"
client = hishel.CacheClient(
    storage=hishel.SQLiteStorage()
    #storage=SQLAlchemyStorage(
        #get_settings().sql_db_url
    #)
)

"""
TODO:
- Add more functions that are related to using GitHub REST API.
! Change the name of this Python file.
"""

def list_closed_pull_requests(repo_name: str, token: str):
    """
    TODO: Implement caching for HTTP(S) requests to GitHub API.
    The ideas:
    - httpx recommends using a drop-in replacement called 'Hishel'
    - Hishel supports SQLite, however let's see if other relational database is supported.
    - Amazingly, devs of Hishel documented the example of caching GitHub responses here,
        https://hishel.com/examples/github/
    """
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
    r = client.get(f"{_GH_API_URL}/repos/{repo_name}/pulls?state=closed", headers=headers)
    if r.status_code != httpx.codes.OK:
        raise RuntimeError(f"Cannot obtain pull requests from GitHub repository, {repo_name}.")
    return r.json()
