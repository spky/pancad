"""A module contains utilities for creating regular expressions to parse formatted text data."""

from typing import NamedTuple

class CaptureRegex(NamedTuple):
    """A NamedTuple used to provide different ways to capture a regular expression pattern."""
    ca: str # A regex that will capture the pattern as a group.
    dc: str # A regex that will *not* capture the pattern as a group.
    na: str # A regex that will capture the pattern as a *named* group.
    pa: str # The regex pattern by itself.

def capture_re(pattern: str, group_name: str) -> CaptureRegex:
    """Initializes a namedtuple with regular expressions that contain a pattern,
    a non-grouped pattern, a grouped pattern, and a named group pattern.
    
    :param pattern: A regular expression pattern
    :param group_name: The name of the named regular expression group
    :returns: A namedtuple with names ca (capture), dc (don't capture), na (named 
        group), and pa (plain pattern)
    """
    return CaptureRegex(f"({pattern})", f"(?:{pattern})", f"(?P<{group_name}>{pattern})", pattern)
