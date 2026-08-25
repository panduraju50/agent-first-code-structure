"""Business logic handlers for Taskly operations."""

from typing import Optional, Tuple, Dict, Any, List
from fastapi import HTTPException, status
from models import (
    UserCreate, UserResponse, UserSession, ProjectCreate, ProjectResponse,
    TaskCreate, TaskUpdate, TaskResponse, CommentCreate, CommentResponse,
    NotificationResponse, TaskSearchQuery
)
from db import db
from utils import (
    hash_password, verify_password, validate_email_address, generate_session_token,
    generate_notification_code, format_datetime, get_utc_now, validate_pagination
)


class UserHandler:
    """Handle user-related operations."""

    @staticmethod
    def register(user_create: UserCreate) -> UserSession:
        """Register a new user. Raises HTTPException if email already exists."""
        # Validate email
        try:
            email = validate_email_address(user_create.email)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Check if user exists
        if db.user_exists(email):
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )

        # Hash password
        try:
            password_hash = hash_password(user_create.password)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Create user
        user_id = db.create_user(user_create.name, email, password_hash)
        user = db.get_user_by_id(user_id)

        # Create session
        token = generate_session_token()
        db.create_session(user_id, token)

        return UserSession(
            user_id=user['id'],
            email=user['email'],
            name=user['name'],
            token=token,
            created_at=format_datetime(user['created_at'])
        )

    @staticmethod
    def login(email: str, password: str) -> UserSession:
        """Login a user. Raises HTTPException if credentials invalid."""
        # Validate email
        try:
            email = validate_email_address(email)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Get user
        user = db.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password
        if not verify_password(password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create session
        token = generate_session_token()
        db.create_session(user['id'], token)

        return UserSession(
            user_id=user['id'],
            email=user['email'],
            name=user['name'],
            token=token,
            created_at=format_datetime(user['created_at'])
        )

    @staticmethod
    def get_user(user_id: str) -> UserResponse:
        """Get a user by ID."""
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            id=user['id'],
            name=user['name'],
            email=user['email'],
            created_at=format_datetime(user['created_at'])
        )


class ProjectHandler:
    """Handle project-related operations."""

    @staticmethod
    def create_project(user_id: str, project_create: ProjectCreate) -> ProjectResponse:
        """Create a new project."""
        # Verify user exists
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        project_id = db.create_project(user_id, project_create.name, project_create.description)
        project = db.get_project(project_id)

        return ProjectResponse(
            id=project['id'],
            user_id=project['user_id'],
            name=project['name'],
            description=project['description'],
            created_at=format_datetime(project['created_at'])
        )

    @staticmethod
    def get_project(project_id: str, user_id: str) -> ProjectResponse:
        """Get a project. Verifies ownership."""
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return ProjectResponse(
            id=project['id'],
            user_id=project['user_id'],
            name=project['name'],
            description=project['description'],
            created_at=format_datetime(project['created_at'])
        )

    @staticmethod
    def list_projects(user_id: str, limit: int = 20, offset: int = 0) -> Tuple[List[ProjectResponse], int]:
        """List projects for a user with pagination."""
        limit, offset = validate_pagination(limit, offset)

        projects = db.get_user_projects(user_id, limit, offset)
        total = db.get_user_projects_count(user_id)

        return [
            ProjectResponse(
                id=p['id'],
                user_id=p['user_id'],
                name=p['name'],
                description=p['description'],
                created_at=format_datetime(p['created_at'])
            )
            for p in projects
        ], total


