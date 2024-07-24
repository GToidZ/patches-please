"""
A file containing systems with game logic.
"""

import random

from functools import lru_cache
from uuid import uuid4
from typing import List
from datetime import datetime
from sqlmodel import Session, select

from .objects import Level, Prompt, Answer, GameSession
from ..git import GitRepositoryManager, list_merged_pull_requests
from ..config import get_settings
from .db import get_engine


repo_manager = GitRepositoryManager()

"""
TODO:
- Save game objects from the system to a database (could be relational database)
- Implement logic for generating levels and prompts. (In progress)
    - Find a workaround, when a merge is rejected and is from forks, the Git will not
      be able to find the commit. (func at line 44)
"""

class GameSystem:

    def generate_new_level(self, repo: str):

        # Generate 14-unit long as seed
        """ __min = 10**(14-1)
        __max = 9*__min + (__min-1) """

        level = Level(
            id=uuid4(),
            repo_id=repo,
        )

        with Session(get_engine(), expire_on_commit=False) as session:
            session.add(level)
            session.commit()
        
        repo_manager.get_repository(repo)   # Preload repository

        return level
    

    @lru_cache
    def __get_candidate_pull_requests(self, repo: str) -> List:
        """
        Returns a list of candidate pull requests

        A pull request must contain changes to `.py` files to be considered
        a candidate
        """
        candidates: List = []
        pr_list_raw = list_merged_pull_requests(
            repo, get_settings().gh_api_token
        )
        repo_accessed = repo_manager.get_repository(repo).gitpython()

        for pr in pr_list_raw.values():

            # Let's fix it the naive way (find a work around later)
            if not pr['head']['repo']: continue
            if pr['base']['repo']['full_name'] != pr['head']['repo']['full_name']:
                continue
            if str(pr['head']['ref']).startswith('dependabot'):
                # Dependabot has no changes stored in repository.
                continue

            try:
                ref = f"{pr['merge_sha']}^1"
                commit = repo_accessed.commit(ref)
                diff_index = commit.diff(f"{pr['merge_sha']}^2")
            except:
                ref = f"{pr['base']['sha']}"
                commit = repo_accessed.commit(ref)
                diff_index = commit.diff(f"{pr['head']['sha']}")

            for item in diff_index.iter_change_type('M'):
                path: str = item.a_path
                if path.endswith(".py"):
                    candidates.append(pr)
                    continue    # If a .py file is detected, the PR is considered a candidate
        
        return candidates


    def generate_new_prompt(self, level: Level):
        """
        Generate a new prompt for a level
        """
        repo = level.repo_id
        bag = self.__get_candidate_pull_requests(repo)
        selected_pr = random.choice(bag)

        repo_accessed = repo_manager.get_repository(repo).gitpython()

        try:
            ref = f"{selected_pr['merge_sha']}^1"
            commit = repo_accessed.commit(ref)
            diff_index = commit.diff(f"{selected_pr['merge_sha']}^2")
        except:
            ref = f"{selected_pr['base']}"
            commit = repo_accessed.commit(ref)
            diff_index = commit.diff(f"{selected_pr['head']}")

        _files = list(diff_index.iter_change_type('M'))
        master_diff = random.choice(
            list(filter(lambda s: s.a_path.endswith(".py"),
                   _files
                   ))
        )
        master_file = master_diff.a_path

        prompt = Prompt(
            id=uuid4(),
            level=level.id,
            title=selected_pr["title"],
            reference=selected_pr["merge_sha"],
            main_file=master_file
        )

        answer = Answer(
            prompt=prompt.id,
            accept=selected_pr["merged"]
        )

        session = Session(get_engine(), expire_on_commit=False)

        session.add_all([prompt, answer])
        session.commit()
        session.close()

        return prompt


    """
    When displaying a change between parent and to-merge:
    For example, merge commit is `1234abcd`

    * The left side (original/parent) must use parent ref, 1234abcd^1
    * The right side (new) must use another parent ref, 1234abcd^2

    ref: https://haacked.com/archive/2014/02/21/reviewing-merge-commits/
    """


    def send_answer(self, game_session: GameSession, answer: bool):

        db_session = Session(get_engine())

        # TODO: Implement a way for game session to access level and prompt.
        level = game_session.current_level
        _stmt = select(Level).where(Level.id == level)
        _res = db_session.exec(_stmt)
        if not _res:
            raise

        level: Level = _res[0]

        if level:

            _stmt = select(Prompt).where(Prompt.level == level.id) \
                .where(Prompt.submission_time == None)
            _res = db_session.exec(_stmt)
            if not _res:
                raise
            prompt: Prompt = _res[0]

            _stmt = select(Answer).where(Answer.prompt == prompt.id)
            _res = db_session.exec(_stmt)
            if not _res:
                raise
            _answer: Answer = _res[0]
            correct_answer = _answer.accept

            if answer == correct_answer:
                # TODO: Add further scoring logic.
                game_session.score += 10
            else:
                game_session.lives -= 1
            
            prompt.submission_time = datetime.now()
            db_session.add(prompt)
            db_session.commit()

        db_session.close()

        return game_session