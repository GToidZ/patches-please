"""
A file containing classess that represent the objects inside the game.
All objects are JSON-serializable and any values must be in purest literal form.

Note: We can use Pydantic's BaseModel to create game object models.
"""

from re import match

from datetime import datetime
from typing import Annotated, Union
from pydantic import BaseModel, UUID4
from pydantic.functional_validators import AfterValidator

"""
TODO: 
- Add statistics game object for calculating and insights for players after the game ends.
"""

def _validate_repo_name(v: str) -> str:
    assert match(r'^[\w.\-]+\/[\w.\-]+$', v), \
        f"'{v}' repository is not in 'owner/name' format."
    return v

"""
Object Hierarchy:

GameSession
Level
|-- Prompt
|-- Answer
"""

class GameSession(BaseModel):
    id: UUID4   # Session ID
    current_level: Union[UUID4, None] = None

    lives: int = 5
    score: int = 0

class Level(BaseModel):
    id: UUID4   # Level ID

    repo_id: Annotated[
        str, AfterValidator(_validate_repo_name)
    ]

    """ rand_seed: int
    rand_step: int = 0 """

class Prompt(BaseModel):
    id: UUID4
    level: UUID4

    reference: str      # Ref string for Git object to merge commit
    main_file: str      # Path from root of repo to file

    start_time: datetime = datetime.now()
    submission_time: Union[datetime, None] = None

class Answer(BaseModel):
    prompt: UUID4
    accept: bool
