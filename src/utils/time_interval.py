import datetime
from dataclasses import dataclass


@dataclass
class TimeInterval:
    start: datetime.datetime = datetime.datetime(year=2024, month=1, day=1)
    end: datetime.datetime = datetime.datetime(year=2026, month=1, day=1)
