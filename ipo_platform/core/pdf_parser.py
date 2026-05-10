# -*- coding: utf-8 -*-
"""
招股书PDF解析引擎 V2

基于真实招股书格式（以翼菲智能06871.HK为模板）优化：
1. 使用PDF目录(Toc)精确定位章节
2. 针对港股招股书表格格式定制正则
3. 自动识别人民币千元/百万元等单位

使用方式：
    parser = ProspectusParser()
    result = parser.parse("path/to/prospectus.pdf", stock_code="06871.HK")
    parser.save_to_db(result)
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("请安装依赖: python3 -m pip install PyMuPDF")

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ipo_platform.models.database import get_db


@dataclass
class ParsedProspectus:
    stock_code: str
    stock_name: str = ""
    
    # 财务数据（单位：百万元人民币，自动转换）
    revenue_2023: Optional[float] = None
    revenue_2024: Optional[float] = None
    revenue_2025: Optional[float] = None
    net_profit_2023: Optional[float] = None
    net_profit_2024: Optional[float] = None
    net_profit_2025: Optional[float] = None
    
    # 配售结构
    total_shares: Optional[float] = None  # 万股
    public_pct: Optional[float] = None
    intl_pct: Optional[float] = None
    price_low: Optional[float] = None
    price_high: Optional[float] = None
    raise_amount: Optional[float] = None  # 亿港元
    
    # 基石
    cornerstone_count: int = 0
    cornerstones: List[Dict] = None
    
    # 稳价
    stabilizer: str = ""
    has_greenshoe: bool = False
    greenshoe_pct: Optional[float] = None
    
    # 元数据
    pages: int = 0
    parsed_at: str = ""
    currency_unit: str = "RMB"  # RMB/HKD/USD
    unit_note: str = ""  # 原始单位说明


class ProspectusParser:
    """招股书解析器 V2"""
    
    def __init__(self):
        self.db = get_db()
        self.doc = None
        self.toc_map = {}  # 章节标题 -> 页码
    
    def load_pdf(self, pdf_path: str) -> bool:
        try:
            self.doc = fitz.open(pdf_path)
            # 构建目录映射
            for item in self.doc.get_toc():
                level, title, page = item
                self.toc_map[title.strip()] = page
            print(f"   PDF加载: {len(self.doc)}页, 目录项{len(self.toc_map)}个")
            return True
        except Exception as e:
            print(f"   ❌ PDF加载失败: {e}")
            return False
    
    def _get_chapter_text(self, keyword: str, context_pages: int = 5) -> str:
        """根据目录关键词获取章节文本"""
        # 模糊匹配目录项
        best_page = None
        for title, page in self.toc_map.items():
            if keyword in title:
                best_page = page
                break
        
        if not best_page:
            #  fallback: 全文搜索
            for i in range(len(self.doc)):
                if keyword in self.doc[i].get_text():
                    best_page = i + 1
                    break
        
        if not best_page:
            return ""
        
        start_idx = max(0, best_page - 1)
        end_idx = min(len(self.doc), best_page - 1 + context_pages)
        texts = [self.doc[i].get_text() for i in range(start_idx, end_idx)]
        return "\n".join(texts)
    
    def _safe_float(self, s: str) -> Optional[float]:
        try:
            return float(s.replace(',', '').replace('(', '-').replace(')', ''))
        except:
            return None
    
    # ============================================================
    # 1. 财务数据提取
    # ============================================================
    
    def extract_financials(self) -> Dict:
        """
        提取综合损益表概要中的财务数据
        
        港股招股书常见格式：
        截至12月31日止年度
        2023年    2024年    2025年
        人民币    %    人民币    %    人民币    %
        （人民币千元，百分比除外）
        收入. . . . . . . . . . . . . . . . . . . . . . . .
        201,170   100.0   268,009   100.0   387,359   100.0
        """
        text = self._get_chapter_text("概要", context_pages=10)
        if not text:
            text = self._get_chapter_text("財務資料", context_pages=10)
        
        if not text:
            print("   ⚠️ 未找到财务章节")
            return {}
        
        result = {}
        
        # 找"综合损益表概要"或"财务资料"后面的表格区域
        summary_match = re.search(
            r'(?:綜合損益表概要|综合损益表概要|財務資料|财务资料).*?(\n.*?)\n(?:有關首次公開發售前|有关首次公开发售前|非國際財務報告準則|非国际财务报告准则)',
            text, re.S
        )
        if not summary_match:
            summary_match = re.search(
                r'(?:綜合損益表概要|综合损益表概要).*',
                text, re.S
            )
        
        table_text = summary_match.group(1) if summary_match else text
        
        # 判断单位
        unit_match = re.search(r'（([^）]*(?:千元|百萬|百万|元)[^）]*)）', table_text)
        unit_str = unit_match.group(1) if unit_match else ""
        result['unit_note'] = unit_str
        
        # 单位转换系数
        if '千元' in unit_str or '千' in unit_str:
            multiplier = 0.001  # 千元 -> 百万元
        elif '百萬' in unit_str or '百万' in unit_str:
            multiplier = 1.0
        elif '億' in unit_str or '亿' in unit_str:
            multiplier = 100.0
        else:
            multiplier = 0.001  # 默认千元
        
        result['multiplier'] = multiplier
        
        # 提取收入
        revenue_pattern = r'收入[\s\.]*\n([\-\d,\.]+)\s+[\d\.]+\s*%?\s*\n([\-\d,\.]+)\s+[\d\.]+\s*%?\s*\n([\-\d,\.]+)\s+[\d\.]+\s*%?'
        rev_match = re.search(revenue_pattern, table_text)
        if rev_match:
            result['revenue_2023'] = self._safe_float(rev_match.group(1)) * multiplier
            result['revenue_2024'] = self._safe_float(rev_match.group(2)) * multiplier
            result['revenue_2025'] = self._safe_float(rev_match.group(3)) * multiplier
        
        # 提取利润/亏损
        # 先判断是利润还是亏损，以确定是否需要取负号
        is_loss = '虧損' in table_text or '亏损' in table_text
        sign = -1 if is_loss else 1
        
        # 策略：逐行解析，找到"年内利润/亏损"标签后提取后续数字
        lines = table_text.split('\n')
        for i, line in enumerate(lines):
            if '年內虧損' in line or '年内亏损' in line or '年內利潤' in line or '年内利润' in line or '期內虧損' in line or '期内亏损' in line or '期內利潤' in line or '期内利润' in line:
                # 收集后续的数字行（跳过百分比行和空行）
                nums = []
                for j in range(i+1, min(i+20, len(lines))):
                    l = lines[j].strip()
                    if not l:
                        continue
                    # 跳过纯百分比行
                    if re.match(r'^\(?[\d\.]+\)?\s*%?$', l):
                        continue
                    # 匹配数字行（可能带括号和逗号）
                    num_match = re.match(r'^\(?([\-\d,\.]+)\)?$', l)
                    if num_match:
                        nums.append(num_match.group(1))
                    # 如果已经收集到3个数字，停止
                    if len(nums) >= 3:
                        break
                    # 如果遇到非数字文本且已有数字，停止
                    if nums and len(l) > 10 and not re.match(r'^\(?[\d,\.\-]+\)?$', l):
                        break
                
                if len(nums) >= 3:
                    result['net_profit_2023'] = self._safe_float(nums[0]) * multiplier * sign
                    result['net_profit_2024'] = self._safe_float(nums[1]) * multiplier * sign
                    result['net_profit_2025'] = self._safe_float(nums[2]) * multiplier * sign
                    break
        
        return result
    
    # ============================================================
    # 2. 配售结构与定价
    # ============================================================
    
    def extract_allocation(self) -> Dict:
        """
        提取配售结构和定价信息
        """
        result = {}
        
        # === 定价：优先搜索前5页（封面/重要提示）===
        price_text = ""
        for i in range(min(5, len(self.doc))):
            price_text += self.doc[i].get_text() + "\n"
        
        price_match = re.search(
            r'(?:發售價|发售价|招股價|招股价)[^\n]*?(\d+\.?\d*)\s*(?:港元|港币|HK\$)?\s*(?:至|到|[-~])\s*(\d+\.?\d*)\s*(?:港元|港币|HK\$)',
            price_text
        )
        if price_match:
            result['price_low'] = float(price_match.group(1))
            result['price_high'] = float(price_match.group(2))
        else:
            fixed_match = re.search(
                r'(?:發售價|发售价|招股價|招股价)[^\n]*?(\d+\.?\d*)\s*(?:港元|港币|HK\$)',
                price_text
            )
            if fixed_match:
                result['price_low'] = float(fixed_match.group(1))
                result['price_high'] = float(fixed_match.group(1))
        
        # === 配售结构：搜索全球发售架构章节 ===
        alloc_text = self._get_chapter_text("全球發售的架構", context_pages=5)
        if not alloc_text:
            alloc_text = self._get_chapter_text("概要", context_pages=8)
        
        if alloc_text:
            # 公开发售股数 & 国际发售股数
            public_shares_match = re.search(
                r'(?:香港公開發售|公开发售)[^\n]*?(\d[\d,]+)\s*股',
                alloc_text
            )
            intl_shares_match = re.search(
                r'(?:國際發售|国际发售)[^\n]*?(\d[\d,]+)\s*股',
                alloc_text
            )
            
            public_shares = None
            intl_shares = None
            
            if public_shares_match:
                public_shares = float(public_shares_match.group(1).replace(',', ''))
            if intl_shares_match:
                intl_shares = float(intl_shares_match.group(1).replace(',', ''))
            
            # 从股数计算比例
            if public_shares and intl_shares:
                total = public_shares + intl_shares
                result['public_pct'] = round(public_shares / total * 100, 1)
                result['intl_pct'] = round(intl_shares / total * 100, 1)
                result['total_shares'] = total / 10000  # 万股
            
            # 如果股数提取失败，直接搜百分比
            if 'public_pct' not in result:
                public_pct_match = re.search(
                    r'(?:香港公開發售|公开发售)[^\n]*?(\d+\.?\d*)\s*%',
                    alloc_text
                )
                if public_pct_match:
                    result['public_pct'] = float(public_pct_match.group(1))
            
            if 'intl_pct' not in result:
                intl_pct_match = re.search(
                    r'(?:國際發售|国际发售|國際配售|国际配售)[^\n]*?(\d+\.?\d*)\s*%',
                    alloc_text
                )
                if intl_pct_match:
                    result['intl_pct'] = float(intl_pct_match.group(1))
            
            # 募资额
            raise_match = re.search(
                r'(?:最高)?(?:集資|募资|筹集)[^\n]*?(\d+\.?\d*)\s*(?:億|亿)\s*(?:港元|港币)',
                alloc_text
            )
            if raise_match:
                result['raise_amount'] = float(raise_match.group(1))
        
        # 互补计算
        if 'public_pct' in result and 'intl_pct' not in result:
            result['intl_pct'] = 100 - result['public_pct']
        elif 'intl_pct' in result and 'public_pct' not in result:
            result['public_pct'] = 100 - result['intl_pct']
        
        return result
    
    # ============================================================
    # 3. 基石投资者
    # ============================================================
    
    def _is_valid_cornerstone_name(self, name: str) -> bool:
        """严格黑名单过滤：判断是否为有效的基石投资者名称"""
        if not name or len(name) < 2 or len(name) > 60:
            return False
        # 2字符名称仅限纯中文
        if len(name) == 2 and not re.match(r'^[\u4e00-\u9fff]{2}$', name):
            return False
        # 排除纯标点/括号的行
        if re.match(r'^[\s\(\)（）「」""''，、。:\.\-\*\d]+$', name):
            return False
        # 排除常见非名称行（含协议/流程/财务关键词）
        garbage_keywords = [
            '基石投資協議', '基石投资协议', '協議', '协议',
            '已訂立', '已订立', '已與', '已与', '據此', '据此',
            '各稱', '各称', '統稱', '统称', '發售價', '发售价',
            '認購', '认购', '全球發售', '全球发售',
            '香港公開發售', '香港公开发售', '國際發售', '国际发售',
            '緊隨', '紧随', '完成後', '完成后', '概約', '概约',
            '百分比', '假設', '假设', '超額配股權', '超额配股权',
            '發售股份', '发售股份', '經紀佣金', '经纪佣金',
            '交易徵費', '交易征费', '交易費', '交易费',
            '董事會', '董事会', '主要股東', '主要股东',
            '關連人士', '关连人士', '聯繫人', '联系人',
            '附帶安排', '附带安排', '優先權', '优先权',
            '上市規則', '上市规则', '新上市申請人指南',
            '保薦人', '保荐人', '整體協調人', '整体协调人',
            '包銷協議', '包销协议', '定價協議', '定价协议',
            '禁售期', '禁售', '六個月', '六个月',
            '保證分配', '保证分配', '最終發售價', '最终发售价',
            '總計', '总计', '附註', '附注', 'Note', 'Notes',
            '認購金額', '认购金额', '發售股份數目', '发售股份数目',
            '佔發售股份的', '占发售股份的', '佔緊隨全球發售', '占紧随全球发售',
            '收入', '成本', '毛利', '研發', '行政開支', '銷售及營銷',
            '其他收入', '其他開支', '其他虧損', '其他收益', '經營虧損',
            '財務收入', '財務開支', '所得稅', '稅前', '稅後',
            '可轉換貸款', '以股份為基礎', '薪酬', '合作協議',
            '年初', '新增', '年末', '因合同完成而終止',
            '已發行非上市股份', '從非上市股份轉換', '根據全球發售將予發行',
            '非國際財務報告準則', '經調整', '虧損',
            '基石投资者', '基石投資者', 'Cornerstone Investors',
        ]
        for kw in garbage_keywords:
            if kw in name:
                return False
        # 排除纯数字/百分比行
        if re.search(r'^\d+[\d\s,\.]*\s*%?$', name):
            return False
        if re.match(r'^\d+\.?\d*\s*(百萬|百万|億|亿|千|万|美元|港元|人民币|USD|HKD|RMB)?$', name):
            return False
        # 排除 Mostly numbers/punctuation
        alpha_chars = len(re.findall(r'[\u4e00-\u9fffA-Za-z]', name))
        total_chars = len(name.replace(' ', ''))
        if total_chars > 0 and alpha_chars / total_chars < 0.3:
            return False
        return True

    def extract_cornerstones(self) -> Tuple[int, List[Dict]]:
        """
        提取基石投资者
        采用多策略提取，优先从表格和结构化段落中识别
        """
        text = self._get_chapter_text("基石投資者", context_pages=10)
        if not text:
            return 0, []

        cornerstones = []
        seen = set()

        def add_name(name: str):
            name = name.strip()
            # 清理尾部标点、省略号、空格
            name = re.sub(r'[\.\.\．\。\,\，\s]+$', '', name)
            # 清理尾部括号标记如 (3)
            name = re.sub(r'\(\d+\)$', '', name).strip()
            if not name or name in seen:
                return
            if not self._is_valid_cornerstone_name(name):
                return
            seen.add(name)
            cornerstones.append({
                'investor_name': name,
                'amount_hkd': None,
                'is_star': self._is_star_investor(name)
            })

        lines_raw = text.split('\n')  # 保留原始行（含缩进/空格）

        # ============================================================
        # 策略1：表格省略号行提取（最可靠）
        # 港股基石表格常见格式：Name . . . . amount shares ...
        # ============================================================
        total_seen = False
        for i, line_raw in enumerate(lines_raw):
            line_stripped = line_raw.strip()
            # 以第一个"總計"作为表格结束标志
            if '總計' in line_stripped or '总计' in line_stripped:
                total_seen = True
            if total_seen:
                continue

            # 匹配 spaced-out dot leaders: ". . ." 或 "...."
            if not re.search(r'\.(?:\s*\.){2,}', line_raw):
                continue

            name = re.split(r'\.(?:\s*\.)+', line_raw)[0].strip()
            if not name:
                continue

            # 判断是否为折行续接（wrapped continuation）
            # 例：上一行 "國風投創新投資基金"，当前行 " 股份有限公司. . ."
            is_wrapped = False
            if line_raw.startswith(' ') or line_raw.startswith('　'):
                prev_has_dots = False
                prev_is_data = False
                for j in range(i - 1, max(0, i - 5), -1):
                    prev_raw = lines_raw[j]
                    prev_stripped = prev_raw.strip()
                    if not prev_stripped:
                        continue
                    # 上一行是纯数字/百分比/金额 -> 当前行是缩进的表格行，不是折行
                    if re.match(r'^[\d\s\.,%]+$', prev_stripped):
                        prev_is_data = True
                        break
                    prev_has_dots = bool(re.search(r'\.(?:\s*\.){2,}', prev_raw))
                    break

                if not prev_has_dots and not prev_is_data:
                    is_wrapped = True
                    for j in range(i - 1, max(0, i - 5), -1):
                        prev = lines_raw[j].strip()
                        if prev and not re.match(r'^[\d\s\.,%]+$', prev):
                            combined = prev + name
                            add_name(combined)
                            break

            if not is_wrapped:
                add_name(name)

        # ============================================================
        # 策略2：兜底——旧正则 + 严格过滤
        # 用于无表格或表格提取失败的情况
        # ============================================================
        if len(cornerstones) < 2:
            # 提取「Name」模式
            for m in re.finditer(r'[（(]「([^」]{2,40})」[）)]', text):
                candidate = m.group(1).strip()
                add_name(candidate)

            # 兜底正则：匹配"已签订基石投资协议"附近的文本块，然后逐行过滤
            fallback_match = re.search(
                r'(?:已签订|已訂立|已與|已签订).*?基石投資協議[。:\n]*(.+?)(?:\n\n|基石投資者|$)',
                text, re.S
            )
            if fallback_match:
                for line in fallback_match.group(1).split('\n'):
                    add_name(line.strip())

        return len(cornerstones), cornerstones

    def _is_star_investor(self, name: str) -> bool:
        """仅匹配特定的知名机构名称"""
        stars = [
            'GIC',
            '贝莱德', 'BlackRock', '貝萊德',
            '富达', 'Fidelity', '富達',
            '高瓴', 'Hillhouse',
            '腾讯', 'Tencent', '騰訊',
            '阿里', 'Alibaba',
            '红杉', 'Sequoia', '紅杉',
            '淡马锡', 'Temasek', '淡馬錫',
            '橡树', 'Oaktree', '橡樹',
            '千禧', 'Millennium',
            '景顺', 'Invesco', '景順',
            'UBS',
            'Deerfield',
            'HHLR', 'HHLRA',
            'LAV',
            'Lake Bleu',
            'RTW',
            'Arc Avenue',
            '清池资本', '清池資本',
            'Sage Partners',
            '未来资产', '未來資產', 'Mirae Asset',
            '国风投', '國風投',
            '工银瑞信', '工銀瑞信',
            '广发基金', '廣發基金',
            '华夏基金', '華夏基金',
            '富国基金', '富國基金',
            '睿遠', '睿远',
            'Prosper High',
            'WWHCP', 'Worldwide Healthcare',
            'First Quarter Moon',
            'Foresight Global',
            '華泰資本', '华泰资本',
            '黃河投資', '黄河投资',
            'Isometry',
            'Huadeng',
            '華泰證券', '华泰证券',
            '中信证券', '中信証券',
            '招商局', '招商',
        ]
        return any(s.lower() in name.lower() for s in stars)
    
    # ============================================================
    # 4. 稳价信息
    # ============================================================
    
    def extract_stabilization(self) -> Dict:
        """
        提取稳价人/绿鞋信息
        """
        text = self._get_chapter_text("承銷", context_pages=5)
        if not text:
            return {}
        
        result = {}
        
        # 稳价操作人
        stabilizer_match = re.search(
            r'(?:穩定價格操作人|稳定价格操作人|Stabilizing Manager)[：:\s]*([^\n。]{2,40})',
            text
        )
        if stabilizer_match:
            result['stabilizer'] = stabilizer_match.group(1).strip()
        else:
            # 如果找不到稳价人，通常保荐人/整体协调人就是稳价人
            # 从"董事及參與全球發售的各方"章节找
            parties_text = self._get_chapter_text("董事及參與全球發售的各方", context_pages=3)
            if parties_text:
                sponsor_match = re.search(r'(?:保薦人|保荐人)[兼及]*(?:整體協調人|整体协调人)[^\n]*\n([^\n]{2,40})', parties_text)
                if sponsor_match:
                    result['stabilizer'] = sponsor_match.group(1).strip()
        
        # 超额配股权/绿鞋
        if '超額配股權' in text or '超额配股权' in text or 'over-allotment' in text.lower():
            result['has_greenshoe'] = True
            greenshoe_match = re.search(r'(?:不超過|不超过|最多).*?(\d+\.?\d*)\s*%', text)
            if greenshoe_match:
                result['greenshoe_pct'] = float(greenshoe_match.group(1))
        else:
            result['has_greenshoe'] = False
        
        return result
    
    # ============================================================
    # 5. 综合解析
    # ============================================================
    
    def parse(self, pdf_path: str, stock_code: str, stock_name: str = "") -> ParsedProspectus:
        print(f"\n【解析招股书】{stock_code} {stock_name}")
        print(f"   文件: {pdf_path}")
        
        if not self.load_pdf(pdf_path):
            return ParsedProspectus(stock_code=stock_code, stock_name=stock_name)
        
        result = ParsedProspectus(
            stock_code=stock_code,
            stock_name=stock_name,
            pages=len(self.doc),
            parsed_at=__import__('datetime').datetime.now().isoformat()
        )
        
        # 1. 财务数据
        fin = self.extract_financials()
        if fin:
            result.revenue_2023 = fin.get('revenue_2023')
            result.revenue_2024 = fin.get('revenue_2024')
            result.revenue_2025 = fin.get('revenue_2025')
            result.net_profit_2023 = fin.get('net_profit_2023')
            result.net_profit_2024 = fin.get('net_profit_2024')
            result.net_profit_2025 = fin.get('net_profit_2025')
            result.unit_note = fin.get('unit_note', '')
            print(f"   财务({fin.get('unit_note','')}): 营收 {result.revenue_2023}/{result.revenue_2024}/{result.revenue_2025}")
            print(f"        利润 {result.net_profit_2023}/{result.net_profit_2024}/{result.net_profit_2025}")
        
        # 2. 配售与定价
        alloc = self.extract_allocation()
        if alloc:
            result.public_pct = alloc.get('public_pct')
            result.intl_pct = alloc.get('intl_pct')
            result.price_low = alloc.get('price_low')
            result.price_high = alloc.get('price_high')
            result.total_shares = alloc.get('total_shares')
            result.raise_amount = alloc.get('raise_amount')
            print(f"   配售: 公配{result.public_pct}% / 国配{result.intl_pct}%")
            print(f"   定价: {result.price_low} ~ {result.price_high} 港元")
        
        # 3. 基石
        cs_count, cs_list = self.extract_cornerstones()
        result.cornerstone_count = cs_count
        result.cornerstones = cs_list
        print(f"   基石: {cs_count}家")
        for cs in cs_list[:5]:
            print(f"      - {cs['investor_name']}")
        
        # 4. 稳价
        stab = self.extract_stabilization()
        if stab:
            result.stabilizer = stab.get('stabilizer', '')
            result.has_greenshoe = stab.get('has_greenshoe', False)
            result.greenshoe_pct = stab.get('greenshoe_pct')
            print(f"   稳价: {result.stabilizer or 'N/A'} | 绿鞋: {'有' if result.has_greenshoe else '无'}")
        
        return result
    
    def save_to_db(self, result: ParsedProspectus):
        """保存解析结果到数据库"""
        db = get_db()
        
        db.execute("""
            UPDATE ipo_base SET
                total_shares = ?,
                public_pct = ?,
                intl_pct = ?,
                price_low = ?,
                price_high = ?,
                raise_amount = ?,
                stabilizer = ?,
                has_greenshoe = ?,
                updated_at = ?
            WHERE stock_code = ?
        """, (
            result.total_shares, result.public_pct, result.intl_pct,
            result.price_low, result.price_high, result.raise_amount,
            result.stabilizer, int(result.has_greenshoe),
            __import__('datetime').datetime.now().isoformat(),
            result.stock_code
        ))
        
        db.execute("""
            INSERT OR REPLACE INTO ipo_financials
            (stock_code, revenue_2023, revenue_2024, revenue_2025,
             net_profit_2023, net_profit_2024, net_profit_2025)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            result.stock_code, result.revenue_2023, result.revenue_2024, result.revenue_2025,
            result.net_profit_2023, result.net_profit_2024, result.net_profit_2025
        ))
        
        db.execute("DELETE FROM ipo_cornerstones WHERE stock_code = ?", (result.stock_code,))
        for cs in result.cornerstones or []:
            db.execute("""
                INSERT INTO ipo_cornerstones (stock_code, investor_name, amount_hkd, is_star)
                VALUES (?, ?, ?, ?)
            """, (result.stock_code, cs['investor_name'], cs.get('amount_hkd'), int(cs.get('is_star', 0))))
        
        print(f"   ✅ 已入库: {result.stock_code}")


if __name__ == '__main__':
    print("招股书PDF解析引擎 V2")
    print("使用方式:")
    print("  parser = ProspectusParser()")
    print("  result = parser.parse('path/to/prospectus.pdf', '06871.HK')")
    print("  parser.save_to_db(result)")
