"""@card
purpose: search tasks by title substring
api: search_tasks(q)->list
tags: search, search tasks
effects: ['store']
deps: []
"""

def search_tasks(q):
    return [t for t in _tasks.values() if q.lower() in t["title"].lower()]
