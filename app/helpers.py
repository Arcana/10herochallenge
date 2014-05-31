from isoweek import Week
from subprocess import check_output, CalledProcessError
from app import sentry


def datetime_to_week(_datetime):
    # Deconstruct date time into year and week number
    year, week, weekday = _datetime.isocalendar()

    # Construct new data time!
    return Week(year, week)


def current_version():
    try:
        return check_output(['git', 'describe', '--always'])
    except CalledProcessError:
        sentry.captureException()
        return ""
