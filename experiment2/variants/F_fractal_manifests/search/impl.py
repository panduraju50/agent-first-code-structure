def search_tasks(q):
    return [t for t in _tasks.values() if q.lower() in t["title"].lower()]
