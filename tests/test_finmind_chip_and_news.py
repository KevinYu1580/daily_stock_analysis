# -*- coding: utf-8 -*-
"""
===================================
FinMind 台股籌碼面 & 台股新聞來源 tests
===================================

覆蓋：
- ChipDistribution(market_type="tw") 的 to_dict / get_chip_status
- src.analyzer._build_chip_structure_from_data / _derive_chip_health_tw 的台股分支
- FinmindFetcher.get_chip_distribution（mock FinMind API）
- FinMindNewsSearchProvider 的代碼解析、非台股讓位、結果映射（mock DataLoader）
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

try:
    import litellm  # noqa: F401
except ModuleNotFoundError:
    sys.modules["litellm"] = MagicMock()

import pandas as pd

from data_provider.realtime_types import ChipDistribution
from src.analyzer import _build_chip_structure_from_data, _derive_chip_health_tw


_TW_METRICS = {
    "inst_net_5d_lots": -2763,
    "inst_net_5d_foreign_lots": -3042,
    "inst_streak_days": -2,
    "margin_balance_lots": 13038,
    "margin_chg_5d_lots": 633,
    "short_balance_lots": 59,
    "foreign_holding_pct": 12.32,
    "foreign_holding_chg_pp": -0.13,
}


class TestChipDistributionTw(unittest.TestCase):
    def _tw_chip(self, **overrides):
        m = dict(_TW_METRICS)
        m.update(overrides)
        return ChipDistribution(code="1609", date="2026-05-11", source="finmind",
                                market_type="tw", tw_metrics=m)

    def test_is_tw_flag(self):
        self.assertTrue(self._tw_chip().is_tw)
        self.assertFalse(ChipDistribution(code="600519").is_tw)

    def test_to_dict_tw_omits_ashare_cost_fields(self):
        d = self._tw_chip().to_dict()
        self.assertEqual(d["market_type"], "tw")
        self.assertIn("tw_metrics", d)
        self.assertNotIn("profit_ratio", d)
        self.assertNotIn("concentration_90", d)
        self.assertEqual(d["tw_metrics"]["foreign_holding_pct"], 12.32)

    def test_to_dict_cn_keeps_cost_fields(self):
        d = ChipDistribution(code="600519", profit_ratio=0.6, concentration_90=0.1).to_dict()
        self.assertEqual(d["market_type"], "cn")
        self.assertIn("profit_ratio", d)
        self.assertNotIn("tw_metrics", d)

    def test_chip_status_tw_mentions_all_dimensions(self):
        s = self._tw_chip().get_chip_status(35.0)
        self.assertIn("三大法人", s)
        self.assertIn("卖超", s)
        self.assertIn("外资持股", s)
        self.assertIn("融资余额", s)

    def test_chip_status_tw_empty_metrics(self):
        c = ChipDistribution(code="1609", market_type="tw", tw_metrics={})
        self.assertEqual(c.get_chip_status(0), "台股筹码面数据缺失")


class TestBuildChipStructureTw(unittest.TestCase):
    def test_tw_object_input_na_for_ashare_fields(self):
        chip = ChipDistribution(code="1609", market_type="tw", tw_metrics=dict(_TW_METRICS))
        out = _build_chip_structure_from_data(chip, language="zh")
        self.assertEqual(out["profit_ratio"], "N/A")
        self.assertEqual(out["avg_cost"], "N/A")
        self.assertEqual(out["concentration"], "N/A")
        self.assertTrue(out["chip_health"])  # 非空

    def test_tw_dict_input(self):
        out = _build_chip_structure_from_data(
            {"market_type": "tw", "tw_metrics": dict(_TW_METRICS)}, language="zh"
        )
        self.assertEqual(out["concentration"], "N/A")

    def test_cn_input_unchanged(self):
        chip = ChipDistribution(code="600519", profit_ratio=0.6, concentration_90=0.1)
        out = _build_chip_structure_from_data(chip, language="zh")
        self.assertEqual(out["profit_ratio"], "60.0%")
        self.assertNotEqual(out["concentration"], "N/A")

    def test_derive_chip_health_tw_warn_on_sell_streak(self):
        h = _derive_chip_health_tw({"inst_streak_days": -3}, language="zh")
        self.assertTrue(h)
        # 連賣 3 日 → 與「警惕」同類（不直接斷字串以免綁定本地化文案）
        self.assertEqual(h, _derive_chip_health_tw({"inst_streak_days": -5}, language="zh"))

    def test_derive_chip_health_tw_healthy_on_buy_streak(self):
        healthy = _derive_chip_health_tw({"inst_streak_days": 4}, language="zh")
        warn = _derive_chip_health_tw({"inst_streak_days": -4}, language="zh")
        self.assertNotEqual(healthy, warn)


class TestFinmindGetChipDistribution(unittest.TestCase):
    def _make_api(self):
        api = MagicMock()
        # 三大法人：兩日，最新日法人合計卖超
        api.taiwan_stock_institutional_investors.return_value = pd.DataFrame([
            {"date": "2026-05-08", "stock_id": "1609", "name": "Foreign_Investor", "buy": 100000, "sell": 50000},
            {"date": "2026-05-08", "stock_id": "1609", "name": "Investment_Trust", "buy": 0, "sell": 10000},
            {"date": "2026-05-11", "stock_id": "1609", "name": "Foreign_Investor", "buy": 20000, "sell": 120000},
            {"date": "2026-05-11", "stock_id": "1609", "name": "Investment_Trust", "buy": 0, "sell": 5000},
        ])
        api.taiwan_stock_margin_purchase_short_sale.return_value = pd.DataFrame([
            {"date": "2026-05-08", "MarginPurchaseTodayBalance": 12400, "ShortSaleTodayBalance": 40},
            {"date": "2026-05-11", "MarginPurchaseTodayBalance": 13038, "ShortSaleTodayBalance": 59},
        ])
        api.taiwan_stock_shareholding.return_value = pd.DataFrame([
            {"date": "2026-05-08", "ForeignInvestmentSharesRatio": 12.45},
            {"date": "2026-05-11", "ForeignInvestmentSharesRatio": 12.32},
        ])
        return api

    def test_returns_tw_chip_for_tw_code(self):
        from data_provider.finmind_fetcher import FinmindFetcher
        f = FinmindFetcher.__new__(FinmindFetcher)  # 跳過 __init__（不需 token）
        f._cache = MagicMock()
        f._cache.get.return_value = None
        f._cache.set.return_value = None
        api = self._make_api()
        with patch.object(FinmindFetcher, "_ensure_api", return_value=api):
            chip = f.get_chip_distribution("1609")
        self.assertIsNotNone(chip)
        self.assertEqual(chip.market_type, "tw")
        m = chip.tw_metrics
        # 最新日（05-11）法人合計 = (20000-120000)+(0-5000) = -105000 股；近2日合計再加 05-08 的 (50000-10000)=40000 → -65000 股 → -65 张
        self.assertEqual(m["inst_net_5d_lots"], -65)
        self.assertEqual(m["inst_streak_days"], -1)  # 僅最新一日為卖超（05-08 為買超）
        self.assertEqual(m["margin_balance_lots"], 13038)
        self.assertEqual(m["short_balance_lots"], 59)
        self.assertEqual(m["foreign_holding_pct"], 12.32)

    def test_returns_none_for_non_tw_code(self):
        from data_provider.finmind_fetcher import FinmindFetcher
        f = FinmindFetcher.__new__(FinmindFetcher)
        self.assertIsNone(f.get_chip_distribution("AAPL"))
        self.assertIsNone(f.get_chip_distribution("600519"))

    def test_returns_none_when_all_datasets_empty(self):
        from data_provider.finmind_fetcher import FinmindFetcher
        f = FinmindFetcher.__new__(FinmindFetcher)
        f._cache = MagicMock()
        f._cache.get.return_value = None
        api = MagicMock()
        api.taiwan_stock_institutional_investors.return_value = pd.DataFrame()
        api.taiwan_stock_margin_purchase_short_sale.return_value = pd.DataFrame()
        api.taiwan_stock_shareholding.return_value = pd.DataFrame()
        with patch.object(FinmindFetcher, "_ensure_api", return_value=api):
            self.assertIsNone(f.get_chip_distribution("1609"))


class TestFinMindNewsSearchProvider(unittest.TestCase):
    def _provider(self):
        from src.search_service import FinMindNewsSearchProvider
        return FinMindNewsSearchProvider(token="dummy-token")

    def test_is_available_requires_token(self):
        from src.search_service import FinMindNewsSearchProvider
        self.assertTrue(FinMindNewsSearchProvider(token="x").is_available)
        self.assertFalse(FinMindNewsSearchProvider(token="").is_available)
        self.assertFalse(FinMindNewsSearchProvider(token=None).is_available)

    def test_resolve_tw_code(self):
        from src.search_service import FinMindNewsSearchProvider as P
        self.assertEqual(P._resolve_tw_code("台積電 2330 股票 最新消息", None), "2330")
        self.assertEqual(P._resolve_tw_code("anything", "1609"), "1609")
        self.assertIsNone(P._resolve_tw_code("Apple AAPL latest news", None))
        self.assertIsNone(P._resolve_tw_code("Apple AAPL latest news", "AAPL"))
        self.assertIsNone(P._resolve_tw_code("大盘 复盘", None))

    def test_search_passes_on_non_tw_without_key_error(self):
        p = self._provider()
        resp = p.search("A股 大盘 复盘", max_results=5, days=3, stock_code="")
        self.assertFalse(resp.success)
        self.assertEqual(p._name, "FinMindNews")
        # 不走 _execute_search → 不記 key 錯誤
        self.assertEqual(p._key_errors.get("dummy-token", 0), 0)

    def test_search_returns_mapped_results_for_tw(self):
        p = self._provider()
        fake_loader = MagicMock()
        fake_loader.taiwan_stock_news.return_value = pd.DataFrame([
            {"date": "2026-05-11 09:00:00", "stock_id": "2330", "link": "http://a", "source": "鉅亨網", "title": "新聞A"},
            {"date": "2026-05-11 12:30:00", "stock_id": "2330", "link": "http://b", "source": "經濟日報", "title": "新聞B"},
            {"date": "2026-05-10 08:00:00", "stock_id": "2330", "link": "http://c", "source": "工商時報", "title": "新聞A"},  # 同標題去重
        ])
        with patch.object(type(p), "_ensure_loader", return_value=fake_loader):
            resp = p.search("台積電 2330 最新 新聞", max_results=5, days=3, stock_code="2330")
        self.assertTrue(resp.success)
        titles = [r.title for r in resp.results]
        self.assertEqual(titles, ["新聞B", "新聞A"])  # 新→舊 + 去重
        self.assertEqual(resp.results[0].published_date, "2026-05-11")
        self.assertEqual(resp.results[0].source, "經濟日報")

    def test_search_empty_news(self):
        p = self._provider()
        fake_loader = MagicMock()
        fake_loader.taiwan_stock_news.return_value = pd.DataFrame()
        with patch.object(type(p), "_ensure_loader", return_value=fake_loader):
            resp = p.search("台積電 2330 最新 新聞", max_results=5, days=3, stock_code="2330")
        self.assertTrue(resp.success)
        self.assertEqual(resp.results, [])


class TestSearchServiceFinmindRegistration(unittest.TestCase):
    def test_provider_registered_when_token_given(self):
        from src.search_service import SearchService, FinMindNewsSearchProvider
        svc = SearchService(searxng_public_instances_enabled=False, finmind_token="tok")
        self.assertIsInstance(svc._providers[0], FinMindNewsSearchProvider)

    def test_provider_absent_without_token(self):
        from src.search_service import SearchService, FinMindNewsSearchProvider
        svc = SearchService(searxng_public_instances_enabled=False, finmind_token=None)
        self.assertFalse(any(isinstance(p, FinMindNewsSearchProvider) for p in svc._providers))


if __name__ == "__main__":
    unittest.main()
