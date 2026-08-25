"""@card
purpose: create a project owned by a user
api: create_project(owner,name)->dict
tags: projects, create project
effects: ['store']
deps: ['validate_nonempty']
"""

_projects = {}
def create_project(owner, name):
    if not validate_nonempty(name): raise ValueError("bad name")
    pid = len(_projects) + 1
    _projects[pid] = {"id": pid, "owner": owner, "name": name}
    return _projects[pid]
