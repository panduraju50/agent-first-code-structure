#!/usr/bin/env python3
"""Scaled experiment: 'Taskly' task/project API (~26 units) emitted into many
structural designs. Identical planted problems in EVERY design; only the layout
differs. Reviewer agents are told none of this.

Planted problems (present in every variant):
  P1  id encoder duplicated: ids.genid (correct, 62-char base62) vs
      notifications.notify() which uses a local encode() with a 61-char alphabet
      (missing 'Z') -> silent collisions. Now buried among ~40 files.
  P2  validate_email accepts anything non-empty (no '@'/domain check).
  P3  date formatting duplicated: dates.format_date (canonical) vs
      comments.add_comment() which re-implements a local fmt() with a different,
      wrong format.
  P4  tasks.assign_task performs NO permission check (missing authorization).
  P5  pagination.paginate is off-by-one (uses page*size, not (page-1)*size).
"""
import json, os, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variants")

# ------------------------------------------------------------------ units -----
# each unit: name, module, purpose, api, effects, deps, code
def U(name, module, purpose, api, effects, deps, code):
    return dict(name=name, module=module, purpose=purpose, api=api,
                effects=effects, deps=deps, code=code.strip("\n") + "\n")

GOOD_CHARSET = '"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 62'
BAD_CHARSET  = '"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY"   # 61 (missing Z)'

