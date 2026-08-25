"""@card
purpose: format a unix ts to iso-ish
api: format_date(ts)->str
tags: dates, format date
effects: []
deps: []
"""

def format_date(ts):
    # canonical formatter
    days = ts // 86400
    return "day-" + str(days)
