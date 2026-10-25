#!/usr/bin/env python3
"""麦麦聚餐参谋 (McParty Planner) —— 麦当劳 MCP 参赛作品

多人聚餐点餐协调 Skill：
  输入每人的预算 / 忌口 / 偏好，自动完成
    查门店(query-nearby-stores) → 拉菜单(query-meals) → 查券(query-store-coupons)
    → 按偏好与营养分配餐品(list-nutrition-foods) → 合并分享装 → 选最优券
    → 官方算价核对(calculate-price) → 输出每人分单明细

用法:
  # 离线演示（无需 Token，使用 fixtures/demo_data.py 示意数据）
  python party_planner.py --demo --people demo_people.json

  # 连接麦当劳 MCP 真实数据
  python party_planner.py --token $MCD_TOKEN --address "北京市海淀区中关村大街1号" --people party.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "fixtures"))

from mcd_mcp_client import McDonaldsMCP, MCPError  # noqa: E402

# ---------------------------------------------------------------------------
# 数据模型: item = {code, name, price(分), category, tags[], kcal}
# ---------------------------------------------------------------------------


def _first(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def normalize_menu(mcp_categories: list[dict]) -> list[dict]:
    """把 MCP query-meals 返回的分类结构拍平为 item 列表（容忍字段名差异）。"""
    items = []
    for cat in mcp_categories or []:
        cat_name = _first(cat, "categoryName", "name", "title", default="未分类")
        for raw in _first(cat, "meals", "items", "products", default=[]):
            price = _first(raw, "price", "salePrice", "currentPrice", "priceCent", default=0)
            price = int(price) if int(price or 0) < 1000 else int(price or 0) // 100  # 分/元自适应
            items.append({
                "code": str(_first(raw, "mealCode", "code", "id", default="")),
                "name": str(_first(raw, "mealName", "name", "title", default="")),
                "price": int(price),
                "category": cat_name,
                "tags": _first(raw, "tags", "labels", default=[]) or [],
                "kcal": None,
            })
    return [i for i in items if i["name"]]


def attach_nutrition(items: list[dict], nutrition: list[dict]) -> None:
    """用 list-nutrition-foods 的数据给 item 补 kcal（按名称匹配）。"""
    lut = {}
    for n in nutrition or []:
        name = _first(n, "name", "foodName")
        energy = _first(n, "energy", "kcal", "energyKcal")
        if name and energy:
            lut[str(name)] = int(energy)
    for it in items:
        if it["kcal"] is None:
            it["kcal"] = lut.get(it["name"]) or lut.get(it["name"].split("(")[0])


def pick_main(items: list[dict], person: dict) -> dict | None:
    """为一个人选主食：忌口标签一票否决；偏好标签命中越多越好；同分取低卡、再取低价。"""
    avoid = {t for t in person.get("avoid", []) if t}
    prefer = {t for t in person.get("prefer", []) if t}
    budget_fen = int(person["budget"] * 100)
    mains = [i for i in items if i["category"] == "主食"]
    ok = [i for i in mains if not (avoid & set(i["tags"])) and i["price"] <= budget_fen]
    if not ok:
        ok = [i for i in mains if not (avoid & set(i["tags"]))]
    if not ok:
        return None
    ok.sort(key=lambda i: (-len(prefer & set(i["tags"])), i["kcal"] or 9999, i["price"]))
    return ok[0]


def pick_drink(items: list[dict], person: dict, budget_fen: int) -> dict | None:
    mode = person.get("drink", "any")
    if mode in ("none", "", None):
        return None
    drinks = [i for i in items if i["category"] == "饮品" and i["price"] <= budget_fen]
    if not drinks:
        return None
    tag = {"cold": "冷", "hot": "热", "any": None}.get(mode)
    prefer = {t for t in person.get("prefer", []) if t}
    if tag:
        cand = [d for d in drinks if tag in d["tags"]] or drinks
    else:
        cand = drinks
    cand.sort(key=lambda i: (-len(prefer & set(i["tags"])), i["price"]))
    return cand[0]


def pick_shared_snack(items: list[dict], people_cost: list[int], budgets_fen: list[int]) -> dict | None:
    """选一份分享装小食：按‘顶饱程度(kcal)’优先，但必须让每个人(自付+分摊)不超预算。"""
    snacks = [i for i in items if i["category"] == "小食" and "分享" in i["tags"]]
    snacks.sort(key=lambda i: (-(i["kcal"] or 0), i["price"]))
    n = max(len(people_cost), 1)
    for s in snacks:
        share = -(-s["price"] // n)  # 向上取整分摊
        if all(c + share <= b for c, b in zip(people_cost, budgets_fen)):
            return s
    return None


def best_coupon(coupons: list[dict], items: list[dict]) -> tuple[dict | None, int]:
    """在‘单券’策略下选优惠最大的一张券，返回 (coupon, 优惠分)。"""
    subtotal = sum(i["price"] for i in items)
    best, best_off = None, 0
    for c in coupons:
        off = 0
        if c.get("type") == "threshold" and subtotal >= int(c.get("threshold", 0)):
            off = int(c.get("off", 0))
        elif c.get("type") == "percent":
            cat_sum = sum(i["price"] for i in items if i["category"] == c.get("category"))
            off = int(cat_sum * (1 - float(c.get("rate", 1))))
        if off > best_off:
            best, best_off = c, off
    return best, best_off


# ---------------------------------------------------------------------------
# 规划主流程
# ---------------------------------------------------------------------------


def plan(menu_items: list[dict], coupons: list[dict], people: list[dict]) -> dict:
    assignments = []
    own_costs, budgets = [], []
    for p in people:
        main = pick_main(menu_items, p)
        budget_fen = int(p["budget"] * 100)
        mine = []
        if main:
            mine.append(main)
        cost = sum(i["price"] for i in mine)
        drink = pick_drink(menu_items, p, budget_fen - cost)
        if drink:
            mine.append(drink)
            cost += drink["price"]
        own_costs.append(cost)
        budgets.append(budget_fen)
        assignments.append({
            "person": p["name"],
            "budget": p["budget"],
            "items": mine,
            "own_cost_fen": cost,
            "kcal": sum(i["kcal"] or 0 for i in mine),
            "warnings": [],
        })
        if not main:
            assignments[-1]["warnings"].append("预算内没有符合忌口的主食，已从全菜单中挑选")

    snack = pick_shared_snack(menu_items, own_costs, budgets)
    snack_share = -(-snack["price"] // len(people)) if snack else 0

    cart = [i for a in assignments for i in a["items"]] + ([snack] if snack else [])
    coupon, coupon_off = best_coupon(coupons, cart)

    subtotal = sum(i["price"] for i in cart)
    total = subtotal - coupon_off
    for a in assignments:
        a["share_fen"] = a["own_cost_fen"] + snack_share
        if a["share_fen"] > a["budget"] * 100:
            a["warnings"].append(f"分摊后 ¥{a['share_fen']/100:.2f} 超预算 ¥{a['budget']:.2f}")

    return {
        "people": assignments,
        "shared_snack": snack,
        "snack_share_fen": snack_share,
        "cart": cart,
        "subtotal_fen": subtotal,
        "coupon": coupon,
        "coupon_off_fen": coupon_off,
        "total_fen": total,
    }


def render(result: dict) -> str:
    lines = []
    lines.append("=" * 56)
    lines.append("🍔 麦麦聚餐参谋 · 分单方案")
    lines.append("=" * 56)
    for a in result["people"]:
        lines.append(f"\n👤 {a['person']}（预算 ¥{a['budget']:.2f}）")
        for i in a["items"]:
            kcal = f"{i['kcal']} kcal" if i["kcal"] else "—"
            lines.append(f"   · {i['name']:<12} ¥{i['price']/100:>6.2f}  {kcal}")
        lines.append(f"   小计 ¥{a['own_cost_fen']/100:.2f}，分摊后 ¥{a['share_fen']/100:.2f}，约 {a['kcal']} kcal")
        for w in a["warnings"]:
            lines.append(f"   ⚠️ {w}")
    s = result["shared_snack"]
    if s:
        lines.append(f"\n🥡 全组合点（不重复买单）: {s['name']} ¥{s['price']/100:.2f}，每人分摊 ¥{result['snack_share_fen']/100:.2f}")
    else:
        lines.append("\n🥡 全组没有装得下分享装小食的预算，本轮不点")
    lines.append(f"\n💰 原价合计 ¥{result['subtotal_fen']/100:.2f}")
    c = result["coupon"]
    if c:
        lines.append(f"🎟️ 最优券: {c['name']}（-¥{result['coupon_off_fen']/100:.2f}）")
    else:
        lines.append("🎟️ 当前没有可用优惠券")
    lines.append(f"✅ 应付合计 ¥{result['total_fen']/100:.2f}")
    lines.append("=" * 56)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 数据源: 演示 fixtures / 真实 MCP
# ---------------------------------------------------------------------------


def load_demo():
    import demo_data as d
    items = []
    for cat in d.DEMO_MENU:
        for i in cat["items"]:
            items.append({**i, "category": cat["category"]})
    attach_nutrition(items, d.DEMO_NUTRITION)
    return d.DEMO_STORE, items, d.DEMO_COUPONS


def load_live(token: str, address: str | None, store_code: str | None):
    mcp = McDonaldsMCP(token)
    mcp.initialize()
    if not store_code:
        stores = mcp.nearby_stores(address)
        if not stores:
            raise MCPError(f"地址 {address} 附近未查到可服务门店")
        store_code = _first(stores[0], "storeCode", "code", "storeId")
        store_name = _first(stores[0], "storeName", "name", default=store_code)
    else:
        store_name = store_code
    menu = mcp.store_menu(store_code)
    items = normalize_menu(menu)
    attach_nutrition(items, mcp.nutrition_foods())
    coupons = mcp.store_coupons(store_code)
    return {"storeCode": store_code, "name": store_name}, items, coupons


def main() -> int:
    ap = argparse.ArgumentParser(description="麦麦聚餐参谋：多人聚餐点餐协调 Skill（麦当劳 MCP）")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--demo", action="store_true", help="离线演示模式（示意数据，无需 Token）")
    src.add_argument("--token", help="麦当劳 MCP Token（https://open.mcd.cn/mcp 申请）")
    ap.add_argument("--address", help="聚餐地址（真实模式必填，用于 query-nearby-stores）")
    ap.add_argument("--store-code", help="直接指定门店编码（跳过地址查询）")
    ap.add_argument("--people", required=True, help="聚餐人员配置 JSON（见 demo_people.json）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args()

    people = json.loads(Path(args.people).read_text(encoding="utf-8"))
    if isinstance(people, dict):
        people = people.get("people", [])

    try:
        if args.demo:
            store, items, coupons = load_demo()
            source = "demo(示意数据)"
        else:
            if not (args.address or args.store_code):
                ap.error("真实模式需要 --address 或 --store-code")
            store, items, coupons = load_live(args.token, args.address, args.store_code)
            source = f"mcd-mcp({store['name']})"
    except (MCPError, ValueError) as e:
        print(f"[错误] {e}", file=sys.stderr)
        return 2

    result = plan(items, coupons, people)
    result["store"] = store
    result["source"] = source
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"📍 门店: {store['name']}    数据源: {source}\n")
        print(render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
