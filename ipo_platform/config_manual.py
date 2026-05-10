# -*- coding: utf-8 -*-
"""
手动配置覆盖系统

用途：
1. 当PDF解析失败或数据不完整时，提供手动配置的兜底数据
2. 市场数据（Q1破发率、HSI月度涨跌）的配置和自动获取
3. 各股票的关键字段覆盖（基石数量、保荐人历史业绩等）

优先级：手动配置 > PDF解析数据 > 默认值
"""

from typing import Dict, Optional
from dataclasses import dataclass

# ============================================================
# 市场数据配置（自动更新 + 手动兜底）
# ============================================================

MARKET_DATA = {
    # Q1破发率（季度更新）
    "q1_break_rate_2026": 10.0,  # 2026年Q1港股新股首日破发率
    
    # HSI月度涨跌（月度更新）
    "hsi_monthly_return_2026_04": 3.99,  # 2026年4月恒生指数涨跌幅
    
    # 历史回测参考值
    "avg_first_day_return_2026_ytd": 37.0,  # 年内平均首日回报
    "avg_cumulative_return_2026_ytd": 71.0,  # 年内平均累计涨幅
}

# ============================================================
# 股票手动覆盖配置
# 格式: {stock_code: {field: override_value}}
# 支持的字段见下表
# ============================================================

@dataclass
class StockOverride:
    """股票数据覆盖项"""
    stock_name: Optional[str] = None
    reg_type: Optional[str] = None  # 18A/18C/主板/W股/AH
    
    # 财务数据覆盖（当PDF解析失败时使用）
    revenue_2023: Optional[float] = None
    revenue_2024: Optional[float] = None
    revenue_2025: Optional[float] = None
    net_profit_2023: Optional[float] = None
    net_profit_2024: Optional[float] = None
    net_profit_2025: Optional[float] = None
    
    # 配售结构覆盖
    public_pct: Optional[float] = None
    intl_pct: Optional[float] = None
    price_low: Optional[float] = None
    price_high: Optional[float] = None
    raise_amount: Optional[float] = None
    
    # 基石投资者覆盖（最关键）
    cornerstone_count: Optional[int] = None
    cornerstones: Optional[list] = None  #[{investor_name, amount_hkd, is_star}]
    
    # 稳价覆盖
    stabilizer: Optional[str] = None
    has_greenshoe: Optional[bool] = None
    greenshoe_pct: Optional[float] = None
    
    # 评分备注
    scoring_note: Optional[str] = None


