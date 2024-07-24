"""
A file containing classess that represent the objects inside the game.
All objects are JSON-serializable and any values must be in purest literal form.

Note: We can use Pydantic's BaseModel to create game object models.
"""

from re import match
from uuid import uuid4, UUID

from datetime import datetime
from typing import Annotated, Union
from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator
from sqlmodel import Field, SQLModel

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
    id: UUID = uuid4()   # Session ID
    current_level: Union[UUID, None] = None

    lives: int = 5
    score: int = 0

class Level(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)   # Level ID

    repo_id: Annotated[
        str, AfterValidator(_validate_repo_name)
    ] = Field()

class Prompt(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    level: UUID = Field()

    title: str = Field()
    reference: str = Field()     # Ref string for Git object to merge commit
    main_file: str = Field()     # Path from root of repo to file

    start_time: datetime = Field(default_factory=datetime.now)
    submission_time: Union[datetime, None] = Field(default=None)

class Answer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    prompt: UUID = Field()
    accept: bool = Field()
