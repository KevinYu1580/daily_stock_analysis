# -*- coding: utf-8 -*-
"""
Shared stock code utilities (台股 + 美股).

支援代碼格式：
- 台股：2330、tw2330、tw00878（5 碼 ETF）、2330.TW、00878.TWO
- 台股指數：TWII、TWO、TW50
- 美股 ticker：AAPL、TSLA、BRK.B、AAPL.US
"""

from __future__ import annotations

import re
from typing import Optional

_TW_BARE_RE = re.compile(r"^\d{4}$")              # 純 4 碼數字（一般股票）
_TW_PREFIX_RE = re.compile(r"^TW(\d{4,5})$")      # tw 前綴 + 4~5 碼（含 ETF）
_TW_SUFFIX_RE = re.compile(r"^(\d{4,5})\.TWO?$")  # .TW / .TWO 後綴
_US_TICKER_RE = re.compile(r"^[A-Z]{1,5}(?:\.(?:US|[A-Z]))?$")
_TW_INDEX = {"TWII", "TWO", "TW50"}


def is_code_like(value: str) -> bool:
    """是否看起來像受支援的股票/指數代碼（台股 / 美股）。"""
    if not value:
        return False
    text = value.strip().upper()
    if text in _TW_INDEX:
        return True
    return normalize_code(text) is not None


def normalize_code(raw: str) -> Optional[str]:
    """正規化並驗證單一股票代碼（台股 / 美股）。

    回傳：
    - 台股：一律回傳純數字代碼（2330、00878）
    - 台股指數：原樣回傳（TWII / TWO / TW50）
    - 美股：原樣回傳 ticker（AAPL、BRK.B）
    - 無法識別：None
    """
    if not raw:
        return None
    text = raw.strip().upper()
    if not text:
        return None

    m = _TW_SUFFIX_RE.match(text)
    if m:
        return m.group(1)
    m = _TW_PREFIX_RE.match(text)
    if m:
        return m.group(1)
    if _TW_BARE_RE.match(text):
        return text
    if text in _TW_INDEX:
        return text
    if _US_TICKER_RE.match(text):
        return text
    return None
