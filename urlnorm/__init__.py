"""urlnorm 包入口，只从 urlnorm.api 再导出。"""

from .api import (
    equal,
    lower_authority,
    normalize,
    normalize_percent,
    normalize_query,
    remove_dot_segments,
    split,
    url_batch,
)

__all__ = [
    "split",
    "lower_authority",
    "remove_dot_segments",
    "normalize_percent",
    "normalize_query",
    "normalize",
    "equal",
    "url_batch",
]