# effects: ['store']
def list_projects(owner):
    return [p for p in _projects.values() if p["owner"] == owner]
