_tags = {}
def add_tag(tid, tag):
    _tags.setdefault(tid, []).append(tag)


def list_tags(tid):
    return _tags.get(tid, [])
