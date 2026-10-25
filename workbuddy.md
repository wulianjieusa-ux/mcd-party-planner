# WorkBuddy 开发记录（workbuddy.md）

> 本文件记录本项目在**腾讯 WorkBuddy** 智能体环境中的真实开发过程，
> 用于「麦当劳程序员创意开发大赛」WorkBuddy 专项奖励核验。
> 所有对话均在 WorkBuddy 中完成，未使用其他 AI 编程工具代写核心代码。

## 项目信息

- **项目**：麦麦聚餐参谋（McParty Planner）—— 多人聚餐点餐协调 Skill
- **开发日期**：2026-10-25（活动截止当日，北京时间）
- **开发环境**：WorkBuddy（Windows + Git Bash + Python 3.13）

## 开发时间线（真实还原）

### 第 1 轮：活动解读与摸底（23:12 – 23:16）

**用户指令**：「https://www.workbuddy.link/p/8QYARuAmZ9RgQty3FSzNUs?source=2 你帮我也搞一个参加下这个活动」

WorkBuddy 动作：
1. 抓取活动页（JS 渲染，仅拿到标题）→ 转用网络搜索定位活动详情；
2. 读取大赛官方仓库 `M-China/mcd-developer-innovation-challenge` 的
   `activityGuidelines.md`，确认硬性要求：
   - 仓库必须含 5 个文件：`README.md` / `CONTEST_DECLARATION.md` /
     `MCP_INTEGRATION.md` / `mcp-config.example.json` / `workbuddy.md`
   - 报名截止 2026-10-25 23:59（当天），需在活动仓库提交指定格式 Issue
   - 排名按 GitHub Star，Star 为 0 不进榜
3. 读取 `M-China/mcd-mcp-server` README，拿到全部 30+ Tool 清单、
   接入地址 `https://mcp.mcd.cn`（Streamable HTTP + Bearer Token）、限流规则；
4. 检查本机环境：无 gh CLI、无已存 GitHub 凭证、Python 3.13 可用。

**关键决策**：官方示例是点餐/省钱/活动推荐助手，其中"省钱"方向预判会扎堆；
营养方向已有参赛作品。最终选择**多人聚餐点餐协调**——一个能同时串起
`query-nearby-stores` → `query-meals` → `query-store-coupons` →
`list-nutrition-foods` → `calculate-price` 五个 Tool 的完整闭环场景，
且切入点（分单/分摊/分享装合并）在大赛示例中未被占据。

### 第 2 轮：核心开发（23:16 – 23:20）

**用户指令**：（继续推进开发）

WorkBuddy 动作（产出均在 WorkBuddy 会话中生成，人工未介入写码）：
1. `mcd_mcp_client.py`：零依赖 MCP 客户端（initialize / tools/list / tools/call），
   同时兼容 `application/json` 与 `text/event-stream`(SSE) 响应，处理 429 限流提示；
2. `fixtures/demo_data.py`：离线演示数据（菜单/优惠券/营养），明确标注为示意数据；
3. `party_planner.py`：规划主程序，含
   - 个人选品（忌口一票否决 → 偏好命中数优先 → 同分取低卡 → 再取低价）
   - 分享装合并（全组只点一份小食，按人头向上取整分摊）
   - 单券最优选择（满减/品类折扣逐张试算）
   - 超支诚实警告（`warnings` 机制，不硬塞方案）

### 第 3 轮：验证（23:21）

运行 `python party_planner.py --demo --people demo_people.json`，
一次通过：4 人配置正确输出分单、分享装合并、最优券（满60减10）与总账。

### 第 4 轮：文档与参赛材料（23:22 – 23:24）

按大赛要求补齐 `README.md`、`CONTEST_DECLARATION.md`、`MCP_INTEGRATION.md`、
`mcp-config.example.json`（仅 `${MCD_TOKEN}` 环境变量占位符，已脱敏）与本文件。

## 使用的 WorkBuddy 能力

- 网页抓取与活动规则检索（`WebFetch` / `WebSearch`）
- 本地文件读写、Python 开发与运行验证（Bash / 文件工具）
- Git 仓库初始化与提交
- 通过 GitHub API 完成仓库创建、代码推送与参赛 Issue 提交

## 真实性承诺

本项目核心代码（两个 Python 文件）与全部文档均在上述 WorkBuddy 会话中生成，
开发过程真实、连续、可复现；未使用任何自动化刷量手段获取 Star。
