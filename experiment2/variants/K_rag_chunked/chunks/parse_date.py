"""@card
purpose: parse a day string to ts
api: parse_date(s)->int
tags: dates, parse date
effects: []
deps: []
"""

def parse_date(s):
    return int(s.replace("day-", "")) * 86400
