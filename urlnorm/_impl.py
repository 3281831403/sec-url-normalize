"""URL 归一化的唯一实现文件。

8 个接口：split / lower_authority / remove_dot_segments /
normalize_percent / normalize_query / normalize / equal / url_batch。

修复顺序对应 README 列出的 10 个缺陷：
 1. 默认端口剔除（lower_authority）
 2. 用户信息剥离（split 保留原文，lower_authority 剥离）
 3. 路径中间点段折叠（remove_dot_segments）
 4. 连续斜杠折叠、空路径不补斜杠（remove_dot_segments / normalize）
 5. 百分号三元组大写、未保留字符解码（normalize_percent）
 6. 已编码保留字符不二次编码（normalize_percent）
 7. 查询参数按名再按值排序（normalize_query）
 8. 空查询与无查询区分（normalize）
 9. 片段默认剥离、策略可保留（normalize）
10. equal 只按归一结果精确比较，路径/查询保持大小写敏感
"""

import re

# 无 scheme 上下文时视为“默认”的常见端口：http/80、https/443。
# lower_authority 的签名只有 authority，验收用例要求 :80 直接剔除，
# 因此对 80 与 443 一视同仁。
_DEFAULT_PORTS = {"80", "443"}

_SCHEME_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.-]*):")
_HEX_PAIR_RE = re.compile(r"^[0-9A-Fa-f]{2}$")
_SLASHES_RE = re.compile(r"/+")

# RFC 3986 的 unreserved 字符：只有这些字符的百分号编码可以解码成原字符。
_UNRESERVED = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-._~"
)


def split(url: str) -> dict:
    """把 URL 拆成 scheme、authority、path、query、fragment 五段。

    缺失的段用空串表示，返回字典始终包含这五个键。各段保留原始文本，
    不做小写化或剥离——归一化是后续函数的职责（验收用例要求 authority
    中的 userinfo 原样保留）。
    """
    parts = {
        "scheme": "",
        "authority": "",
        "path": "",
        "query": "",
        "fragment": "",
    }
    rest = url

    # 先切 fragment：第一个 '#' 之后全部是片段。
    hash_pos = rest.find("#")
    if hash_pos != -1:
        parts["fragment"] = rest[hash_pos + 1:]
        rest = rest[:hash_pos]

    # 再切 query：第一个 '?' 之后（到 fragment 之前）是查询串。
    q_pos = rest.find("?")
    if q_pos != -1:
        parts["query"] = rest[q_pos + 1:]
        rest = rest[:q_pos]

    # scheme 必须位于开头，形如 letter*( letter/digit/+/-/. ) ':'。
    match = _SCHEME_RE.match(rest)
    if match:
        parts["scheme"] = match.group(1)
        rest = rest[match.end():]

    # '//' 之后到下一个 '/' 之前是 authority，其余是 path。
    if rest.startswith("//"):
        rest = rest[2:]
        slash_pos = rest.find("/")
        if slash_pos == -1:
            parts["authority"] = rest
            parts["path"] = ""
        else:
            parts["authority"] = rest[:slash_pos]
            parts["path"] = rest[slash_pos:]
    else:
        parts["path"] = rest

    return parts


def _split_host_port(authority: str):
    """从已去除 userinfo 的 authority 中拆出 (host, port|None)。

    正确处理 IPv6 字面量 [::1]:8080；普通主机只在恰好一个冒号时认端口，
    避免误伤裸 IPv6 或其他多冒号文本。
    """
    if authority.startswith("["):
        end = authority.find("]")
        if end != -1:
            host = authority[: end + 1]
            tail = authority[end + 1:]
            if tail.startswith(":"):
                return host, tail[1:]
            return host, None

    if authority.count(":") == 1:
        host, port = authority.rsplit(":", 1)
        return host, port

    return authority, None


def lower_authority(authority: str) -> str:
    """规范化 authority：主机小写、去掉用户信息、去掉默认端口。"""
    if not authority:
        return ""

    # 缺陷 2：最后一个 '@' 之前（含 @）全部是 userinfo，整体剥离。
    at_pos = authority.rfind("@")
    if at_pos != -1:
        authority = authority[at_pos + 1:]

    host, port = _split_host_port(authority)
    host = host.lower()

    # 缺陷 1：默认端口剔除（80/http、443/https），非常见默认端口保留。
    if port is not None and port not in _DEFAULT_PORTS:
        return host + ":" + port
    return host


