from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid

# Constants
MAX_TITLE_LENGTH = 200
MAX_INGREDIENTS = 50

class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str  # TODO: Add validation for max length
    description: str
    ingredients: List[str]
    instructions: List[str]
    tags: List[str] = Field(default_factory=list)
    region: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    # Future fields?
    # difficulty: str
    # prep_time: int
    # cook_time: int

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RecipeCreate(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    tags: List[str] = Field(default_factory=list)
    region: str


class RecipeUpdate(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    tags: List[str]
    region: str
