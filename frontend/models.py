from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict


class Role(Enum):
    user = "user"
    agent = "agent"


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role
    message: str


class Transcript(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript: List[Message]
