# -*- coding: utf-8 -*-
"""
===================================
台股市場識別與指數映射
===================================

策略：純 4 碼數字 → 台股
- 與陸股 6 碼、港股 5 碼、美股字母完全不衝突
- 5 碼台股 ETF（00878 等）需顯式前綴 `tw00878`，否則會被港股判斷搶走
- 興櫃股無 yfinance 資料，本模組不支援
"""

from typing import Optional, Tuple

# Yahoo Finance 指數代碼對應
TW_INDEX_MAP = {
    "TWII": ("^TWII", "加權指數"),
    "TWO": ("^TWOII", "櫃買指數"),
    "TW50": ("0050.TW", "台灣 50"),
}


def is_tw_stock_code(code: str) -> bool:
    """判斷是否為台股代碼。

    規則：
    - 純 4 碼數字（2330、2317）
    - tw 前綴 + 4 碼數字（tw2330、tw00878 5 碼 ETF）
    - 已含 .TW/.TWO 後綴
    """
    if not code:
        return False
    c = str(code).strip().upper()

    if c.endswith(".TWO"):
        base = c[:-4]
        return base.isdigit() and len(base) in (4, 5)
    if c.endswith(".TW"):
        base = c[:-3]
        return base.isdigit() and len(base) in (4, 5)
    if c.startswith("TW") and c[2:].isdigit() and len(c) in (6, 7):
        return True

    return c.isdigit() and len(c) == 4


def is_tw_index_code(code: str) -> bool:
    if not code:
        return False
    return str(code).strip().upper() in TW_INDEX_MAP


def get_tw_index_yf_symbol(code: str) -> Tuple[Optional[str], Optional[str]]:
    """回傳 (yf_symbol, 中文名)，非台股指數則回傳 (None, None)。"""
    if not code:
        return None, None
    info = TW_INDEX_MAP.get(str(code).strip().upper())
    if info:
        return info
    return None, None


def to_tw_yf_code(code: str) -> str:
    """轉換台股代碼為 yfinance 格式（預設加 .TW 後綴）。

    上櫃股需手動傳 tw00xxx.TWO 或 .TWO 後綴格式。
    """
    if not code:
        return code
    c = str(code).strip().upper()
    if c.endswith(".TW") or c.endswith(".TWO"):
        return c
    if c.startswith("TW"):
        c = c[2:]
    return f"{c}.TW"


def normalize_tw_code(code: str) -> str:
    """回傳純數字代碼（供顯示/儲存用），去除 tw 前綴與 yfinance 後綴。"""
    if not code:
        return code
    c = str(code).strip().upper()
    if c.endswith(".TWO"):
        c = c[:-4]
    elif c.endswith(".TW"):
        c = c[:-3]
    if c.startswith("TW") and c[2:].isdigit():
        c = c[2:]
    return c
