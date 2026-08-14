# 新王觉醒 官网 · 部署上线指南

本站点为零构建的静态网站（HTML + CSS + JS），可部署到任意静态托管平台。
本地文件结构：

```
.
├── index.html        # 主页面（含 SEO / Open Graph / 无障碍标签）
├── css/style.css     # 响应式样式（暗色 + 金色觉醒主题）
└── js/main.js        # 交互脚本（菜单 / 滚动动画 / 计数 / 表单校验）
```

---

## 一、部署前检查清单

- [ ] 修改 `index.html` 中的标题、描述、关键词与 `og:` 社交分享信息
- [ ] 将 `<link rel="canonical" href="https://www.example.com/">` 改为你的正式域名
- [ ] 替换品牌文案、统计数字、动态内容（当前为占位示例）
- [ ] 如需 LOGO 图片，准备 `favicon.ico` 并加在 `<head>`：
      `<link rel="icon" href="./favicon.ico">`
- [ ] 本地预览确认：`python -m http.server 8080` 后访问 `http://127.0.0.1:8080`
- [ ] 确认移动端（手机/窄屏）菜单、布局正常

---

## 二、方案 A：Vercel（推荐，最快）

1. 注册 https://vercel.com （可用 GitHub 登录）。
2. 安装 CLI：`npm i -g vercel`（或用网页端「Add New → Project」导入 Git 仓库）。
3. 项目根目录执行：
   ```bash
   vercel
   ```
   按提示确认，无需额外配置（零构建静态站，默认识别 `index.html`）。
4. 验证：Vercel 会返回 `.vercel.app` 临时域名，访问确认。
5. 绑定正式域名：Dashboard → 项目 → Settings → Domains，填入你的域名，按提示配置 DNS 的 CNAME 记录。
6. HTTPS 默认自动签发（Let's Encrypt），无需额外操作。

**常见失败**：构建命令被识别错误 → 在 `vercel.json` 显式声明：
```json
{ "buildCommand": null, "outputDirectory": ".", "framework": "none" }
```

---

## 三、方案 B：Netlify（拖拽即上线）

1. 打开 https://app.netlify.com/drop 。
2. 把 `index.html`、`css/`、`js/` 三个文件/文件夹直接拖入虚线框。
3. 数秒后获得 `.netlify.app` 域名，可立即访问。
4. 绑定域名：Site settings → Domain management → Add custom domain，按提示改 DNS。
5. HTTPS 自动启用。

**回滚**：Deploys 页面可一键「Publish」历史版本。

---

## 四、方案 C：Cloudflare Pages（国内访问友好）

1. 登录 https://pages.cloudflare.com ，「Create a project」→ 连接 Git 仓库（或 Direct Upload 上传压缩包）。
2. 构建设置：Build command 留空，Build output directory 填 `/`（根目录）。
3. 部署完成后在「Custom domains」绑定域名，Cloudflare 自动签发 HTTPS。
4. 优势：全球 CDN + 国内节点，访问速度快、免费额度高。

---

## 五、方案 D：GitHub Pages（免费、需 Git）

1. 把项目推送到 GitHub 仓库（如 `newking-awakening`）。
2. 仓库 Settings → Pages → Source 选择 `main` 分支根目录。
3. 等待数分钟，访问 `https://<用户名>.github.io/<仓库名>/`。
4. 自定义域名：Settings → Pages → Custom domain，并配置 DNS（A 记录指向 GitHub Pages IP，或 CNAME 指向 `<用户名>.github.io`），开启「Enforce HTTPS」。

> 注意：GitHub Pages 子路径部署时，CSS/JS 引用建议用相对路径（本项目已使用 `./css/...` 相对路径，兼容子路径）。

---

## 六、方案 E：腾讯云 EdgeOne / 对象存储（国内合规首选）

1. 将文件上传至腾讯云 COS 存储桶（开启「静态网站托管」）。
2. 通过 EdgeOne 加速域名绑定，配置 DNS 解析到 EdgeOne 提供的 CNAME。
3. 在 EdgeOne 控制台开启 HTTPS（免费证书）与缓存规则。
4. 适合面向中国大陆用户、需要备案合规的场景（域名需完成 ICP 备案）。

---

## 七、上线后验证（必做）

- [ ] 浏览器打开正式域名，确认页面、样式、脚本均正常加载
- [ ] 移动端真机/开发者工具验证券幕布局与汉堡菜单
- [ ] 查看源代码确认 `<title>`、Meta 描述、OG 标签正确
- [ ] 用 https://search.google.com/test/rich-results 或分享到社交平台验证 OG 卡片
- [ ] 确认 HTTPS（地址栏锁标）无混合内容（mixed content）警告
- [ ] 用 Lighthouse（Chrome DevTools → Lighthouse）跑一次性能/SEO/无障碍评分

---

## 八、回滚与维护

- **回滚**：Vercel / Netlify / Cloudflare Pages 均保留每次部署历史，可一键回退。
- **持续更新**：修改文件后重新部署（Git 推送自动触发，或重新拖拽/上传）。
- **缓存**：静态资源更新后若未生效，可在边缘节点/浏览器强制刷新（Ctrl/Cmd + Shift + R），必要时给 CSS/JS 文件名加版本号（如 `style.v2.css`）。

---

## 影响评估

本站点为纯静态前端，**不包含任何服务端密钥或后端逻辑**，表单仅为前端演示（不向任何服务器发送数据）。
若后续接入真实预约/收集功能，需另行搭建后端或对接表单服务（如 Formspree、腾讯问卷、自有 API），并留意《个人信息保护法》合规与隐私政策声明。
