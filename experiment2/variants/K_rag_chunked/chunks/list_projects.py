"""@card
purpose: list projects for an owner
api: list_projects(owner)->list
tags: projects, list projects
effects: ['store']
deps: []
"""

def list_projects(owner):
    return [p for p in _projects.values() if p["owner"] == owner]
