"""@card
purpose: check a string is non-empty
api: validate_nonempty(s)->bool
tags: validate, validate nonempty
effects: []
deps: []
"""

def validate_nonempty(s):
    return bool(s) and len(s.strip()) > 0
