# -*- coding: utf-8 -*-
"""
初始化数据脚本
把前两周手工分析的IPO数据导入数据库，作为平台启动的基础数据
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ipo_platform.models.database import get_db

# ============================================================
# 已分析的IPO基础数据
# ============================================================

IPO_BASE_DATA = [
    # 5月招股/上市
    {
        'stock_code': '07630.HK', 'stock_name': '英派药业-B', 'industry': '生物医药', 'industry_cat': '医疗健康',
        'reg_type': '18A', 'sponsor': '高盛,中金', 'sponsor_primary': '高盛',
        'ipo_start_date': '20260430', 'ipo_end_date': '20260507', 'list_date': '20260513',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 21.75, 'price_high': 21.75,
        'raise_amount': 9.13, 'stabilizer': '高盛', 'has_greenshoe': 1,
        'status': 'ipoing',
    },
    {
        'stock_code': '07666.HK', 'stock_name': '剂泰科技', 'industry': 'AI制药', 'industry_cat': '医疗健康',
        'reg_type': '18C', 'sponsor': '富瑞金融,德意志银行,中信里昂', 'sponsor_primary': '富瑞金融',
        'ipo_start_date': '20260430', 'ipo_end_date': '20260507', 'list_date': '20260513',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 10.50, 'price_high': 10.50,
        'raise_amount': 21.1, 'stabilizer': '德意志银行', 'has_greenshoe': 1,
        'status': 'ipoing',
    },
    {
        'stock_code': '06871.HK', 'stock_name': '翼菲智能', 'industry': '机器人', 'industry_cat': '硬科技',
        'reg_type': '18C', 'sponsor': '中金,中信建投', 'sponsor_primary': '中金',
        'ipo_start_date': '20260505', 'ipo_end_date': '20260508', 'list_date': '20260515',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 30.50, 'price_high': 30.50,
        'raise_amount': 8.5, 'stabilizer': None, 'has_greenshoe': 0,
        'status': 'ipoing',
    },

    {
        'stock_code': '01187.HK', 'stock_name': '可孚医疗', 'industry': '医疗器械', 'industry_cat': '医疗健康',
        'reg_type': '主板', 'sponsor': '华泰金融,法国巴黎', 'sponsor_primary': '华泰金融',
        'ipo_start_date': '20260427', 'ipo_end_date': '20260429', 'list_date': '20260506',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 39.33, 'price_high': 39.33,
        'raise_amount': 10.6, 'stabilizer': '华泰金融', 'has_greenshoe': 1,
        'status': 'ipoing',
    },
    {
        'stock_code': '01609.HK', 'stock_name': '天星医疗', 'industry': '医疗器械', 'industry_cat': '医疗健康',
        'reg_type': '主板', 'sponsor': '中信里昂,建银国际', 'sponsor_primary': '中信里昂',
        'ipo_start_date': '20260424', 'ipo_end_date': '20260428', 'list_date': '20260505',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 98.50, 'price_high': 98.50,
        'raise_amount': 8.29, 'stabilizer': '中信里昂', 'has_greenshoe': 1,
        'status': 'ipoing',
    },
    {
        'stock_code': '01236.HK', 'stock_name': '乐动机器人', 'industry': '机器人', 'industry_cat': '硬科技',
        'reg_type': '18C', 'sponsor': '海通国际,国泰君安,中金', 'sponsor_primary': '海通国际',
        'ipo_start_date': '20260430', 'ipo_end_date': '20260505', 'list_date': '20260511',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 24.00, 'price_high': 30.00,
        'raise_amount': 10.0, 'stabilizer': '海通国际', 'has_greenshoe': 1,
        'status': 'ipoing',
    },
    # 4月已上市
    {
        'stock_code': '06656.HK', 'stock_name': '思格新能', 'industry': '新能源/储能', 'industry_cat': '硬科技',
        'reg_type': '18C', 'sponsor': '中信证券,法国巴黎银行', 'sponsor_primary': '中信证券',
        'list_date': '20260416',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 324.20, 'price_high': 324.20, 'offer_price': 324.20,
        'raise_amount': 44.0, 'stabilizer': '中信里昂', 'has_greenshoe': 1,
        'status': 'listed',
    },
    {
        'stock_code': '00068.HK', 'stock_name': '群核科技', 'industry': '软件服务/云设计', 'industry_cat': 'AI/软件',
        'reg_type': '主板', 'sponsor': 'J.P. Morgan,建银国际', 'sponsor_primary': 'J.P. Morgan',
        'list_date': '20260417',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 6.72, 'price_high': 7.62, 'offer_price': 7.62,
        'raise_amount': 12.2, 'stabilizer': 'J.P. Morgan', 'has_greenshoe': 1,
        'status': 'listed',
    },
    {
        'stock_code': '03277.HK', 'stock_name': '长光辰芯', 'industry': '半导体/CIS芯片', 'industry_cat': '硬科技',
        'reg_type': '主板', 'sponsor': '中信证券,国泰君安', 'sponsor_primary': '中信证券',
        'list_date': '20260417',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 39.88, 'price_high': 39.88, 'offer_price': 39.88,
        'raise_amount': 26.0, 'stabilizer': '中信证券', 'has_greenshoe': 1,
        'status': 'listed',
    },
    {
        'stock_code': '02476.HK', 'stock_name': '胜宏科技', 'industry': 'PCB/AI算力硬件', 'industry_cat': '硬科技',
        'reg_type': 'AH', 'sponsor': 'J.P. Morgan,中信建投,广发证券', 'sponsor_primary': 'J.P. Morgan',
        'list_date': '20260421',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 209.88, 'price_high': 209.88, 'offer_price': 209.88,
        'raise_amount': 174.9, 'stabilizer': '摩根大通', 'has_greenshoe': 1,
        'status': 'listed',
    },
    {
        'stock_code': '03296.HK', 'stock_name': '华勤技术', 'industry': 'ODM/智能硬件', 'industry_cat': '硬科技',
        'reg_type': 'AH', 'sponsor': '中金,美林', 'sponsor_primary': '中金',
        'list_date': '20260423',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 77.70, 'price_high': 77.70, 'offer_price': 77.70,
        'raise_amount': 45.5, 'stabilizer': '中金', 'has_greenshoe': 1,
        'status': 'listed',
    },
    {
        'stock_code': '01879.HK', 'stock_name': '曦智科技-P', 'industry': '光互连/硅光芯片', 'industry_cat': '硬科技',
        'reg_type': '18C', 'sponsor': '中金,海通国际', 'sponsor_primary': '中金',
        'list_date': '20260428',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 166.60, 'price_high': 183.20, 'offer_price': 183.20,
        'raise_amount': 25.3, 'stabilizer': '中金', 'has_greenshoe': 1,
        'status': 'listed',
    },
    {
        'stock_code': '02493.HK', 'stock_name': '迈威生物-B', 'industry': '生物医药', 'industry_cat': '医疗健康',
        'reg_type': '18A', 'sponsor': '中信里昂,海通国际,兴证国际,招银国际', 'sponsor_primary': '中信里昂',
        'list_date': '20260428',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 27.64, 'price_high': 30.71, 'offer_price': 27.64,
        'raise_amount': 14.4, 'stabilizer': '中信里昂', 'has_greenshoe': 1,
        'status': 'listed',
    },
    {
        'stock_code': '06810.HK', 'stock_name': '商米科技-W', 'industry': '商用IoT/支付终端', 'industry_cat': '硬科技',
        'reg_type': 'W股', 'sponsor': '德意志银行,中信里昂,农银国际', 'sponsor_primary': '德意志银行',
        'list_date': '20260429',
        'public_pct': 5, 'intl_pct': 95, 'price_low': 24.86, 'price_high': 24.86, 'offer_price': 24.86,
        'raise_amount': 10.6, 'stabilizer': '德意志银行', 'has_greenshoe': 1,
        'status': 'listed',
    },
]

# 财务数据
IPO_FINANCIALS = {
    '07630.HK': {'revenue_2023': 0, 'revenue_2024': 0, 'revenue_2025': 0, 'net_profit_2023': -5.5, 'net_profit_2024': -4.8, 'net_profit_2025': -3.2},
    '07666.HK': {'revenue_2023': 0.8, 'revenue_2024': 1.2, 'revenue_2025': 1.8, 'net_profit_2023': -2.1, 'net_profit_2024': -1.5, 'net_profit_2025': -0.8},
    '06871.HK': {'revenue_2023': 201.17, 'revenue_2024': 268.01, 'revenue_2025': 387.36, 'net_profit_2023': -110.61, 'net_profit_2024': -71.50, 'net_profit_2025': -152.94},

    '01187.HK': {'revenue_2023': 28.5, 'revenue_2024': 32.1, 'revenue_2025': 38.6, 'net_profit_2023': 3.2, 'net_profit_2024': 3.8, 'net_profit_2025': 4.5},
    '01609.HK': {'revenue_2023': 2.1, 'revenue_2024': 3.5, 'revenue_2025': 5.2, 'net_profit_2023': -1.2, 'net_profit_2024': 0.3, 'net_profit_2025': 1.1},
    '01236.HK': {'revenue_2023': 1.5, 'revenue_2024': 2.8, 'revenue_2025': 4.2, 'net_profit_2023': -0.5, 'net_profit_2024': -0.3, 'net_profit_2025': 0.1},
    # 4月上市（简化数据）
    '06656.HK': {'revenue_2023': 15.2, 'revenue_2024': 28.6, 'revenue_2025': 42.3, 'net_profit_2023': -2.1, 'net_profit_2024': -0.8, 'net_profit_2025': 1.5},
    '00068.HK': {'revenue_2023': 5.8, 'revenue_2024': 7.2, 'revenue_2025': 9.1, 'net_profit_2023': -1.5, 'net_profit_2024': -0.9, 'net_profit_2025': -0.3},
    '03277.HK': {'revenue_2023': 8.5, 'revenue_2024': 12.3, 'revenue_2025': 18.6, 'net_profit_2023': 0.8, 'net_profit_2024': 1.5, 'net_profit_2025': 2.3},
    '02476.HK': {'revenue_2023': 85.2, 'revenue_2024': 128.6, 'revenue_2025': 185.3, 'net_profit_2023': 8.5, 'net_profit_2024': 15.2, 'net_profit_2025': 22.8},
    '03296.HK': {'revenue_2023': 852.1, 'revenue_2024': 928.5, 'revenue_2025': 1025.3, 'net_profit_2023': 25.8, 'net_profit_2024': 28.6, 'net_profit_2025': 32.1},
    '01879.HK': {'revenue_2023': 0.5, 'revenue_2024': 1.2, 'revenue_2025': 3.8, 'net_profit_2023': -8.5, 'net_profit_2024': -10.2, 'net_profit_2025': -13.42},
    '02493.HK': {'revenue_2023': 1.2, 'revenue_2024': 2.8, 'revenue_2025': 4.5, 'net_profit_2023': -3.5, 'net_profit_2024': -3.2, 'net_profit_2025': -2.8},
    '06810.HK': {'revenue_2023': 12.5, 'revenue_2024': 15.8, 'revenue_2025': 18.2, 'net_profit_2023': -2.1, 'net_profit_2024': -1.5, 'net_profit_2025': -0.8},
}

# 基石投资者
IPO_CORNERSTONES = {
    '07630.HK': [
        {'investor_name': '腾讯', 'amount_hkd': 1.5, 'is_star': 1},
        {'investor_name': 'LAV', 'amount_hkd': 0.8, 'is_star': 1},
        {'investor_name': '其他11家', 'amount_hkd': 2.0, 'is_star': 0},
    ],
    '07666.HK': [
        {'investor_name': '贝莱德', 'amount_hkd': 2.0, 'is_star': 1},
        {'investor_name': 'HHLRA', 'amount_hkd': 1.5, 'is_star': 1},
        {'investor_name': 'Deerfield', 'amount_hkd': 1.2, 'is_star': 1},
        {'investor_name': '其他15家', 'amount_hkd': 5.0, 'is_star': 0},
    ],
    '06871.HK': [],  # 零基石，触发黑名单
    '01187.HK': [
        {'investor_name': '高瓴资本', 'amount_hkd': 1.0, 'is_star': 1},
        {'investor_name': '其他4家', 'amount_hkd': 1.5, 'is_star': 0},
    ],
    '01609.HK': [
        {'investor_name': 'GIC', 'amount_hkd': 1.2, 'is_star': 1},
        {'investor_name': '其他5家', 'amount_hkd': 2.0, 'is_star': 0},
    ],
    '01236.HK': [
        {'investor_name': '美团', 'amount_hkd': 0.8, 'is_star': 1},
        {'investor_name': '其他3家', 'amount_hkd': 1.2, 'is_star': 0},
    ],
    '01879.HK': [
        {'investor_name': '阿里巴巴', 'amount_hkd': 3.0, 'is_star': 1},
        {'investor_name': 'GIC', 'amount_hkd': 2.0, 'is_star': 1},
        {'investor_name': '贝莱德', 'amount_hkd': 1.5, 'is_star': 1},
        {'investor_name': '富达国际', 'amount_hkd': 1.5, 'is_star': 1},
        {'investor_name': '其他16家', 'amount_hkd': 6.0, 'is_star': 0},
    ],
    '02493.HK': [
        {'investor_name': '高瓴资本', 'amount_hkd': 1.0, 'is_star': 1},
        {'investor_name': '其他7家', 'amount_hkd': 3.0, 'is_star': 0},
    ],
}

# 上市后表现（4月上市股票）
POST_LISTING_DATA = {
    '06656.HK': {'list_date': '20260416', 'd1_open': 600.0, 'd1_high': 680.0, 'd1_low': 580.0, 'd1_close': 659.0, 'd1_return': 103.42, 'd1_volume': 1500000},
    '00068.HK': {'list_date': '20260417', 'd1_open': 15.0, 'd1_high': 20.0, 'd1_low': 14.5, 'd1_close': 18.6, 'd1_return': 144.09, 'd1_volume': 50000000},
    '03277.HK': {'list_date': '20260417', 'd1_open': 65.0, 'd1_high': 72.0, 'd1_low': 62.0, 'd1_close': 70.0, 'd1_return': 75.53, 'd1_volume': 8000000},
    '02476.HK': {'list_date': '20260421', 'd1_open': 330.0, 'd1_high': 336.2, 'd1_low': 302.0, 'd1_close': 315.0, 'd1_return': 50.09, 'd1_volume': 50000000},
    '03296.HK': {'list_date': '20260423', 'd1_open': 87.5, 'd1_high': 90.95, 'd1_low': 85.0, 'd1_close': 88.0, 'd1_return': 13.26, 'd1_volume': 24000000},
    '01879.HK': {'list_date': '20260428', 'd1_open': 880.0, 'd1_high': 996.0, 'd1_low': 850.0, 'd1_close': 886.0, 'd1_return': 383.62, 'd1_volume': 8000000},
    '02493.HK': {'list_date': '20260428', 'd1_open': 28.3, 'd1_high': 28.5, 'd1_low': 26.5, 'd1_close': 27.8, 'd1_return': 0.58, 'd1_volume': 12000000},
    '06810.HK': {'list_date': '20260429', 'd1_open': 80.0, 'd1_high': 90.0, 'd1_low': 75.0, 'd1_close': 84.8, 'd1_return': 241.11, 'd1_volume': 15000000},
}


def init_database():
    """初始化数据库并导入所有基础数据"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from ipo_platform.config_manual import STOCK_OVERRIDES
    
    db = get_db()
    
    print("="*60)
    print(" 港股IPO数据平台 — 数据初始化")
    print("="*60)
    
    # 1. 导入IPO基础信息
    print(f"\n【导入IPO基础信息】共 {len(IPO_BASE_DATA)} 只")
    for ipo in IPO_BASE_DATA:
        db.execute("""
            INSERT OR REPLACE INTO ipo_base 
            (stock_code, stock_name, industry, industry_cat, reg_type, sponsor, sponsor_primary,
             ipo_start_date, ipo_end_date, list_date, public_pct, intl_pct,
             price_low, price_high, offer_price, raise_amount,
             stabilizer, has_greenshoe, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ipo['stock_code'], ipo['stock_name'], ipo['industry'], ipo['industry_cat'],
            ipo['reg_type'], ipo['sponsor'], ipo['sponsor_primary'],
            ipo.get('ipo_start_date'), ipo.get('ipo_end_date'), ipo.get('list_date'),
            ipo['public_pct'], ipo['intl_pct'], ipo['price_low'], ipo['price_high'],
            ipo.get('offer_price'), ipo['raise_amount'],
            ipo['stabilizer'], int(ipo['has_greenshoe']), ipo['status']
        ))
        print(f"   ✅ {ipo['stock_code']} {ipo['stock_name']}")
    
    # 2. 导入财务数据
    print(f"\n【导入财务数据】共 {len(IPO_FINANCIALS)} 只")
    for code, fin in IPO_FINANCIALS.items():
        db.execute("""
            INSERT OR REPLACE INTO ipo_financials
            (stock_code, revenue_2023, revenue_2024, revenue_2025,
             net_profit_2023, net_profit_2024, net_profit_2025)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, fin['revenue_2023'], fin['revenue_2024'], fin['revenue_2025'],
              fin['net_profit_2023'], fin['net_profit_2024'], fin['net_profit_2025']))
    print(f"   ✅ 完成")
    
    # 3. 导入基石投资者
    print(f"\n【导入基石投资者】")
    total_cs = 0
    for code, cs_list in IPO_CORNERSTONES.items():
        # 先清空该股票的旧记录（防止重复运行）
        db.execute("DELETE FROM ipo_cornerstones WHERE stock_code = ?", (code,))
        for cs in cs_list:
            db.execute("""
                INSERT INTO ipo_cornerstones (stock_code, investor_name, amount_hkd, is_star)
                VALUES (?, ?, ?, ?)
            """, (code, cs['investor_name'], cs['amount_hkd'], int(cs['is_star'])))
            total_cs += 1
    print(f"   ✅ 共 {total_cs} 条记录")
    
    # 4. 导入上市后表现
    print(f"\n【导入上市后表现】共 {len(POST_LISTING_DATA)} 只")
    for code, post in POST_LISTING_DATA.items():
        db.execute("""
            INSERT OR REPLACE INTO post_listing
            (stock_code, list_date, d1_open, d1_high, d1_low, d1_close, d1_return, d1_volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (code, post['list_date'], post['d1_open'], post['d1_high'],
              post['d1_low'], post['d1_close'], post['d1_return'], post['d1_volume']))
    print(f"   ✅ 完成")
    
    # 5. 应用config_manual覆盖（确保数据库数据与手动配置一致）
    print(f"\n【应用手动覆盖配置】共 {len(STOCK_OVERRIDES)} 只")
    for code, override in STOCK_OVERRIDES.items():
        # 覆盖ipo_base
        update_fields = []
        update_vals = []
        if override.stock_name:
            update_fields.append("stock_name = ?")
            update_vals.append(override.stock_name)
        if override.reg_type:
            update_fields.append("reg_type = ?")
            update_vals.append(override.reg_type)
        if override.public_pct is not None:
            update_fields.append("public_pct = ?")
            update_vals.append(override.public_pct)
        if override.intl_pct is not None:
            update_fields.append("intl_pct = ?")
            update_vals.append(override.intl_pct)
        if override.price_low is not None:
            update_fields.append("price_low = ?")
            update_vals.append(override.price_low)
        if override.price_high is not None:
            update_fields.append("price_high = ?")
            update_vals.append(override.price_high)
        if override.raise_amount is not None:
            update_fields.append("raise_amount = ?")
            update_vals.append(override.raise_amount)
        if override.stabilizer is not None:
            update_fields.append("stabilizer = ?")
            update_vals.append(override.stabilizer)
        if override.has_greenshoe is not None:
            update_fields.append("has_greenshoe = ?")
            update_vals.append(int(override.has_greenshoe))
        
        if update_fields:
            sql = f"UPDATE ipo_base SET {', '.join(update_fields)} WHERE stock_code = ?"
            db.execute(sql, update_vals + [code])
        
        # 覆盖ipo_financials
        fin_fields = []
        fin_vals = []
        if override.revenue_2023 is not None:
            fin_fields.append("revenue_2023 = ?")
            fin_vals.append(override.revenue_2023)
        if override.revenue_2024 is not None:
            fin_fields.append("revenue_2024 = ?")
            fin_vals.append(override.revenue_2024)
        if override.revenue_2025 is not None:
            fin_fields.append("revenue_2025 = ?")
            fin_vals.append(override.revenue_2025)
        if override.net_profit_2023 is not None:
            fin_fields.append("net_profit_2023 = ?")
            fin_vals.append(override.net_profit_2023)
        if override.net_profit_2024 is not None:
            fin_fields.append("net_profit_2024 = ?")
            fin_vals.append(override.net_profit_2024)
        if override.net_profit_2025 is not None:
            fin_fields.append("net_profit_2025 = ?")
            fin_vals.append(override.net_profit_2025)
        
        if fin_fields:
            # 先检查是否存在记录
            exists = db.fetchone("SELECT 1 FROM ipo_financials WHERE stock_code = ?", (code,))
            if exists:
                sql = f"UPDATE ipo_financials SET {', '.join(fin_fields)} WHERE stock_code = ?"
                db.execute(sql, fin_vals + [code])
            else:
                # 插入新记录（其他字段为NULL）
                placeholders = ', '.join(['?'] * (len(fin_vals) + 1))
                cols = ['stock_code'] + [f.split(' = ')[0].strip() for f in fin_fields]
                sql = f"INSERT INTO ipo_financials ({', '.join(cols)}) VALUES ({placeholders})"
                db.execute(sql, [code] + fin_vals)
        
        # 覆盖ipo_cornerstones
        if override.cornerstones is not None:
            db.execute("DELETE FROM ipo_cornerstones WHERE stock_code = ?", (code,))
            for cs in override.cornerstones:
                db.execute("""
                    INSERT INTO ipo_cornerstones (stock_code, investor_name, amount_hkd, is_star)
                    VALUES (?, ?, ?, ?)
                """, (code, cs.get('investor_name', cs.get('name', '')), 
                      cs.get('amount_hkd', 0), int(cs.get('is_star', 0))))
        
        print(f"   ✅ {code} {override.stock_name or ''}")
    
    print("\n" + "="*60)
    print(" ✅ 数据初始化完成")
    print("="*60)


def run_scoring():
    """对所有IPO运行评分引擎"""
    from ipo_platform.core.scorer import IPOScorer
    
    print("\n【自动评分】")
    scorer = IPOScorer()
    db = get_db()
    
    codes = db.fetchall("SELECT stock_code FROM ipo_base")
    for row in codes:
        code = row['stock_code']
        try:
            result = scorer.calculate(code, q1_break_rate=10.0, hsi_return=3.99)
            print(f"   {code}: {result['total_score']}/110 [{result['category']}]")
        except Exception as e:
            print(f"   {code}: 评分失败 - {e}")
    
    print("\n✅ 评分完成")


if __name__ == '__main__':
    init_database()
    run_scoring()
