"""15 条严格验收测试。

每条测试都断言精确输出串。初始状态下所有断言都会因为
urlnorm/_impl.py 中的桩抛出 NotImplementedError 而失败。
"""

from urlnorm import (
    equal,
    lower_authority,
    normalize,
    normalize_percent,
    normalize_query,
    remove_dot_segments,
    split,
    url_batch,
)


def test_default_port_removed():
    """缺陷 1：默认端口必须剔除。"""
    assert lower_authority("Example.COM:80") == "example.com"
    assert normalize("http://Example.COM:80/a") == "http://example.com/a"


def test_userinfo_stripped():
    """缺陷 2：用户信息必须剥离，split 的五个键必须齐全。"""
    assert split("http://user:pass@Example.com:8080/a?x=1#f") == {
        "scheme": "http",
        "authority": "user:pass@Example.com:8080",
        "path": "/a",
        "query": "x=1",
        "fragment": "f",
    }
    assert split("http://example.com/a") == {
        "scheme": "http",
        "authority": "example.com",
        "path": "/a",
        "query": "",
        "fragment": "",
    }
    assert lower_authority("user:pass@Example.com:8080") == "example.com:8080"
    assert (
        normalize("http://user:pass@Example.com:8080/a?x=1#f")
        == "http://example.com:8080/a?x=1"
    )


def test_dot_segments_folded_in_middle():
    """缺陷 3：路径中间的点段也必须折叠。"""
    assert remove_dot_segments("/a/./b/../c") == "/a/c"
    assert normalize("http://example.com/a/./b/../c") == "http://example.com/a/c"


def test_repeated_slashes_collapsed():
    """缺陷 4：连续斜杠折叠，空路径不追加斜杠。"""
    assert remove_dot_segments("//a///b//") == "/a/b/"
    assert normalize("http://example.com//a///b") == "http://example.com/a/b"
    assert normalize("http://example.com") == "http://example.com"


def test_percent_encoding_uppercased():
    """缺陷 5：百分号三元组统一大写，未保留字符解码。"""
    assert normalize_percent("/a%2fb%3a%7e%41") == "/a%2Fb%3A~A"


def test_encoded_reserved_not_double_encoded():
    """缺陷 6：已编码的保留字符保持原编码，不二次编码。"""
    assert normalize_percent("/a%2Fb%3Fc") == "/a%2Fb%3Fc"


def test_query_parameters_sorted():
    """缺陷 7：查询按名称再按值排序，空值保留等号。"""
    assert normalize_query("b=2&a=1&a=0&empty=") == "a=0&a=1&b=2&empty="


def test_empty_query_preserved():
    """缺陷 8：空查询与无查询不能合并。"""
    assert normalize("http://example.com/path?") == "http://example.com/path?"
    assert normalize("http://example.com/path") == "http://example.com/path"
    assert (
        normalize("http://example.com/path?b=2&a=1")
        == "http://example.com/path?a=1&b=2"
    )


def test_fragment_stripped_by_default():
    """缺陷 9：片段默认剥离，策略允许时保留。"""
    assert normalize("http://example.com/a#section") == "http://example.com/a"
    assert (
        normalize("http://example.com/a#section", {"keep_fragment": True})
        == "http://example.com/a#section"
    )


def test_equal_is_path_case_sensitive():
    """缺陷 10：路径大小写必须参与比较。"""
    assert equal("http://example.com/Path", "http://example.com/path") is False
    assert equal("HTTP://Example.COM/Path", "http://example.com/Path") is True


def test_normalized_url_is_idempotent():
    """补充 1：已规范地址再次归一后保持不变。"""
    normalized = "http://example.com/a/b?a=1&b=2"
    assert normalize(normalized) == normalized


def test_default_port_equivalent():
    """补充 2：带默认端口与不带默认端口的地址相等。"""
    assert equal("http://Example.com:80/a", "http://example.com/a") is True


def test_dot_segments_expected_path():
    """补充 3：点段折叠后的路径和末尾斜杠精确匹配。"""
    assert normalize("http://example.com/a/./b/../c/") == "http://example.com/a/c/"


def test_query_order_equivalent():
    """补充 4：查询参数顺序不同但归一结果相等。"""
    assert (
        equal("http://example.com/a?b=2&a=1", "http://example.com/a?a=1&b=2")
        is True
    )


def test_batch_matches_individual():
    """补充 5：批量归一结果与逐条归一完全相同。"""
    urls = [
        "http://Example.com:80/a",
        "HTTP://example.com/b/./c?z=2&a=1#f",
    ]
    assert url_batch(urls, {}) == {
        "http://Example.com:80/a": "http://example.com/a",
        "HTTP://example.com/b/./c?z=2&a=1#f": "http://example.com/b/c?a=1&z=2",
    }