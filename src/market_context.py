# -*- coding: utf-8 -*-
"""
Market context detection for LLM prompts.

Detects the market (A-shares, HK, US) from a stock code and returns
market-specific role descriptions so prompts are not hardcoded to a
single market.

Fixes: https://github.com/ZhuLinsen/daily_stock_analysis/issues/644
"""

import re
from typing import Optional


def detect_market(stock_code: Optional[str]) -> str:
    """Detect market from stock code.

    Returns:
        One of 'cn', 'hk', 'us', 'tw', or 'cn' as fallback.
    """
    if not stock_code:
        return "cn"

    code = stock_code.strip().upper()

    # 台股指數
    if code in {"TWII", "TWO", "TW50"}:
        return "tw"
    # 台股：純 4 碼數字、tw 前綴、.TW(.TWO) 後綴
    if code.endswith(".TW") or code.endswith(".TWO"):
        return "tw"
    if code.startswith("TW") and code[2:].isdigit() and len(code) in (6, 7):
        return "tw"
    if code.isdigit() and len(code) == 4:
        return "tw"

    # HK stocks: HK00700, 00700.HK, or 5-digit pure numbers
    if code.startswith("HK") or code.endswith(".HK"):
        return "hk"
    lower = code.lower()
    if lower.endswith(".hk"):
        return "hk"
    # 5-digit pure numbers are HK (A-shares are 6-digit)
    if code.isdigit() and len(code) == 5:
        return "hk"

    # US stocks: 1-5 uppercase letters (AAPL, TSLA, GOOGL)
    # Also handles suffixed forms like BRK.B
    if re.match(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$', code):
        return "us"

    # Default: A-shares (6-digit numbers like 600519, 000001)
    return "cn"


# -- Market-specific role descriptions --

_MARKET_ROLES = {
    "cn": {
        "zh": " A 股",
        "en": "China A-shares",
    },
    "hk": {
        "zh": "港股",
        "en": "Hong Kong stock",
    },
    "us": {
        "zh": "美股",
        "en": "US stock",
    },
    "tw": {
        "zh": "台股",
        "en": "Taiwan stock",
    },
}

_MARKET_GUIDELINES = {
    "cn": {
        "zh": (
            "- 本次分析对象为 **A 股**（中国沪深交易所上市股票）。\n"
            "- 请关注 A 股特有的涨跌停机制（±10%/±20%/±30%）、T+1 交易制度及相关政策因素。"
        ),
        "en": (
            "- This analysis covers a **China A-share** (listed on Shanghai/Shenzhen exchanges).\n"
            "- Consider A-share-specific rules: daily price limits (±10%/±20%/±30%), T+1 settlement, and PRC policy factors."
        ),
    },
    "hk": {
        "zh": (
            "- 本次分析对象为 **港股**（香港交易所上市股票）。\n"
            "- 港股无涨跌停限制，支持 T+0 交易，需关注港币汇率、南北向资金流及联交所特有规则。"
        ),
        "en": (
            "- This analysis covers a **Hong Kong stock** (listed on HKEX).\n"
            "- HK stocks have no daily price limits, allow T+0 trading. Consider HKD FX, Southbound/Northbound flows, and HKEX-specific rules."
        ),
    },
    "us": {
        "zh": (
            "- 本次分析对象为 **美股**（美国交易所上市股票）。\n"
            "- 美股无涨跌停限制（但有熔断机制），支持 T+0 交易和盘前盘后交易，需关注美元汇率、美联储政策及 SEC 监管动态。"
        ),
        "en": (
            "- This analysis covers a **US stock** (listed on NYSE/NASDAQ).\n"
            "- US stocks have no daily price limits (but have circuit breakers), allow T+0 and pre/after-market trading. Consider USD FX, Fed policy, and SEC regulations."
        ),
    },
    "tw": {
        "zh": (
            "- 本次分析對象為 **台股**（台灣證券交易所/櫃買中心上市櫃股票）。\n"
            "- 台股漲跌幅限制 ±10%（一般股票），新上市前 5 個交易日不設限；採 T+2 交割（券款交割）。\n"
            "- 須留意三大法人買賣超（外資、投信、自營商）動向，外資籌碼為主導力量。\n"
            "- 月營收於每月 10 日前公告，年報/季報依規定揭露；觀察月營收 YoY/MoM 為短線重要訊號。\n"
            "- 加權指數受權值股（台積電、鴻海、聯發科等）主導，分析個股需考量大盤連動與類股輪動。\n"
            "- 美股費半（SOX）、AI/HPC 供應鏈訊息對台股科技類股影響顯著。\n"
            "- 所有輸出（包含 trend_prediction、operation_advice、敘述性摘要）必須使用**繁體中文**，禁止使用簡體字。"
        ),
        "en": (
            "- This analysis covers a **Taiwan stock** (listed on TWSE or TPEx).\n"
            "- Daily price limit ±10% (waived for first 5 days of newly listed stocks); T+2 settlement.\n"
            "- Pay attention to the Three Major Institutional Investors (Foreign, Investment Trust, Dealer) — foreign capital is the dominant force.\n"
            "- Monthly revenue is disclosed before the 10th of each month; YoY/MoM revenue growth is a key short-term signal.\n"
            "- The TAIEX is dominated by heavyweight stocks (TSMC, Hon Hai, MediaTek). Consider index correlation and sector rotation.\n"
            "- US semiconductor index (SOX) and AI/HPC supply chain news significantly impact Taiwan tech stocks."
        ),
    },
}


def get_market_role(stock_code: Optional[str], lang: str = "zh") -> str:
    """Return market-specific role description for LLM prompt.

    Args:
        stock_code: The stock code being analyzed.
        lang: 'zh' or 'en'.

    Returns:
        Role string like 'A 股投资分析' or 'US stock investment analysis'.
    """
    market = detect_market(stock_code)
    lang_key = "en" if lang == "en" else "zh"
    return _MARKET_ROLES.get(market, _MARKET_ROLES["cn"])[lang_key]


def get_market_guidelines(stock_code: Optional[str], lang: str = "zh") -> str:
    """Return market-specific analysis guidelines for LLM prompt.

    Args:
        stock_code: The stock code being analyzed.
        lang: 'zh' or 'en'.

    Returns:
        Multi-line string with market-specific guidelines.
    """
    market = detect_market(stock_code)
    lang_key = "en" if lang == "en" else "zh"
    return _MARKET_GUIDELINES.get(market, _MARKET_GUIDELINES["cn"])[lang_key]
