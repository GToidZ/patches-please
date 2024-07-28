"""
A file containing classess that represent the objects inside the game.
All objects are JSON-serializable and any values must be in purest literal form.

Note: We can use Pydantic's BaseModel to create game object models.
"""

from re import match
from uuid import uuid4, UUID

from datetime import datetime
from typing import Annotated, Union, Optional
from pydantic import BaseModel
from pydantic import Field as PydanticField
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
    id: UUID = PydanticField(default_factory=uuid4)   # Session ID
    current_level: Optional["Level"] = None
    current_prompt: Optional["Prompt"] = None

    lives: int = 5
    score: int = 0

class Level(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)   # Level ID

    repo_id: Annotated[
        str, AfterValidator(_validate_repo_name)
    ] = Field()

    prompt_number: int = Field(default=1)
    max_prompts: int = Field(default=10)

class Prompt(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    level: UUID = Field(foreign_key="level.id", ondelete="CASCADE")

    title: str = Field()
    reference: str = Field()     # Ref string for Git object to merge commit
    main_file: str = Field()     # Path from root of repo to file
    file_a_contents: bytes = Field()
    file_b_contents: bytes = Field()

    start_time: datetime = Field(default_factory=datetime.now)
    submission_time: Optional[datetime] = Field(default=None)

class Answer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt: UUID = Field(foreign_key="prompt.id", ondelete="CASCADE")
    accept: bool = Field()
