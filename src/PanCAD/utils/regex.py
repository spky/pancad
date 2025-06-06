"""A module contains utilities for creating regular expressions to parse 
formatted data."""

from collections import namedtuple

def capture_re(pattern: str, group_name: str) -> namedtuple:
    """Initializes a namedtuple with regular expressions that contain a pattern,
    a non-grouped pattern, a grouped pattern, and a named group pattern.
    
    :param pattern: A regular expression pattern
    :param group_name: The name of the named regular expression group
    :returns: A namedtuple with names ca (capture), dc (don't capture), na (named 
        group), and pa (plain pattern)
    """
    CaptureRegex = namedtuple("CaptureRegex", ["ca", "dc", "na", "pa"])
    return CaptureRegex(
        f"({pattern})",
        f"(?:{pattern})",
        f"(?P<{group_name}>{pattern})",
        pattern,
    )