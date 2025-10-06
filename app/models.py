from pydantic import BaseModel, Field, ConfigDict, field_serializer, field_validator
from datetime import datetime
from typing import List, Optional, Literal
import uuid
import re

# Constants
MAX_TITLE_LENGTH = 200
MAX_INGREDIENTS = 50
MAX_INSTRUCTIONS = 50
MAX_TAGS = 20
MAX_DESCRIPTION_LENGTH = 2000

class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=3, max_length=MAX_TITLE_LENGTH, description="Recipe title (3-200 characters)")
    description: str = Field(..., min_length=10, max_length=MAX_DESCRIPTION_LENGTH, description="Recipe description (10-2000 characters)")
    ingredients: List[str] = Field(..., min_length=1, max_length=MAX_INGREDIENTS, description="List of ingredients (1-50 items)")
    instructions: List[str] = Field(..., min_length=1, max_length=MAX_INSTRUCTIONS, description="List of instruction steps (1-50 items)")
    tags: List[str] = Field(default_factory=list, max_length=MAX_TAGS, description="Optional tags (max 20)")
    region: str = Field(..., min_length=2, max_length=100, description="Geographic region (2-100 characters)")
    cuisine: str = Field(..., min_length=2, max_length=100, description="Cuisine type (2-100 characters)")
    source: Literal["internal", "external"] = Field(default="internal", description="Recipe source: internal or external")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict()
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError('At least one ingredient is required')
        
        validated_ingredients = []
        for i, ingredient in enumerate(v):
            if not isinstance(ingredient, str):
                raise ValueError(f'Ingredient {i+1} must be a string')
            ingredient = ingredient.strip()
            if not ingredient:
                raise ValueError(f'Ingredient {i+1} cannot be empty')
            if len(ingredient) < 2:
                raise ValueError(f'Ingredient {i+1} must be at least 2 characters')
            validated_ingredients.append(ingredient)
        
        return validated_ingredients
    
    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v):
        if not v:
            raise ValueError('At least one instruction step is required')
        
        validated_instructions = []
        for i, instruction in enumerate(v):
            if not isinstance(instruction, str):
                raise ValueError(f'Instruction step {i+1} must be a string')
            instruction = instruction.strip()
            if not instruction:
                raise ValueError(f'Instruction step {i+1} cannot be empty')
            if len(instruction) < 5:
                raise ValueError(f'Instruction step {i+1} must be at least 5 characters')
            validated_instructions.append(instruction)
        
        return validated_instructions
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if not v:
            return []
        
        validated_tags = []
        for i, tag in enumerate(v):
            if not isinstance(tag, str):
                raise ValueError(f'Tag {i+1} must be a string')
            tag = tag.strip()
            if not tag:
                continue  # Skip empty tags
            if len(tag) > 30:
                raise ValueError(f'Tag {i+1} cannot exceed 30 characters')
            validated_tags.append(tag)
        
        return validated_tags
    
    @field_validator('region', 'cuisine')
    @classmethod
    def validate_region_cuisine(cls, v):
        if not v or not v.strip():
            raise ValueError('Region and cuisine cannot be empty or whitespace only')
        return v.strip()
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=MAX_TITLE_LENGTH, description="Recipe title (3-200 characters)")
    description: str = Field(..., min_length=10, max_length=MAX_DESCRIPTION_LENGTH, description="Recipe description (10-2000 characters)")
    ingredients: List[str] = Field(..., min_length=1, max_length=MAX_INGREDIENTS, description="List of ingredients (1-50 items)")
    instructions: List[str] = Field(..., min_length=1, max_length=MAX_INSTRUCTIONS, description="List of instruction steps (1-50 items)")
    tags: List[str] = Field(default_factory=list, max_length=MAX_TAGS, description="Optional tags (max 20)")
    region: str = Field(..., min_length=2, max_length=100, description="Geographic region (2-100 characters)")
    cuisine: str = Field(..., min_length=2, max_length=100, description="Cuisine type (2-100 characters)")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError('At least one ingredient is required')
        
        validated_ingredients = []
        for i, ingredient in enumerate(v):
            if not isinstance(ingredient, str):
                raise ValueError(f'Ingredient {i+1} must be a string')
            ingredient = ingredient.strip()
            if not ingredient:
                raise ValueError(f'Ingredient {i+1} cannot be empty')
            if len(ingredient) < 2:
                raise ValueError(f'Ingredient {i+1} must be at least 2 characters')
            validated_ingredients.append(ingredient)
        
        return validated_ingredients
    
    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v):
        if not v:
            raise ValueError('At least one instruction step is required')
        
        validated_instructions = []
        for i, instruction in enumerate(v):
            if not isinstance(instruction, str):
                raise ValueError(f'Instruction step {i+1} must be a string')
            instruction = instruction.strip()
            if not instruction:
                raise ValueError(f'Instruction step {i+1} cannot be empty')
            if len(instruction) < 5:
                raise ValueError(f'Instruction step {i+1} must be at least 5 characters')
            validated_instructions.append(instruction)
        
        return validated_instructions
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if not v:
            return []
        
        validated_tags = []
        for i, tag in enumerate(v):
            if not isinstance(tag, str):
                raise ValueError(f'Tag {i+1} must be a string')
            tag = tag.strip()
            if not tag:
                continue  # Skip empty tags
            if len(tag) > 30:
                raise ValueError(f'Tag {i+1} cannot exceed 30 characters')
            validated_tags.append(tag)
        
        return validated_tags
    
    @field_validator('region', 'cuisine')
    @classmethod
    def validate_region_cuisine(cls, v):
        if not v or not v.strip():
            raise ValueError('Region and cuisine cannot be empty or whitespace only')
        return v.strip()


