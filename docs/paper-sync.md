# 论文与成员来源同步

`scripts/sync_papers.py` 从 [source.md](source.md) 读取“姓名 → 来源”，更新 `_papers/*.md` 和 `_data/people_sources.yml`。网站仍由 Jekyll 生成，访问页面时不请求 Scholar。

## 日常使用

需要 Python 3.10+、curl 和 PyYAML。首次安装：

```bash
python3 -m venv _private/paper-sync-venv
_private/paper-sync-venv/bin/python -m pip install -r scripts/requirements.txt
```

更新 `docs/source.md` 后，在项目根目录执行：

```bash
# 预览变更，不改论文或成员数据
_private/paper-sync-venv/bin/python scripts/sync_papers.py

# 阅读终端统计与 _private/paper-sync-report.json 后写入
_private/paper-sync-venv/bin/python scripts/sync_papers.py --write

# 验证，再按 README 的公开导出流程提交和推送 main
_private/paper-sync-venv/bin/python -m unittest discover -s scripts/tests -v
bundle exec ruby scripts/check.rb
JEKYLL_ENV=production bundle exec jekyll build
python3 scripts/check_html.py _site
```

GitHub Actions 会运行离线测试、检查和部署已提交的论文数据；不会在每次构建中抓取 Scholar。修改来源后需运行同步脚本，只有推送公开仓库后线上内容才会更新。

## 来源与人员对应

来源行使用 `- 中文姓名 https://…`，姓名须与 `_data/team.yml` 一致。当前支持 Scholar 个人主页、Crossref 作者检索和 Scholar CSV 导出。仅提供 Scholar 主页也可运行；添加 Crossref 时需同时填写已核实的身份配置。

脚本先读取 Scholar 最近的论文列表，再检索 Crossref 的出版方元数据；未匹配的条目读取 Scholar 详情，以获取完整作者与发表信息。Crossref 每人最多检查 1,000 条候选，报告记录候选数量及总搜索结果。这是有界检索，不能保证覆盖所有成果；漏项可用 CSV 或人工维护补充。

英文姓名相同不能证明是同一人。Crossref 记录还需匹配已验证的 ORCID、该人的 Scholar 题名或已知合作者。明确冲突的 ORCID 优先排除；缺少身份依据的候选放入报告的 `identity_rejected`。新增身份信息必须先核实。

生成的 `_data/people_sources.yml` 供团队页面按姓名显示 Scholar 图标链接；同一个人同时出现在科研伙伴与校友中时，两处共用相同主页。请编辑 `source.md`，不要手动改生成文件。

## 时间、去重与现有内容

- 默认近 **3 个自然年**，包括当前年：2026 年对应 **2024–2026**，2027 年对应 2025–2027。脚本按运行日期取窗口；页面按构建日期和 `_config.yml` 的 `paper_years: 3` 筛选首页及论文列表。每年重新同步并构建后窗口前移。
- 使用发表日期，优先出版方在线日期，不使用索引、入库或元数据更新时间。已知精确日期晚于运行日的记录跳过；只有年或月时保留对应的 `date_precision`，不展示虚构的月日。
- DOI 大小写及网址形式统一；arXiv 版本号归一；出版方提供的预印本/正式版关系用于合并。没有共同标识时，规范化题名且至少一位完整作者一致才合并。不同人员的同一篇合著只留一条，`source_members` 保存归属。
- 默认收录正式发表记录。单独预印本跳过；如需收录，增加 `--include-preprints`。正式版与预印本匹配时保留正式版书目数据及已有链接，不另建条目。不对不同标题做模糊合并；没有标识关系的改题版本需人工核对。
- 保留现有人工简介、正文、链接、文件名与草稿决定；自动导入记录的预印本可升级为正式版本。同一数据再次运行不会新增或改写条目。发现现有文件存在歧义重复时停止，避免破坏详情 URL。
- 来源中暂时消失的论文不会自动删除。较早论文的详情 URL 保留，但不进入近三年的列表；需要彻底移除时人工处理。

## 网络与补充导入

请求间隔至少 1 秒，响应缓存 24 小时，缓存与报告位于 `_private/`，不进入公开导出。沿用系统网络配置及代理环境变量；无需 API key。`--offline` 完全使用已有缓存，`--refresh` 强制重新获取，二者不能同时使用。

Scholar 没有批量访问 API，公开页面可能限流或改变结构（见 [Google Scholar 帮助](https://scholar.google.com/intl/en/scholar/help.html)）。遇到 403、429、验证页或解析失败时脚本停止，不尝试绕过；所有来源获取及合并成功前不写论文与成员数据。可以稍后重试，或显式使用 `--crossref-only` 跳过 Scholar 请求。Crossref 的接口说明见 [官方 REST API 文档](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)。

Scholar 导出的 CSV 可作为补充，原件放在 `_private/`：

```bash
_private/paper-sync-venv/bin/python scripts/sync_papers.py \
  --crossref-only --csv '蒋卓人=_private/jiang-scholar.csv'
# 确认预览后，在相同命令末尾追加 --write
```

CSV 至少包含 `Title,Authors,Year`，作者以分号分隔，支持 `Publication`、`DOI`、`URL`。没有 DOI/原文 URL 时保留该人的 Scholar 来源链接。上例仍会请求配置中的 Crossref；不会静默忽略其他人员来源失败。`--as-of YYYY-MM-DD` 与 `--years N` 可用于复核历史窗口；长期改变窗口时应同步调整站点的 `paper_years`。

## 首次同步记录

2026-09-11，4 位人员，2024–2026 年窗口：收集 71 条候选记录，合并 27 条重复，排除去重后仅有预印本的 7 条，得到 **37 篇**正式发表成果，其中新增 29 篇、为原有 8 篇补充来源信息。另有在 Scholar 列表阶段跳过的预印本，不计入上述 71 条。重复运行结果为新增 0、修改 0。

原有 2027 年会议摘要论文草稿保持不公开。新导入条目只填来源提供的书目信息，不自动生成摘要或研究结论。
