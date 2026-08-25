def format_date(ts):
    # canonical formatter
    days = ts // 86400
    return "day-" + str(days)
