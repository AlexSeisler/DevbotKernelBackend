"""
DEPRECATED — tagging_hook.py

This file has been replaced by `tagger.py` as part of Phase 3 Modularization.
It is retained temporarily for backward compatibility and will be removed
in a future release.
"""

import warnings
from .tagger import Tagger

warnings.warn(
    "tagging_hook.py is deprecated. Please import Tagger from tagger.py instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["Tagger"]