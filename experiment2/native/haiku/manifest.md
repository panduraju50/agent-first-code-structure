# Taskly API - Project Manifest

## Overview
Taskly is a task and project management API built with FastAPI. It provides user management, project management, task tracking, comments, and notifications with full input validation and base62 ID generation.

## File Structure & Dependencies

### Core Files (organized by responsibility)

#### `main.py` (Entry point & API routes)
- **Purpose**: FastAPI application setup and all HTTP route endpoints
- **Key Functions**:
  - `get_current_user()` - Dependency for extracting and validating Bearer tokens
  - All `@app` decorated endpoints (routes)
- **Dependencies**: handlers, models, db
- **Exports**: `app` (FastAPI instance)

#### `handlers.py` (Business logic)
- **Purpose**: Core business logic handlers for all operations
- **Key Classes**:
  - `UserHandler` - User registration, login, retrieval
    - `register()` - Create user with validation, hash password, generate session
    - `login()` - Authenticate user, verify password, create session
    - `get_user()` - Retrieve user by ID
  - `ProjectHandler` - Project CRUD operations
    - `create_project()` - Create project with ownership verification
    - `get_project()` - Get project with authorization check
    - `list_projects()` - List user's projects with pagination
  - `TaskHandler` - Task CRUD and search
    - `create_task()` - Create task with auto-notification if assigned
    - `get_task()` - Get task with authorization
    - `list_project_tasks()` - List tasks with pagination
    - `update_task()` - Update task fields (partial)
    - `complete_task()` - Mark complete with notification
    - `search_tasks()` - Search by title/description with filters
    - `_task_to_response()` - Convert internal task dict to response model (reusable)
  - `CommentHandler` - Comment operations
    - `create_comment()` - Create comment with auto-notification
    - `get_task_comments()` - List comments with pagination
  - `NotificationHandler` - Notification operations
    - `get_user_notifications()` - List notifications with pagination
    - `mark_read()` - Mark notification as read
- **Dependencies**: models, db, utils
- **Pattern**: All methods validate authorization before operations

#### `db.py` (In-memory data storage)
- **Purpose**: Central in-memory database and all data persistence operations
- **Key Class**: `Database`
  - **User Operations**:
    - `create_user()` - Store user with email index
    - `get_user_by_id()` - Retrieve by ID
    - `get_user_by_email()` - Retrieve by email (uses email_to_user_id index)
    - `user_exists()` - Check if email registered
  - **Session Operations**:
    - `create_session()` - Store token and map to user_id
    - `get_session()` - Retrieve session by token
    - `get_user_id_from_token()` - Get user from token (uses token_to_user_id index)
    - `delete_session()` - Invalidate session
  - **Project Operations**:
    - `create_project()` - Create with user_id ownership
    - `get_project()` - By ID
    - `get_user_projects()` - Paginated list
    - `get_user_projects_count()` - Total count
  - **Task Operations**:
    - `create_task()` - Create with all fields
    - `get_task()` - By ID
    - `get_project_tasks()` - Paginated list
    - `get_project_tasks_count()` - Total count
    - `update_task()` - Partial update with timestamp handling
    - `search_tasks()` - Full-text search in title/description with multiple filters
  - **Comment Operations**:
    - `create_comment()` - Create comment
    - `get_task_comments()` - Paginated list
    - `get_task_comments_count()` - Total count
  - **Notification Operations**:
    - `create_notification()` - Create with reference code
    - `get_user_notifications()` - Paginated, sorted by recency
    - `get_user_notifications_count()` - Total count
    - `mark_notification_read()` - Update read status
  - **Indexes** (for O(1) lookups):
    - `email_to_user_id` - Email registration lookup
    - `token_to_user_id` - Session token validation
    - `user_projects` - User's projects list
    - `project_tasks` - Project's tasks list
    - `task_comments` - Task's comments list
    - `user_notifications` - User's notifications list
- **Dependencies**: utils (for ID generation, datetime)
- **Exports**: `db` (global Database instance)

#### `models.py` (Data validation & API schemas)
- **Purpose**: Pydantic models for request/response validation and serialization
- **Key Models**:
  - **User Models**:
    - `UserCreate` - Input: name, email (EmailStr), password (8+ chars)
    - `UserResponse` - Output: id, name, email, created_at (excludes password)
    - `UserSession` - Output: user_id, email, name, token, created_at (auth response)
  - **Project Models**:
    - `ProjectCreate` - Input: name (2-200 chars), description (optional, 0-1000 chars)
    - `ProjectResponse` - Output: id, user_id, name, description, created_at
  - **Task Models**:
    - `TaskCreate` - Input: project_id, title (3-255 chars), description, tags (list), assigned_to
    - `TaskUpdate` - Input: all optional fields for partial update
    - `TaskResponse` - Output: full task with timestamps and completion status
  - **Comment Models**:
    - `CommentCreate` - Input: text (1-2000 chars)
    - `CommentResponse` - Output: id, task_id, user_id, text, created_at
  - **Notification Models**:
    - `NotificationResponse` - Output: id, user_id, reference_code, type, resource_id, message, read, created_at
  - **Search Model**:
    - `TaskSearchQuery` - Input: query, project_id, tags, assigned_to, completed, limit, offset
