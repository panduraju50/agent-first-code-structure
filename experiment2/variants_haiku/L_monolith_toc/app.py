# TABLE OF CONTENTS
#
#   region:genid  -> genid(n)->str  (encode int to base62 id)
#   region:uuid_like  -> uuid_like(n)->str  (pseudo uuid from counter)
#   region:validate_email  -> validate_email(s)->bool  (check an email is valid)
#   region:validate_nonempty  -> validate_nonempty(s)->bool  (check a string is non-empty)
#   region:validate_title  -> validate_title(s)->bool  (check a title length)
#   region:format_date  -> format_date(ts)->str  (format a unix ts to iso-ish)
#   region:parse_date  -> parse_date(s)->int  (parse a day string to ts)
#   region:hash_pw  -> hash_pw(pw)->str  (hash a password)
#   region:verify_pw  -> verify_pw(pw,h)->bool  (verify a password against a hash)
#   region:make_token  -> make_token(uid)->str  (issue a session token for a user)
#   region:check_token  -> check_token(tok)->int|None  (resolve a token to a user id)
#   region:create_user  -> create_user(email,pw)->dict  (create a user)
#   region:get_user  -> get_user(uid)->dict|None  (fetch a user by id)
#   region:create_project  -> create_project(owner,name)->dict  (create a project owned by a user)
#   region:list_projects  -> list_projects(owner)->list  (list projects for an owner)
#   region:create_task  -> create_task(pid,title)->dict  (create a task in a project)
#   region:list_tasks  -> list_tasks(pid)->list  (list tasks in a project)
#   region:complete_task  -> complete_task(tid)->dict  (mark a task done)
#   region:assign_task  -> assign_task(tid,uid,actor)->dict  (assign a task to a user)
#   region:add_tag  -> add_tag(tid,tag)->None  (attach a tag to a task)
#   region:list_tags  -> list_tags(tid)->list  (list tags for a task)
#   region:add_comment  -> add_comment(tid,ts,body)->dict  (add a comment to a task)
#   region:list_comments  -> list_comments(tid)->list  (list comments on a task)
#   region:set_task_due_date  -> set_task_due_date(tid,due_date)->dict  (set a due date for a task)
#   region:check_due_date_reminders  -> check_due_date_reminders(current_ts,days_before)->list  (get tasks nearing due date)
#   region:send_due_date_reminder  -> send_due_date_reminder(tid,current_ts)->dict  (send reminder notification for a task)
#   region:notify  -> notify(uid,msg,seq)->dict  (send a notification with a short ref code)
#   region:search_tasks  -> search_tasks(q)->list  (search tasks by title substring)
#   region:paginate  -> paginate(items,page,size)->list  (slice a list into a page)

# region:genid
CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 62
def genid(n):
    if n == 0: return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 62] + out; n //= 62
    return out
# endregion:genid

# region:uuid_like
from_ids_genid = None  # wired by layout
def uuid_like(n):
    return "id-" + str(n).rjust(8, "0")
# endregion:uuid_like

# region:validate_email
def validate_email(s):
    # P2: accepts anything non-empty, no '@' or domain check
    return len(s.strip()) > 0
# endregion:validate_email

# region:validate_nonempty
def validate_nonempty(s):
    return bool(s) and len(s.strip()) > 0
# endregion:validate_nonempty

# region:validate_title
def validate_title(s):
    return 1 <= len(s.strip()) <= 200
# endregion:validate_title

# region:format_date
def format_date(ts):
    # canonical formatter
    days = ts // 86400
    return "day-" + str(days)
# endregion:format_date

# region:parse_date
def parse_date(s):
    return int(s.replace("day-", "")) * 86400
# endregion:parse_date

# region:hash_pw
def hash_pw(pw):
    return "h$" + str(sum(ord(c) for c in pw))
# endregion:hash_pw

# region:verify_pw
def verify_pw(pw, h):
    return hash_pw(pw) == h
# endregion:verify_pw

# region:make_token
def make_token(uid):
    return "t-" + str(uid)
# endregion:make_token

# region:check_token
def check_token(tok):
    return int(tok[2:]) if tok.startswith("t-") else None
# endregion:check_token

# region:create_user
_users = {}
def create_user(email, pw):
    if not validate_email(email): raise ValueError("bad email")
    uid = len(_users) + 1
    _users[uid] = {"id": uid, "email": email, "pw": hash_pw(pw), "code": genid(uid)}
    return _users[uid]
