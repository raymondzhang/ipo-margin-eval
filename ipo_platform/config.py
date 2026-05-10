# -*- coding: utf-8 -*-
"""平台配置"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "prospectus"
DB_PATH = DATA_DIR / "ipo_platform.db"
LOG_DIR = DATA_DIR / "logs"
REPORT_DIR = DATA_DIR / "reports"

for d in [DATA_DIR, PDF_DIR, LOG_DIR, REPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 披露易
HKEXNEWS_URL = "https://www.hkexnews.hk"

# 调度：交易日9:30轮询
SCHEDULE_TIME = "09:30"
TIMEZONE = "Asia/Hong_Kong"

# Tushare
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "")
