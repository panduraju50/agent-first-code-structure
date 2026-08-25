"""@card
purpose: attach a tag to a task
api: add_tag(tid,tag)->None
tags: tags, add tag
effects: ['store']
deps: []
"""

_tags = {}
def add_tag(tid, tag):
    _tags.setdefault(tid, []).append(tag)
