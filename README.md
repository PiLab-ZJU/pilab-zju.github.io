# PiLab 实验室主页

PiLab 的 Jekyll 静态网站，正式站点为 [pilab-zju.github.io](https://pilab-zju.github.io/)。日常内容通过 YAML、Markdown 和图片维护，推送 `main` 后由 GitHub Pages 自动发布。

## 日常维护

请按 [最简维护说明](docs/maintenance.md) 操作。它说明了：

- 公开内容应该改哪些文件；
- 成员照片、新闻、论文、项目和站点配置如何更新；
- GitHub SSH key 的配置与验证；
- 本地检查、提交、推送和部署确认。

完整资料工作区中的公开仓库位于 `_private/github-pages/`；该目录（或独立克隆的公开仓库）是唯一需要提交和推送的目录。项目根目录中的原始素材和草稿不进入公开仓库。

## 本地预览

```bash
bundle install
bundle exec jekyll serve
bundle exec ruby scripts/check.rb
```

浏览器打开 <http://localhost:4000> 可预览页面。

## 详细资料

- [论文同步说明](docs/paper-sync.md)
- [GitHub Pages 首次上线记录](docs/github-pages-deployment-plan.md)
- [视觉设计复核](docs/design-review-2026-09-10.md)
