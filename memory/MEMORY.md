# 项目长期约定（暗黑2 Mod 资料站）

## 网页章节标题样式约定
- **高级章节标题**（形如 `4.1.1`、`2.4.1`、`5.1.1` 的编号小节）用 `<h3 class="feature-section-title">`，**独立成行、不放进 `.feature-subsection` 包裹内**。
- **其下的子项标题**（如 `1. 新增技能强化词缀`）用 `<h4 class="feature-subsection-title">`，并包裹在 `<div class="feature-subsection">` 内。
- 参考实现：`changes-basic.html`、`changes-awaken.html`、`guide.html`、`download.html` 等。
- 这是用户明确要求的全局约定，新建/填充任何资料页都须遵守，不要再把高级标题写成 `feature-subsection-title`。

## 表格样式约定（已全局生效）
- `.feature-table` / `.price-table`：文字 `text-align:center`（全站所有表格）。
- 单元格含行、列分割线（`border-bottom` + `border-right`，最后一列右边框去重）。
- 合成配方页首列表窄：`.recipe-first th/td:first-child { width:24% }`。

## 图行（fig-row）约定
- 并排图统一用 `.fig-row`（two/three/four/single），图 `object-fit:contain` + `aspect-ratio:4/3` 等高对齐，不裁切，且不突破 1200px 内容栏。
- 竖图特例：基础改动页三列图框 4:7、四列图框 4:5（贴合图比例消留白）。

## 页面编号约定（导航基准 X.Y.Z）
- 每个详情页的章节编号 = `导航顶级项位置·下拉子项位置·序列号`（X.Y.Z）。
- **kicker 分隔符已改为竖线 `|`**（用户 2026-08-14 要求）：
  - 详情页（Name 在前）：`Name | X · Y`，数字段 `X · Y` 包进 `<span class="kicker-num">`（如 `模组概览 | 1 · 1`）。
  - 首页分区卡（数字在前）：`NN | Name`，数字 `NN` 包进 `<span class="kicker-num">`（如 `01 | 模组概览`）。
  - 数字段放大约 15%：`.section-kicker .kicker-num { font-size: 1.15em; letter-spacing: 0.05em }`（`style.css`）。
  - 旧格式 `Name·X·Y` / `NN · Name` 已全站替换，不要再写回中点分隔。
- 导航顶级项位置：模组概览=1 / 新手专区=2 / 全新系统=3 / 职业技能=4（装备详情=5、装备打造=6、物品和配方=7，来自 index.html 区块序）。
- 下拉子项位置：模组概览→特色简介=1 / 作者简介=2 / 赞助详情=3 / 下载地址=4 / **更新日志=5 / 讨论社群=6**（注意：更新日志在讨论社群之前）；全新系统→基础改动=1 / 觉醒系统=2 / 转职系统=3 / 合成配方=4；职业技能→技能总览=1 / 女巫=2 / 亚马逊=3 / 死灵法师=4 / 圣骑士=5 / 野蛮人=6 / 德鲁伊=7 / 刺客=8 / 术士=9；**装备详情→装备系统=1 / 赞助装备=2 / 基底装备=3 / 魔法装备=4 / 稀有装备=5 / 套装装备=6 / 符文之语=7 / 暗金装备=8 / 手工装备=9 / 传奇装备=10 / 混沌装备=11**（编号 5.1~5.11，对应 equipment-system/donate/special/magic/rare/set/rune/unique/crafted/legend/chaos.html；符文之语于 2026-08-14 在套装与暗金之间插入；**基底装备原名特等装备，于 2026-08-14 改显示名，文件 equipment-special.html 与链接保持不变**）。
- **装备打造→强化卷轴=1 / 锻造系统=2 / 重铸与无形化=3 / 符文共鸣=4 / 封印词条=5**（原 6 项含套装继承系统，2026-08-14 删除套装继承；编号 6.1~6.5，强化卷轴=6.1 已有独立页 crafting-scroll.html，锻造系统=6.2 crafting-forge.html、重铸与无形化=6.3 crafting-reforge.html 已填充正式内容，符文共鸣=6.4 crafting-rune.html/封印词条=6.5 crafting-seal.html 占位"该内容尚未实装，敬请期待。"）。
- **物品和配方→合成配方=1 / 新增物品=2**（编号 7.1~7.2；合成配方=7.1 items-recipe.html 已填充正式内容，新增物品=7.2 items-new.html 占位"该内容尚未实装，敬请期待。"）。注意：全新系统(3)下也有一个"合成配方"=3.4 指向 changes-recipe.html，与 7.1 是两个不同页面。
- 由此：基础改动内容 3.1.x、觉醒系统 3.2.x、合成配方 3.4.x、技能总览 4.1.x、下载 1.4.x、安装指南 2.1.x、常见问题 2.2.x、套装装备 5.6.1「套装」改动总览 / 5.6.2 套装随机词条一览；强化卷轴 6.1.1 系统简介 / 6.1.2 强化卷轴一览（4 种卷轴 × 武器/防甲/饰品 三组 feature-list）；物品和配方 7.1.1 原版配方 / 7.1.2 改动配方 / 7.1.3 新增配方（items-recipe.html）等。新建任何资料页须按此派生编号。

