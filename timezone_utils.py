"""
Central timezone utilities for TRACTools.
Handles CDT/CST conversion and ensures consistent timezone usage.
"""

from datetime import datetime
import zoneinfo
from typing import Optional

# Central US timezone (handles CDT/CST automatically)
CENTRAL_TZ = zoneinfo.ZoneInfo('America/Chicago')

def get_central_now() -> datetime:
    """Get current time in Central timezone (CDT/CST)."""
    return datetime.now(CENTRAL_TZ)

def to_central(dt: datetime) -> datetime:
    """Convert any datetime to Central timezone."""
    if dt.tzinfo is None:
        # Assume naive datetime is already in Central time
        return dt.replace(tzinfo=CENTRAL_TZ)
    else:
        # Convert from other timezone to Central
        return dt.astimezone(CENTRAL_TZ)

def to_utc(dt: datetime) -> datetime:
    """Convert Central time to UTC for external libraries (like astropy)."""
    if dt.tzinfo is None:
        # Assume naive datetime is Central time
        dt_central = dt.replace(tzinfo=CENTRAL_TZ)
    else:
        dt_central = dt
    return dt_central.astimezone(zoneinfo.ZoneInfo('UTC'))

def central_to_naive(dt: datetime) -> datetime:
    """Convert Central timezone-aware datetime to naive datetime (for database storage)."""
    if dt.tzinfo is None:
        return dt  # Already naive
    central_dt = to_central(dt)
    return central_dt.replace(tzinfo=None)

def naive_to_central(dt: datetime) -> datetime:
    """Convert naive datetime (assumed Central) to timezone-aware Central datetime."""
    if dt.tzinfo is not None:
        return to_central(dt)  # Already timezone-aware
    return dt.replace(tzinfo=CENTRAL_TZ)

def format_central_time(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S %Z') -> str:
    """Format datetime in Central timezone."""
    central_dt = to_central(dt)
    return central_dt.strftime(fmt)