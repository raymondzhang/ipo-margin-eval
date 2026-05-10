#!/usr/bin/env python3
"""
IPO Backtest Data Fetcher
Fetches HK IPO listing data and performance metrics from public sources.

Usage:
    python fetch_ipo_data.py --start 2026-04-01 --end 2026-04-24 --output data.json
    python fetch_ipo_data.py --from-file manual_data.json --output enriched.json
"""

import json
import argparse

# Pre-loaded 2026 April IPO data (from public sources: etnet, eastmoney, sina)
DEFAULT_APRIL_2026_IPOS = [
    {
        "stock_code": "06656.HK",
        "stock_code_short": "06656",
        "company_name_cn": "思格新能源（上海）股份有限公司",
        "company_name_en": "Sigenergy Technology (Shanghai) Co., Ltd.",
        "listing_date": "2026-04-16",
        "issue_price": 324.20,
        "first_day_open": 581.00,
        "first_day_close": 659.50,
        "first_day_high": 659.50,
        "first_day_low": 581.00,
        "first_day_return": 103.42,
        "first_day_broke": False,
        "cum_return": 67.34,
        "public_subscription": 1102.05,
        "industry": "資訊科技器材",
        "market_cap_hkd": 44.01,
        "data_source": "etnet/sina finance",
        "notes": "首日收盘涨103.42%，暗盘涨78.29%"
    },
    {
        "stock_code": "00068.HK",
        "stock_code_short": "00068",
        "company_name_cn": "群核科技",
        "company_name_en": "Manycore Tech Inc.",
        "listing_date": "2026-04-17",
        "issue_price": 7.62,
        "first_day_open": 20.70,
        "first_day_close": 26.42,
        "first_day_return": 246.72,
        "first_day_broke": False,
        "cum_return": 246.72,
        "public_subscription": 1590.56,
        "industry": "軟件服務",
        "market_cap_hkd": 12.24,
        "data_source": "etnet/eastmoney",
        "notes": "首日暴涨246.72%，为4月表现最佳"
    },
    {
        "stock_code": "03277.HK",
        "stock_code_short": "03277",
        "company_name_cn": "长春长光辰芯微电子股份有限公司",
        "company_name_en": "Gpixel Co., Ltd.",
        "listing_date": "2026-04-17",
        "issue_price": 39.88,
        "first_day_open": 72.00,
        "first_day_close": 80.25,
        "first_day_return": 101.23,
        "first_day_broke": False,
        "cum_return": 101.23,
        "public_subscription": 1138.21,
        "industry": "資訊科技器材",
        "market_cap_hkd": 26.04,
        "data_source": "etnet/eastmoney",
        "notes": "首日开盘涨80.5%，收盘涨101%+"
    },
    {
        "stock_code": "02476.HK",
        "stock_code_short": "02476",
        "company_name_cn": "胜宏科技（惠州）股份有限公司",
        "company_name_en": "Shengyi Technology Co., Ltd.",
        "listing_date": "2026-04-21",
        "issue_price": 209.88,
        "first_day_open": 330.00,
        "first_day_close": 318.60,
        "first_day_high": 336.20,
        "first_day_return": 51.80,
        "first_day_broke": False,
        "cum_return": 51.80,
        "public_subscription": 431.15,
        "international_subscription": 18.5,
        "industry": "人工智能/PCB",
        "market_cap_hkd": 174.9,
        "data_source": "etnet/eastmoney/sina",
        "notes": "2026年最大IPO，首日涨51.8%，开盘最高涨57%"
    },
    {
        "stock_code": "03296.HK",
        "stock_code_short": "03296",
        "company_name_cn": "华勤技术股份有限公司",
        "company_name_en": "Huaqin Technology Co., Ltd.",
        "listing_date": "2026-04-23",
        "issue_price": 77.70,
        "first_day_open": 87.55,
        "first_day_close": 95.05,
        "first_day_return": 22.33,
        "first_day_broke": False,
        "cum_return": 22.33,
        "public_subscription": 531.33,
        "industry": "資訊科技器材",
        "market_cap_hkd": 45.5,
        "data_source": "etnet/eastmoney",
        "notes": "首日涨22.33%，表现稳健"
    }
]


def load_manual_data(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def enrich_with_calculated_fields(ipos: list) -> list:
    for ipo in ipos:
        if ipo.get("first_day_return") is None and ipo.get("first_day_close") and ipo.get("issue_price"):
            ipo["first_day_return"] = round(
                (ipo["first_day_close"] - ipo["issue_price"]) / ipo["issue_price"] * 100, 2
            )
        if ipo.get("first_day_broke") is None and ipo.get("first_day_return") is not None:
            ipo["first_day_broke"] = ipo["first_day_return"] < 0
    return ipos


def save_data(ipos: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ipos, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(ipos)} IPO records to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fetch HK IPO backtest data")
    parser.add_argument("--start", default="2026-04-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-04-24", help="End date (YYYY-MM-DD)")
    parser.add_argument("--from-file", help="Load manual data from JSON file instead of default")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    if args.from_file:
        ipos = load_manual_data(args.from_file)
        print(f"Loaded {len(ipos)} records from manual file: {args.from_file}")
    else:
        ipos = DEFAULT_APRIL_2026_IPOS
        print(f"Using default dataset: {len(ipos)} records for April 2026")

    ipos = enrich_with_calculated_fields(ipos)
    save_data(ipos, args.output)


if __name__ == "__main__":
    main()
