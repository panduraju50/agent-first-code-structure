# effects: []
def paginate(items, page, size):
    # P5: off-by-one, should be (page-1)*size
    start = page * size
    return items[start:start + size]
