# -*- coding: utf-8 -*-
"""数据库模型 — 港股IPO平台核心表结构"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

SCHEMA = """
-- =====================================================
-- 1. IPO基础信息表（所有进入系统的IPO）
-- =====================================================
CREATE TABLE IF NOT EXISTS ipo_base (
    stock_code      TEXT PRIMARY KEY,           -- 如 06871.HK
    stock_name      TEXT NOT NULL,
    name_en         TEXT,
    industry        TEXT,
    industry_cat    TEXT,                       -- 硬科技/医疗/消费/金融...
    reg_type        TEXT,                       -- 主板/18A/18C/W股/AH
    sponsor         TEXT,                       -- 保荐人，逗号分隔
    sponsor_primary TEXT,                       -- 第一保荐人
    
    -- 时间线
    hearing_date    TEXT,                       -- 通过聆讯日
    prospectus_date TEXT,                       -- 招股书发布日
    ipo_start_date  TEXT,                       -- 招股开始日
    ipo_end_date    TEXT,                       -- 招股截止日
    list_date       TEXT,                       -- 上市日
    
    -- 发行结构
    total_shares    REAL,                       -- 发行总股数（万股）
    public_pct      REAL,                       -- 公开发售比例 %
    intl_pct        REAL,                       -- 国际配售比例 %
    price_low       REAL,                       -- 招股价下限
    price_high      REAL,                       -- 招股价上限
    offer_price     REAL,                       -- 最终定价
    raise_amount    REAL,                       -- 募资额（亿港元）
    
    -- 稳价
    stabilizer      TEXT,                       -- 稳价人
    has_greenshoe   INTEGER DEFAULT 0,          -- 0/1
    greenshoe_pct   REAL,                       -- 绿鞋比例
    
    -- 状态
    status          TEXT DEFAULT 'prospectus',  -- prospectus/ipoing/listed/tracked
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. 财务数据表
-- =====================================================
CREATE TABLE IF NOT EXISTS ipo_financials (
    stock_code      TEXT PRIMARY KEY,
    revenue_2023    REAL,
    revenue_2024    REAL,
    revenue_2025    REAL,
    net_profit_2023 REAL,
    net_profit_2024 REAL,
    net_profit_2025 REAL,
    gross_margin    REAL,
    rmb_to_hkd_rate REAL DEFAULT 1.09,
    FOREIGN KEY (stock_code) REFERENCES ipo_base(stock_code)
);

-- =====================================================
-- 3. 基石投资者表
-- =====================================================
CREATE TABLE IF NOT EXISTS ipo_cornerstones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code      TEXT NOT NULL,
    investor_name   TEXT,
    amount_hkd      REAL,                       -- 认购金额（亿港元）
    lockup_months   INTEGER DEFAULT 6,
    is_star         INTEGER DEFAULT 0,          -- 1=知名机构(GIC/贝莱德/高瓴等)
    FOREIGN KEY (stock_code) REFERENCES ipo_base(stock_code)
);

-- =====================================================
-- 4. 市场情绪表（孖展/超购，定时更新）
-- =====================================================
CREATE TABLE IF NOT EXISTS market_sentiment (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code      TEXT NOT NULL,
    record_date     TEXT,                       -- YYYY-MM-DD
    record_time     TEXT,                       -- HH:MM
    source          TEXT,                       -- asiatimes/futu/huasheng
    margin_amount   REAL,                       -- 孖展金额（亿港元）
    oversub_times   REAL,                       -- 超购倍数
    subscribers     INTEGER,                    -- 认购人数
    sentiment_score REAL,                       -- 0-100 热度评分
    UNIQUE(stock_code, record_date, record_time, source)
);

-- =====================================================
-- 5. 评分结果表
-- =====================================================
CREATE TABLE IF NOT EXISTS ipo_scores (
    score_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code      TEXT NOT NULL,
    scored_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    
    -- 7维度得分
    profitability   INTEGER,                    -- 盈利 0-30
    allocation      INTEGER,                    -- 分配 0-10
    cornerstone     INTEGER,                    -- 基石 0-15
    pricing         INTEGER,                    -- 定价 0-20
    stabilization   INTEGER,                    -- 稳价 0-10
    q1_break_rate   INTEGER,                    -- Q1破发率 0-15
    hsi_monthly     INTEGER,                    -- HSI月度 0-10
    
    base_score      INTEGER,                    -- 基础分 0-100
    total_score     INTEGER,                    -- 含稳价 0-110
    
    -- 分类
    category        TEXT,                       -- whitelist/greylist/blacklist
    leverage_advice TEXT,                       -- 杠杆建议
    risk_warning    TEXT,                       -- 风险提示
    
    -- 证据链JSON
    evidence_json   TEXT,
    FOREIGN KEY (stock_code) REFERENCES ipo_base(stock_code)
);

-- =====================================================
-- 6. 上市后跟踪表（验证评分模型）
-- =====================================================
CREATE TABLE IF NOT EXISTS post_listing (
    stock_code      TEXT PRIMARY KEY,
    list_date       TEXT,
    
    -- 首日表现
    d1_open         REAL,
    d1_high         REAL,
    d1_low          REAL,
    d1_close        REAL,
    d1_return       REAL,                       -- 首日涨幅%
    d1_volume       REAL,
    
    -- 首周/首月
    w1_close        REAL,
    w1_return       REAL,
    m1_close        REAL,
    m1_return       REAL,
    
    -- 极值
    max_price       REAL,
    max_return      REAL,                       -- 上市后最高涨幅%
    min_price       REAL,
    max_drawdown    REAL,                       -- 最大回撤%
    
    -- 与评分对比
    predicted_score INTEGER,
    actual_return   REAL,
    prediction_hit  INTEGER DEFAULT 0,          -- 1=预测正确(白名单涨/黑名单跌)
    
    last_update     TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_code) REFERENCES ipo_base(stock_code)
);

-- =====================================================
-- 7. 系统日志表
-- =====================================================
CREATE TABLE IF NOT EXISTS system_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    log_time        TEXT DEFAULT CURRENT_TIMESTAMP,
    level           TEXT DEFAULT 'INFO',
    module          TEXT,
    message         TEXT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ipo_status ON ipo_base(status);
CREATE INDEX IF NOT EXISTS idx_ipo_list_date ON ipo_base(list_date);
CREATE INDEX IF NOT EXISTS idx_sentiment_code ON market_sentiment(stock_code);
CREATE INDEX IF NOT EXISTS idx_scores_code ON ipo_scores(stock_code);
CREATE INDEX IF NOT EXISTS idx_post_listing_code ON post_listing(stock_code);
"""


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_schema()
    
    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def init_schema(self):
        with self.connect() as conn:
            conn.executescript(SCHEMA)
    
    def execute(self, sql, params=()):
        with self.connect() as conn:
            return conn.execute(sql, params)
    
    def fetchall(self, sql, params=()):
        with self.connect() as conn:
            return conn.execute(sql, params).fetchall()
    
    def fetchone(self, sql, params=()):
        with self.connect() as conn:
            return conn.execute(sql, params).fetchone()


# 单例
db = None

def get_db(db_path=None):
    global db
    if db is None:
        from ipo_platform.config import DB_PATH
        db = Database(db_path or str(DB_PATH))
    return db