class RecipeUpdate(BaseModel):
    title: str = Field(..., min_length=3, max_length=MAX_TITLE_LENGTH, description="Recipe title (3-200 characters)")
    description: str = Field(..., min_length=10, max_length=MAX_DESCRIPTION_LENGTH, description="Recipe description (10-2000 characters)")
    ingredients: List[str] = Field(..., min_length=1, max_length=MAX_INGREDIENTS, description="List of ingredients (1-50 items)")
    instructions: List[str] = Field(..., min_length=1, max_length=MAX_INSTRUCTIONS, description="List of instruction steps (1-50 items)")
    tags: List[str] = Field(default_factory=list, max_length=MAX_TAGS, description="Optional tags (max 20)")
    region: str = Field(..., min_length=2, max_length=100, description="Geographic region (2-100 characters)")
    cuisine: str = Field(..., min_length=2, max_length=100, description="Cuisine type (2-100 characters)")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v):
        if not v:
            raise ValueError('At least one ingredient is required')
        
        validated_ingredients = []
        for i, ingredient in enumerate(v):
            if not isinstance(ingredient, str):
                raise ValueError(f'Ingredient {i+1} must be a string')
            ingredient = ingredient.strip()
            if not ingredient:
                raise ValueError(f'Ingredient {i+1} cannot be empty')
            if len(ingredient) < 2:
                raise ValueError(f'Ingredient {i+1} must be at least 2 characters')
            validated_ingredients.append(ingredient)
        
        return validated_ingredients
    
    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v):
        if not v:
            raise ValueError('At least one instruction step is required')
        
        validated_instructions = []
        for i, instruction in enumerate(v):
            if not isinstance(instruction, str):
                raise ValueError(f'Instruction step {i+1} must be a string')
            instruction = instruction.strip()
            if not instruction:
                raise ValueError(f'Instruction step {i+1} cannot be empty')
            if len(instruction) < 5:
                raise ValueError(f'Instruction step {i+1} must be at least 5 characters')
            validated_instructions.append(instruction)
        
        return validated_instructions
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if not v:
            return []
        
        validated_tags = []
        for i, tag in enumerate(v):
            if not isinstance(tag, str):
                raise ValueError(f'Tag {i+1} must be a string')
            tag = tag.strip()
            if not tag:
                continue  # Skip empty tags
            if len(tag) > 30:
                raise ValueError(f'Tag {i+1} cannot exceed 30 characters')
            validated_tags.append(tag)
        
        return validated_tags
    
    @field_validator('region', 'cuisine')
    @classmethod
    def validate_region_cuisine(cls, v):
        if not v or not v.strip():
            raise ValueError('Region and cuisine cannot be empty or whitespace only')
        return v.strip()
