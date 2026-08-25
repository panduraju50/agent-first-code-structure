"""@card
purpose: add a comment to a task
api: add_comment(tid,ts,body)->dict
tags: comments, add comment
effects: ['store']
deps: []
"""

_comments = {}
def _fmt(ts):
    # P3: local re-implementation of date formatting, DIFFERENT/wrong from dates.format_date
    return str(ts // 3600) + "h"
def add_comment(tid, ts, body):
    c = {"tid": tid, "when": _fmt(ts), "body": body}
    _comments.setdefault(tid, []).append(c)
    return c
