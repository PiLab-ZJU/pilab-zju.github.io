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

## 2026-09-13 高校彩色组合标识

合作高校统一显示原版彩色“校徽＋校名”，取消默认灰度滤镜。

| 高校 | 本地文件 | 来源及处理 |
|---|---|---|
| 武汉大学 | `assets/img/collab/whu-1.png` | 用户提供的彩色校徽、中英文校名组合原图 |
| 江苏大学 | `assets/img/collab/ujs-color.png` | [校友会官方下载页](https://xyh.ujs.edu.cn/info/1003/1131.htm)的[AI 源文件包](https://xyh.ujs.edu.cn/jiangdalogoyuanwenjian.zip)，使用“4 常用校标组合（横板）.ai”，150 dpi 导出并裁去画布外沿留白；保留原配色与组合 |
| 北京大学 | `assets/img/collab/pku-color.png` | [官网原版 PNG](https://www.pku.edu.cn/Uploads/Picture/2019/12/26/s5e04176fbbfa3.png)，红色校徽、中文校名及英文校名 |
| 华东师范大学 | `assets/img/collab/ecnu-color.png` | [学校标识页](https://www.ecnu.edu.cn/wzcd/xxgk/xxbs.htm)的[标志组合包](https://www.ecnu.edu.cn/fj/biaozhizuhe.rar)，原版“标志组合/4.png” |
| 南洋理工大学、伍斯特理工学院 | 原有 `ntu.png`、`wpi.png` | 已核对原图含彩色校徽与校名，继续使用 |
