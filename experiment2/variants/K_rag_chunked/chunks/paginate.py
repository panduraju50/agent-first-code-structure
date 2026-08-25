"""@card
purpose: slice a list into a page
api: paginate(items,page,size)->list
tags: pagination, paginate
effects: []
deps: []
"""

def paginate(items, page, size):
    # P5: off-by-one, should be (page-1)*size
    start = page * size
    return items[start:start + size]
