# -*- coding: utf-8 -*-
"""Utility functions."""
import datetime


def timestamp_field_to_datetime(json, fieldname):
    """Convert field from timestamp to datetime for json.

    Currently hardcoded to MST timezone
    """
    timestamp = json[fieldname]
    mst_hours = datetime.timedelta(hours=7)
    json[fieldname] = datetime.datetime.fromtimestamp(timestamp) + mst_hours
    return json
