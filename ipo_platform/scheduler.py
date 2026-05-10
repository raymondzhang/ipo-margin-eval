# -*- coding: utf-8 -*-
"""
调度器主入口

功能：
1. 每个交易日定时轮询披露易，发现新IPO
2. 自动下载招股书PDF
3. 触发评分流程
4. 生成报告+公众号推文

运行方式:
    python scheduler.py          # 单次运行
    python scheduler.py --daemon # 后台常驻（APScheduler）
"""

import argparse
import time
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ipo_platform.config import SCHEDULE_TIME, TIMEZONE, LOG_DIR
from ipo_platform.core.monitor import HKEXMonitor, MockMonitor
from ipo_platform.core.scorer import IPOScorer
from ipo_platform.models.database import get_db


def is_trading_day() -> bool:
    """判断今天是否为港股交易日（简化版，实际应调用交易日历API）"""
    from datetime import date
    today = date.today()
    # 周末休市
    if today.weekday() >= 5:
        return False
    # TODO: 接入Tushare trade_cal接口排除公众假期
    return True


def log(level: str, module: str, message: str):
    """记录系统日志"""
    db = get_db()
    db.execute(
        "INSERT INTO system_log (level, module, message) VALUES (?, ?, ?)",
        (level, module, message)
    )
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] [{module}] {message}")


def run_pipeline(use_mock: bool = False):
    """
    完整流水线：
    1. 发现新IPO
    2. 下载招股书
    3. 解析结构化数据（预留接口）
    4. 自动评分
    5. 生成报告（预留接口）
    """
    print("\n" + "="*70)
    print(f" IPO流水线启动 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    if not is_trading_day():
        log('INFO', 'scheduler', '今日非交易日，跳过')
        return
    
    # 1. 发现新IPO
    monitor = MockMonitor() if use_mock else HKEXMonitor()
    new_ipos = monitor.check_new_ipos()
    
    if not new_ipos:
        log('INFO', 'monitor', '未发现新IPO')
        return
    
    log('INFO', 'monitor', f'发现 {len(new_ipos)} 个新IPO')
    
    scorer = IPOScorer()
    
    for ipo in new_ipos:
        code = ipo['stock_code']
        name = ipo.get('stock_name', '')
        
        try:
            # 2. 入库
            monitor.save_to_db(ipo)
            log('INFO', 'pipeline', f'[{code}] 已入库')
            
            # 3. 下载招股书（如果有URL）
            pdf_url = ipo.get('prospectus_pdf_url') or ipo.get('prospectus_url')
            if pdf_url:
                pdf_path = monitor.download_prospectus(code, pdf_url)
                if pdf_path:
                    log('INFO', 'pipeline', f'[{code}] 招股书已下载: {pdf_path}')
                    # TODO: 触发PDF解析引擎，自动提取结构化数据写入 ipo_financials / ipo_cornerstones
            
            # 4. 自动评分（需先确保基础数据已入库）
            # 注意：如果financials/cornerstones还未录入，评分会基于默认值
            # 实际运行中，PDF解析完成后才触发评分
            
            # result = scorer.calculate(code, q1_break_rate=10.0, hsi_return=3.99)
            # scorer.print_report(result)
            # log('INFO', 'scorer', f'[{code}] 评分完成: {result["total_score"]}/110')
            
            # 5. 生成报告（预留）
            # TODO: 调用报告生成器，输出 docx + HTML
            # report_path = generate_report(code)
            # log('INFO', 'reporter', f'[{code}] 报告已生成: {report_path}')
            
        except Exception as e:
            log('ERROR', 'pipeline', f'[{code}] 处理失败: {str(e)}')
    
    print("\n" + "="*70)
    print(" 流水线完成")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(description='港股IPO数据平台调度器')
    parser.add_argument('--daemon', action='store_true', help='后台常驻模式')
    parser.add_argument('--mock', action='store_true', help='使用模拟数据（测试用）')
    parser.add_argument('--run-now', action='store_true', help='立即执行一次')
    args = parser.parse_args()
    
    if args.run_now:
        run_pipeline(use_mock=args.mock)
        return
    
    if args.daemon:
        print(f"启动后台调度器，每日 {SCHEDULE_TIME} 执行（时区: {TIMEZONE}）")
        scheduler = BackgroundScheduler(timezone=TIMEZONE)
        
        # 每个交易日9:30执行
        hour, minute = map(int, SCHEDULE_TIME.split(':'))
        trigger = CronTrigger(hour=hour, minute=minute, day_of_week='mon-fri')
        
        scheduler.add_job(run_pipeline, trigger, args=[args.mock], id='ipo_daily_scan')
        scheduler.start()
        
        print("调度器已启动，按 Ctrl+C 停止")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n停止调度器")
            scheduler.shutdown()
    else:
        # 默认单次运行
        run_pipeline(use_mock=args.mock)


if __name__ == '__main__':
    main()
