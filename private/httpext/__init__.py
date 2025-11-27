"""
HTTP-related utility functions for internal Akave SDK components.

Currently exposes a `range_download` helper, which mirrors the behaviour of the
Go `httpext.RangeDownload` function.
"""

from .httpext import range_download

__all__ = ["range_download"]


