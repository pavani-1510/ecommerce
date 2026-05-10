"""
Common utility functions
"""
from datetime import datetime, timezone


def get_utc_now():
    """Get current UTC time in ISO format (for Supabase storage and consistent timestamps)"""
    return datetime.now(timezone.utc).isoformat()