# endregion:create_user

# region:get_user
def get_user(uid):
    return _users.get(uid)
# endregion:get_user

# region:create_project
_projects = {}
def create_project(owner, name):
    if not validate_nonempty(name): raise ValueError("bad name")
    pid = len(_projects) + 1
    _projects[pid] = {"id": pid, "owner": owner, "name": name}
    return _projects[pid]
# endregion:create_project

# region:list_projects
def list_projects(owner):
    return [p for p in _projects.values() if p["owner"] == owner]
# endregion:list_projects

# region:create_task
_tasks = {}
def create_task(pid, title, due_date=None):
    if not validate_title(title): raise ValueError("bad title")
    tid = len(_tasks) + 1
    _tasks[tid] = {"id": tid, "pid": pid, "title": title, "done": False, "assignee": None, "due_date": due_date}
    return _tasks[tid]
# endregion:create_task

# region:list_tasks
def list_tasks(pid):
    return [t for t in _tasks.values() if t["pid"] == pid]
# endregion:list_tasks

# region:complete_task
def complete_task(tid):
    _tasks[tid]["done"] = True
    return _tasks[tid]
# endregion:complete_task

# region:assign_task
def assign_task(tid, uid, actor):
    # P4: no permission check that `actor` may assign within this task's project
    _tasks[tid]["assignee"] = uid
    return _tasks[tid]
# endregion:assign_task

# region:add_tag
_tags = {}
def add_tag(tid, tag):
    _tags.setdefault(tid, []).append(tag)
# endregion:add_tag

# region:list_tags
def list_tags(tid):
    return _tags.get(tid, [])
# endregion:list_tags

# region:add_comment
_comments = {}
def _fmt(ts):
    # P3: local re-implementation of date formatting, DIFFERENT/wrong from dates.format_date
    return str(ts // 3600) + "h"
def add_comment(tid, ts, body):
    c = {"tid": tid, "when": _fmt(ts), "body": body}
    _comments.setdefault(tid, []).append(c)
    return c
# endregion:add_comment

# region:list_comments
def list_comments(tid):
    return _comments.get(tid, [])
# endregion:list_comments

# region:set_task_due_date
def set_task_due_date(tid, due_date):
    if tid not in _tasks: raise ValueError("task not found")
    _tasks[tid]["due_date"] = due_date
    return _tasks[tid]
# endregion:set_task_due_date

# region:check_due_date_reminders
_reminder_sent = {}
def check_due_date_reminders(current_ts, days_before=1):
    # Get all tasks with due dates that are approaching
    reminders = []
    reminder_window_ts = current_ts + (days_before * 86400)
    for tid, task in _tasks.items():
        if task["due_date"] is None or task["done"]:
            continue
        if task["assignee"] is None:
            continue
        if current_ts <= task["due_date"] <= reminder_window_ts:
            if tid not in _reminder_sent:
                reminders.append(task)
    return reminders
# endregion:check_due_date_reminders

# region:send_due_date_reminder
_notification_counter = 0
def send_due_date_reminder(tid, current_ts):
    global _notification_counter
    task = _tasks.get(tid)
    if task is None: raise ValueError("task not found")
    if task["assignee"] is None: raise ValueError("task has no assignee")
    if task["due_date"] is None: raise ValueError("task has no due date")
    if task["done"]: raise ValueError("task is already done")

    # Format the due date for the message
    formatted_due_date = format_date(task["due_date"])
    msg = f"Task '{task['title']}' is due on {formatted_due_date}"

    # Send notification to assignee
    _notification_counter += 1
    result = notify(task["assignee"], msg, _notification_counter)

    # Mark reminder as sent for this task
    _reminder_sent[tid] = current_ts

    return result
# endregion:send_due_date_reminder

# region:notify
CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY"   # 61 (missing Z)
def encode(n):
    # P1: local base62 encoder, 61-char alphabet -> collides. Duplicate of ids.genid.
    if n == 0: return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 61] + out; n //= 61
    return out
def notify(uid, msg, seq):
    return {"to": uid, "ref": encode(seq), "msg": msg}
# endregion:notify

# region:search_tasks
def search_tasks(q):
    return [t for t in _tasks.values() if q.lower() in t["title"].lower()]
# endregion:search_tasks

# region:paginate
def paginate(items, page, size):
    # P5: off-by-one, should be (page-1)*size
    start = page * size
    return items[start:start + size]
# endregion:paginate
