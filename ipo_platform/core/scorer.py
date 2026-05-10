# -*- coding: utf-8 -*-
"""
IPO评分引擎 V2

升级点：
1. 基于数据库结构化数据自动评分（非手工输入）
2. 引入动态权重（根据市场环境调整）
3. 纳入情绪因子（超购倍数）
4. 证据链自动记录（评分依据+页码）
5. 回测接口（与实际表现对比）
"""

import json
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ipo_platform.models.database import get_db
from ipo_platform.config_manual import (
    get_market_data, 
    apply_overrides,
    STOCK_OVERRIDES
)


class IPOScorer:
    """
    7维度IPO评分引擎
    总分110分 = 基础100分 + 稳价奖励10分
    """
    
    def __init__(self):
        self.db = get_db()
        self.rules = self._load_rules()
    
    def _load_rules(self):
        """评分规则（可从数据库或配置文件加载，实现动态调整）"""
        return {
            'profitability': {
                'max': 30,
                'tiers': [
                    (30, '连续三年盈利且增长', lambda p: p['np_2025'] > 0 and p['np_2024'] > 0 and p['np_2023'] > 0 and p['revenue_growth'] > 0),
                    (20, '最近一年盈利', lambda p: p['np_2025'] > 0),
                    (10, '亏损但收窄', lambda p: p['np_2025'] < 0 and p['np_2025'] > p['np_2024']),
                    (5,  '亏损扩大', lambda p: p['np_2025'] < 0 and p['np_2025'] <= p['np_2024']),
                    (0,  '严重亏损/无数据', lambda p: True),
                ]
            },
            'allocation': {
                'max': 10,
                'tiers': [
                    (10, '机制B（公开发售5%）', lambda a: a['public_pct'] <= 5),
                    (7,  '机制A标准回拨', lambda a: 5 < a['public_pct'] <= 10),
                    (4,  '高回拨比例', lambda a: a['public_pct'] > 10),
                    (0,  '未知', lambda a: True),
                ]
            },
            'cornerstone': {
                'max': 15,
                'tiers': [
                    (15, '≥10家基石或顶级机构领投', lambda c: c['count'] >= 10 or c['has_star_lead']),
                    (12, '5-9家基石', lambda c: 5 <= c['count'] < 10),
                    (8,  '3-4家基石', lambda c: 3 <= c['count'] < 5),
                    (3,  '1-2家基石', lambda c: 1 <= c['count'] < 3),
                    (0,  '零基石', lambda c: c['count'] == 0),
                ]
            },
            'pricing': {
                'max': 20,
                'tiers': [
                    (20, '估值显著折价', lambda p: p['valuation_discount'] > 20),
                    (15, '合理估值', lambda p: -10 <= p['valuation_discount'] <= 20),
                    (10, '估值偏高', lambda p: p['valuation_discount'] < -10),
                    (10, '亏损企业（无PE）', lambda p: p['is_loss_making']),
                    (0,  '数据不足', lambda p: True),
                ]
            },
            'stabilization': {
                'max': 10,
                'tiers': [
                    (10, '有绿鞋+知名稳价人', lambda s: s['has_greenshoe'] and s['stabilizer_tier'] == 'top'),
                    (7,  '有绿鞋', lambda s: s['has_greenshoe']),
                    (4,  '有稳价人无绿鞋', lambda s: s['stabilizer'] and not s['has_greenshoe']),
                    (0,  '无稳价/无绿鞋', lambda s: True),
                ]
            },
            'q1_break_rate': {
                'max': 15,
                'tiers': [
                    (15, '破发率<15%', lambda q: q < 15),
                    (10, '破发率15-25%', lambda q: 15 <= q < 25),
                    (5,  '破发率25-35%', lambda q: 25 <= q < 35),
                    (0,  '破发率>35%', lambda q: q >= 35),
                ]
            },
            'hsi_monthly': {
                'max': 10,
                'tiers': [
                    (10, 'HSI月度涨幅>3%', lambda h: h > 3),
                    (7,  'HSI月度涨幅0-3%', lambda h: 0 <= h <= 3),
                    (4,  'HSI月度跌幅<5%', lambda h: -5 <= h < 0),
                    (0,  'HSI月度跌幅>5%', lambda h: h < -5),
                ]
            },
        }
    
    # -----------------------------------------------------------
    # 数据加载
    # -----------------------------------------------------------
    
    def load_ipo_data(self, stock_code: str) -> Dict:
        """从数据库加载IPO全部数据，并应用手动覆盖配置"""
        base = self.db.fetchone("SELECT * FROM ipo_base WHERE stock_code = ?", (stock_code,))
        financials = self.db.fetchone("SELECT * FROM ipo_financials WHERE stock_code = ?", (stock_code,))
        cornerstones = self.db.fetchall("SELECT * FROM ipo_cornerstones WHERE stock_code = ?", (stock_code,))
        sentiment = self.db.fetchone(
            "SELECT * FROM market_sentiment WHERE stock_code = ? ORDER BY record_date DESC, record_time DESC LIMIT 1",
            (stock_code,)
        )
        
        data = {
            'stock_code': stock_code,
            'base': dict(base) if base else {},
            'financials': dict(financials) if financials else {},
            'cornerstones': [dict(c) for c in cornerstones],
            'sentiment': dict(sentiment) if sentiment else {},
        }
        
        # 应用手动覆盖配置（优先级：手动 > 数据库 > 默认值）
        if stock_code in STOCK_OVERRIDES:
            # 合并base数据
            merged_base = apply_overrides(stock_code, data['base'])
            data['base'] = merged_base
            
            # 合并financials数据
            merged_fin = apply_overrides(stock_code, data['financials'])
            data['financials'] = merged_fin
            
            # 合并cornerstones数据（手动配置优先）
            override = STOCK_OVERRIDES[stock_code]
            if override.cornerstones is not None:
                data['cornerstones'] = override.cornerstones
        
        return data
    
    # -----------------------------------------------------------
    # 各维度评分
    # -----------------------------------------------------------
    
    def score_profitability(self, data: Dict) -> Tuple[int, str, Dict]:
        """盈利维度 0-30分"""
        fin = data.get('financials', {})
        base = data.get('base', {})
        
        np_2023 = fin.get('net_profit_2023', 0)
        np_2024 = fin.get('net_profit_2024', 0)
        np_2025 = fin.get('net_profit_2025', 0)
        rev_2025 = fin.get('revenue_2025', 0) or 0
        rev_2024 = fin.get('revenue_2024', 0) or 0
        
        # 判断是否所有利润数据都缺失（None或0）
        # 注意：0可能是真实的零利润，但连续3年0利润极其罕见
        all_none = all(v is None or v == 0 for v in [np_2023, np_2024, np_2025])
        reg_type = base.get('reg_type', '')
        
        revenue_growth = 0
        if rev_2024 and rev_2024 != 0:
            revenue_growth = (rev_2025 / rev_2024 - 1) * 100
        
        params = {
            'np_2023': np_2023 or 0, 'np_2024': np_2024 or 0, 'np_2025': np_2025 or 0,
            'revenue_growth': revenue_growth,
        }
        
        for score, desc, check in self.rules['profitability']['tiers']:
            if check(params):
                evidence = {
                    'revenue_2023': fin.get('revenue_2023'),
                    'revenue_2024': fin.get('revenue_2024'),
                    'revenue_2025': rev_2025,
                    'net_profit_2023': np_2023,
                    'net_profit_2024': np_2024,
                    'net_profit_2025': np_2025,
                    'revenue_growth_pct': round(params['revenue_growth'], 1),
                    'data_source': 'manual_override' if data.get('stock_code') in STOCK_OVERRIDES and any(
                        getattr(STOCK_OVERRIDES[data['stock_code']], f'net_profit_{y}', None) is not None 
                        for y in [2023, 2024, 2025]
                    ) else 'database',
                }
                # 修复：当所有利润数据缺失时，18A/18C给最低档5分，而非0分
                if all_none and score == 0:
                    if reg_type in ('18A', '18C'):
                        score = 5
                        desc = '18A/18C特专科技，无盈利数据（默认最低档）'
                    else:
                        score = 0
                        desc = '严重亏损/无数据'
                return score, desc, evidence
        
        return 0, '未匹配任何规则', {}
    
    def score_allocation(self, data: Dict) -> Tuple[int, str, Dict]:
        """分配维度 0-10分"""
        base = data.get('base', {})
        public_pct = base.get('public_pct', 0) or 0
        
        params = {'public_pct': public_pct}
        
        for score, desc, check in self.rules['allocation']['tiers']:
            if check(params):
                evidence = {
                    'public_offer_pct': public_pct,
                    'intl_offer_pct': base.get('intl_pct'),
                    'total_shares': base.get('total_shares'),
                }
                return score, desc, evidence
        
        return 0, '未匹配', {}
    
    def score_cornerstone(self, data: Dict) -> Tuple[int, str, Dict]:
        """基石维度 0-15分"""
        cs_list = data.get('cornerstones', [])
        count = len(cs_list)
        has_star = any(c.get('is_star', 0) for c in cs_list)
        total_amount = sum(c.get('amount_hkd', 0) or 0 for c in cs_list)
        star_names = [c['investor_name'] for c in cs_list if c.get('is_star')]
        
        params = {
            'count': count,
            'has_star_lead': has_star,
            'total_amount_hkd': round(total_amount, 2),
        }
        
        for score, desc, check in self.rules['cornerstone']['tiers']:
            if check(params):
                evidence = {
                    'cornerstone_count': count,
                    'cornerstone_list': [c['investor_name'] for c in cs_list],
                    'star_investors': star_names,
                    'total_amount_hkd': total_amount,
                }
                return score, desc, evidence
        
        return 0, '未匹配', {}
    
    def score_pricing(self, data: Dict) -> Tuple[int, str, Dict]:
        """定价维度 0-20分"""
        base = data.get('base', {})
        fin = data.get('financials', {})
        
        np_2025 = fin.get('net_profit_2025', 0) or 0
        is_loss = np_2025 < 0
        
        # 简化：用发行价中位数 vs 招股价区间判断
        price_low = base.get('price_low', 0) or 0
        price_high = base.get('price_high', 0) or 0
        offer_price = base.get('offer_price')
        
        # 如果有最终定价，看落在区间的位置
        if offer_price and price_low and price_high:
            if price_high > price_low:
                price_position = (offer_price - price_low) / (price_high - price_low) * 100
            else:
                price_position = 50  # 固定定价，取中位
            discount = 100 - price_position  # 越接近下限越"折价"
        else:
            price_position = 50
            discount = 0
        
        params = {
            'valuation_discount': discount,
            'is_loss_making': is_loss,
        }
        
        for score, desc, check in self.rules['pricing']['tiers']:
            if check(params):
                evidence = {
                    'price_low': price_low,
                    'price_high': price_high,
                    'offer_price': offer_price,
                    'price_position_pct': round(price_position, 1),
                    'is_loss_making': is_loss,
                }
                return score, desc, evidence
        
        return 10, '亏损企业默认分', {'is_loss_making': is_loss}
    
    def score_stabilization(self, data: Dict) -> Tuple[int, str, Dict]:
        """稳价维度 0-10分"""
        base = data.get('base', {})
        stabilizer = base.get('stabilizer', '')
        has_greenshoe = bool(base.get('has_greenshoe', 0))
        greenshoe_pct = base.get('greenshoe_pct', 0) or 0
        
        # 稳价人分级（国际大行 + 中资头部券商）
        top_stabilizers = {
            '摩根大通', 'J.P. Morgan', '高盛', '摩根士丹利',
            '中金', '中信里昂', '中信证券',
            '德意志银行', 'Deutsche Bank',
            '瑞银', 'UBS', '汇丰', 'HSBC', '花旗', 'Citi',
            '华泰金融', '华泰国际', '海通国际',
        }
        stabilizer_tier = 'top' if stabilizer and any(s in stabilizer for s in top_stabilizers) else 'normal'
        
        params = {
            'has_greenshoe': has_greenshoe,
            'stabilizer': stabilizer,
            'stabilizer_tier': stabilizer_tier,
        }
        
        for score, desc, check in self.rules['stabilization']['tiers']:
            if check(params):
                evidence = {
                    'stabilizer': stabilizer,
                    'has_greenshoe': has_greenshoe,
                    'greenshoe_pct': greenshoe_pct,
                    'stabilizer_tier': stabilizer_tier,
                }
                return score, desc, evidence
        
        return 0, '未匹配', {}
    
    def score_q1_break_rate(self, break_rate: float = 10.0) -> Tuple[int, str, Dict]:
        """Q1破发率维度 0-15分（系统级参数，非个股参数）"""
        params = {'break_rate': break_rate}
        
        for score, desc, check in self.rules['q1_break_rate']['tiers']:
            if check(break_rate):
                evidence = {'q1_break_rate_pct': break_rate, 'period': '2026Q1'}
                return score, desc, evidence
        
        return 0, '未匹配', {}
    
    def score_hsi_monthly(self, hsi_return: float = 3.99) -> Tuple[int, str, Dict]:
        """HSI月度涨跌维度 0-10分（系统级参数）"""
        for score, desc, check in self.rules['hsi_monthly']['tiers']:
            if check(hsi_return):
                evidence = {'hsi_monthly_return_pct': hsi_return}
                return score, desc, evidence
        
        return 0, '未匹配', {}
    
    # -----------------------------------------------------------
    # 情绪因子（新增V2）
    # -----------------------------------------------------------
    
    def score_sentiment(self, data: Dict) -> Tuple[int, str, Dict]:
        """
        市场情绪因子 0-10分（额外加分项，不纳入110分基础分）
        基于孖展超购倍数
        """
        sentiment = data.get('sentiment', {})
        oversub = sentiment.get('oversub_times', 0) or 0
        margin = sentiment.get('margin_amount', 0) or 0
        
        if oversub >= 1000:
            score, desc = 10, '极度火爆（超购≥1000倍）'
        elif oversub >= 100:
            score, desc = 7, '非常火热（超购100-1000倍）'
        elif oversub >= 15:
            score, desc = 5, '热度正常（超购15-100倍）'
        elif oversub > 0:
            score, desc = 2, '偏冷（超购<15倍）'
        else:
            score, desc = 0, '无数据'
        
        evidence = {
            'oversub_times': oversub,
            'margin_amount_hkd': margin,
            'sentiment_source': sentiment.get('source'),
        }
        return score, desc, evidence
    
    # -----------------------------------------------------------
    # 总分计算
    # -----------------------------------------------------------
    
    def calculate(self, stock_code: str, 
                  q1_break_rate: float = None,
                  hsi_return: float = None) -> Dict:
        """
        计算单只IPO的完整评分
        
        市场参数默认从config_manual读取，也可外部传入覆盖
        """
        # 使用配置的市场数据（支持外部传入覆盖）
        if q1_break_rate is None:
            q1_break_rate = get_market_data('q1_break_rate_2026', 10.0)
        if hsi_return is None:
            hsi_return = get_market_data('hsi_monthly_return_2026_04', 3.99)
        """
        计算单只IPO的完整评分
        
        Returns:
            {
                'stock_code': str,
                'dimensions': {dim: {'score': int, 'max': int, 'desc': str, 'evidence': {}}},
                'base_score': int,
                'total_score': int,
                'sentiment_bonus': int,
                'category': str,  # whitelist/greylist/blacklist
                'leverage_advice': str,
                'risk_warning': str,
            }
        """
        data = self.load_ipo_data(stock_code)
        
        if not data['base']:
            raise ValueError(f"数据库中未找到 {stock_code}")
        
        dimensions = {}
        
        # 6个基于个股数据的维度
        dimensions['profitability'] = {
            'score': self.score_profitability(data)[0],
            'max': 30,
            'desc': self.score_profitability(data)[1],
            'evidence': self.score_profitability(data)[2],
        }
        dimensions['allocation'] = {
            'score': self.score_allocation(data)[0],
            'max': 10,
            'desc': self.score_allocation(data)[1],
            'evidence': self.score_allocation(data)[2],
        }
        dimensions['cornerstone'] = {
            'score': self.score_cornerstone(data)[0],
            'max': 15,
            'desc': self.score_cornerstone(data)[1],
            'evidence': self.score_cornerstone(data)[2],
        }
        dimensions['pricing'] = {
            'score': self.score_pricing(data)[0],
            'max': 20,
            'desc': self.score_pricing(data)[1],
            'evidence': self.score_pricing(data)[2],
        }
        dimensions['stabilization'] = {
            'score': self.score_stabilization(data)[0],
            'max': 10,
            'desc': self.score_stabilization(data)[1],
            'evidence': self.score_stabilization(data)[2],
        }
        
        # 2个系统级维度
        dimensions['q1_break_rate'] = {
            'score': self.score_q1_break_rate(q1_break_rate)[0],
            'max': 15,
            'desc': self.score_q1_break_rate(q1_break_rate)[1],
            'evidence': self.score_q1_break_rate(q1_break_rate)[2],
        }
        dimensions['hsi_monthly'] = {
            'score': self.score_hsi_monthly(hsi_return)[0],
            'max': 10,
            'desc': self.score_hsi_monthly(hsi_return)[1],
            'evidence': self.score_hsi_monthly(hsi_return)[2],
        }
        
        # 情绪因子（额外）
        sentiment_score, sentiment_desc, sentiment_evidence = self.score_sentiment(data)
        
        # 计算总分
        base_score = sum(d['score'] for d in dimensions.values())
        total_score = base_score  # 稳价奖励已包含在stabilization维度中
        
        # 分类判定
        reg_type = data['base'].get('reg_type', '')
        cornerstone_count = len(data.get('cornerstones', []))
        
        # 黑名单优先：零基石
        if cornerstone_count == 0:
            category = 'blacklist'
        elif reg_type in ('18A', '18C'):
            category = 'greylist'
        elif total_score >= 70:
            category = 'whitelist'
        else:
            category = 'greylist'
        
        # 杠杆建议
        if category == 'blacklist':
            leverage = '不建议参与'
        elif category == 'greylist':
            leverage = '现金申购或3倍以内孖展'
        elif total_score >= 80:
            leverage = '10-20倍孖展'
        elif total_score >= 65:
            leverage = '5-10倍孖展'
        else:
            leverage = '现金申购'
        
        # 风险提示
        risks = []
        if reg_type in ('18A', '18C'):
            risks.append(f'{reg_type}特专科技公司，未盈利/高估值风险')
        if cornerstone_count == 0:
            risks.append('零基石投资者，机构认可度存疑')
        if not data['base'].get('has_greenshoe'):
            risks.append('无超额配股权/绿鞋，上市后缺乏护盘机制')
        if sentiment_score >= 10:
            risks.append('市场情绪极度狂热，需警惕高开低走')
        
        result = {
            'stock_code': stock_code,
            'stock_name': data['base'].get('stock_name', ''),
            'dimensions': dimensions,
            'base_score': base_score,
            'total_score': total_score,
            'sentiment_bonus': sentiment_score,
            'category': category,
            'leverage_advice': leverage,
            'risk_warning': '；'.join(risks) if risks else '常规风险',
            'scored_at': datetime.now().isoformat(),
        }
        
        # 保存到数据库
        self._save_score(result)
        
        return result
    
    def _save_score(self, result: Dict):
        """保存评分结果（同一股票每天只保留一条记录，防止重复）"""
        dims = result['dimensions']
        stock_code = result['stock_code']
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 先删除该股票今天的旧记录（去重）
        self.db.execute(
            "DELETE FROM ipo_scores WHERE stock_code = ? AND date(scored_at) = ?",
            (stock_code, today)
        )
        
        self.db.execute("""
            INSERT INTO ipo_scores 
            (stock_code, profitability, allocation, cornerstone, pricing, 
             stabilization, q1_break_rate, hsi_monthly,
             base_score, total_score, category, leverage_advice, risk_warning, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stock_code,
            dims['profitability']['score'],
            dims['allocation']['score'],
            dims['cornerstone']['score'],
            dims['pricing']['score'],
            dims['stabilization']['score'],
            dims['q1_break_rate']['score'],
            dims['hsi_monthly']['score'],
            result['base_score'],
            result['total_score'],
            result['category'],
            result['leverage_advice'],
            result['risk_warning'],
            json.dumps(result, ensure_ascii=False, default=str)
        ))
    
    def print_report(self, result: Dict):
        """打印评分报告到控制台"""
        print("\n" + "="*60)
        print(f" IPO评分报告: {result['stock_name']} ({result['stock_code']})")
        print("="*60)
        
        for dim_name, dim_data in result['dimensions'].items():
            print(f"\n【{dim_name}】{dim_data['score']}/{dim_data['max']} — {dim_data['desc']}")
        
        print(f"\n{'='*60}")
        print(f" 基础得分: {result['base_score']}/100")
        print(f" 含稳价总分: {result['total_score']}/110")
        print(f" 情绪加分: +{result['sentiment_bonus']}/10")
        print(f" 分类: {result['category']}")
        print(f" 杠杆建议: {result['leverage_advice']}")
        print(f" 风险提示: {result['risk_warning']}")
        print("="*60)


if __name__ == '__main__':
    # 测试评分引擎
    scorer = IPOScorer()
    # 需要先往数据库插入测试数据才能运行
    print("评分引擎已加载，需配合数据库数据使用")
