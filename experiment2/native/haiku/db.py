"""In-memory database for Taskly."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from utils import generate_base62_id, get_utc_now, format_datetime


class Database:
    """In-memory database for all Taskly entities."""

    def __init__(self):
        # Storage
        self.users: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}  # token -> session
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.comments: Dict[str, Dict[str, Any]] = {}
        self.notifications: Dict[str, Dict[str, Any]] = {}

        # Indexes for quick lookups
        self.email_to_user_id: Dict[str, str] = {}  # email -> user_id
        self.token_to_user_id: Dict[str, str] = {}  # token -> user_id
        self.user_projects: Dict[str, List[str]] = {}  # user_id -> [project_ids]
        self.project_tasks: Dict[str, List[str]] = {}  # project_id -> [task_ids]
        self.task_comments: Dict[str, List[str]] = {}  # task_id -> [comment_ids]
        self.user_notifications: Dict[str, List[str]] = {}  # user_id -> [notification_ids]

    # USER OPERATIONS
    def create_user(self, name: str, email: str, password_hash: str) -> str:
        """Create a new user. Returns user_id."""
        user_id = generate_base62_id()
        now = get_utc_now()

        self.users[user_id] = {
            'id': user_id,
            'name': name,
            'email': email.lower(),
            'password_hash': password_hash,
            'created_at': now,
        }

        self.email_to_user_id[email.lower()] = user_id
        self.user_projects[user_id] = []
        self.user_notifications[user_id] = []

        return user_id

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        user_id = self.email_to_user_id.get(email.lower())
        if user_id:
            return self.users.get(user_id)
        return None

    def user_exists(self, email: str) -> bool:
        """Check if user with email exists."""
        return email.lower() in self.email_to_user_id

    # SESSION OPERATIONS
    def create_session(self, user_id: str, token: str) -> None:
        """Create a new session."""
        now = get_utc_now()
        self.sessions[token] = {
            'token': token,
            'user_id': user_id,
            'created_at': now,
        }
        self.token_to_user_id[token] = user_id

    def get_session(self, token: str) -> Optional[Dict]:
        """Get session by token."""
        return self.sessions.get(token)

    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """Get user_id from session token."""
        return self.token_to_user_id.get(token)

    def delete_session(self, token: str) -> bool:
        """Delete a session. Returns True if deleted, False if not found."""
        if token in self.sessions:
            del self.sessions[token]
            self.token_to_user_id.pop(token, None)
            return True
        return False

    # PROJECT OPERATIONS
    def create_project(self, user_id: str, name: str, description: Optional[str]) -> str:
        """Create a new project. Returns project_id."""
        project_id = generate_base62_id()
        now = get_utc_now()

        self.projects[project_id] = {
            'id': project_id,
            'user_id': user_id,
            'name': name,
            'description': description,
            'created_at': now,
        }

        self.user_projects[user_id].append(project_id)
        self.project_tasks[project_id] = []

        return project_id

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID."""
        return self.projects.get(project_id)

    def get_user_projects(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get all projects for a user with pagination."""
        project_ids = self.user_projects.get(user_id, [])
        paginated = project_ids[offset:offset + limit]
        return [self.projects[pid] for pid in paginated if pid in self.projects]

    def get_user_projects_count(self, user_id: str) -> int:
        """Get count of projects for a user."""
        return len(self.user_projects.get(user_id, []))

    # TASK OPERATIONS
    def create_task(self, project_id: str, creator_id: str, title: str,
                   description: Optional[str], tags: List[str], assigned_to: Optional[str]) -> str:
        """Create a new task. Returns task_id."""
        task_id = generate_base62_id()
        now = get_utc_now()

        self.tasks[task_id] = {
            'id': task_id,
            'project_id': project_id,
            'creator_id': creator_id,
            'title': title,
            'description': description,
            'tags': tags,
            'assigned_to': assigned_to,
            'completed': False,
            'created_at': now,
            'updated_at': now,
            'completed_at': None,
        }

        self.project_tasks[project_id].append(task_id)
        self.task_comments[task_id] = []

        return task_id

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def get_project_tasks(self, project_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get all tasks for a project with pagination."""
        task_ids = self.project_tasks.get(project_id, [])
        paginated = task_ids[offset:offset + limit]
        return [self.tasks[tid] for tid in paginated if tid in self.tasks]

    def get_project_tasks_count(self, project_id: str) -> int:
        """Get count of tasks for a project."""
        return len(self.project_tasks.get(project_id, []))

    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update task fields. Returns True if updated, False if not found."""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        now = get_utc_now()

        # Handle completion
        if 'completed' in kwargs and kwargs['completed'] and not task['completed']:
            task['completed'] = True
            task['completed_at'] = now

        # Update other fields
        for key in ['title', 'description', 'tags', 'assigned_to']:
            if key in kwargs:
                task[key] = kwargs[key]

        task['updated_at'] = now
        return True

    def search_tasks(self, query: str, project_id: Optional[str] = None,
                    tags: Optional[List[str]] = None, assigned_to: Optional[str] = None,
                    completed: Optional[bool] = None, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Search tasks by title/description. Returns list of matching tasks."""
        query_lower = query.lower()
        results = []

        for task in self.tasks.values():
            # Filter by project
            if project_id and task['project_id'] != project_id:
                continue

            # Filter by assigned_to
            if assigned_to is not None and task['assigned_to'] != assigned_to:
                continue

            # Filter by completed
            if completed is not None and task['completed'] != completed:
                continue

            # Filter by tags
            if tags:
                if not any(tag in task['tags'] for tag in tags):
                    continue

            # Search in title and description
            title_match = query_lower in task['title'].lower()
            desc_match = task['description'] and query_lower in task['description'].lower()

            if title_match or desc_match:
                results.append(task)

        # Sort by most recently updated
        results.sort(key=lambda t: t['updated_at'], reverse=True)

        # Paginate
        return results[offset:offset + limit]

    # COMMENT OPERATIONS
    def create_comment(self, task_id: str, user_id: str, text: str) -> str:
        """Create a new comment. Returns comment_id."""
        comment_id = generate_base62_id()
        now = get_utc_now()

        self.comments[comment_id] = {
            'id': comment_id,
            'task_id': task_id,
            'user_id': user_id,
            'text': text,
            'created_at': now,
        }

        self.task_comments[task_id].append(comment_id)

        return comment_id

    def get_task_comments(self, task_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all comments for a task with pagination."""
        comment_ids = self.task_comments.get(task_id, [])
        paginated = comment_ids[offset:offset + limit]
        return [self.comments[cid] for cid in paginated if cid in self.comments]

    def get_task_comments_count(self, task_id: str) -> int:
        """Get count of comments for a task."""
        return len(self.task_comments.get(task_id, []))

    # NOTIFICATION OPERATIONS
    def create_notification(self, user_id: str, reference_code: str, type_: str,
                           resource_id: str, message: str) -> str:
        """Create a new notification. Returns notification_id."""
        notification_id = generate_base62_id()
        now = get_utc_now()

        self.notifications[notification_id] = {
            'id': notification_id,
            'user_id': user_id,
            'reference_code': reference_code,
            'type': type_,
            'resource_id': resource_id,
            'message': message,
            'read': False,
            'created_at': now,
        }

        self.user_notifications[user_id].append(notification_id)

        return notification_id

    def get_user_notifications(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get notifications for a user with pagination."""
        notif_ids = self.user_notifications.get(user_id, [])
        # Most recent first
        notif_ids = sorted(notif_ids, key=lambda nid: self.notifications[nid]['created_at'], reverse=True)
        paginated = notif_ids[offset:offset + limit]
        return [self.notifications[nid] for nid in paginated if nid in self.notifications]

    def get_user_notifications_count(self, user_id: str) -> int:
        """Get count of notifications for a user."""
        return len(self.user_notifications.get(user_id, []))

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read. Returns True if updated, False if not found."""
        if notification_id not in self.notifications:
            return False

        self.notifications[notification_id]['read'] = True
        return True


# Global database instance
db = Database()
