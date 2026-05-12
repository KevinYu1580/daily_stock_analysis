# -*- coding: utf-8 -*-
"""
Tests for src/services/stock_code_utils.py（台股 / 美股）。
Covers: is_code_like, normalize_code.
"""

from src.services.stock_code_utils import is_code_like, normalize_code


class TestIsCodeLike:
    # --- Taiwan stock / index codes ---
    def test_tw_4_digit(self):
        assert is_code_like("2330") is True

    def test_tw_4_digit_etf(self):
        assert is_code_like("0050") is True

    def test_tw_prefix_5_digit_etf(self):
        assert is_code_like("tw00878") is True

    def test_tw_suffix_tw(self):
        assert is_code_like("2330.TW") is True

    def test_tw_suffix_two(self):
        assert is_code_like("6488.TWO") is True

    def test_tw_index(self):
        assert is_code_like("TWII") is True
        assert is_code_like("TW50") is True

    # --- US tickers ---
    def test_us_ticker(self):
        assert is_code_like("AAPL") is True

    def test_us_ticker_share_class(self):
        assert is_code_like("BRK.B") is True

    def test_us_ticker_with_exchange_suffix(self):
        assert is_code_like("TSLA.US") is True

    # --- Rejected: unsupported markets (A-share / HK / BSE) ---
    def test_a_share_6_digit_rejected(self):
        assert is_code_like("600519") is False

    def test_hk_5_digit_rejected(self):
        assert is_code_like("00700") is False

    def test_exchange_prefixed_cn_rejected(self):
        assert is_code_like("SH600519") is False
        assert is_code_like("HK00700") is False
        assert is_code_like("BJ920493") is False

    def test_cn_suffix_rejected(self):
        assert is_code_like("600519.SH") is False
        assert is_code_like("00700.HK") is False

    # --- Negative cases ---
    def test_plain_text(self):
        assert is_code_like("台積電") is False

    def test_empty(self):
        assert is_code_like("") is False

    def test_mixed_invalid(self):
        assert is_code_like("abc123") is False


class TestNormalizeCode:
    # --- Taiwan ---
    def test_tw_4_digit(self):
        assert normalize_code("2330") == "2330"

    def test_tw_4_digit_etf(self):
        assert normalize_code("0050") == "0050"

    def test_tw_prefix_strips(self):
        assert normalize_code("tw2330") == "2330"
        assert normalize_code("TW00878") == "00878"

    def test_tw_suffix_tw_strips(self):
        assert normalize_code("2330.TW") == "2330"

    def test_tw_suffix_two_strips(self):
        assert normalize_code("6488.TWO") == "6488"

    def test_tw_index_unchanged(self):
        assert normalize_code("twii") == "TWII"
        assert normalize_code("TW50") == "TW50"

    def test_whitespace_stripped(self):
        assert normalize_code("  2330  ") == "2330"

    # --- US ---
    def test_us_ticker(self):
        assert normalize_code("AAPL") == "AAPL"

    def test_us_ticker_uppercased(self):
        assert normalize_code("aapl") == "AAPL"

    def test_us_ticker_share_class(self):
        assert normalize_code("BRK.B") == "BRK.B"

    # --- Rejected ---
    def test_a_share_6_digit_returns_none(self):
        assert normalize_code("600519") is None

    def test_hk_5_digit_returns_none(self):
        assert normalize_code("00700") is None

    def test_cn_prefix_returns_none(self):
        assert normalize_code("SH600519") is None
        assert normalize_code("BJ920493") is None

    def test_cn_suffix_returns_none(self):
        assert normalize_code("600519.SH") is None
        assert normalize_code("00700.HK") is None

    def test_empty_returns_none(self):
        assert normalize_code("") is None

    def test_plain_text_returns_none(self):
        assert normalize_code("台積電") is None
