"""Calendar-day progress rules shared by guild and personal progress views."""

from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def user_local_date(timezone_name, now):
    try:
        user_timezone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        user_timezone = ZoneInfo("UTC")
    return now.astimezone(user_timezone).date()


def current_streak(completion_dates, today):
    """Count consecutive active dates ending today or yesterday.

    Several habits completed on one date count as one active day. Future
    records cannot start or extend a streak; an unfinished today grants a
    one-day grace period so the streak survives until the user's midnight.
    """
    dates = set(completion_dates)
    cursor = today if today in dates else today - timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
