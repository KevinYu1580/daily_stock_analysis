# -*- coding: utf-8 -*-
"""Tests for market strategy blueprints (TW / US)."""

import unittest

from src.core.market_strategy import get_market_strategy_blueprint
from src.market_analyzer import MarketAnalyzer, MarketOverview


class TestMarketStrategyBlueprint(unittest.TestCase):
    """Validate TW/US strategy blueprint basics."""

    def test_tw_blueprint_contains_action_framework(self):
        blueprint = get_market_strategy_blueprint("tw")
        block = blueprint.to_prompt_block()

        self.assertIn("台股市場三段式復盤策略", block)
        self.assertIn("Action Framework", block)
        self.assertIn("進攻", block)

    def test_us_blueprint_contains_regime_strategy(self):
        blueprint = get_market_strategy_blueprint("us")
        block = blueprint.to_prompt_block()

        self.assertIn("US Market Regime Strategy", block)
        self.assertIn("Risk-on", block)
        self.assertIn("Macro & Flows", block)

    def test_unknown_region_falls_back_to_tw(self):
        self.assertIs(get_market_strategy_blueprint("xx"), get_market_strategy_blueprint("tw"))


class TestMarketAnalyzerStrategyPrompt(unittest.TestCase):
    """Validate strategy section is injected into prompt/report."""

    def test_tw_prompt_contains_strategy_plan_section(self):
        analyzer = MarketAnalyzer(region="tw")
        prompt = analyzer._build_review_prompt(MarketOverview(date="2026-02-24"), [])

        self.assertIn("明日交易计划", prompt)
        self.assertIn("台股市場三段式復盤策略", prompt)

    def test_us_prompt_contains_strategy_plan_section(self):
        analyzer = MarketAnalyzer(region="us")
        prompt = analyzer._build_review_prompt(MarketOverview(date="2026-02-24"), [])

        self.assertIn("Strategy Plan", prompt)
        self.assertIn("US Market Regime Strategy", prompt)


if __name__ == "__main__":
    unittest.main()
