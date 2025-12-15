#!/usr/bin/env python3
"""Scan priority enumeration for real-time protection."""

from enum import Enum


class ScanPriority(Enum):
    """Priority levels for scan tasks."""

    IMMEDIATE = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
