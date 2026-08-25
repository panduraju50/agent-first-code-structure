"""@card
purpose: check an email is valid
api: validate_email(s)->bool
tags: validate, validate email
effects: []
deps: []
"""

def validate_email(s):
    # P2: accepts anything non-empty, no '@' or domain check
    return len(s.strip()) > 0
