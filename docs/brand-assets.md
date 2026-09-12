# 平台标识来源

2026-09-11 获取以下官方素材，保留原始文件，不重绘或重新着色。本地托管用于平台及个人主页链接，页面无需向第三方加载图片。

| 标识 | 本地文件 | 官方来源 |
|---|---|---|
| GitHub Invertocat 黑色 | `assets/img/brands/github.svg` | [官方 Logo ZIP](https://brand.github.com/GitHub_Logos.zip) 内 `GitHub Logos/SVG/GitHub_Invertocat_Black.svg`；[使用说明](https://brand.github.com/foundations/logo) |
| Hugging Face 彩色 | `assets/img/brands/huggingface.svg` | [官方无边框 SVG](https://huggingface.co/front/assets/huggingface_logo-noborder.svg)；[品牌页面](https://huggingface.co/brand) |
| Google Scholar | `assets/img/brands/google-scholar.ico` | [Scholar 官方网站图标](https://scholar.google.com/favicon.ico) |

统一通过 `_includes/brand-icon.html` 引用。图标旁有平台文字或链接的可访问名称，装饰图片的 `alt` 留空。首页、页脚、项目及论文资源链接共用官方 GitHub/Hugging Face 素材；团队 Scholar 图标通过 `_includes/scholar-link.html` 按姓名关联来源。

## 合作机构标识补充

2026-09-12：江苏大学附属医院使用[医院官网](https://www.jdfy.cn/)页首的[官方 PNG 标识](https://www.jdfy.cn/template/default/index/images/logo.png)，原文件保存为 `assets/img/collab/ujs-hospital.png`。合作机构名称由用户确认。

合作机构后续调整为江苏大学，使用[江苏大学官网原版 PNG](https://www.ujs.edu.cn/images/logo.png)，保存为 `assets/img/collab/ujs.png`。原图为白色标识，使用 `logo_light: true` 在浅色背景上显示。
