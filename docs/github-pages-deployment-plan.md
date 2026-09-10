# PiLab GitHub Pages 公开发布方案

记录日期：2026-09-10  
项目检查基线：2026-09-09  
状态：目标公开仓库已创建且启用了 Pages，SSH 已验证为 PiLab-ZJU；正在进行首次推送与线上部署验证。

## 2026-09-10 实施进度

- 根据 `team/members.md` 接入 3 位博士研究生、3 位硕士研究生、3 位科研伙伴和 3 位校友，更新研究方向、职务与毕业去向。
- 将 9 张成员照片生成最长边 640px 的网站版本，存放于 `assets/img/team/`；史宇飞使用实际提供的 `syf.png`，言鹏韦新补充的 `ypw.jpg` 已接入。
- 团队页按学位分组，科研伙伴展示职务，校友展示单位和岗位；桌面、390px 与 320px 窄屏检查及手机菜单交互通过。
- 正式地址已配置为 `https://pilab-zju.github.io`，根路径 `baseurl` 留空。
- `.github/workflows/deploy-pages.yml` 已接入内容检查、生产构建、产物检查和 Pages 自动发布；PR 只检查，`main` 才部署。
- 根据 RubyGems 官方平台元数据补齐 Linux GNU 版本的 `ffi`、`google-protobuf`、`sass-embedded` 及其校验值，并补齐原锁文件内其余 gem 的 SHA-256，修复空校验值导致冻结安装失败的问题。Mac 冻结模式下的全部检查通过，两个平台的锁定依赖关系完整；Linux runner 的实际安装与构建需在首次 Actions 运行时验证。
- 网站构建排除成员资料原稿、原始照片、字体样张、开发脚本和本地工具配置；新增检查防止这些文件被发布。
- `scripts/prepare_public.rb` 可导出公开源码，过滤论文、新闻和 YAML 数据中的草稿，保留本地原稿。首次发布应使用该导出结果。
- 导出的公开源码已通过冻结依赖检查、生产构建、14 页链接与正式 canonical 检查，且确认不含草稿或成员原稿。可上传的源码包保存在本地 `_private/pilab-pages-source-2026-09-10.tar.gz`，解压后包含 Pages 工作流，不包含 `_site/`。
- 当前本地检查覆盖 14 个 HTML 页面，网站产物约 1.8 MB；Actions 工作流已通过 actionlint 语法检查。
- 已核对旧仓库 `PiLab-ZJU/pilabzju_web` 启用了 Pages，旧站可访问；本次发布使用新建的 `PiLab-ZJU/pilab-zju.github.io`，不迁移旧仓库历史。
- 本机 SSH 别名 `github-pilab` 已验证成功，GitHub 返回 `Hi PiLab-ZJU!`；目标根站点仓库现已创建为公开仓库，并启用了 Pages。

已进入首次推送与部署阶段。推送使用现有 SSH key，不需要额外登录 `gh`；创建仓库和修改 Pages 设置需要网页管理会话或具备对应权限的 API 登录，SSH key 本身不提供这些 API 权限。推送后检查 Actions 和线上页面；不得把本地检查通过记为线上发布成功。

本机目标远端为 `git@github-pilab:PiLab-ZJU/pilab-zju.github.io.git`，SSH 配置如下，仅记录路径，不复制私钥内容：

```sshconfig
Host github-pilab
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_pilab
  IdentitiesOnly yes
```

如决定先复用旧仓库，可将已构建页面发布到 `https://pilab-zju.github.io/pilabzju_web/`；需要将构建 `baseurl` 设为 `/pilabzju_web` 并沿用旧仓库历史。这是备用发布路径，当前代码和源码包仍按根站点准备。

## 推荐路径

采用 **PiLab 账号根站点 + 公开网站仓库 + GitHub Actions 自动发布**。

当前项目已经是 Jekyll 静态网站，保留现有页面、模板和 Markdown/YAML 内容维护方式即可。上线准备主要包括公开内容整理、构建环境适配和自动发布配置。

## 已验证的项目状态

以下结果来自 2026-09-09 的本地检查，实施时应根据最新代码重新确认：

- 项目固定使用 Jekyll 4.4.1，本地 Ruby 和 Bundler 版本分别为 4.0.6、4.0.16。
- `bundle exec ruby scripts/check.rb` 通过；检查覆盖 14 个页面、本地链接、锚点、图片、日期、草稿排除，以及根路径和 `/qa` 子路径部署。
- 当前本地目录尚未初始化 Git，也没有 GitHub Pages 发布工作流。
- `_config.yml` 中的 `url` 和 `baseurl` 均为空。
- `Gemfile.lock` 只记录了 `arm64-darwin` 平台，Linux 构建环境尚待验证。
- 当前 `_site/` 中仍包含 `复古字体样张.pdf` 和 `retro_specimen.swift`，发布排除规则需要补齐。
- 页面引用了 Google Fonts，首次上线时需要验证实际访客网络下的加载体验。

上述检查不代表线上部署验收完成，也不包含外部链接可用性检查。

## 1. 确定账号、仓库和正式网址

如果使用现有 `PiLab-ZJU` 账号，推荐配置如下：

| 项目 | 推荐值 |
| --- | --- |
| GitHub 账号 | `PiLab-ZJU` |
| 网站仓库 | `PiLab-ZJU/pilab-zju.github.io` |
| 正式网址 | `https://pilab-zju.github.io` |
| 主分支 | `main` |
| Pages 发布来源 | GitHub Actions |

