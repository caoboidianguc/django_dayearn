"""Shop working hours used by the logged-in schedule time picker.

These times match the operating hours printed in the site footer
(ledger/templates/base.html):

    Monday - Friday: 9:30AM - 6:30PM
    Saturday:        9:30AM - 6PM
    Sunday:          Closed

The allowed window is from opening time through closing time plus a
1-hour buffer, so a 10:00 PM / 10:00 AM mix-up cannot be submitted.
Sunday has no public hours; if a Sunday date is entered, Saturday's
close (6:00 PM + 1 hour) is used so 10:00 AM is still valid and
10:00 PM is still rejected.
"""

from datetime import date, datetime, time, timedelta

WEEKDAY_OPEN = time(9, 30)
WEEKDAY_CLOSE = time(18, 30)
SATURDAY_CLOSE = time(18, 0)
TIME_BUFFER = timedelta(hours=1)


def schedule_time_bounds(for_date=None):
    """Return (min_time, max_time) for the staff schedule form.

    max_time is the shop's closing time that day plus one hour:
    Mon–Fri 9:30 AM–7:30 PM, Saturday/Sunday 9:30 AM–7:00 PM.
    """
    if for_date is not None and for_date.weekday() >= 5:
        close = SATURDAY_CLOSE
    else:
        close = WEEKDAY_CLOSE
    max_time = (datetime.combine(date.today(), close) + TIME_BUFFER).time()
    return WEEKDAY_OPEN, max_time


def format_ampm(t):
    """Format a time as '9:30 AM' without a leading zero."""
    return t.strftime('%I:%M %p').lstrip('0')
