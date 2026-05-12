# -*- coding: utf-8 -*-
"""
===================================
数据源策略层 - 包初始化
===================================

本包实现策略模式管理多个数据源，实现：
1. 统一的数据获取接口
2. 自动故障切换
3. 防封禁流控策略

仅支持 **台股（TW）** 与 **美股（US）**：
- YfinanceFetcher (Priority 4) - Yahoo Finance（美股 + 台股兜底）
- FinmindFetcher  - 台股 K 线 / 财报 / 月营收 / 三大法人（FINMIND_TOKEN 设定时优先级提升为 0）

提示：优先级数字越小越优先，同优先级按初始化顺序排列
"""

from .base import BaseFetcher, DataFetcherManager
from .yfinance_fetcher import YfinanceFetcher
from .finmind_fetcher import FinmindFetcher
from .tw_market import (
    TW_INDEX_MAP,
    is_tw_stock_code,
    is_tw_index_code,
    get_tw_index_yf_symbol,
    to_tw_yf_code,
    normalize_tw_code,
)
from .us_index_mapping import is_us_index_code, is_us_stock_code, get_us_index_yf_symbol, US_INDEX_MAPPING

__all__ = [
    'BaseFetcher',
    'DataFetcherManager',
    'YfinanceFetcher',
    'FinmindFetcher',
    'is_us_index_code',
    'is_us_stock_code',
    'get_us_index_yf_symbol',
    'US_INDEX_MAPPING',
    'is_tw_stock_code',
    'is_tw_index_code',
    'get_tw_index_yf_symbol',
    'to_tw_yf_code',
    'normalize_tw_code',
    'TW_INDEX_MAP',
]
