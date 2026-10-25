# 麦麦聚餐参谋 (McParty Planner)

> 多人聚餐点餐协调 Skill —— 基于麦当劳 MCP 能力开发
> 「1024 造物挑战」程序员节应用创作大赛参赛作品

一句话：**把"我想吃这个/我不吃辣/我预算30"翻译成一张不超支、不重复、用对券的麦当劳分单表。**

## 解决什么问题

三五好友聚在一起点麦当劳，最常见的四个痛点：

1. **各说各话**——有人要辣有人忌口，有人要减肥有人要省钱，人工对齐耗时费力；
2. **重复点单**——4 个人点 4 份小食 4 杯饮料，其实一份分享装 + 各自选饮料就够；
3. **优惠券用错**——满减、品类折扣券摆在账户里不会算，手动凑单经常凑亏；
4. **没人知道总账**——分摊到每个人头上到底多少，结账时才算清。

麦麦聚餐参谋把这件事闭环：输入每个人的预算和忌口，输出**到人、到券、到分**的完整方案。

## 目标用户

- 经常组织朋友/同事聚餐点餐的人（"点餐官"角色）
- 对预算敏感、想花明白钱的学生与年轻上班族
- 想控制热量又不得不参加聚餐的人

## 功能特性

- 🎯 **个人偏好分配**：忌口标签一票否决，偏好标签优先匹配，同分取低卡再取低价
- 🥡 **分享装合并**：自动检测"可合并"小食，全组只点一份，费用按人头分摊
- 🎟️ **智能选券**：对购物车评估每张可用券（满减/品类折扣），自动选优惠最大的一张
- 📊 **营养透明**：接入 `list-nutrition-foods` 官方营养数据，每单标注热量
- 💰 **诚实预算**：任何人分摊后超预算都会明确警告（`warnings`），不硬塞方案
- 🔌 **双数据源**：`--demo` 离线演示（示意数据）；`--token` 连接麦当劳 MCP 真实菜单/门店/优惠券/官方算价

## 安装

```bash
git clone https://github.com/<your-name>/mcd-party-planner.git
cd mcd-party-planner
# 零第三方依赖，Python 3.10+ 标准库即可运行
python party_planner.py --demo --people demo_people.json
```

## 使用示例

准备一份人员配置（见 [demo_people.json](demo_people.json)）：

```json
{
  "address": "北京市海淀区中关村大街1号",
  "people": [
    {"name": "小明", "budget": 40, "avoid": ["辣"], "prefer": ["牛肉"], "drink": "cold"},
    {"name": "小红", "budget": 35, "avoid": [], "prefer": ["鸡肉", "不辣"], "drink": "hot"},
    {"name": "阿伟", "budget": 30, "avoid": ["鱼肉"], "prefer": ["辣"], "drink": "none"},
    {"name": "小美", "budget": 45, "avoid": [], "prefer": ["素食", "甜"], "drink": "any"}
  ]
}
```

运行（离线演示）：

```bash
python party_planner.py --demo --people demo_people.json
```

输出：

```text
👤 小明（预算 ¥40.00）
   · 双层吉士堡        ¥ 21.50  480 kcal
   · 可口可乐(中)      ¥  9.00  170 kcal
   小计 ¥30.50，分摊后 ¥32.88，约 650 kcal
...
🥡 全组合点（不重复买单）: 洋葱圈(小) ¥9.50，每人分摊 ¥2.38
💰 原价合计 ¥123.50
🎟️ 最优券: 满60减10（-¥10.00）
✅ 应付合计 ¥113.50
```

连接麦当劳 MCP 真实数据（先在 [open.mcd.cn/mcp](https://open.mcd.cn/mcp) 申请 Token，配置方式见 [mcp-config.example.json](mcp-config.example.json)）：

```bash
export MCD_TOKEN="你的MCP_Token"
python party_planner.py --token "$MCD_TOKEN" --address "北京市海淀区中关村大街1号" --people demo_people.json
# 加 --json 可输出结构化结果，便于接入其他 Agent
```

## 项目结构

```text
mcd-party-planner/
├── party_planner.py        # 主程序：偏好分配 / 分享合并 / 选券 / 渲染
├── mcd_mcp_client.py       # 麦当劳 MCP 极简客户端（Streamable HTTP，零依赖）
├── demo_people.json        # 示例人员配置
├── fixtures/demo_data.py   # 离线演示示意数据（非实时菜单）
├── MCP_INTEGRATION.md      # MCP 接入说明
├── CONTEST_DECLARATION.md  # 参赛声明
└── workbuddy.md            # WorkBuddy 开发记录
```

## 已知边界（诚实声明）

- 演示模式使用 `fixtures/demo_data.py` 中的**示意数据**，与实时菜单/价格无关；
- 选券为单券策略（每次选最优一张），多券叠加规则以门店与 `calculate-price` 实际返回为准；
- 真实模式下最终金额以 MCP `calculate-price` 官方算价为准，本工具的输出用于决策参考，不直接下单。

## License

MIT，见 [LICENSE](LICENSE)。