class TaskHandler:
    """Handle task-related operations."""

    @staticmethod
    def create_task(user_id: str, task_create: TaskCreate) -> TaskResponse:
        """Create a new task."""
        # Verify project exists and is owned by user
        project = db.get_project(task_create.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # If assigned_to specified, verify user exists
        if task_create.assigned_to:
            assigned_user = db.get_user_by_id(task_create.assigned_to)
            if not assigned_user:
                raise HTTPException(status_code=404, detail="Assigned user not found")

        task_id = db.create_task(
            task_create.project_id,
            user_id,
            task_create.title,
            task_create.description,
            task_create.tags,
            task_create.assigned_to
        )
        task = db.get_task(task_id)

        # Create notification if assigned
        if task_create.assigned_to:
            ref_code = generate_notification_code()
            db.create_notification(
                task_create.assigned_to,
                ref_code,
                'task_assigned',
                task_id,
                f"You've been assigned to task: {task_create.title}"
            )

        return TaskHandler._task_to_response(task)

    @staticmethod
    def get_task(task_id: str, user_id: str) -> TaskResponse:
        """Get a task. Verifies user has access to the project."""
        task = db.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        project = db.get_project(task['project_id'])
        if project['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return TaskHandler._task_to_response(task)

    @staticmethod
    def list_project_tasks(project_id: str, user_id: str, limit: int = 20, offset: int = 0) -> Tuple[List[TaskResponse], int]:
        """List tasks for a project with pagination."""
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        limit, offset = validate_pagination(limit, offset)

        tasks = db.get_project_tasks(project_id, limit, offset)
        total = db.get_project_tasks_count(project_id)

        return [TaskHandler._task_to_response(t) for t in tasks], total

    @staticmethod
    def update_task(task_id: str, user_id: str, task_update: TaskUpdate) -> TaskResponse:
        """Update a task."""
        task = db.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        project = db.get_project(task['project_id'])
        if project['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Validate assigned_to if specified
        if task_update.assigned_to:
            assigned_user = db.get_user_by_id(task_update.assigned_to)
            if not assigned_user:
                raise HTTPException(status_code=404, detail="Assigned user not found")

        # Prepare update dict with only provided fields
        update_dict = {}
        if task_update.title is not None:
            update_dict['title'] = task_update.title
        if task_update.description is not None:
            update_dict['description'] = task_update.description
        if task_update.tags is not None:
            update_dict['tags'] = task_update.tags
        if task_update.assigned_to is not None:
            update_dict['assigned_to'] = task_update.assigned_to
        if task_update.completed is not None:
            update_dict['completed'] = task_update.completed

        db.update_task(task_id, **update_dict)
        task = db.get_task(task_id)

        # Create notification if task completed
        if task_update.completed and not task['completed']:
            ref_code = generate_notification_code()
            db.create_notification(
                task['creator_id'],
                ref_code,
                'task_completed',
                task_id,
                f"Task '{task['title']}' has been completed"
            )

        return TaskHandler._task_to_response(task)

    @staticmethod
    def complete_task(task_id: str, user_id: str) -> TaskResponse:
        """Mark a task as complete."""
        task = db.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        project = db.get_project(task['project_id'])
        if project['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        db.update_task(task_id, completed=True)
        task = db.get_task(task_id)

        # Create notification to creator
        ref_code = generate_notification_code()
        db.create_notification(
            task['creator_id'],
            ref_code,
            'task_completed',
            task_id,
            f"Task '{task['title']}' has been completed"
        )

        return TaskHandler._task_to_response(task)

    @staticmethod
    def search_tasks(user_id: str, search_query: TaskSearchQuery) -> Tuple[List[TaskResponse], int]:
        """Search tasks."""
        results = db.search_tasks(
            search_query.query,
            project_id=search_query.project_id,
            tags=search_query.tags if search_query.tags else None,
            assigned_to=search_query.assigned_to,
            completed=search_query.completed,
            limit=search_query.limit,
            offset=search_query.offset
        )

        # Filter by user authorization (only return tasks from user's projects)
        authorized_results = []
        for task in results:
            project = db.get_project(task['project_id'])
            if project and project['user_id'] == user_id:
                authorized_results.append(task)

        return [TaskHandler._task_to_response(t) for t in authorized_results], len(authorized_results)

    @staticmethod
    def _task_to_response(task: Dict[str, Any]) -> TaskResponse:
        """Convert task dict to TaskResponse."""
        return TaskResponse(
            id=task['id'],
            project_id=task['project_id'],
            creator_id=task['creator_id'],
            title=task['title'],
            description=task['description'],
            tags=task['tags'],
            assigned_to=task['assigned_to'],
            completed=task['completed'],
            created_at=format_datetime(task['created_at']),
            updated_at=format_datetime(task['updated_at']),
            completed_at=format_datetime(task['completed_at'])
        )


class CommentHandler:
    """Handle comment-related operations."""

    @staticmethod
    def create_comment(task_id: str, user_id: str, comment_create: CommentCreate) -> CommentResponse:
        """Create a comment on a task."""
        task = db.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        comment_id = db.create_comment(task_id, user_id, comment_create.text)
        comment = db.comments[comment_id]

        # Create notification to task creator
        ref_code = generate_notification_code()
        db.create_notification(
            task['creator_id'],
            ref_code,
            'comment_added',
            comment_id,
            f"New comment on task '{task['title']}'"
        )

        return CommentResponse(
            id=comment['id'],
            task_id=comment['task_id'],
            user_id=comment['user_id'],
            text=comment['text'],
            created_at=format_datetime(comment['created_at'])
        )

    @staticmethod
    def get_task_comments(task_id: str, limit: int = 50, offset: int = 0) -> Tuple[List[CommentResponse], int]:
        """Get comments for a task."""
        task = db.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        limit, offset = validate_pagination(limit, offset)

        comments = db.get_task_comments(task_id, limit, offset)
        total = db.get_task_comments_count(task_id)

        return [
            CommentResponse(
                id=c['id'],
                task_id=c['task_id'],
                user_id=c['user_id'],
                text=c['text'],
                created_at=format_datetime(c['created_at'])
            )
            for c in comments
        ], total


class NotificationHandler:
    """Handle notification-related operations."""

    @staticmethod
    def get_user_notifications(user_id: str, limit: int = 20, offset: int = 0) -> Tuple[List[NotificationResponse], int]:
        """Get notifications for a user."""
        limit, offset = validate_pagination(limit, offset)

        notifications = db.get_user_notifications(user_id, limit, offset)
        total = db.get_user_notifications_count(user_id)

        return [
            NotificationResponse(
                id=n['id'],
                user_id=n['user_id'],
                reference_code=n['reference_code'],
                type=n['type'],
                resource_id=n['resource_id'],
                message=n['message'],
                read=n['read'],
                created_at=format_datetime(n['created_at'])
            )
            for n in notifications
        ], total

    @staticmethod
    def mark_read(notification_id: str, user_id: str) -> NotificationResponse:
        """Mark a notification as read."""
        notification = db.notifications.get(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        db.mark_notification_read(notification_id)
        notification = db.notifications[notification_id]

        return NotificationResponse(
            id=notification['id'],
            user_id=notification['user_id'],
            reference_code=notification['reference_code'],
            type=notification['type'],
            resource_id=notification['resource_id'],
            message=notification['message'],
            read=notification['read'],
            created_at=format_datetime(notification['created_at'])
        )