def remove_dot_segments(path: str) -> str:
    """折叠路径中的点段，保留末尾斜杠语义，连续斜杠折叠为单斜杠。"""
    if not path:
        # 缺陷 4：空路径必须保持为空，不能补出根斜杠。
        return ""

    # 缺陷 4：连续斜杠统一折叠成一个（含开头的 '//'）。
    collapsed = _SLASHES_RE.sub("/", path)
    is_absolute = collapsed.startswith("/")
    keep_trailing_slash = collapsed.endswith("/")

    stack = []
    for segment in collapsed.split("/"):
        if segment == "" or segment == ".":
            # 空段来自开头/结尾斜杠，'.' 原地消失。
            continue
        if segment == "..":
            # 缺陷 3：路径中间任意位置的 '..' 都回退一级；
            # 栈已空时（开头的 '..'）直接丢弃，不得越过根。
            if stack:
                stack.pop()
            continue
        stack.append(segment)

    if is_absolute:
        result = "/" + "/".join(stack)
    else:
        result = "/".join(stack)

    # 输入带末尾斜杠时保留“目录”语义；栈空时绝对路径结果已是 '/'。
    if keep_trailing_slash and not result.endswith("/"):
        result += "/"

    return result


def normalize_percent(text: str) -> str:
    """统一百分号编码：三元组大写，不重复编码，未保留字符解码。"""
    if not text:
        return text

    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # 缺陷 5：识别合法的 %XX 三元组。
        if ch == "%" and i + 2 < n and _HEX_PAIR_RE.match(text[i + 1:i + 3]):
            code = int(text[i + 1:i + 3], 16)
            decoded = chr(code)
            if decoded in _UNRESERVED:
                # 未保留字符（含字母数字与 -._~，如 %7e、%41）直接解码。
                out.append(decoded)
            else:
                # 缺陷 5：十六进制字母大写。
                # 缺陷 6：已有三元组整体重写为 %XX，'%' 不会被再次编码，
                # 因此 %2F / %3F 等保留字符编码保持原样、长度不会翻倍。
                out.append("%%%02X" % code)
            i += 3
        else:
            # 普通字符（含字面 '/'、'?'、'&' 等保留字符）原样保留，
            # 不做额外编码。
            out.append(ch)
            i += 1

    return "".join(out)


def normalize_query(query: str) -> str:
    """按参数名再按参数值排序查询参数，空值保留等号，空查询返回空串。"""
    if query == "":
        # 缺陷 8 配套：空查询串排序后仍为空串（'?' 的有无由 normalize 区分）。
        return ""

    pairs = []
    for item in query.split("&"):
        if "=" in item:
            name, value = item.split("=", 1)
            pairs.append((name, value, True))
        else:
            # 没有等号的裸参数保持无等号形式。
            pairs.append((item, "", False))

    # 缺陷 7：先按参数名、再按参数值排序；Python 排序稳定，完全相同的
    # 参数保持原相对顺序。
    pairs.sort(key=lambda pair: (pair[0], pair[1]))

    rendered = []
    for name, value, has_equal in pairs:
        if has_equal:
            # 'empty=' 这类空值参数必须保留等号。
            rendered.append(name + "=" + value)
        else:
            rendered.append(name)
    return "&".join(rendered)


def normalize(url: str, policy=None) -> str:
    """组合归一化 URL；policy 中 keep_fragment 为 True 时保留片段。"""
    if policy is None:
        policy = {}

    parts = split(url)

    # scheme 大小写不敏感，统一小写。
    scheme = parts["scheme"].lower()
    authority = lower_authority(parts["authority"])

    # 先做百分号归一（%2e 等会变成普通点段），再折叠点段，
    # 使编码点段无法绕过目录折叠，且结果幂等。%2F 属于保留字符不会被
    # 解码成斜杠，因此不会改变路径层级。
    path = remove_dot_segments(normalize_percent(parts["path"]))

    query = normalize_query(normalize_percent(parts["query"]))

    # 缺陷 8：split 按约定把“无 query”和“空 query（末尾 '?'）”都表示成
    # 空串，因此这里依据原始 URL 中 fragment 之前是否存在 '?' 来区分。
    before_fragment = url.split("#", 1)[0]
    has_query = "?" in before_fragment

    # 缺陷 9：片段默认剥离；仅当策略显式 keep_fragment 为 True 时保留，
    # 且只在原 URL 确实含 '#' 时才追加片段分隔符。
    keep_fragment = policy.get("keep_fragment") is True
    has_fragment = "#" in url

    result = ""
    if scheme:
        result += scheme + ":"
    if parts["authority"]:
        result += "//" + authority
    result += path

    if has_query:
        result += "?" + query

    if keep_fragment and has_fragment:
        result += "#" + normalize_percent(parts["fragment"])

    return result


def equal(a: str, b: str) -> bool:
    """按归一结果比较两个 URL，仅路径与查询区分大小写。"""
    # 缺陷 10：先归一（scheme/host 已小写，路径与查询原样保留大小写），
    # 再做精确字符串比较，绝不能对整串或路径做 lower()。
    return normalize(a) == normalize(b)


def url_batch(urls, policy=None) -> dict:
    """批量归一，返回原 URL 到归一结果的字典，各条互不影响。"""
    # 每条独立调用 normalize，不共享任何可变状态。
    return {url: normalize(url, policy) for url in urls}
