# -*- coding: utf-8 -*-
"""
港股IPO监控器 V2（真实爬虫版）

双源监控策略：
1. etnet IPO日历 —— 发现活跃IPO（代码/名称/日期/状态）
2. 港交所披露易 —— 获取招股书PDF下载链接

调度：每个交易日自动轮询，发现新标的自动入库+下载PDF
"""

import re
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("请安装依赖: python3 -m pip install requests beautifulsoup4")

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ipo_platform.config import PDF_DIR
from ipo_platform.models.database import get_db


class IPOCrawler:
    """港股IPO真实数据爬虫"""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh-HK,zh-TW,en-US,en;q=0.9",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.db = get_db()
        self.pdf_dir = Path(PDF_DIR)
    
    def _get(self, url: str, retries: int = 3, timeout: int = 30) -> Optional[str]:
        """带重试的GET请求"""
        for i in range(retries):
            try:
                resp = self.session.get(url, timeout=timeout)
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                print(f"  请求失败 ({i+1}/{retries}): {url[:60]}... | {e}")
                if i < retries - 1:
                    time.sleep(2 ** i)
        return None
    
    # ============================================================
    # 数据源1: etnet IPO日历
    # ============================================================
    
    def etnet_fetch_calendar(self) -> List[Dict]:
        """
        从etnet获取IPO日历
        URL: https://www.etnet.com.hk/www/tc/stocks/ipo-calendar.php
        
        返回: [{code, name, date, status_tag, detail_url}]
        """
        url = "https://www.etnet.com.hk/www/tc/stocks/ipo-calendar.php"
        print(f"\n【etnet IPO日历】{url}")
        
        html = self._get(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        ipos = []
        
        # 定位IPO列表容器
        detail_div = soup.find('div', class_='ipo-detail')
        if not detail_div:
            print("  ⚠️ 未找到 ipo-detail 容器")
            return []
        
        # 查找所有IPO条目（在 popular-keyword 下的 <a> 标签）
        result_div = detail_div.find('div', class_='result')
        if not result_div:
            print("  ⚠️ 未找到 result 容器")
            return []
        
        keyword_div = result_div.find('div', class_='popular-keyword')
        if not keyword_div:
            print("  ⚠️ 未找到 popular-keyword 容器")
            return []
        
        for a in keyword_div.find_all('a', href=True):
            # 提取日期
            date_span = a.find('span', class_='date')
            date_str = date_span.get_text(strip=True) if date_span else None
            
            # 提取股票代码和名称
            code_name_span = a.find('span', class_='mr-s')
            code_name = code_name_span.get_text(strip=True) if code_name_span else ''
            
            # 提取状态标签
            label_span = a.find('span', class_='label')
            status_tag = label_span.get_text(strip=True) if label_span else ''
            
            # 解析代码和名称
            # 格式: "01236 樂動機器人" 或 "07630 英派藥業－Ｂ"
            code_match = re.match(r'(\d{4,5})\s+(.+)', code_name)
            if not code_match:
                continue
            
            code = f"{code_match.group(1).zfill(5)}.HK"
            name = code_match.group(2).strip()
            
            # etnet详情页URL
            detail_url = a.get('href')
            if detail_url and not detail_url.startswith('http'):
                detail_url = urljoin(url, detail_url)
            
            # 标准化状态
            status = self._normalize_status(status_tag)
            
            ipos.append({
                'source': 'etnet',
                'stock_code': code,
                'stock_name': name,
                'date': date_str,  # YYYY/MM/DD
                'status_tag': status_tag,
                'status': status,
                'detail_url': detail_url,
            })
        
        print(f"  ✅ 发现 {len(ipos)} 个活跃IPO")
        for ipo in ipos:
            print(f"     {ipo['stock_code']} {ipo['stock_name'][:12]:12s} | {ipo['date']} | {ipo['status_tag']}")
        
        return ipos
    
    def _normalize_status(self, tag: str) -> str:
        """标准化etnet状态标签"""
        tag = tag.strip()
        if '招股' in tag or '截止' in tag:
            return 'ipoing'  # 招股中
        elif '上市' in tag and '明天' in tag:
            return 'listing_tomorrow'
        elif '上市' in tag:
            return 'listing_soon'  # 即将上市
        elif '半新股' in tag:
            return 'listed'  # 已上市
        elif '暗盤' in tag:
            return 'grey_market'
        else:
            return 'unknown'
    
    # ============================================================
    # 数据源2: 港交所披露易新上市页面
    # ============================================================
    
    def hkex_fetch_new_listings(self) -> List[Dict]:
        """
        从港交所披露易获取主板新上市信息+招股书PDF链接
        URL: https://www2.hkexnews.hk/New-Listings/New-Listing-Information/Main-Board?sc_lang=zh-HK
        
        返回: [{code, name, announcement_pdf, prospectus_pdf, allotment_pdf}]
        """
        url = "https://www2.hkexnews.hk/New-Listings/New-Listing-Information/Main-Board?sc_lang=zh-HK"
        print(f"\n【港交所披露易】{url}")
        
        html = self._get(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        ipos = []
        
        table = soup.find('table')
        if not table:
            print("  ⚠️ 未找到表格")
            return []
        
        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]  # 跳过表头
        
        for row in rows:
            tds = row.find_all('td')
            if len(tds) < 4:
                continue
            
            code = tds[0].get_text(strip=True)
            name = tds[1].get_text(strip=True)
            
            # 提取PDF链接
            announcement_a = tds[2].find('a', href=True) if len(tds) > 2 else None
            prospectus_a = tds[3].find('a', href=True) if len(tds) > 3 else None
            allotment_a = tds[4].find('a', href=True) if len(tds) > 4 else None
            
            # 补全URL
            def full_url(href):
                if not href:
                    return None
                if href.startswith('http'):
                    return href
                return f"https://www2.hkexnews.hk{href}"
            
            ipos.append({
                'source': 'hkex',
                'stock_code': f"{code.zfill(5)}.HK",
                'stock_name': name,
                'announcement_pdf': full_url(announcement_a.get('href')) if announcement_a else None,
                'prospectus_pdf': full_url(prospectus_a.get('href')) if prospectus_a else None,
                'allotment_pdf': full_url(allotment_a.get('href')) if allotment_a else None,
            })
        
        print(f"  ✅ 发现 {len(ipos)} 个新上市条目")
        for ipo in ipos:
            has_pdf = '✅' if ipo['prospectus_pdf'] else '❌'
            print(f"     {has_pdf} {ipo['stock_code']} {ipo['stock_name'][:15]:15s}")
        
        return ipos
    
    # ============================================================
    # 数据融合 + 自动下载
    # ============================================================
    
    def merge_and_sync(self) -> List[Dict]:
        """
        融合两个数据源，发现新IPO并自动下载招股书
        
        策略:
        1. 从etnet获取活跃IPO列表（有状态信息：招股中/即将上市/已上市）
        2. 从hkex获取招股书PDF链接
        3. 按stock_code匹配，合并数据
        4. 新IPO自动入库，自动下载PDF
        """
        print("\n" + "="*70)
        print(" IPO监控器 —— 双源数据融合")
        print("="*70)
        
        # 获取两个数据源
        etnet_ipos = self.etnet_fetch_calendar()
        hkex_ipos = self.hkex_fetch_new_listings()
        
        if not etnet_ipos and not hkex_ipos:
            print("\n❌ 两个数据源均无数据")
            return []
        
        # 构建hkex索引（按代码）
        hkex_map = {ipo['stock_code']: ipo for ipo in hkex_ipos}
        
        # 融合数据
        merged = []
        for et_ipo in etnet_ipos:
            code = et_ipo['stock_code']
            hk_ipo = hkex_map.get(code, {})
            
            merged_ipo = {
                'stock_code': code,
                'stock_name': et_ipo['stock_name'],
                'date': et_ipo.get('date'),
                'status': et_ipo.get('status'),
                'status_tag': et_ipo.get('status_tag'),
                'prospectus_pdf': hk_ipo.get('prospectus_pdf'),
                'announcement_pdf': hk_ipo.get('announcement_pdf'),
                'detail_url': et_ipo.get('detail_url'),
            }
            merged.append(merged_ipo)
        
        # 注：不再自动补充"披露易有但etnet没有"的股票。
        # 披露易新上市页面包含所有发布过招股书的公司（已上市/推迟/结束招股），
        # 不等于"当前活跃IPO"。etnet IPO日历才是活跃状态的标准来源。
        # 如etnet尚未更新，可手动添加或等次日etnet同步。
        
        print(f"\n📊 融合后共 {len(merged)} 个活跃IPO（etnet确认）")
        return merged
    
    def check_new_ipos(self) -> List[Dict]:
        """
        主入口：检查是否有新IPO，返回需要处理的新IPO列表
        """
        merged = self.merge_and_sync()
        
        # 获取已入库的IPO
        existing = self.db.fetchall("SELECT stock_code, status FROM ipo_base")
        existing_map = {row['stock_code']: row['status'] for row in existing}
        
        new_ipos = []
        updated_ipos = []
        
        for ipo in merged:
            code = ipo['stock_code']
            
            if code not in existing_map:
                # 全新IPO
                new_ipos.append(ipo)
            elif existing_map.get(code) != ipo.get('status') and ipo.get('status'):
                # 状态变更（如从prospectus变为listed）
                updated_ipos.append(ipo)
        
        if new_ipos:
            print(f"\n🆕 发现 {len(new_ipos)} 个新IPO:")
            for ipo in new_ipos:
                print(f"   • {ipo['stock_code']} {ipo['stock_name']} | {ipo.get('status_tag', 'N/A')}")
        
        if updated_ipos:
            print(f"\n📝 {len(updated_ipos)} 个IPO状态变更:")
            for ipo in updated_ipos:
                print(f"   • {ipo['stock_code']} {ipo['stock_name']} → {ipo.get('status')}")
        
        if not new_ipos and not updated_ipos:
            print("\n✅ 无新IPO，无状态变更")
        
        return new_ipos + updated_ipos
    
    def save_to_db(self, ipo: Dict):
        """将IPO存入数据库（仅更新状态，不覆盖已有字段）"""
        # 解析日期格式 YYYY/MM/DD -> YYYYMMDD
        date_str = ipo.get('date')
        if date_str:
            date_str = date_str.replace('/', '')
        
        code = ipo['stock_code']
        exists = self.db.fetchone("SELECT 1 FROM ipo_base WHERE stock_code = ?", (code,))
        
        if exists:
            # 已存在，只更新状态和日期（不覆盖稳价人等已有数据）
            self.db.execute("""
                UPDATE ipo_base 
                SET status = ?, updated_at = ?
                WHERE stock_code = ?
            """, (
                ipo.get('status', 'prospectus'),
                datetime.now().isoformat(),
                code
            ))
        else:
            # 新IPO，插入基础记录
            self.db.execute("""
                INSERT INTO ipo_base 
                (stock_code, stock_name, list_date, status, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                code,
                ipo['stock_name'],
                date_str,
                ipo.get('status', 'prospectus'),
                datetime.now().isoformat()
            ))
        print(f"   ✅ 已入库: {code} {ipo['stock_name']}")
    
    def download_prospectus(self, stock_code: str, pdf_url: str, force: bool = False) -> Optional[Path]:
        """下载招股书PDF"""
        if not pdf_url:
            print(f"   ⚠️ {stock_code} 无招股书PDF链接")
            return None
        
        safe_code = stock_code.replace('.', '_')
        pdf_path = self.pdf_dir / f"{safe_code}_prospectus.pdf"
        
        if pdf_path.exists() and not force:
            print(f"   {stock_code} 招股书已存在 ({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)，跳过")
            return pdf_path
        
        print(f"   ⬇️  下载 {stock_code} 招股书...")
        try:
            resp = self.session.get(pdf_url, timeout=120, stream=True)
            resp.raise_for_status()
            
            with open(pdf_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            size_mb = pdf_path.stat().st_size / 1024 / 1024
            print(f"   ✅ 完成: {pdf_path.name} ({size_mb:.1f} MB)")
            return pdf_path
        except Exception as e:
            print(f"   ❌ 下载失败: {e}")
            return None
    
    def run_pipeline(self, auto_download: bool = True):
        """完整流水线：发现 → 入库 → 下载PDF"""
        print("\n" + "="*70)
        print(f" IPO监控流水线 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        ipos = self.check_new_ipos()
        
        for ipo in ipos:
            code = ipo['stock_code']
            
            # 入库
            self.save_to_db(ipo)
            
            # 下载PDF
            if auto_download and ipo.get('prospectus_pdf'):
                self.download_prospectus(code, ipo['prospectus_pdf'])
        
        print("\n" + "="*70)
        print(" 流水线完成")
        print("="*70)
        return ipos


# ============================================================
# MockMonitor 保留用于测试
# ============================================================

class MockMonitor(IPOCrawler):
    """模拟监控器（用于无网络环境的测试）"""
    
    def etnet_fetch_calendar(self):
        print("\n【Mock模式】返回测试数据")
        return [
            {
                'source': 'etnet',
                'stock_code': '09999.HK',
                'stock_name': '测试科技',
                'date': '2026/05/13',
                'status_tag': '招股中',
                'status': 'ipoing',
                'detail_url': None,
            }
        ]
    
    def hkex_fetch_new_listings(self):
        return []


if __name__ == '__main__':
    # 直接运行测试
    crawler = IPOCrawler()
    crawler.run_pipeline(auto_download=False)
