"""Data models and entities for Taskly."""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime
from utils import validate_string_field, validate_tags


class UserCreate(BaseModel):
    """Request model for creating a user."""
    name: str
    email: EmailStr
    password: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return validate_string_field(v, 'name', min_length=2, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserResponse(BaseModel):
    """Response model for a user (excludes password)."""
    id: str
    name: str
    email: str
    created_at: str


class UserSession(BaseModel):
    """Represents an authenticated user session."""
    user_id: str
    email: str
    name: str
    token: str
    created_at: str


class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    name: str
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return validate_string_field(v, 'name', min_length=2, max_length=200)

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None:
            return validate_string_field(v, 'description', min_length=0, max_length=1000)
        return v


class ProjectResponse(BaseModel):
    """Response model for a project."""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    created_at: str


class TaskCreate(BaseModel):
    """Request model for creating a task."""
    project_id: str
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    assigned_to: Optional[str] = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        return validate_string_field(v, 'title', min_length=3, max_length=255)

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None:
            return validate_string_field(v, 'description', min_length=0, max_length=2000)
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags_field(cls, v):
        return validate_tags(v)


class TaskUpdate(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None:
            return validate_string_field(v, 'title', min_length=3, max_length=255)
        return v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None:
            return validate_string_field(v, 'description', min_length=0, max_length=2000)
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags_field(cls, v):
        if v is not None:
            return validate_tags(v)
        return v


class TaskResponse(BaseModel):
    """Response model for a task."""
    id: str
    project_id: str
    creator_id: str
    title: str
    description: Optional[str]
    tags: List[str]
    assigned_to: Optional[str]
    completed: bool
    created_at: str
    updated_at: str
    completed_at: Optional[str]


class CommentCreate(BaseModel):
    """Request model for creating a comment."""
    text: str

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        return validate_string_field(v, 'text', min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    """Response model for a comment."""
    id: str
    task_id: str
    user_id: str
    text: str
    created_at: str


class NotificationResponse(BaseModel):
    """Response model for a notification."""
    id: str
    user_id: str
    reference_code: str
    type: str  # 'task_assigned', 'task_completed', 'comment_added'
    resource_id: str  # task_id or comment_id
    message: str
    read: bool
    created_at: str


class TaskSearchQuery(BaseModel):
    """Request model for searching tasks."""
    query: str = Field(..., min_length=1, max_length=255)
    project_id: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    assigned_to: Optional[str] = None
    completed: Optional[bool] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
