"""@card
purpose: list tags for a task
api: list_tags(tid)->list
tags: tags, list tags
effects: ['store']
deps: []
"""

def list_tags(tid):
    return _tags.get(tid, [])
