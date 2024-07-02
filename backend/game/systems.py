"""
A file containing systems with game logic.
"""

import random

from uuid import uuid4
from .objects import Level, Prompt, Answer
from ..git import GitRepositoryManager


repo_manager = GitRepositoryManager()

"""
TODO:
- Save game objects from the system to a database (could be relational database)
- Implement logic for generating levels and prompts.
"""

class GameSystem:

    @classmethod
    def generate_new_level(cls, repo: str):

        # Generate 14-unit long as seed
        __min = 10**(14-1)
        __max = 9*__min + (__min-1)

        level = Level(
            id=uuid4(),
            repo_id=repo,
            rand_seed=random.randint(
                __min, __max
            )
        )
        
        repo_manager.get_repository(repo)   # Preload repository

        return level

    @classmethod
    def generate_new_prompt(cls, level: Level):

        # TODO: Make a logic to select a pull request,
        # and master file to prompt.

        prompt = Prompt(
            id=uuid4(),
            level=level.id,
        )

        answer = Answer(
            prompt=prompt.id,
        )

        # return prompt