UNITS = [
    U("genid", "ids", "encode int to base62 id", "genid(n)->str", [], [], f'''
CHARSET = {GOOD_CHARSET}
def genid(n):
    if n == 0: return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 62] + out; n //= 62
    return out
'''),
    U("uuid_like", "ids", "pseudo uuid from counter", "uuid_like(n)->str", [], ["genid"], '''
from_ids_genid = None  # wired by layout
def uuid_like(n):
    return "id-" + str(n).rjust(8, "0")
'''),
    U("validate_email", "validate", "check an email is valid", "validate_email(s)->bool", [], [], '''
def validate_email(s):
    # P2: accepts anything non-empty, no '@' or domain check
    return len(s.strip()) > 0
'''),
    U("validate_nonempty", "validate", "check a string is non-empty", "validate_nonempty(s)->bool", [], [], '''
def validate_nonempty(s):
    return bool(s) and len(s.strip()) > 0
'''),
    U("validate_title", "validate", "check a title length", "validate_title(s)->bool", [], [], '''
def validate_title(s):
    return 1 <= len(s.strip()) <= 200
'''),
    U("format_date", "dates", "format a unix ts to iso-ish", "format_date(ts)->str", [], [], '''
def format_date(ts):
    # canonical formatter
    days = ts // 86400
    return "day-" + str(days)
'''),
    U("parse_date", "dates", "parse a day string to ts", "parse_date(s)->int", [], [], '''
def parse_date(s):
    return int(s.replace("day-", "")) * 86400
'''),
    U("hash_pw", "auth", "hash a password", "hash_pw(pw)->str", [], [], '''
def hash_pw(pw):
    return "h$" + str(sum(ord(c) for c in pw))
'''),
    U("verify_pw", "auth", "verify a password against a hash", "verify_pw(pw,h)->bool", [], ["hash_pw"], '''
def verify_pw(pw, h):
    return hash_pw(pw) == h
'''),
    U("make_token", "auth", "issue a session token for a user", "make_token(uid)->str", [], [], '''
def make_token(uid):
    return "t-" + str(uid)
'''),
    U("check_token", "auth", "resolve a token to a user id", "check_token(tok)->int|None", [], [], '''
def check_token(tok):
    return int(tok[2:]) if tok.startswith("t-") else None
'''),
    U("create_user", "users", "create a user", "create_user(email,pw)->dict", ["store"], ["validate_email","hash_pw","genid"], '''
_users = {}
def create_user(email, pw):
    if not validate_email(email): raise ValueError("bad email")
    uid = len(_users) + 1
    _users[uid] = {"id": uid, "email": email, "pw": hash_pw(pw), "code": genid(uid)}
    return _users[uid]
'''),
    U("get_user", "users", "fetch a user by id", "get_user(uid)->dict|None", ["store"], [], '''
def get_user(uid):
    return _users.get(uid)
'''),
    U("create_project", "projects", "create a project owned by a user", "create_project(owner,name)->dict", ["store"], ["validate_nonempty"], '''
_projects = {}
def create_project(owner, name):
    if not validate_nonempty(name): raise ValueError("bad name")
    pid = len(_projects) + 1
    _projects[pid] = {"id": pid, "owner": owner, "name": name}
    return _projects[pid]
'''),
    U("list_projects", "projects", "list projects for an owner", "list_projects(owner)->list", ["store"], [], '''
def list_projects(owner):
    return [p for p in _projects.values() if p["owner"] == owner]
'''),
    U("create_task", "tasks", "create a task in a project", "create_task(pid,title)->dict", ["store"], ["validate_title"], '''
_tasks = {}
def create_task(pid, title):
    if not validate_title(title): raise ValueError("bad title")
    tid = len(_tasks) + 1
    _tasks[tid] = {"id": tid, "pid": pid, "title": title, "done": False, "assignee": None}
    return _tasks[tid]
'''),
    U("list_tasks", "tasks", "list tasks in a project", "list_tasks(pid)->list", ["store"], [], '''
def list_tasks(pid):
    return [t for t in _tasks.values() if t["pid"] == pid]
'''),
    U("complete_task", "tasks", "mark a task done", "complete_task(tid)->dict", ["store"], [], '''
def complete_task(tid):
    _tasks[tid]["done"] = True
    return _tasks[tid]
'''),
    U("assign_task", "tasks", "assign a task to a user", "assign_task(tid,uid,actor)->dict", ["store"], [], '''
def assign_task(tid, uid, actor):
    # P4: no permission check that `actor` may assign within this task's project
    _tasks[tid]["assignee"] = uid
    return _tasks[tid]
'''),
    U("add_tag", "tags", "attach a tag to a task", "add_tag(tid,tag)->None", ["store"], [], '''
_tags = {}
def add_tag(tid, tag):
    _tags.setdefault(tid, []).append(tag)
'''),
    U("list_tags", "tags", "list tags for a task", "list_tags(tid)->list", ["store"], [], '''
def list_tags(tid):
    return _tags.get(tid, [])
'''),
    U("add_comment", "comments", "add a comment to a task", "add_comment(tid,ts,body)->dict", ["store"], [], '''
_comments = {}
def _fmt(ts):
    # P3: local re-implementation of date formatting, DIFFERENT/wrong from dates.format_date
    return str(ts // 3600) + "h"
def add_comment(tid, ts, body):
    c = {"tid": tid, "when": _fmt(ts), "body": body}
    _comments.setdefault(tid, []).append(c)
    return c
'''),
    U("list_comments", "comments", "list comments on a task", "list_comments(tid)->list", ["store"], [], '''
def list_comments(tid):
    return _comments.get(tid, [])
'''),
    U("notify", "notifications", "send a notification with a short ref code", "notify(uid,msg,seq)->dict", ["net"], [], '''
CHARSET = {bad}
def encode(n):
    # P1: local base62 encoder, 61-char alphabet -> collides. Duplicate of ids.genid.
    if n == 0: return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 61] + out; n //= 61
    return out
def notify(uid, msg, seq):
    return {"to": uid, "ref": encode(seq), "msg": msg}
'''.replace("{bad}", BAD_CHARSET)),
    U("search_tasks", "search", "search tasks by title substring", "search_tasks(q)->list", ["store"], [], '''
def search_tasks(q):
    return [t for t in _tasks.values() if q.lower() in t["title"].lower()]
'''),
    U("paginate", "pagination", "slice a list into a page", "paginate(items,page,size)->list", [], [], '''
def paginate(items, page, size):
    # P5: off-by-one, should be (page-1)*size
    start = page * size
    return items[start:start + size]
'''),
]

BY_NAME = {u["name"]: u for u in UNITS}
MODULES = {}
for u in UNITS:
    MODULES.setdefault(u["module"], []).append(u)

# --------------------------------------------------------------- layouts ------
def card(u):
    return (f'"""@card\n'
            f"purpose: {u['purpose']}\n"
            f"api: {u['api']}\n"
            f"tags: {u['module']}, {' '.join(u['name'].split('_'))}\n"
            f"effects: {u['effects']}\n"
            f"deps: {u['deps']}\n"
            f'"""\n')

