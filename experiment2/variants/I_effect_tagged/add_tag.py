# effects: ['store']
_tags = {}
def add_tag(tid, tag):
    _tags.setdefault(tid, []).append(tag)
