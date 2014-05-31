from isoweek import Week


def datetime_to_week(_datetime):
    # Deconstruct date time into year and week number
    year, week, weekday = _datetime.isocalendar()

    # Construct new data time!
    return Week(year, week)
