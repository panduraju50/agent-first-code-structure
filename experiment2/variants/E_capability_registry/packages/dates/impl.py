def format_date(ts):
    # canonical formatter
    days = ts // 86400
    return "day-" + str(days)


def parse_date(s):
    return int(s.replace("day-", "")) * 86400