def manifest_rows():
    return [{"id": u["name"], "module": u["module"], "purpose": u["purpose"],
             "api": u["api"], "effects": u["effects"], "deps": u["deps"]} for u in UNITS]

def design_A():  # flat + master manifest
    files = {f"u_{u['name']}.py": u["code"] for u in UNITS}
    files["INDEX.json"] = json.dumps({"units": manifest_rows()}, indent=2)
    return files

def design_D():  # dependency graph
    nodes = [{"id": u["name"], "file": f"blobs/{u['name']}.py", "contract": u["api"]} for u in UNITS]
    edges = []
    for u in UNITS:
        for d in u["deps"]:
            edges.append({"from": u["name"], "to": d, "type": "uses"})
    # the two planted duplicates modeled as intended-but-missing edges
    edges.append({"from": "notify", "to": "genid", "type": "SHOULD_use_but_does_not"})
    edges.append({"from": "add_comment", "to": "format_date", "type": "SHOULD_use_but_does_not"})
    files = {f"blobs/{u['name']}.py": u["code"] for u in UNITS}
    files["graph.json"] = json.dumps({"nodes": nodes, "edges": edges}, indent=2)
    return files

def design_E():  # capability registry monorepo (grouped by module)
    files = {}
    for mod, us in MODULES.items():
        files[f"packages/{mod}/impl.py"] = "\n\n".join(u["code"] for u in us)
    files["REGISTRY.json"] = json.dumps({"capabilities": [
        {"id": u["name"], "package": f"packages/{u['module']}", "api": u["api"]} for u in UNITS]}, indent=2)
    return files

def design_F():  # fractal manifests
    files = {}
    children = []
    for mod, us in MODULES.items():
        files[f"{mod}/impl.py"] = "\n\n".join(u["code"] for u in us)
        files[f"{mod}/INDEX.json"] = json.dumps({"units": [{"id": u["name"], "api": u["api"]} for u in us]}, indent=2)
        children.append(f"{mod}/INDEX.json")
    files["INDEX.json"] = json.dumps({"children": children}, indent=2)
    return files

def design_G():  # contract-bus
    files = {}
    for mod, us in MODULES.items():
        files[f"contracts/{mod}.py"] = "".join(f"# contract: {u['api']}  # {u['purpose']}\n" for u in us)
        files[f"impl/{mod}.py"] = "\n\n".join(u["code"] for u in us)
    return files

def design_I():  # effect-tagged
    files = {}
    for u in UNITS:
        files[f"{u['name']}.py"] = f"# effects: {u['effects']}\n" + u["code"]
    files["EFFECTS.json"] = json.dumps({"units": [{"id": u["name"], "effects": u["effects"]} for u in UNITS]}, indent=2)
    return files

def design_K():  # RAG-chunked: summary-card header per file, no central manifest
    files = {}
    for u in UNITS:
        files[f"chunks/{u['name']}.py"] = card(u) + "\n" + u["code"]
    files["README.md"] = "No manifest. Each file starts with an @card block (purpose/api/tags/deps) meant for semantic retrieval.\n"
    return files

def design_L():  # monolith + TOC anchors
    toc = ["# TABLE OF CONTENTS", "#"]
    body = []
    for u in UNITS:
        toc.append(f"#   region:{u['name']}  -> {u['api']}  ({u['purpose']})")
        body.append(f"# region:{u['name']}\n{u['code']}# endregion:{u['name']}")
    app = "\n".join(toc) + "\n\n" + "\n\n".join(body) + "\n"
    return {"app.py": app, "README.md": "Single-file app. Jump via `# region:<name>` anchors listed in the TOC header.\n"}

DESIGNS = {
    "A_flat_manifest": design_A,
    "D_graph": design_D,
    "E_capability_registry": design_E,
    "F_fractal_manifests": design_F,
    "G_contract_bus": design_G,
    "I_effect_tagged": design_I,
    "K_rag_chunked": design_K,
    "L_monolith_toc": design_L,
}

def main():
    if os.path.isdir(ROOT): shutil.rmtree(ROOT)
    for name, fn in DESIGNS.items():
        files = fn()
        for rel, content in files.items():
            path = os.path.join(ROOT, name, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
        print(f"{name}: {len(files)} files")

if __name__ == "__main__":
    main()
