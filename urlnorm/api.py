"""公开门面：只从 urlnorm._impl 再导出 8 个接口。"""

from ._impl import (
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