# 手动覆盖数据表（基于已分析股票的准确数据）
STOCK_OVERRIDES: Dict[str, StockOverride] = {
    # 7630.HK 英派药业 — 已手工分析
    "07630.HK": StockOverride(
        stock_name="英派药业-B",
        reg_type="18A",
        revenue_2023=0, revenue_2024=0, revenue_2025=0,
        net_profit_2023=-5.5, net_profit_2024=-4.8, net_profit_2025=-3.2,
        public_pct=5.0, intl_pct=95.0,
        price_low=21.75, price_high=21.75,
        raise_amount=9.13,
        cornerstone_count=13,
        cornerstones=[
            {"investor_name": "腾讯", "amount_hkd": 1.5, "is_star": 1},
            {"investor_name": "LAV", "amount_hkd": 0.8, "is_star": 1},
            {"investor_name": "其他11家机构", "amount_hkd": 2.0, "is_star": 0},
        ],
        stabilizer="高盛",
        has_greenshoe=True,
        scoring_note="18A生物制药，13家基石含腾讯/LAV，亏损收窄中",
    ),
    
    # 7666.HK 剂泰科技 — 已手工分析
    "07666.HK": StockOverride(
        stock_name="剂泰科技",
        reg_type="18C",
        revenue_2023=0.8, revenue_2024=1.2, revenue_2025=1.8,
        net_profit_2023=-2.1, net_profit_2024=-1.5, net_profit_2025=-0.8,
        public_pct=5.0, intl_pct=95.0,
        price_low=10.50, price_high=10.50,
        raise_amount=21.1,
        cornerstone_count=18,
        cornerstones=[
            {"investor_name": "贝莱德", "amount_hkd": 2.0, "is_star": 1},
            {"investor_name": "HHLRA", "amount_hkd": 1.5, "is_star": 1},
            {"investor_name": "Deerfield", "amount_hkd": 1.2, "is_star": 1},
            {"investor_name": "其他15家机构", "amount_hkd": 5.0, "is_star": 0},
        ],
        stabilizer="德意志银行",
        has_greenshoe=True,
        scoring_note="18C AI制药，18家基石含贝莱德/HHLRA/Deerfield",
    ),
    
    # 6871.HK 翼菲智能 — 已手工分析
    "06871.HK": StockOverride(
        stock_name="翼菲智能",
        reg_type="18C",
        # 财务数据已由PDF解析成功，无需覆盖
        # revenue_2023=201.17, revenue_2024=268.01, revenue_2025=387.36,
        # net_profit_2023=-110.61, net_profit_2024=-71.50, net_profit_2025=-152.94,
        public_pct=5.0, intl_pct=95.0,
        price_low=30.50, price_high=30.50,
        raise_amount=8.5,
        cornerstone_count=0,
        cornerstones=[],
        stabilizer=None,
        has_greenshoe=False,
        scoring_note="18C机器人，零基石，无绿鞋，连续三年亏损且2025年亏损扩大",
    ),
    
    # 1236.HK 乐动机器人 — 已手工分析（PDF解析基本成功，补充基石）
    "01236.HK": StockOverride(
        stock_name="乐动机器人",
        reg_type="18C",
        public_pct=5.0, intl_pct=95.0,
        price_low=24.0, price_high=30.0,
        raise_amount=10.0,
        cornerstone_count=3,
        cornerstones=[
            {"investor_name": "美团", "amount_hkd": 0.8, "is_star": 1},
            {"investor_name": "其他2家机构", "amount_hkd": 1.2, "is_star": 0},
        ],
        stabilizer="海通国际",
        has_greenshoe=True,
    ),
    
    # 1187.HK 可孚医疗
    "01187.HK": StockOverride(
        stock_name="可孚医疗",
        reg_type="主板",
        revenue_2023=28.5, revenue_2024=32.1, revenue_2025=38.6,
        net_profit_2023=3.2, net_profit_2024=3.8, net_profit_2025=4.5,
        public_pct=5.0, intl_pct=95.0,
        price_low=39.33, price_high=39.33,
        raise_amount=10.6,
        cornerstone_count=5,
        cornerstones=[
            {"investor_name": "高瓴资本", "amount_hkd": 1.0, "is_star": 1},
            {"investor_name": "其他4家机构", "amount_hkd": 1.5, "is_star": 0},
        ],
        stabilizer="华泰金融",
        has_greenshoe=True,
    ),
    
    # 1609.HK 天星医疗
    "01609.HK": StockOverride(
        stock_name="天星医疗",
        reg_type="主板",
        revenue_2023=2.1, revenue_2024=3.5, revenue_2025=5.2,
        net_profit_2023=-1.2, net_profit_2024=0.3, net_profit_2025=1.1,
        public_pct=5.0, intl_pct=95.0,
        price_low=98.50, price_high=98.50,
        raise_amount=8.29,
        cornerstone_count=6,
        cornerstones=[
            {"investor_name": "GIC", "amount_hkd": 1.2, "is_star": 1},
            {"investor_name": "其他5家机构", "amount_hkd": 2.0, "is_star": 0},
        ],
        stabilizer="中信里昂",
        has_greenshoe=True,
    ),
}


def get_market_data(key: str, default=None):
    """获取市场数据"""
    return MARKET_DATA.get(key, default)


def get_stock_override(stock_code: str) -> Optional[StockOverride]:
    """获取股票手动覆盖配置"""
    return STOCK_OVERRIDES.get(stock_code)


def apply_overrides(stock_code: str, data: dict) -> dict:
    """
    将手动覆盖配置应用到数据字典上
    data: 来自数据库或PDF解析的数据
    返回: 合并后的数据（手动配置优先）
    """
    override = get_stock_override(stock_code)
    if not override:
        return data
    
    # 映射 override 字段到 data 字段
    field_map = {
        'stock_name': 'stock_name',
        'reg_type': 'reg_type',
        'revenue_2023': 'revenue_2023',
        'revenue_2024': 'revenue_2024',
        'revenue_2025': 'revenue_2025',
        'net_profit_2023': 'net_profit_2023',
        'net_profit_2024': 'net_profit_2024',
        'net_profit_2025': 'net_profit_2025',
        'public_pct': 'public_pct',
        'intl_pct': 'intl_pct',
        'price_low': 'price_low',
        'price_high': 'price_high',
        'raise_amount': 'raise_amount',
        'stabilizer': 'stabilizer',
        'has_greenshoe': 'has_greenshoe',
        'greenshoe_pct': 'greenshoe_pct',
    }
    
    result = dict(data)
    for override_field, data_field in field_map.items():
        value = getattr(override, override_field, None)
        if value is not None:
            result[data_field] = value
    
    # 基石投资者特殊处理
    if override.cornerstones is not None:
        result['cornerstones'] = override.cornerstones
        result['cornerstone_count'] = override.cornerstone_count or len(override.cornerstones)
    elif override.cornerstone_count is not None:
        result['cornerstone_count'] = override.cornerstone_count
    
    return result
