# PiLab 网站最简维护说明

## 只维护一个公开版本

日常公开内容只在 GitHub 仓库 `PiLab-ZJU/pilab-zju.github.io` 中修改并提交。在完整资料工作区中，该仓库位于 `_private/github-pages/`；若单独克隆仓库，则克隆目录本身就是维护目录。

项目根目录中的原始照片、草稿和内部资料只作本地留存，不提交到公开仓库。`published: false` 只能隐藏网页内容，不能隐藏已提交的源码或历史记录。

## 第一次使用：配置 GitHub SSH

1. 先确认 GitHub 账号已经拥有 `PiLab-ZJU/pilab-zju.github.io` 的写入权限。
2. 使用已有 SSH 公钥，或生成一对新密钥：

   ```bash
   ssh-keygen -t ed25519 -C "your-github-email@example.com"
   ```

3. 将 `~/.ssh/id_ed25519.pub` 的内容添加到 GitHub：**Settings → SSH and GPG keys → New SSH key**。私钥 `id_ed25519` 不上传、不发送给任何人。
4. 在 `~/.ssh/config` 中加入以下配置；若密钥文件名不同，替换 `IdentityFile` 的路径：

   ```sshconfig
   Host github-pilab
     HostName github.com
     User git
     IdentityFile ~/.ssh/id_ed25519
     IdentitiesOnly yes
   ```

5. 验证连接：

   ```bash
   ssh -T git@github-pilab
   ```

   GitHub 返回 `Hi <账号名>!` 即表示 SSH 身份可用。

首次克隆和安装依赖：

```bash
git clone git@github-pilab:PiLab-ZJU/pilab-zju.github.io.git
cd pilab-zju.github.io
bundle install
git config user.name "你的名字"
git config user.email "你的 GitHub 邮箱"
```

## 改什么、怎么改

日常内容只改数据文件、Markdown 和图片；通常不需要改页面模板。

| 要更新的内容 | 修改位置 | 修改方法 |
| --- | --- | --- |
| 团队成员 | `_data/team.yml` | 复制同类成员条目，修改姓名、年级/职务、关键词和 `photo`。 |
| 成员照片 | `assets/img/team/` 和 `_data/team.yml` | 将网页版图片放入前者，并在 `photo` 填 `/assets/img/team/文件名.jpg`。人物构图重要时先裁为成员卡的 25:28 比例。 |
| 新闻 | `_news/YYYY-MM-DD-标题.md` | 新建一篇带 YAML 头信息的 Markdown，复制邻近新闻的字段填写。 |
| 论文 | `_papers/<slug>.md` | 新建一篇带 YAML 头信息的 Markdown；批量同步论文时按 `docs/paper-sync.md` 操作。 |
| 项目 / GitHub / Hugging Face | `_data/projects.yml` | 在对应列表追加一条记录。 |
| 导航、介绍、联系方式 | `_data/settings.yml` | 直接修改相应字段。 |
| 合作机构 | `_data/collaborations.yml` | 追加或修改机构条目和 logo 路径。 |
| 页面布局和视觉样式 | `assets/css/main.css`、`_includes/`、`_layouts/` | 只在需要改页面表现时修改。 |

YAML 用空格缩进，优先复制同类的现有条目。公开的新内容写 `published: true`；尚未公开的草稿不要放进公开仓库。

## 检查、提交和推送

在公开仓库目录执行。完整资料工作区的路径是 `cd _private/github-pages`。

```bash
git pull --ff-only origin main

# 修改文件后执行检查
bundle exec ruby scripts/check.rb
git diff --check
git status

# 只暂存本次修改的文件，不使用 git add .
git add _data/team.yml assets/img/team/姓名.jpg
git commit -m "Update team profile"
git push origin main
```

将 `git add` 和提交说明换成实际修改内容。推送到 `main` 后，GitHub Actions 会自动检查、构建并部署；在 [Actions 页面](https://github.com/PiLab-ZJU/pilab-zju.github.io/actions)确认对应提交成功即可。

如需从完整资料工作区批量导出公开源码，使用 `bundle exec ruby scripts/prepare_public.rb <空目录>`；导出后先审查差异，再把确认公开的文件同步到上述公开仓库。