仓库名为 `<owner>.github.io` 时，对应账号根站点；普通项目仓库对应 `https://<owner>.github.io/<repository>/`。GitHub Free 支持公开仓库使用 Pages。[GitHub Pages 官方说明](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

账号公开页面还列有一个 `pilabzju_web` 仓库。实施前应核对它是否承载旧站、是否有需要保留的历史，以及目标根站点仓库是否已经存在；同时确认发布账号具有相应管理权限，再确定复用或新建仓库的方式。[PiLab-ZJU 账号页面](https://github.com/PiLab-ZJU)

## 2. 整理适合公开的源码和构建产物

**不显示在网页上，不等于没有公开。** `published: false` 可以阻止内容出现在网站中，但文件一旦提交到公开仓库，仍可从源码和提交历史读取。

首次提交前应完成：

- 核对 `_papers/`、`_news/`、`_data/` 中的草稿与占位样例，将未准备公开的材料留在公开仓库外；可以公开的教学或维护样例应明确标识。
- 整理 `.claude/` 等本地工具配置、开发截图和内部记录的提交范围。
- 补齐 `_config.yml` 的排除规则，使字体样张 PDF、Swift 脚本等开发文件不进入 `_site/`。
- 保持 `_site/`、缓存和本地依赖目录不进入源码提交。
- 检查实际构建产物的文件清单，确认其中只有拟公开的网站文件。

需要分别维护两类规则：`.gitignore` 控制未跟踪文件是否被 Git 收录；Jekyll 的 `exclude` 控制文件是否进入网站产物。两者不能互相替代。

## 3. 使用 GitHub Actions 构建和发布

保留 Jekyll 4.4.1，通过自定义工作流构建。方案核对时，GitHub Pages 默认构建环境列出的 Jekyll 版本为 3.10.0，与本项目不同。[GitHub Pages 依赖版本表](https://pages.github.com/versions/)

目标流程：

```text
修改 Markdown / YAML / 页面文件
              ↓
提交 PR：自动检查和构建
              ↓
合并或提交到 main
              ↓
自动检查 → Jekyll 构建 → 上传 _site/ → 部署 GitHub Pages
```

实施内容：

1. 新增 `.github/workflows/deploy-pages.yml`。
2. 在 Ubuntu runner 上验证 Ruby、Bundler 和 Jekyll 环境，补齐并提交 Linux 平台的依赖锁定。
3. 接入现有 `bundle exec ruby scripts/check.rb`，检查失败时停止发布。
4. 使用生产环境构建网站，部署本次生成的 `_site/`。
5. PR 只执行检查和构建；`main` 更新后自动部署，并保留手动触发入口。
6. 使用 GitHub 官方 Pages artifact 上传和部署 actions，配置所需权限及 `github-pages` environment，将正式部署限制到 `main`。

具体 action 版本在实施时核对。工作流结构参考 [GitHub Pages 自定义工作流文档](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 4. 配置正式地址并完成首次上线

账号根站点的 `_config.yml` 配置为：

```yaml
url: "https://pilab-zju.github.io"
baseurl: ""
```

如果最终选择普通项目仓库，`url` 仍为账号域名，`baseurl` 改为 `/仓库名`。账号根站点不需要把 `pilab-zju.github.io` 填进 `baseurl`。

首次上线步骤：

1. 完成公开范围整理、工作流配置和本地检查。
2. 根据目标仓库现状，初始化本地 Git 或接入已有仓库，保留需要的历史。
3. 推送网站源码和工作流。
4. 在仓库 `Settings → Pages → Build and deployment → Source` 中选择 `GitHub Actions`。
5. 运行工作流，确认检查、构建和部署成功，记录最终访问地址。

发布来源配置参考 [GitHub 官方文档](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。新建的 `github.io` 站点会自动使用 HTTPS，无需购买域名或自行维护证书。[HTTPS 说明](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https)

## 5. 线上验收与后续维护

首次部署后，完成以下验收再宣布上线：

- 首页、新闻、论文列表、论文详情、项目和团队页面均可访问。
- 手机菜单、页面锚点、图片和样式正常，页面没有明显溢出。
- 深层页面可直接打开和刷新，不存在的路径显示自定义 404 页面。
- canonical 和 Open Graph URL 使用正式地址，内部链接没有本地地址或错误的子目录前缀。
- 草稿页面和开发文件无法通过网站路径访问。
- 外部论文与项目链接可用。
- 使用实际访客网络测试加载速度，包括 Google Fonts；如影响体验，再调整为本地字体资源或合适的系统字体方案。

成员资料可以在上线后逐步补齐；网站上线新闻应在站点实际可访问后填写真实日期，再改为公开。

日常维护继续修改 Markdown/YAML，通过 PR 检查后合并到 `main` 自动发布。出现问题时回退相应提交并重新部署。同步更新 [README 发布说明](../README.md)，使新维护者可以按文档操作。

## 实施待办

- [ ] 核对发布账号权限、`pilabzju_web` 用途及目标根站点仓库状态。
- [x] 确认公开源码范围，提供过滤草稿及本地开发文件的导出脚本。
- [x] 补齐 Git 忽略规则及 Jekyll 发布排除规则。
- [x] 补齐 Linux 依赖锁定并检查依赖关系。
- [ ] 在 GitHub Actions 验证 Linux 构建环境。
- [x] 添加检查、构建和 Pages 自动部署工作流。
- [x] 配置正式 `url`、`baseurl`，更新 README。
- [ ] 接入 GitHub 仓库并启用 Pages。
- [ ] 完成首次线上验收。
- [ ] 按实际日期发布上线新闻。
