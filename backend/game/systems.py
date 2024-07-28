"""
A file containing systems with game logic.
"""

import random

from functools import lru_cache
from uuid import uuid4
from typing import List, Dict
from datetime import datetime
from sqlmodel import Session, select
from git import Diff

from .objects import Level, Prompt, Answer, GameSession
from ..git import GitRepositoryManager, list_merged_pull_requests
from ..config import get_settings
from .db import get_engine


repo_manager = GitRepositoryManager()

class GameSystem:

    _game_sessions: Dict[str, GameSession] = dict()

    def __new__(cls) -> "GameSystem":
        if not hasattr(cls, "instance"):
            cls.instance = super(GameSystem, cls).__new__(cls)
        return cls.instance
    
    def new_game(self) -> GameSession:
        session = GameSession()
        self._game_sessions[str(session.id)] = session
        return session
    
    def get_session(self, sid: str) -> GameSession:
        try:
            return self._game_sessions[sid]
        except:
            raise ValueError("Session with such ID does not exist")

    def generate_new_level(self, sid: str, repo: str):

        game_session = self.get_session(sid)

        level = Level(
            id=uuid4(),
            repo_id=repo,
        )

        with Session(get_engine(), expire_on_commit=False) as session:
            session.add(level)
            session.commit()
        
        repo_manager.get_repository(repo)   # Preload repository
        game_session.current_level = level

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


    def generate_new_prompt(self, sid: str, level: Level):
        """
        Generate a new prompt for a level
        """
        game_session = self.get_session(sid)
        
        repo = level.repo_id
        bag = self.__get_candidate_pull_requests(repo)
        selected_pr = random.choice(bag)

        repo_accessed = repo_manager.get_repository(repo).gitpython()

        try:
            ref = f"{selected_pr['merge_sha']}^1"
            commit = repo_accessed.commit(ref)
            diff_index = commit.diff(f"{selected_pr['merge_sha']}^2")
        except:
            ref = f"{selected_pr['base']['sha']}"
            commit = repo_accessed.commit(ref)
            diff_index = commit.diff(f"{selected_pr['head']['sha']}")

        _files: List[Diff] = list(diff_index.iter_change_type('M'))
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
            main_file=master_file,
            file_a_contents=master_diff.a_blob.data_stream.read(),
            file_b_contents=master_diff.b_blob.data_stream.read(),
        )

        answer = Answer(
            prompt=prompt.id,
            accept=selected_pr["merged"]
        )

        session = Session(get_engine(), expire_on_commit=False)

        session.add_all([prompt, answer])
        session.commit()
        session.close()

        game_session.current_prompt = prompt

        return prompt


    """
    When displaying a change between parent and to-merge:
    For example, merge commit is `1234abcd`

    * The left side (original/parent) must use parent ref, 1234abcd^1
    * The right side (new) must use another parent ref, 1234abcd^2

    ref: https://haacked.com/archive/2014/02/21/reviewing-merge-commits/
    """


    def send_answer(self, sid: str, answer: bool) -> GameSession:
        db_session = Session(get_engine(), expire_on_commit=False)

        game_session = self.get_session(sid)
        level = game_session.current_level
        _stmt = select(Level).where(Level.id == level)
        _res = db_session.exec(_stmt)

        level: Level = _res.one()

        if level:

            _stmt = select(Prompt).where(Prompt.level == level.id) \
                .where(Prompt.submission_time == None)
            _res = db_session.exec(_stmt)
            if not _res:
                raise
            prompt: Prompt = _res.one()

            _stmt = select(Answer).where(Answer.prompt == prompt.id)
            _res = db_session.exec(_stmt)
            if not _res:
                raise
            _answer: Answer = _res.one()
            correct_answer = _answer.accept

            if answer == correct_answer:
                # TODO: Add further scoring logic.
                game_session.score += 10
            else:
                game_session.lives -= 1
            
            prompt.submission_time = datetime.now()
            db_session.add(prompt)

            if level.prompt_number < level.max_prompts:
                level.prompt_number += 1
                self.generate_new_prompt(game_session.id, level)
                db_session.add(level)
            else:
                game_session.current_prompt = None
                game_session.current_level = None

            db_session.commit()

        db_session.close()

        return game_session
