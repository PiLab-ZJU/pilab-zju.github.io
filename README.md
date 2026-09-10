# PiLab 实验室主页

白蓝主题的中文学术网站。基于 Jekyll、Liquid 和自定义 CSS，设计参考 [Bedford Lab](https://bedford.io/)。内容通过 Markdown/YAML 增量维护，无需修改模板。

## 本地预览与检查

已在 Ruby **4.0.6**、Bundler **4.0.16**、Jekyll **4.4.1** 上验证。Ruby 版本记录于 `.ruby-version`，依赖由 `Gemfile.lock` 固定；不使用 macOS 自带的旧 Ruby。

```bash
bundle install
bundle exec jekyll serve         # http://localhost:4000
bundle exec ruby scripts/check.rb
bundle exec jekyll build         # 静态产物：_site/
```

检查脚本需要 Python 3（仅标准库），在临时目录构建根路径和 `/qa` 子路径。检查本地链接、锚点、图片地址、日期、公开状态、头像降级、标题特殊字符及近期成果排序；不修改正式内容、不访问外部链接。视觉检查仍需在浏览器完成。

## 内容位置

| 内容 | 文件 |
|---|---|
| 首页 | `index.html` |
| 新闻 | `_news/*.md`，列表 `news/index.html` |
| 论文 | `_papers/*.md`，列表 `papers/index.html`，详情 `_layouts/paper.html` |
| GitHub/HF 资源 | `_data/projects.yml` |
| 导师、博士生、硕士生、科研伙伴、校友 | `_data/team.yml` |
| 导航、介绍、联系方式 | `_data/settings.yml` |
| 合作机构 | `_data/collaborations.yml` |
| 照片、标识和样式 | `assets/img/`、`assets/css/main.css` |

## 增量维护

新内容建议先设 `published: false`，核实后改为 `true`。草稿不进入列表、计数、首页聚合或论文详情产物；历史占位样例已全部设为草稿。未填写该字段视为公开，因此不要直接复制样例后删除草稿状态。

新增论文：创建 `_papers/<slug>.md`。作者、题名、出处和 DOI 优先核对出版方。日期使用**发表时间**，仅知道月份时加 `date_precision: month`，不要虚构具体日期。

```yaml
---
title: "论文题名"
published: false
date: 2026-09-01
date_precision: month       # 仅知年月，展示为 2026-09；确知日期则省略
date_kind: publication
venue: 期刊或会议全名
status: Published
authors: [Author One, Zhuoren Jiang]
links:
  - {label: DOI, url: "https://doi.org/具体DOI"}
source: "出版方或元数据来源地址"
summary: 一两句中文研究简介。
---
```

详情页支持 `abstract`（正式摘要）或 `summary`（中文研究简介），正文可留空。确有接收通知时可设置 `status: Accepted`，但应先核实日期口径并同步调整列表说明。

新增新闻：创建 `_news/YYYY-MM-DD-标题.md`，填写 `date`、`category`、`label`、`title`，可选 `desc`、`link` 和 `published`。新闻日期指动态发生或发布的时间；不要直接套用论文的期次日期。

新增项目：在 `_data/projects.yml` 的 `github` 或 `huggingface` 下追加：

```yaml
- name: 资源名称
  published: false
  desc: 一句话说明用途。
  url: https://github.com/PiLab-ZJU/具体仓库
  date: "2026-09"            # YYYY-MM 或 YYYY-MM-DD
  date_kind: updated         # 表示更新日期；首次发布用 released
  tags: [Benchmark, LLM]
```

首页自动合并**公开论文和项目**，按日期取最新 5 条。月份按该月首日排序、仍按月显示；项目更新与论文发表使用各自记录的日期。项目必须链接到具体仓库、模型或数据集。

成员：在 `_data/team.yml` 维护。`students` 使用 `degree: 博士研究生` 或 `degree: 硕士研究生` 分组，填写姓名、入学年份、研究关键词及可选个人主页；`partners` 填写科研伙伴及 `role`；`alumni` 填写毕业时间、去向与可选岗位 `role`。校友 `grad` 使用带引号的 `"YYYY.MM"`，页面自动倒序。言鹏韦分别保留科研伙伴与校友记录。

`photo` 缺失、空字符串或空格均使用姓名首字；网站照片填 `/assets/img/team/文件名.jpg`。2026-09-10 的成员资料已接入 6 位学生、3 位科研伙伴和 3 位校友，导师及 9 位成员照片使用最长边 640px 的网页版本；导师新照片为 `assets/img/team/jzr.jpg`。`team/members.md` 与 `team/` 下的原图属于本地资料，不进入公开源码导出或网站产物；后续内容更新以 `_data/team.yml` 为准。

视觉风格以留白、文字链接和照片为主，使用系统字体，不依赖 Google Fonts。参考与调整见 [Bedford 风格复核](docs/design-review-2026-09-10.md)。

机构标识：使用 `logo` 路径；白色原版标识加 `logo_light: true`，页面以深灰显示。素材保留原文件，来源见 [素材记录](docs/fix-assets-2026-09-09/asset-sources.json)。

## 发布

网站已于 **2026-09-10 上线**：[pilab-zju.github.io](https://pilab-zju.github.io/)。公开仓库为 [PiLab-ZJU/pilab-zju.github.io](https://github.com/PiLab-ZJU/pilab-zju.github.io)。`_config.yml` 已配置正式 `url`，根站点的 `baseurl` 留空；页面会生成 canonical 与 Open Graph URL。部署记录见 [部署方案与进度](docs/github-pages-deployment-plan.md)。

工作流 `.github/workflows/deploy-pages.yml` 在 PR 上运行检查和构建，在 `main` 更新或手动触发时发布。它使用 Ubuntu 24.04、`.ruby-version` 和 `Gemfile.lock` 中的版本，自行构建 Jekyll 4.4.1，再上传 `_site/`。Linux 安装、检查、构建及部署已在 GitHub Actions 实际通过。仓库的 `Settings → Pages → Source` 已设为 `GitHub Actions`。本机通过 SSH 远端 `git@github-pilab:PiLab-ZJU/pilab-zju.github.io.git` 推送。

首次公开前，先导出只含公开内容的源码：

```bash
release_dir=$(mktemp -d /tmp/pilab-pages-source.XXXXXX)
bundle exec ruby scripts/prepare_public.rb "$release_dir"
cd "$release_dir"
BUNDLE_FROZEN=true bundle exec ruby scripts/check.rb
JEKYLL_ENV=production bundle exec jekyll build
python3 scripts/check_html.py _site
```

只将导出的源码接入公开仓库。导出脚本过滤 `_papers/`、`_news/` 和 `_data/` 中 `published: false` 的记录，并只复制网站需要的文件；原始工作目录及草稿保留在本地。

当前本机的公开仓库检出位于项目目录下 `_private/github-pages/`，跟踪远端 `main`；项目根目录仍保存原始资料与草稿。后续在项目根目录修改内容后，重新导出到临时目录，将变更同步至公开检出并审查 `git diff`，运行上述检查，再提交和推送 `main`。若有删除或改名，也需同步删除公开检出中的旧文件。推送后在仓库 Actions 页面确认对应提交部署成功。也可以直接在公开仓库维护公开内容；使用其中一种方式后，及时同步另一份，避免覆盖更新。

`published: false` 只控制网站展示，不能隐藏公开仓库内的源码或提交历史。`.gitignore` 也不会自动过滤 YAML 中的草稿记录。

构建检查会阻止成员原稿、原图、字体样张、开发脚本、工具配置、`docs/` 和嵌套 `_site/` 进入网站。上线公告记录实际首次发布日期 2026-09-10。以后修改模板或资源后，应复查手机菜单、论文详情、404、正式 URL 和图片。

## 当前待补

- 成员个人主页可选补充。
- 会议摘要论文的在线发表时间；该论文目前保留为草稿。
- 英文对应内容与语言切换，作为中文版本稳定后的下一阶段。

发布步骤和实施进度见 [GitHub Pages 部署方案](docs/github-pages-deployment-plan.md)。