## 备份约定
- 用户说「备份」= `git add -A` + commit + `git tag vX.Y.Z`，仅本地仓库（无 remote）。
- 当前标签链到 v1.3.3（v1.0.1→…→v1.2.0→v1.3.0→v1.3.1→v1.3.2→v1.3.3）。
- 每次备份打标签时，先把**全站所有 html 的页脚 `.version-badge`**（含 `index.html` 与 40 个详情页，共 41 处）文本同步为最新 git tag 版本号（如 `网站版本 v1.3.4`），再 commit + tag，使徽章与发布版本一致。
- 全站页脚结构已统一为 `index.html` 的 v1.3.4 样式（王+新王觉醒 brand-line、不蒜子 visitor-counter、5 外链「资料站链接」、By 隔壁大王、版本徽章）。今后若主页页脚有改动（如增删外链），需用脚本批量同步各详情页 `<footer>` 块，否则会出现不一致。
- 参考源（assets/导出网页/ 等）已清理，需找回用 `git checkout v1.0.8 -- "assets/导出网页/"`。

## 部署架构（用户 2026-08-14 说明）
- **主站**：GitHub 仓库（当前本地仓库尚无 remote，需先 `git remote add origin` + `git push -u origin main`）+ Vercel 静态托管（Framework Preset 选 Other，Build/Install Command 留空，Output Directory 留空=根目录），用于国内访问。
- **备用站**：阿里云 OSS 静态网站托管（Bucket 开启"静态网站托管"，默认首页 Index Document = `index.html`，建议错误页也设 `index.html`），绑定自定义域名，国内访问稳定。
- 站点为纯静态多页面（根目录 `index.html` + 各 `.html` + `css/` + `js/`），相对路径引用、无需构建；上传/部署整个文件夹（保持目录结构）即可，OSS/Vercel 均把 `index.html` 当首页、其他页按 `/xxx.html` 访问。
- 部署时建议排除 `.git/`、`.workbuddy/`（及可选 `*.py`/`tools/`/`DEPLOYMENT.md`）避免暴露源码与 git 历史；Vercel 可加 `.vercelignore`。

## 基底装备数据生成约定（equipment-special.html）
- 数据来源：`armor.txt`（D2 原始，tab 分隔）+ `objects.json`（官方中文本地化，list 结构，每项 `{Key, zhCN, zhTW}`）。
- 生成脚本：`_build_base_data.py`（保留），输出 `assets/mod/armor_zh.csv`（**带 UTF-8 BOM / utf-8-sig，Excel 双击不乱码**）+ `js/base-items.js`（`window.BASE_ITEMS` 全局变量，兼容本地 file:// 打开）。
- **tier（普通/扩展/精英）必须来自 objects.json 中文名的上标**：`¹`=普通、`²`=扩展、`³`=精英（脚本用 Unicode 转义 `\u00b9`/`\u00b2`/`\u00b3`，避免文件编码歧义）；**不要用 armor.txt 的 `version` 列**（version 是 classic/expansion 概念，与 tier 无关，仅作 objects.json 缺失时的回退）。
- 中文名取 `zhCN`，用 `clean_zh()` 剥掉开头 Mod 标记（`ㅱ` + 上标 + 空格）；并剔除游戏显示装饰符号（当前仅 `★` U+2605，脚本 `SYMBOL_STRIP` 集合一并覆盖 ☆◆●◇ 等常见装饰符，防止以后出现），剔除后两端去空格。
- 排除：空 code 行、`M01-M09`（召唤物专用，不在游戏中）。当前 217 条分布：普通 73 / 扩展 72 / 精英 72。
- 网页端 tier 下拉由 `js/base-db.js` 从 `DATA` 动态生成；新增 tier 值时需在 `css/style.css` 补 `.base-tier.tier-XXX` 配色（已有 普通=蓝 `#8ec5ff` / 扩展=金 `--gold-soft` / 精英=紫 `#d39bff`）。
- **卡片图片管线**：游戏原图是 D2R 的 `.sprite`（SpA1 格式，未压缩 RGBA8888，头 40 字节后 `w*h*4` 像素；宽在 off6、高 off8）。转换脚本 `sprite_to_webp.py`（保留，依赖 venv 的 Pillow）**递归扫描** `assets/sprite/<分类>/<stem>.sprite`（如 `assets/sprite/helmet/bone_helm.sprite`），**自动跳过 `.lowend.sprite`**（低模占位图，每件物品都有 `.sprite`+`.lowend.sprite` 两份，只转成品那份），转成 `assets/equipment/<stem>.webp`（q85，带透明通道），并留 `assets/equipment/_preview/*.png` 供核对。图片文件名映射来自 `assets/sprite/items.json`（`[{code:{asset:"分类/文件名"}}, ...]`，文件名=asset 的 basename；**多个 tier 的 code 共用同一张图**，如 `cap/xap/uap` 都指向 `cap_hat`）。该 json 混有 `//` 注释与尾逗号，解析需容错（去注释+去尾逗号再 json.loads）。`_build_base_data.py` 用 `load_item_map()`+`resolve_img(code)` 反查 code→stem，仅当 `assets/equipment/<stem>.webp` 存在时才给该条目写 `img` 字段（相对路径），否则留空——以后补图重跑即自动生效。`js/base-db.js` 卡片有 `img` 时给 `.base-thumb` 加 `has-img` 类显示 webp（CSS 已处理）。独特/特殊物品（不在 `armor.txt` 里，如 `chaos_andarielsvisage`、`crown_of_thieves`、`duskdeep` 等）的 webp 会生成但不接线，属正常。**可复现流程**：往 `assets/sprite/<分类>/` 丢 `.sprite` → 跑 `sprite_to_webp.py assets/sprite/<分类> assets/equipment` → 跑 `_build_base_data.py`。

## 工作路径
- 站点根目录：`F:\Work_Test\WebSite\2026-08-11-22-00-10`（注意：日志文件仍写在 `C:\Users\wyj70\WorkBuddy\2026-08-11-22-00-10\.workbuddy\memory\`）。
