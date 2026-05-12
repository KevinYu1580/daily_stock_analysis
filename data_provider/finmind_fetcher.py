# -*- coding: utf-8 -*-
"""
===================================
FinmindFetcher - 台股資料源 (Priority 0 for TW)
===================================

資料來源：FinMind (https://finmindtrade.com/)
- 免費版每小時 400 次、每日 6000 次（個人帳號）
- 提供台股 K 線、財報、月營收、三大法人買賣超

策略：
1. 早退路由：DataFetcherManager 識別到 4 碼台股 → 優先 Finmind → Yfinance
2. 內建 sqlite cache（TTL 6 小時）以節省呼叫額度
3. 缺 token 時 priority 降為 99（永遠落後）
"""

import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS
from .tw_market import is_tw_stock_code, normalize_tw_code

logger = logging.getLogger(__name__)


_DEFAULT_CACHE_PATH = Path.home() / ".cache" / "dsa" / "finmind_cache.sqlite"
_DEFAULT_CACHE_TTL = 6 * 3600  # 6 小時


class _FinmindCache:
    """簡易 sqlite cache，避免重複呼叫 FinMind API 浪費額度。"""

    def __init__(self, path: Optional[str] = None, ttl: int = _DEFAULT_CACHE_TTL):
        self.path = Path(path or os.getenv("FINMIND_CACHE_PATH", _DEFAULT_CACHE_PATH))
        self.ttl = ttl
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS finmind_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload   TEXT NOT NULL,
                    fetched_at INTEGER NOT NULL
                )
                """
            )

    def get(self, key: str) -> Optional[Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload, fetched_at FROM finmind_cache WHERE cache_key=?",
                (key,),
            ).fetchone()
        if not row:
            return None
        payload, fetched_at = row
        if int(time.time()) - int(fetched_at) > self.ttl:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None

    def set(self, key: str, value: Any) -> None:
        try:
            payload = json.dumps(value, ensure_ascii=False, default=str)
        except TypeError:
            return
        with self._connect() as conn:
            conn.execute(
                "REPLACE INTO finmind_cache(cache_key, payload, fetched_at) VALUES(?,?,?)",
                (key, payload, int(time.time())),
            )


class FinmindFetcher(BaseFetcher):
    """FinMind 台股資料源。"""

    name = "FinmindFetcher"

    def __init__(self):
        self._token = (os.getenv("FINMIND_TOKEN") or "").strip()
        # 沒 token 時降到最低優先級，避免擠到 cn 路由
        self.priority = int(os.getenv("FINMIND_PRIORITY", "0")) if self._token else 99
        self._api = None
        self._cache = _FinmindCache()

    # ---------- API ----------

    def _ensure_api(self):
        if self._api is not None:
            return self._api
        if not self._token:
            raise DataFetchError("FINMIND_TOKEN 未設定，無法呼叫 FinMind API")
        try:
            from FinMind.data import DataLoader
        except ImportError as e:
            raise DataFetchError("未安裝 FinMind 套件：pip install FinMind") from e
        api = DataLoader()
        try:
            api.login_by_token(api_token=self._token)
        except Exception as e:
            logger.warning(f"[FinMind] login_by_token 失敗，改用匿名額度: {e}")
        self._api = api
        return api

    def _cache_key(self, endpoint: str, **params) -> str:
        items = sorted((k, str(v)) for k, v in params.items())
        return f"{endpoint}|" + "|".join(f"{k}={v}" for k, v in items)

    def _call_with_cache(self, endpoint: str, fetch_callable, **params):
        key = self._cache_key(endpoint, **params)
        cached = self._cache.get(key)
        if cached is not None:
            logger.debug(f"[FinMind] cache hit: {key}")
            return cached
        result = fetch_callable()
        self._cache.set(key, result)
        return result

    # ---------- BaseFetcher 抽象實作 ----------

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        if not is_tw_stock_code(stock_code):
            raise DataFetchError(f"FinMind 僅支援台股，{stock_code} 非台股代碼")

        code = normalize_tw_code(stock_code)
        api = self._ensure_api()

        def _fetch():
            df = api.taiwan_stock_daily(
                stock_id=code, start_date=start_date, end_date=end_date
            )
            if df is None or df.empty:
                return []
            return df.to_dict(orient="records")

        rows = self._call_with_cache(
            "taiwan_stock_daily",
            _fetch,
            stock_id=code,
            start=start_date,
            end=end_date,
        )
        if not rows:
            raise DataFetchError(f"FinMind 未查詢到 {code} 的資料")
        return pd.DataFrame(rows)

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """FinMind taiwan_stock_daily 欄位：
        date, stock_id, Trading_Volume, Trading_money, open, max, min, close,
        spread, Trading_turnover
        """
        df = df.copy()

        rename_map = {
            "max": "high",
            "min": "low",
            "Trading_Volume": "volume",
            "Trading_money": "amount",
        }
        df = df.rename(columns=rename_map)

        if "close" in df.columns:
            df["pct_chg"] = df["close"].pct_change() * 100
            df["pct_chg"] = df["pct_chg"].fillna(0).round(2)

        df["code"] = normalize_tw_code(stock_code)

        keep = ["code"] + STANDARD_COLUMNS
        existing = [c for c in keep if c in df.columns]
        return df[existing]

    # ---------- 基本面 bundle ----------

    def get_fundamental_bundle(self, stock_code: str) -> Dict[str, Any]:
        """提供台股基本面：月營收、財報、三大法人買賣超。

        回傳 schema 與 AkshareFundamentalAdapter 對齊（growth/earnings/institution），
        以便 manager 與報告生成器無縫消費。
        """
        # 預設 schema（fail-open）
        result: Dict[str, Any] = {
            "status": "not_supported",
            "growth": {},
            "earnings": {},
            "institution": {},
            "source_chain": [],
            "errors": [],
            # FinMind 原始資料（保留供繁中報告語境取用）
            "tw_items": {},
        }

        if not is_tw_stock_code(stock_code):
            result["errors"].append("non-TW stock")
            return result

        code = normalize_tw_code(stock_code)
        try:
            api = self._ensure_api()
        except DataFetchError as e:
            result["errors"].append(str(e))
            return result

        today = datetime.now().date()
        one_year_ago = (today - timedelta(days=365)).isoformat()
        tw_items: Dict[str, Any] = {}

        # 月營收 → growth
        try:
            rev = self._call_with_cache(
                "taiwan_stock_month_revenue",
                lambda: api.taiwan_stock_month_revenue(
                    stock_id=code, start_date=one_year_ago
                ).to_dict(orient="records"),
                stock_id=code,
                start=one_year_ago,
            )
            recent = (rev or [])[-12:]
            tw_items["month_revenue"] = recent
            if recent:
                latest = recent[-1]
                result["growth"] = {
                    "latest_revenue": latest.get("revenue"),
                    "latest_month": latest.get("revenue_month"),
                    "latest_year": latest.get("revenue_year"),
                    "yoy_pct": latest.get("revenue_year_increasing_rate"),
                    "mom_pct": latest.get("revenue_month_increasing_rate"),
                    "history_12m": recent,
                }
            result["source_chain"].append({"provider": "FinMind", "endpoint": "taiwan_stock_month_revenue", "result": "ok"})
        except Exception as e:
            logger.warning(f"[FinMind] 取得月營收失敗 {code}: {e}")
            result["errors"].append(f"month_revenue: {e}")

        # 財報（每季） → earnings
        try:
            fs = self._call_with_cache(
                "taiwan_stock_financial_statement",
                lambda: api.taiwan_stock_financial_statement(
                    stock_id=code, start_date=one_year_ago
                ).to_dict(orient="records"),
                stock_id=code,
                start=one_year_ago,
            )
            recent_fs = (fs or [])[-80:]
            tw_items["financial_statement"] = recent_fs
            if recent_fs:
                eps_rows = [r for r in recent_fs if str(r.get("type", "")).upper() == "EPS"]
                result["earnings"] = {
                    "latest_quarter_date": recent_fs[-1].get("date"),
                    "eps_latest_quarters": eps_rows[-4:],
                    "raw_count": len(recent_fs),
                }
            result["source_chain"].append({"provider": "FinMind", "endpoint": "taiwan_stock_financial_statement", "result": "ok"})
        except Exception as e:
            logger.warning(f"[FinMind] 取得財報失敗 {code}: {e}")
            result["errors"].append(f"financial_statement: {e}")

        # 三大法人 → institution
        try:
            inst_start = (today - timedelta(days=30)).isoformat()
            inst = self._call_with_cache(
                "taiwan_stock_institutional_investors",
                lambda: api.taiwan_stock_institutional_investors(
                    stock_id=code, start_date=inst_start
                ).to_dict(orient="records"),
                stock_id=code,
                start=inst_start,
            )
            tw_items["institutional"] = inst or []
            if inst:
                # 近 5 日合計
                recent_inst = inst[-5 * 3:]  # 三大法人 × 5 日
                result["institution"] = {
                    "recent_5d": recent_inst,
                    "row_count": len(inst),
                }
            result["source_chain"].append({"provider": "FinMind", "endpoint": "taiwan_stock_institutional_investors", "result": "ok"})
        except Exception as e:
            logger.warning(f"[FinMind] 取得三大法人失敗 {code}: {e}")
            result["errors"].append(f"institutional: {e}")

        result["tw_items"] = tw_items

        has_content = any([result["growth"], result["earnings"], result["institution"]])
        result["status"] = "ok" if has_content else "partial"
        return result

    # ---------- 工具 ----------

    def get_stock_name(self, stock_code: str) -> Optional[str]:
        """從 FinMind taiwan_stock_info 取得中文股名。"""
        if not is_tw_stock_code(stock_code):
            return None
        code = normalize_tw_code(stock_code)
        try:
            api = self._ensure_api()
        except DataFetchError:
            return None
        try:
            df = self._call_with_cache(
                "taiwan_stock_info",
                lambda: api.taiwan_stock_info().to_dict(orient="records"),
            )
        except Exception as e:
            logger.warning(f"[FinMind] 取得股票清單失敗: {e}")
            return None
        for row in df or []:
            if str(row.get("stock_id", "")).strip() == code:
                name = str(row.get("stock_name", "")).strip()
                if name:
                    return name
        return None

    @property
    def is_available(self) -> bool:
        return bool(self._token)
