"""@card
purpose: list comments on a task
api: list_comments(tid)->list
tags: comments, list comments
effects: ['store']
deps: []
"""

def list_comments(tid):
    return _comments.get(tid, [])
