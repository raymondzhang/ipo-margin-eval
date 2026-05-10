# -*- coding: utf-8 -*-
"""
IPO全自动化调度器

功能：
1. 每个交易日（周一至周五）8:30 自动扫描新股日历
2. 发现新IPO后自动入库 → 下载PDF → 解析 → 评分
3. 结果记录到system_log，支持邮件/企业微信通知（预留接口）

运行方式：
    python3 -m ipo_platform.core.scheduler
    
后台运行：
    nohup python3 -m ipo_platform.core.scheduler > logs/scheduler.log 2>&1 &
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ipo_platform.core.monitor import IPOCrawler
from ipo_platform.core.pdf_parser import ProspectusParser
from ipo_platform.core.scorer import IPOScorer
from ipo_platform.models.database import get_db

# APScheduler
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    raise ImportError("请安装APScheduler: python3 -m pip install apscheduler")


class IPOScheduler:
    """IPO自动扫描与评分调度器"""
    
    def __init__(self):
        self.crawler = IPOCrawler()
        self.parser = ProspectusParser()
        self.scorer = IPOScorer()
        self.db = get_db()
        self.scheduler = BackgroundScheduler()
    
    def _log(self, level: str, message: str):
        """记录系统日志"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level}] {message}")
        try:
            self.db.execute(
                "INSERT INTO system_log (level, message) VALUES (?, ?)",
                (level, message)
            )
        except Exception as e:
            print(f"  日志写入失败: {e}")
    
    def auto_scan_job(self):
        """
        核心自动任务：扫描 → 入库 → 下载 → 解析 → 评分 → 情绪数据
        """
        self._log("INFO", "=" * 60)
        self._log("INFO", "【自动扫描任务启动】")
        
        try:
            # 1. 扫描双源数据，发现新IPO
            ipos = self.crawler.run_pipeline(auto_download=True)
            
            # 2. 抓取情绪因子数据（孖展/超购）
            try:
                from ipo_platform.core.sentiment_crawler import SentimentCrawler
                sentiment_crawler = SentimentCrawler()
                sentiment_crawler.run(max_pages=2)
            except Exception as e:
                self._log("WARN", f"情绪因子爬虫失败: {e}")
            
            if not ipos:
                self._log("INFO", "未发现新IPO或状态变更")
                return
            
            # 3. 对新IPO进行PDF解析和评分
            for ipo in ipos:
                code = ipo['stock_code']
                name = ipo['stock_name']
                
                # 检查是否有手动覆盖配置（优先使用）
                from ipo_platform.config_manual import get_stock_override
                override = get_stock_override(code)
                
                # 如果有手动覆盖配置且包含完整数据，跳过PDF解析
                if override and override.cornerstone_count is not None:
                    self._log("INFO", f"{code} 使用手动覆盖配置，跳过PDF解析")
                    # 直接评分
                    try:
                        result = self.scorer.calculate(code)
                        self._log(
                            "INFO",
                            f"{code} 评分完成: {result['base_score']}/100 "
                            f"({result['category']}) | {result['leverage_advice']}"
                        )
                    except Exception as e:
                        self._log("ERROR", f"{code} 评分失败: {e}")
                    continue
                
                # 4. PDF解析（招股书已下载）
                pdf_path = self.crawler.pdf_dir / f"{code.replace('.', '_')}_prospectus.pdf"
                if pdf_path.exists():
                    self._log("INFO", f"{code} 开始PDF解析...")
                    try:
                        parse_result = self.parser.parse(str(pdf_path), code, name)
                        if parse_result:
                            self._log(
                                "INFO",
                                f"{code} PDF解析完成: "
                                f"财务={parse_result.revenue_2025 is not None}, "
                                f"基石={parse_result.cornerstone_count}家"
                            )
                        else:
                            self._log("WARN", f"{code} PDF解析无结果")
                    except Exception as e:
                        self._log("ERROR", f"{code} PDF解析失败: {e}")
                else:
                    self._log("WARN", f"{code} 招股书PDF未找到: {pdf_path}")
                
                # 5. 评分
                try:
                    result = self.scorer.calculate(code)
                    self._log(
                        "INFO",
                        f"{code} 评分完成: {result['base_score']}/100 "
                        f"({result['category']}) | {result['leverage_advice']}"
                    )
                except Exception as e:
                    self._log("ERROR", f"{code} 评分失败: {e}")
            
            self._log("INFO", "【自动扫描任务完成】")
            
        except Exception as e:
            self._log("ERROR", f"自动扫描任务异常: {e}")
    
    def start(self):
        """启动调度器（交易日上午8:30执行）"""
        #  cron: 周一到周五 8:30 执行
        trigger = CronTrigger(
            day_of_week='mon-fri',
            hour=8,
            minute=30,
        )
        
        self.scheduler.add_job(
            self.auto_scan_job,
            trigger=trigger,
            id='ipo_auto_scan',
            name='IPO自动扫描与评分',
            replace_existing=True,
        )
        
        self.scheduler.start()
        self._log("INFO", "调度器已启动 —— 交易日上午8:30自动扫描")
        self._log("INFO", "按 Ctrl+C 停止")
        
        # 保持主线程运行
        try:
            while True:
                import time
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            self._log("INFO", "调度器停止")
            self.scheduler.shutdown()
    
    def run_once(self):
        """立即执行一次扫描（用于手动触发或测试）"""
        self._log("INFO", "【手动触发扫描】")
        self.auto_scan_job()


def main():
    """入口函数"""
    import argparse
    parser = argparse.ArgumentParser(description='IPO自动扫描调度器')
    parser.add_argument('--once', action='store_true', help='立即执行一次扫描后退出')
    parser.add_argument('--code', type=str, help='指定股票代码评分（如 07666.HK）')
    args = parser.parse_args()
    
    if args.code:
        # 单只评分模式
        scorer = IPOScorer()
        result = scorer.calculate(args.code)
        scorer.print_report(result)
        return
    
    scheduler = IPOScheduler()
    if args.once:
        scheduler.run_once()
    else:
        scheduler.start()


if __name__ == '__main__':
    main()
