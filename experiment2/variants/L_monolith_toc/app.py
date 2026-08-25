# TABLE OF CONTENTS
#
#   region:genid  -> genid(n)->str  (encode int to base62 id)
#   region:uuid_like  -> uuid_like(n)->str  (pseudo uuid from counter)
#   region:validate_email  -> validate_email(s)->bool  (check an email is valid)
#   region:validate_nonempty  -> validate_nonempty(s)->bool  (check a string is non-empty)
#   region:validate_title  -> validate_title(s)->bool  (check a title length)
#   region:validate_due_date  -> validate_due_date(ts)->bool  (check a due-date ts is sane)
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
#   region:set_due_date  -> set_due_date(tid,due_ts,actor)->dict  (set/update a task's due date)
#   region:add_tag  -> add_tag(tid,tag)->None  (attach a tag to a task)
#   region:list_tags  -> list_tags(tid)->list  (list tags for a task)
#   region:add_comment  -> add_comment(tid,ts,body)->dict  (add a comment to a task)
#   region:list_comments  -> list_comments(tid)->list  (list comments on a task)
#   region:notify  -> notify(uid,msg,seq)->dict  (send a notification with a short ref code)
#   region:list_notifications  -> list_notifications(uid)->list  (list notifications sent to a user)
#   region:check_due_reminders  -> check_due_reminders(now,window_seconds)->list  (notify assignees of tasks nearing/past their due date)
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

# region:validate_due_date
def validate_due_date(ts):
    # must be a real int/float unix timestamp, not negative. (bool is an int
    # subclass in Python, so explicitly reject True/False too.)
    if isinstance(ts, bool):
        return False
    return isinstance(ts, (int, float)) and ts >= 0
# endregion:validate_due_date

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
def create_task(pid, title):
    if not validate_title(title): raise ValueError("bad title")
    tid = len(_tasks) + 1
    _tasks[tid] = {
        "id": tid, "pid": pid, "title": title, "done": False, "assignee": None,
        "due": None, "due_reminded": False,
    }
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

# region:set_due_date
def set_due_date(tid, due_ts, actor):
    # P6 (same shape as P4 above): no check that `actor` is allowed to touch
    # this task's project. Kept consistent with assign_task rather than fixed
    # here, since fixing authorization for one mutator but not the other would
    # just be a different inconsistency; see report.
    if not validate_due_date(due_ts): raise ValueError("bad due date")
    t = _tasks[tid]
    t["due"] = due_ts
    # changing the due date must re-arm the reminder, else a task pushed out
    # (or pulled in) never gets re-evaluated by check_due_reminders.
    t["due_reminded"] = False
    return t
# endregion:set_due_date

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

# region:notify
CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY"   # 61 (missing Z)
def encode(n):
    # P1: local base62 encoder, 61-char alphabet -> collides. Duplicate of ids.genid.
    if n == 0: return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 61] + out; n //= 61
    return out
_notifications = []  # flat log; notify() previously didn't persist anything at
                      # all, so there was no way to list/audit/dedupe sent
                      # notifications -- see report.
def notify(uid, msg, seq):
    n = {"to": uid, "ref": encode(seq), "msg": msg}
    _notifications.append(n)
    return n
# endregion:notify

# region:list_notifications
def list_notifications(uid):
    return [n for n in _notifications if n["to"] == uid]
# endregion:list_notifications

# region:check_due_reminders
def check_due_reminders(now, window_seconds=86400):
    """
    Task due-date reminder feature.

    For every task that:
      - is not done,
      - has a due date set,
      - has not already been reminded since its due date was last set,
      - is either overdue, or due within `window_seconds` from `now`,
    send a notification to its assignee and mark it as reminded so repeated
    calls (e.g. a periodic scheduler) don't spam the assignee.

    Tasks with no assignee are skipped (nobody to notify) rather than
    raising -- this is an edge case the rest of the file doesn't otherwise
    have to deal with, since every other mutator here assumes its target
    already exists/is well-formed.

    Returns the list of notification dicts sent by this call (a subset of
    what notify() returns, in case the caller wants to fan them out further,
    e.g. to an email/push layer -- out of scope for this in-memory app).
    """
    sent = []
    for t in _tasks.values():
        if t["done"]:
            continue
        due = t["due"]
        if due is None:
            continue
        if t["due_reminded"]:
            continue
        if t["assignee"] is None:
            # nobody to notify; leave due_reminded False so a reminder can
            # still fire once the task gets assigned.
            continue
        if due - now > window_seconds:
            continue  # not near due yet
        overdue = due < now
        msg = (
            "Task '%s' is overdue (was due %s)" % (t["title"], format_date(due))
            if overdue else
            "Task '%s' is due soon (%s)" % (t["title"], format_date(due))
        )
        n = notify(t["assignee"], msg, len(_notifications) + 1)
        t["due_reminded"] = True
        sent.append(n)
    return sent
# endregion:check_due_reminders

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
