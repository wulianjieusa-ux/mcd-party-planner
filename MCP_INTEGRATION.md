# MCP 接入说明（MCP_INTEGRATION）

## 一、使用的 MCP Server

- **服务名称**：麦当劳中国 MCP Server（mcd-mcp-server）
- **官方仓库**：https://github.com/M-China/mcd-mcp-server
- **接入地址**：`https://mcp.mcd.cn`（Streamable HTTP）
- **认证方式**：请求头 `Authorization: Bearer <MCP_TOKEN>`
- **Token 申请**：https://open.mcd.cn/mcp （手机号验证登录 → 控制台 → 激活）
- **限流**：每 Token 每分钟最多 600 次请求

客户端实现见 [`mcd_mcp_client.py`](mcd_mcp_client.py)：仅用 Python 标准库实现
JSON-RPC over Streamable HTTP（initialize / tools/list / tools/call），
自动兼容 `application/json` 与 `text/event-stream` 两种响应体。

## 二、实际调用的 Tool 及用途

| Tool | 用途 | 在本项目中的角色 |
|---|---|---|
| `query-nearby-stores` | 按地址查询附近可用门店 | 定位聚餐门店，拿到 `storeCode` |
| `query-meals` | 查询门店在售餐品（分类/编码/标签） | 真实菜单数据源（替代演示 fixtures） |
| `query-store-coupons` | 查询当前门店可用优惠券 | 选券模块的候选池 |
| `list-nutrition-foods` | 餐品营养信息列表 | 给每个餐品标注热量，支持"同分取低卡"决策 |
| `calculate-price` | 商品价格计算（含券） | 官方算价核对，保证分摊金额权威准确 |

说明：项目刻意只调用**只读/算价类** Tool，不调用 `create-order` 等写操作工具——
聚餐方案应由所有参与者确认后自行决定是否下单，工具只做决策辅助，不代替用户消费。

## 三、调用流程（真实模式）

```text
用户输入（地址 + 每人预算/忌口/偏好/饮品偏好）
        │
        ▼
① initialize ────────────► 建立 MCP 会话（protocolVersion 2025-03-26）
        │
        ▼
② query-nearby-stores(address) ──► 选定门店 storeCode
        │
        ▼
③ query-meals(storeCode) ──► 拍平为 [{code,name,price,category,tags}]
        │
        ▼
④ list-nutrition-foods() ──► 按名称匹配补全 kcal
        │
        ▼
⑤ query-store-coupons(storeCode) ──► 候选优惠券
        │
        ▼
⑥ 本地规划：个人选品（忌口否决/偏好优先）→ 分享装合并 → 逐券试算选最优
        │
        ▼
⑦ calculate-price(storeCode, items, [coupon]) ──► 官方算价核对总额
        │
        ▼
输出：到人 / 到券 / 到分的完整分单方案（文本或 --json）
```

## 四、业务价值

1. **把原子能力编排成闭环**：单看每个 Tool 都很"碎"（查店、查菜单、查券、算价），
   本项目把它们串成"多人聚餐"这一高频真实场景下的完整决策流。
2. **数据驱动决策**：营养数据（158 个餐品）不是摆设，直接参与"同分取低卡"的
   选品排序；优惠券不是罗列，而是逐张试算后选最优。
3. **诚实优先**：预算不够时明确输出超支警告，而不是硬塞方案；最终金额以
   `calculate-price` 官方算价为准，避免本地估算与真实账单不一致。
4. **可嵌入**：`--json` 输出可直接被其他 Agent / 前端消费，可作为"餐饮场景
   多Agent协作"中的一个决策技能节点。
