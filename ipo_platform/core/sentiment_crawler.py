# -*- coding: utf-8 -*-
"""
IPO情绪因子爬虫

从etnet IPO新闻中提取孖展/超购数据

数据源：
- etnet IPO新闻频道 (https://www.etnet.com.hk/www/tc/stocks/ipo-news.php)
- 单只新股的新闻文章中通常包含孖展金额和超购倍数

提取策略：
1. 遍历etnet IPO新闻列表
2. 从文章标题中提取股票代码和关键数字
3. 从正文中用正则提取孖展金额和超购倍数
4. 存入market_sentiment表
"""

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, unquote

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ipo_platform.models.database import get_db

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("请安装依赖: python3 -m pip install requests beautifulsoup4")


class SentimentCrawler:
    """IPO情绪数据爬虫"""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    # 正则模式：提取超购倍数和孖展金额
    PATTERNS = {
        'oversub': [
            r'超額認購\s*([\d\.]+)\s*倍',
            r'超購\s*([\d\.]+)\s*倍',
            r'超額認購近?\s*([\d\.]+)\s*倍',
            r'超額認購逾?\s*([\d\.]+)\s*倍',
            r'獲超額認購\s*([\d\.]+)\s*倍',
            r'超額認購約?\s*([\d\.]+)\s*倍',
        ],
        'margin': [
            r'孖展(?:額|金额)?(?:達|约|近|逾)?\s*([\d\.]+)\s*(億|亿|萬|万)',
            r'獲(?:借出)?\s*([\d\.]+)\s*(億|亿|萬|万)\s*元?孖展',
            r'孖展認購(?:達|约|近|逾)?\s*([\d\.]+)\s*(億|亿|萬|万)',
        ],
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.db = get_db()
    
    def _get(self, url: str, retries: int = 3) -> Optional[str]:
        """带重试的GET请求"""
        for i in range(retries):
            try:
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                print(f"  请求失败 ({i+1}/{retries}): {e}")
                if i < retries - 1:
                    time.sleep(2 ** i)
        return None
    
    def fetch_news_list(self, topic: str = 'margin', max_pages: int = 3) -> List[Dict]:
        """
        获取etnet IPO新闻列表，同时从标题中提取情绪数据
        
        Returns:
            [{title, url, date, stock_code, oversub_times}]
        """
        articles = []
        base_url = "https://www.etnet.com.hk/www/tc/stocks/ipo-news.php"
        
        for page in range(1, max_pages + 1):
            url = f"{base_url}?topic={topic}&page={page}"
            print(f"【etnet IPO新闻】{url}")
            
            html = self._get(url)
            if not html:
                break
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找新闻列表 - 直接找所有ipo-news-article链接
            for a in soup.find_all('a', href=re.compile(r'ipo-news-article')):
                title = a.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                
                href = a.get('href')
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                # 去重
                if any(a2['url'] == href for a2 in articles):
                    continue
                
                # 从标题中提取股票代码 (如 "樂動機器人(01236)")
                code_match = re.search(r'\((\d{4,5})\)', title)
                stock_code = None
                if code_match:
                    stock_code = f"{code_match.group(1).zfill(5)}.HK"
                
                # 从标题中提取超购倍数（标题通常包含关键数字）
                oversub = None
                for pattern in self.PATTERNS['oversub']:
                    m = re.search(pattern, title)
                    if m:
                        try:
                            oversub = float(m.group(1))
                            break
                        except:
                            pass
                
                # 从标题中提取孖展金额
                margin = None
                for pattern in self.PATTERNS['margin']:
                    m = re.search(pattern, title)
                    if m:
                        try:
                            amount = float(m.group(1))
                            unit = m.group(2)
                            if unit in ['億', '亿']:
                                margin = amount
                            elif unit in ['萬', '万']:
                                margin = amount / 10000
                            break
                        except:
                            pass
                
                # 日期 - 从URL或附近元素提取
                date_match = re.search(r'(\d{8})', href)
                date_str = None
                if date_match:
                    d = date_match.group(1)
                    date_str = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
                
                articles.append({
                    'title': title,
                    'url': href,
                    'date': date_str,
                    'stock_code': stock_code,
                    'oversub_times': oversub,
                    'margin_amount': margin,
                })
            
            print(f"  第{page}页: {len(articles)} 篇文章")
        
        return articles
    
    def extract_from_article(self, url: str) -> Optional[Dict]:
        """
        从单篇文章中提取情绪数据
        
        Returns:
            {'oversub_times': float, 'margin_amount': float} or None
        """
        html = self._get(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 获取正文
        article = soup.find('article') or soup.find('div', class_='article-content')
        if article:
            text = article.get_text()
        else:
            text = soup.get_text()
        
        result = {}
        
        # 提取超购倍数
        for pattern in self.PATTERNS['oversub']:
            m = re.search(pattern, text)
            if m:
                try:
                    result['oversub_times'] = float(m.group(1))
                    break
                except:
                    pass
        
        # 提取孖展金额
        for pattern in self.PATTERNS['margin']:
            m = re.search(pattern, text)
            if m:
                try:
                    amount = float(m.group(1))
                    unit = m.group(2)
                    # 统一为亿港元
                    if unit in ['億', '亿']:
                        result['margin_amount'] = amount
                    elif unit in ['萬', '万']:
                        result['margin_amount'] = amount / 10000
                    break
                except:
                    pass
        
        return result if result else None
    
    def update_sentiment(self, stock_code: str, data: Dict, source: str = "etnet"):
        """将情绪数据存入数据库"""
        now = datetime.now()
        self.db.execute("""
            INSERT INTO market_sentiment (stock_code, record_date, record_time, source,
                                          margin_amount, oversub_times)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            stock_code,
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M'),
            source,
            data.get('margin_amount'),
            data.get('oversub_times'),
        ))
        print(f"   ✅ {stock_code} 情绪数据已更新: 超购={data.get('oversub_times')}x, 孖展={data.get('margin_amount')}亿")
    
    def run(self, max_pages: int = 3):
        """
        主入口：抓取etnet IPO新闻并提取情绪数据
        
        策略：
        1. 优先从新闻标题中提取超购倍数（标题通常包含关键数字）
        2. 如果标题中没有孖展金额，再访问文章正文提取
        """
        print("\n" + "="*60)
        print(" IPO情绪因子爬虫")
        print("="*60)
        
        articles = self.fetch_news_list(topic='margin', max_pages=max_pages)
        
        updated = 0
        for article in articles:
            code = article.get('stock_code')
            if not code:
                continue
            
            # 检查是否已存在今日记录
            existing = self.db.fetchone(
                "SELECT 1 FROM market_sentiment WHERE stock_code = ? AND record_date = date('now')",
                (code,)
            )
            if existing:
                print(f"   {code} 今日已有记录，跳过")
                continue
            
            data = {}
            
            # 优先使用标题中的超购倍数
            if article.get('oversub_times'):
                data['oversub_times'] = article['oversub_times']
                print(f"   {code} 标题提取: 超购={data['oversub_times']}x")
            
            # 如果需要孖展金额或标题没有超购，访问正文
            if not data:
                article_data = self.extract_from_article(article['url'])
                if article_data:
                    data.update(article_data)
            
            if data:
                self.update_sentiment(code, data)
                updated += 1
            else:
                print(f"   {code} 未提取到情绪数据")
            
            time.sleep(0.3)
        
        print(f"\n✅ 情绪因子更新完成: {updated} 只股票")
        return updated


if __name__ == '__main__':
    crawler = SentimentCrawler()
    crawler.run()
