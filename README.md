白名单按归一后的地址比对，攻击者用默认端口和点段绕过，同一个地址被判成了两个：默认端口不剔除，带端口与不带端口被判不同；用户信息不剥离，凭据留在归一结果里；点段折叠只在路径开头生效，中间的点段残留；双斜杠不折叠，路径为空时输出多一个斜杠；百分号编码转小写，等价编码被判不同；已编码的保留字符被二次编码，长度翻倍；查询参数不排序，顺序不同被判不同；空查询与无查询被合并，语义丢失；片段默认保留，带锚点的地址被当成不同资源；比较函数对路径做小写化，大小写敏感路径被误判相等。urlnorm/_impl.py 是核心，tests/test_normalize.py 15个红。要修的是：按上面的顺序把 10 个缺陷逐个修掉。

## 运行方式

在仓库根目录执行：

    python -m pytest tests -q

初始状态必须恰好是 15 failed，并且每个 failed 的原因都必须是 urlnorm/_impl.py 中的 NotImplementedError。不允许出现 collection error、import error 或其他断言失败。补完实现后再跑同一命令，应看到 15 passed。

## 字段表

| 字段 | 内容 |
| --- | --- |
| 方向 | 安全 |
| 分类 | 漏洞检测与攻防 |
| 类型 | Bugfix |
| 运行环境 | Python 3, pytest |
| 外部依赖 | 无外部依赖 |

## tests 不可修改

tests/test_normalize.py 是验收标准，不允许修改、跳过、删除、重命名或放宽断言。所有断言都要求精确的归一输出串，不能只检查前缀、子串或类型。

## 门面布局

    sec-url-normalize/
      README.md
      conftest.py
      urlnorm/__init__.py
      urlnorm/_impl.py
      urlnorm/api.py
      tests/test_normalize.py

urlnorm/_impl.py 是唯一实现文件，恰好有 8 个桩，初始全部 raise NotImplementedError。urlnorm/api.py 只做再导出，urlnorm/__init__.py 从 urlnorm.api 导出。conftest.py 只负责把仓库根加入 sys.path。tests/test_normalize.py 只通过公开门面导入。

8 个桩的职责如下：

1. split：拆分五段，缺失段返回空串而不是缺键。
2. lower_authority：主机小写、端口去默认值、去用户信息。
3. remove_dot_segments：折叠点段，保留末尾斜杠语义，双斜杠只折叠为单斜杠。
4. normalize_percent：百分号编码统一为大写，不重复编码，未保留字符解码。
5. normalize_query：查询参数按名称再按值排序，空值保留等号，空查询返回空串。
6. normalize：组合归一，片段默认剥离但可按策略保留。
7. equal：按归一结果比较，区分大小写的部分只有路径与查询。
8. url_batch：批量归一，各条独立。

split 固定返回 scheme、authority、path、query、fragment 五个键。normalize 的 policy 是可选字典，其中 keep_fragment 为 True 时保留片段。url_batch 返回原 URL 到归一结果的字典。

## 10 条边角约定逐条核对

1. 默认端口：http 的 80 和 https 的 443 在主机名后视为默认端口并删除。示例：http://Example.com:80/a 归一为 http://example.com/a。
2. 用户信息：authority 中最后一个 at 号之前的用户信息全部剥离，只保留主机与端口。示例：http://user:pass@Example.com:8080/a 归一为 http://example.com:8080/a。
3. 点段：路径中任意位置的点和双点都按层级折叠，开头的双点不得越过根。示例：/a/./b/../c 归一为 /a/c。
4. 斜杠：连续斜杠只保留一个；路径为空时不追加斜杠，路径为单斜杠时保留根斜杠。示例：http://example.com//a///b 归一为 http://example.com/a/b，http://example.com 归一为 http://example.com。
5. 百分号大小写：所有合法的百分号三元组统一大写。示例：/a%2fb%3a 归一为 /a%2Fb%3A。
6. 二次编码：已经编码的保留字符保持原编码，不得把百分号本身再次编码。示例：/a%2Fb%3Fc 保持 /a%2Fb%3Fc。
7. 查询排序：查询参数按名称、再按值排序，空值保留等号。示例：b=2&a=1&a=0&empty= 归一为 a=0&a=1&b=2&empty=。
8. 空查询：原地址末尾有问号时保留空查询，没有问号时不添加问号。示例：/path? 保持 /path?，/path 保持 /path。
9. 片段：片段默认删除；policy 中 keep_fragment 为 True 时保留片段。示例：/a#section 默认归一为 /a，保留策略下为 /a#section。
10. 比较：equal 先归一再用精确字符串比较，路径与查询区分大小写。示例：/Path 与 /path 不相等。

15 条测试中，前 10 条分别对应上面 10 个缺陷，后 5 条分别覆盖幂等、默认端口等价、点段折叠结果、查询顺序等价、批量与单条一致。建议实现时逐条对照本节，不要只以测试通过作为唯一标准。

## 字段表

| 字段 | 取值 |
| --- | --- |
| 所属领域 | 安全 |
| 子方向 | 漏洞检测与攻防 |
| 任务类型 | Bugfix |
| 语言/框架 | Python 3, pytest |
| 环境可复现等级 | 无外部依赖 |

