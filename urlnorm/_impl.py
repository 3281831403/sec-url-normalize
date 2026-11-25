"""URL 归一化的唯一实现文件。

本文件恰好包含 8 个桩。初始状态下每个桩只抛出 NotImplementedError，
解题方需要按 README 中列出的缺陷顺序逐个补齐。
"""


def split(url: str) -> dict:
    """把 URL 拆成 scheme、authority、path、query、fragment 五段。

    缺失的段用空串表示，返回字典始终包含这五个键。
    """
    raise NotImplementedError


def lower_authority(authority: str) -> str:
    """规范化 authority：主机小写、去掉用户信息、去掉默认端口。"""
    raise NotImplementedError


def remove_dot_segments(path: str) -> str:
    """折叠路径中的点段，保留末尾斜杠语义，连续斜杠折叠为单斜杠。"""
    raise NotImplementedError


def normalize_percent(text: str) -> str:
    """统一百分号编码：三元组大写，不重复编码，未保留字符解码。"""
    raise NotImplementedError


def normalize_query(query: str) -> str:
    """按参数名再按参数值排序查询参数，空值保留等号，空查询返回空串。"""
    raise NotImplementedError


def normalize(url: str, policy=None) -> str:
    """组合归一化 URL；policy 中 keep_fragment 为 True 时保留片段。"""
    raise NotImplementedError


def equal(a: str, b: str) -> bool:
    """按归一结果比较两个 URL，仅路径与查询区分大小写。"""
    raise NotImplementedError


def url_batch(urls, policy=None) -> dict:
    """批量归一，返回原 URL 到归一结果的字典，各条互不影响。"""
    raise NotImplementedError