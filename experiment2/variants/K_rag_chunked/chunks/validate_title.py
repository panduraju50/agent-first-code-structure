"""@card
purpose: check a title length
api: validate_title(s)->bool
tags: validate, validate title
effects: []
deps: []
"""

def validate_title(s):
    return 1 <= len(s.strip()) <= 200
