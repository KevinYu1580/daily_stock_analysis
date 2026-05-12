# -*- coding: utf-8 -*-
"""
大盤復盤市場區域配置

定義各市場區域的指數、新聞搜尋詞、Prompt 提示等元資料，
供 MarketAnalyzer 按 region 切換台股/美股復盤行為。
"""

from dataclasses import dataclass
from typing import List


@dataclass
class MarketProfile:
    """大盤復盤市場區域配置"""

    region: str  # "tw" | "us"
    # 用於判斷整體走勢的指數代碼，tw 用加權指數 TWII，us 用標普 SPX
    mood_index_code: str
    # 新聞搜尋關鍵詞
    news_queries: List[str]
    # 指數點評 Prompt 提示語
    prompt_index_hint: str
    # 市場概況是否包含漲跌家數、漲停跌停
    has_market_stats: bool
    # 市場概況是否包含板塊（類股）漲跌
    has_sector_rankings: bool


TW_PROFILE = MarketProfile(
    region="tw",
    mood_index_code="TWII",
    news_queries=[
        "台股 大盤 復盤",
        "Taiwan stock market TAIEX",
        "台股 三大法人 類股 焦點",
    ],
    prompt_index_hint="分析加權指數、櫃買指數、台灣 50 等各指數走勢特點，並留意三大法人買賣超與費半 SOX 連動",
    has_market_stats=False,
    has_sector_rankings=False,
)

US_PROFILE = MarketProfile(
    region="us",
    mood_index_code="SPX",
    news_queries=[
        "美股 大盤",
        "US stock market",
        "S&P 500 NASDAQ",
    ],
    prompt_index_hint="分析标普500、纳斯达克、道指等各指数走势特点",
    has_market_stats=False,
    has_sector_rankings=False,
)


def get_profile(region: str) -> MarketProfile:
    """根據 region 返回對應的 MarketProfile"""
    if region == "us":
        return US_PROFILE
    return TW_PROFILE
