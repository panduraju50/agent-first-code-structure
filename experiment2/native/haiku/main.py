"""Taskly API - Task and Project Management System."""

from fastapi import FastAPI, Depends, HTTPException, status
from typing import Optional, Tuple, List
from models import (
    UserCreate, UserResponse, UserSession, ProjectCreate, ProjectResponse,
    TaskCreate, TaskUpdate, TaskResponse, CommentCreate, CommentResponse,
    NotificationResponse, TaskSearchQuery
)
from handlers import (
    UserHandler, ProjectHandler, TaskHandler, CommentHandler, NotificationHandler
)
from db import db

# FastAPI app
app = FastAPI(
    title="Taskly API",
    description="Task and Project Management System",
    version="1.0.0"
)


# Dependency: Extract and validate session token
def get_current_user(authorization: Optional[str] = None) -> str:
    """Extract and validate session token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    user_id = db.get_user_id_from_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


# ========== USER ENDPOINTS ==========

@app.post("/auth/register", response_model=UserSession, tags=["Auth"])
def register(user_create: UserCreate):
    """Register a new user with email and password."""
    return UserHandler.register(user_create)


@app.post("/auth/login", response_model=UserSession, tags=["Auth"])
def login(email: str, password: str):
    """Login a user with email and password."""
    return UserHandler.login(email, password)


@app.post("/auth/logout", tags=["Auth"])
def logout(authorization: Optional[str] = None):
    """Logout a user (invalidate session token)."""
    user_id = get_current_user(authorization)
    # Note: In a real system, we'd need to send token in body or extract it differently
    # For now, tokens are valid until server restart since we're in-memory
    return {"message": "Logged out successfully"}


@app.get("/users/me", response_model=UserResponse, tags=["Users"])
def get_current_user_info(authorization: Optional[str] = None):
    """Get current authenticated user info."""
    user_id = get_current_user(authorization)
    return UserHandler.get_user(user_id)


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: str):
    """Get user by ID."""
    return UserHandler.get_user(user_id)


# ========== PROJECT ENDPOINTS ==========

@app.post("/projects", response_model=ProjectResponse, tags=["Projects"])
def create_project(project_create: ProjectCreate, authorization: Optional[str] = None):
    """Create a new project."""
    user_id = get_current_user(authorization)
    return ProjectHandler.create_project(user_id, project_create)


@app.get("/projects", tags=["Projects"])
def list_projects(limit: int = 20, offset: int = 0, authorization: Optional[str] = None):
    """List all projects for current user."""
    user_id = get_current_user(authorization)
    projects, total = ProjectHandler.list_projects(user_id, limit, offset)
    return {
        "projects": projects,
        "total": total,
        "limit": limit,
        "offset": offset

    }


@app.get("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
def get_project(project_id: str, authorization: Optional[str] = None):
    """Get a project by ID."""
    user_id = get_current_user(authorization)
    return ProjectHandler.get_project(project_id, user_id)


# ========== TASK ENDPOINTS ==========

@app.post("/projects/{project_id}/tasks", response_model=TaskResponse, tags=["Tasks"])
def create_task(project_id: str, task_create: TaskCreate, authorization: Optional[str] = None):
    """Create a new task in a project."""
    user_id = get_current_user(authorization)
    # Override project_id from path
    task_create.project_id = project_id
    return TaskHandler.create_task(user_id, task_create)


@app.get("/projects/{project_id}/tasks", tags=["Tasks"])
def list_project_tasks(project_id: str, limit: int = 20, offset: int = 0, authorization: Optional[str] = None):
    """List all tasks in a project."""
    user_id = get_current_user(authorization)
    tasks, total = TaskHandler.list_project_tasks(project_id, user_id, limit, offset)
    return {
        "tasks": tasks,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task(task_id: str, authorization: Optional[str] = None):
    """Get a task by ID."""
    user_id = get_current_user(authorization)
    return TaskHandler.get_task(task_id, user_id)


@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(task_id: str, task_update: TaskUpdate, authorization: Optional[str] = None):
    """Update a task."""
    user_id = get_current_user(authorization)
    return TaskHandler.update_task(task_id, user_id, task_update)


@app.post("/tasks/{task_id}/complete", response_model=TaskResponse, tags=["Tasks"])
def complete_task(task_id: str, authorization: Optional[str] = None):
    """Mark a task as complete."""
    user_id = get_current_user(authorization)
    return TaskHandler.complete_task(task_id, user_id)


@app.post("/tasks/search", tags=["Tasks"])
def search_tasks(search_query: TaskSearchQuery, authorization: Optional[str] = None):
    """Search for tasks."""
    user_id = get_current_user(authorization)
    tasks, total = TaskHandler.search_tasks(user_id, search_query)
    return {
        "tasks": tasks,
        "total": total,
        "limit": search_query.limit,
        "offset": search_query.offset
    }


# ========== COMMENT ENDPOINTS ==========

@app.post("/tasks/{task_id}/comments", response_model=CommentResponse, tags=["Comments"])
def create_comment(task_id: str, comment_create: CommentCreate, authorization: Optional[str] = None):
    """Create a comment on a task."""
    user_id = get_current_user(authorization)
    return CommentHandler.create_comment(task_id, user_id, comment_create)


@app.get("/tasks/{task_id}/comments", tags=["Comments"])
def get_task_comments(task_id: str, limit: int = 50, offset: int = 0):
    """Get all comments for a task."""
    comments, total = CommentHandler.get_task_comments(task_id, limit, offset)
    return {
        "comments": comments,
        "total": total,
        "limit": limit,
        "offset": offset
    }


# ========== NOTIFICATION ENDPOINTS ==========

@app.get("/notifications", tags=["Notifications"])
def get_notifications(limit: int = 20, offset: int = 0, authorization: Optional[str] = None):
    """Get notifications for current user."""
    user_id = get_current_user(authorization)
    notifications, total = NotificationHandler.get_user_notifications(user_id, limit, offset)
    return {
        "notifications": notifications,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.post("/notifications/{notification_id}/read", response_model=NotificationResponse, tags=["Notifications"])
def mark_notification_read(notification_id: str, authorization: Optional[str] = None):
    """Mark a notification as read."""
    user_id = get_current_user(authorization)
    return NotificationHandler.mark_read(notification_id, user_id)


# ========== HEALTH CHECK ==========

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Taskly API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