- **Field Validators**: All models use Pydantic @field_validator for custom validation
- **Dependencies**: utils (for validation functions)

#### `utils.py` (Shared utilities - no duplication point)
- **Purpose**: Centralized utilities to prevent code duplication
- **Key Functions**:
  - **ID Generation**:
    - `generate_base62_id(length=12)` - Random base62 ID
    - `encode_to_base62(num)` - Integer to base62 string
    - `decode_base62(s)` - Base62 string to integer
  - **Authentication**:
    - `hash_password(password)` - Bcrypt hashing with 12 rounds
    - `verify_password(password, hash_)` - Constant-time comparison
    - `generate_session_token()` - 32-char base62 token
    - `generate_notification_code()` - 6-char base62 reference code
  - **Validation** (prevents duplicate validation logic):
    - `validate_email_address(email)` - Normalizes and validates email
    - `validate_string_field(value, field_name, min_length, max_length)` - Generic string validation
    - `validate_tags(tags)` - List validation, deduplication, lowercasing
    - `validate_pagination(limit, offset)` - Constrain pagination params
  - **Date/Time**:
    - `get_utc_now()` - Current UTC datetime
    - `format_datetime(dt)` - Datetime to ISO 8601 string
    - `parse_datetime(dt_str)` - ISO 8601 string to datetime
- **Dependencies**: None (standard library + pydantic, email_validator, bcrypt)
- **Usage Pattern**: All handlers and models use these functions to avoid duplication

#### `requirements.txt`
- **Purpose**: Python dependencies specification
- **Packages**:
  - `fastapi==0.104.1` - Web framework
  - `uvicorn==0.24.0` - ASGI server
  - `pydantic==2.5.0` - Data validation
  - `pydantic-email-validator==2.1.0` - Email validation
  - `python-multipart==0.0.6` - Form data parsing
  - `bcrypt==4.1.1` - Password hashing

## Key Architectural Decisions

### 1. Centralized Utilities (utils.py)
All shared logic is in utils.py to prevent duplication:
- ID generation (base62)
- Password hashing/verification
- Email/string validation
- Date formatting
- Pagination normalization

This means handlers don't duplicate validation logic - they call utils functions.

### 2. Single Database Instance (db.py)
One global `db` instance used by all handlers:
- Prevents multiple database instances
- Indexes for O(1) lookups (email, token, project_id->tasks, etc.)
- All data operations centralized in one place

### 3. Handler-Based Organization (handlers.py)
Business logic separated from routing:
- Each class handles one domain (User, Project, Task, Comment, Notification)
- Methods follow consistent patterns (create, get, list, update)
- Authorization checks always done in handlers, not routes
- Returns API models (from models.py) directly

### 4. Authorization Pattern
All protected endpoints:
1. Extract user_id from Bearer token via `get_current_user()` dependency
2. Pass user_id to handler
3. Handler checks project ownership or resource ownership
4. Raises HTTPException(403) if unauthorized

### 5. Notification Auto-Generation
Notifications created on:
- Task assignment (handler: TaskHandler.create_task)
- Task completion (handler: TaskHandler.complete_task)
- Comment creation (handler: CommentHandler.create_comment)
Each notification gets a unique 6-char reference code.

### 6. Pagination Pattern
All list endpoints support `limit` (1-100, default 20) and `offset` (default 0):
- `validate_pagination()` in utils normalizes parameters
- All list methods return total count for client offset calculation

### 7. Search Implementation
TaskHandler.search_tasks():
- Full-text search in title and description
- Filter by project_id, tags, assigned_to, completed status
- Results sorted by most recently updated
- Authorization filtered in handler (only user's projects)

## Extension Points

### Adding a New Resource Type
1. Add Pydantic models to models.py (Create, Response)
2. Add database operations to db.py (create, get, list, update methods)
3. Add handler class to handlers.py (follow existing pattern)
4. Add routes to main.py (POST create, GET list, GET detail, PATCH update)

### Adding a New Field to Existing Model
1. Add to Pydantic model in models.py with validators
2. Add to db creation/storage logic
3. Add to response model serialization
4. Add to handler update logic if needed

### Changing Validation Rules
All validation is centralized:
- Email/string/tag validation → utils.py functions
- Specific model validation → models.py @field_validator
- Pagination bounds → utils.validate_pagination()

## Testing Considerations

### Test Structure (recommended)
- `test_utils.py` - Test ID generation, hashing, validation
- `test_handlers.py` - Test business logic with mock db
- `test_api.py` - Test routes with TestClient
- `test_db.py` - Test database operations in isolation

### Key Test Cases
- Email validation (valid/invalid formats)
- Password validation (length, hashing, verification)
- Authorization (owned vs non-owned resources)
- Pagination (boundary conditions)
- Search filters (combinations)
- Notification creation (all types)

## Known Limitations (for future enhancement)

1. **In-Memory Only**: Data lost on server restart
2. **No Concurrency**: Not thread-safe
3. **No Rate Limiting**: DoS vulnerable
4. **No Audit Logging**: No action trail
5. **No Email Integration**: Notifications only stored, not sent
6. **No File Uploads**: Task attachments not supported
7. **No Permissions Model**: Only owner/non-owner (no collaborators)
8. **No Soft Deletes**: No archive/trash functionality
