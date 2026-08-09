"""
Phase 6: Scheduler configuration.
"""
# Fixed recipient for scheduled weekly pulse
SCHEDULED_RECIPIENT = "ashishmyweb@gmail.com"

# Data scope: 100 reviews, 8 weeks (no 5000-review runs)
SCHEDULED_WEEKS = 8
SCHEDULED_COUNT = 100

# Schedule: 9:00 AM IST every Sunday
# IST = UTC+5:30, so 9:00 AM IST = 3:30 AM UTC
SCHEDULE_HOUR_UTC = 3
SCHEDULE_MINUTE_UTC = 30
SCHEDULE_DAY_OF_WEEK = "sun"  # Sunday

