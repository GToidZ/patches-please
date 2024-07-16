from re import match

import hishel, httpx
#from hishel_sqla._sync import SQLAlchemyStorage

_GH_API_URL = "https://api.github.com"
client = hishel.CacheClient(
    storage=hishel.SQLiteStorage()
    #storage=SQLAlchemyStorage(
        #get_settings().sql_db_url
    #)
)

def list_closed_pull_requests(repo_name: str, token: str):
    # Sends a GET request to GitHub API, /repos/{owner}/{repo}/pulls
    if not match(r'^[\w.\-]+\/[\w.\-]+$', repo_name):
        raise ValueError(f"Name of the repository {repo_name} is not in 'owner/name' format.")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    r = client.get(f"{_GH_API_URL}/repos/{repo_name}/pulls?state=closed&per_page=100", headers=headers)
    if r.status_code != httpx.codes.OK:
        raise RuntimeError(f"Cannot obtain pull requests from GitHub repository, {repo_name}.")
    return r.json()


def list_merged_pull_requests(repo_name: str, token: str):
    result = {}
    resp = list_closed_pull_requests(repo_name, token)
    for idx, entry in enumerate(resp):
        result[str(idx)] = {
            "title": entry["title"],
            "merged": True if entry["merged_at"] else False,
            "merge_sha": entry["merge_commit_sha"],
        }
    return result
