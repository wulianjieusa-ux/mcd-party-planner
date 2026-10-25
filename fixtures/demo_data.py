"""演示数据（离线 Demo 模式使用）。

⚠️ 这些数据为**示意数据**，用于在没有 MCP Token 的情况下演示完整规划流程，
不与麦当劳实时菜单/价格绑定。真实使用时请通过 --token 连接麦当劳 MCP
（query-meals / query-store-coupons / list-nutrition-foods / calculate-price）。
"""

# 门店菜单（演示）: categories -> items
# item: code / name / price(分) / tags / kcal
DEMO_STORE = {"storeCode": "DEMO001", "name": "麦麦餐厅(演示店)", "address": "演示地址"}

DEMO_MENU = [
    {
        "category": "主食",
        "items": [
            {"code": "BMC01", "name": "巨无霸", "price": 2350, "tags": ["牛肉", "不辣"], "kcal": 520},
            {"code": "BMC02", "name": "麦辣鸡腿堡", "price": 2150, "tags": ["鸡肉", "辣"], "kcal": 490},
            {"code": "BMC03", "name": "板烧鸡腿堡", "price": 2250, "tags": ["鸡肉", "不辣"], "kcal": 430},
            {"code": "BMC04", "name": "麦香鱼", "price": 2050, "tags": ["鱼肉", "不辣"], "kcal": 380},
            {"code": "BMC05", "name": "双层吉士堡", "price": 2150, "tags": ["牛肉", "不辣"], "kcal": 480},
            {"code": "BMC06", "name": "培根蔬萃双层牛堡", "price": 2550, "tags": ["牛肉", "不辣", "培根"], "kcal": 560},
        ],
    },
    {
        "category": "小食",
        "items": [
            {"code": "SNK01", "name": "薯条(大)", "price": 1350, "tags": ["分享"], "kcal": 430},
            {"code": "SNK02", "name": "薯条(中)", "price": 1150, "tags": ["分享"], "kcal": 320},
            {"code": "SNK03", "name": "麦乐鸡(5块)", "price": 1250, "tags": ["鸡肉", "分享"], "kcal": 260},
            {"code": "SNK04", "name": "玉米杯(小)", "price": 850, "tags": ["素食", "分享"], "kcal": 120},
            {"code": "SNK05", "name": "洋葱圈(小)", "price": 950, "tags": ["素食", "分享"], "kcal": 200},
        ],
    },
    {
        "category": "甜品",
        "items": [
            {"code": "DSR01", "name": "香芋派", "price": 850, "tags": ["甜"], "kcal": 250},
            {"code": "DSR02", "name": "菠萝派", "price": 850, "tags": ["甜"], "kcal": 240},
        ],
    },
    {
        "category": "饮品",
        "items": [
            {"code": "DRK01", "name": "可口可乐(中)", "price": 900, "tags": ["汽水", "冷"], "kcal": 170},
            {"code": "DRK02", "name": "雪碧(中)", "price": 900, "tags": ["汽水", "冷"], "kcal": 160},
            {"code": "DRK03", "name": "鲜橙汁(中)", "price": 1100, "tags": ["果汁", "冷"], "kcal": 150},
            {"code": "DRK04", "name": "热咖啡(美式)", "price": 1200, "tags": ["咖啡", "热"], "kcal": 15},
            {"code": "DRK05", "name": "锡兰红茶(中)", "price": 1000, "tags": ["茶", "热"], "kcal": 90},
        ],
    },
]

# 门店可用优惠券（演示）
# type: threshold(满X减Y) / percent(品类Z折)
DEMO_COUPONS = [
    {"id": "C001", "name": "满40减5", "type": "threshold", "threshold": 4000, "off": 500},
    {"id": "C002", "name": "小食类8折", "type": "percent", "category": "小食", "rate": 0.8},
    {"id": "C003", "name": "满60减10", "type": "threshold", "threshold": 6000, "off": 1000},
]

# 餐品营养（演示，与 list-nutrition-foods 对齐的字段）
DEMO_NUTRITION = [
    {"name": "巨无霸", "energy": 520, "protein": 25, "fat": 27, "carbohydrate": 42, "sodium": 1010},
    {"name": "麦辣鸡腿堡", "energy": 490, "protein": 24, "fat": 24, "carbohydrate": 45, "sodium": 980},
    {"name": "板烧鸡腿堡", "energy": 430, "protein": 27, "fat": 17, "carbohydrate": 40, "sodium": 860},
    {"name": "麦香鱼", "energy": 380, "protein": 17, "fat": 16, "carbohydrate": 42, "sodium": 640},
    {"name": "双层吉士堡", "energy": 480, "protein": 27, "fat": 25, "carbohydrate": 40, "sodium": 1090},
    {"name": "薯条(大)", "energy": 430, "protein": 5, "fat": 20, "carbohydrate": 55, "sodium": 330},
    {"name": "麦乐鸡(5块)", "energy": 260, "protein": 14, "fat": 15, "carbohydrate": 19, "sodium": 560},
]
