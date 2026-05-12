# -*- coding: utf-8 -*-
"""Market strategy blueprints for TW/US daily market recap."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class StrategyDimension:
    """Single strategy dimension used by market recap prompts."""

    name: str
    objective: str
    checkpoints: List[str]


@dataclass(frozen=True)
class MarketStrategyBlueprint:
    """Region specific market strategy blueprint."""

    region: str
    title: str
    positioning: str
    principles: List[str]
    dimensions: List[StrategyDimension]
    action_framework: List[str]

    def to_prompt_block(self) -> str:
        """Render blueprint as prompt instructions."""
        principles_text = "\n".join([f"- {item}" for item in self.principles])
        action_text = "\n".join([f"- {item}" for item in self.action_framework])

        dims = []
        for dim in self.dimensions:
            checkpoints = "\n".join([f"  - {cp}" for cp in dim.checkpoints])
            dims.append(f"- {dim.name}: {dim.objective}\n{checkpoints}")
        dimensions_text = "\n".join(dims)

        return (
            f"## Strategy Blueprint: {self.title}\n"
            f"{self.positioning}\n\n"
            f"### Strategy Principles\n{principles_text}\n\n"
            f"### Analysis Dimensions\n{dimensions_text}\n\n"
            f"### Action Framework\n{action_text}"
        )

    def to_markdown_block(self) -> str:
        """Render blueprint as markdown section for template fallback report."""
        dims = "\n".join([f"- **{dim.name}**: {dim.objective}" for dim in self.dimensions])
        section_title = "### VI. Strategy Framework" if self.region == "us" else "### 六、策略框架"
        return f"{section_title}\n{dims}\n"


TW_BLUEPRINT = MarketStrategyBlueprint(
    region="tw",
    title="台股市場三段式復盤策略",
    positioning="聚焦加權/櫃買指數趨勢、三大法人籌碼與類股輪動，形成次一交易日計畫。",
    principles=[
        "先看加權/櫃買指數方向，再看三大法人資金，最後看類股輪動的持續性。",
        "結論必須對應到部位、節奏與風險控制動作。",
        "判斷只用當日資料與近 3 日新聞，不臆測未驗證資訊。",
        "所有敘述輸出一律使用繁體中文，禁用簡體字。",
    ],
    dimensions=[
        StrategyDimension(
            name="趨勢結構",
            objective="判斷市場處於上升、盤整還是防守階段。",
            checkpoints=[
                "加權指數與櫃買指數是否同向",
                "放量上漲或量縮下跌是否成立",
                "關鍵支撐壓力（季線、年線）是否被攻克或跌破",
            ],
        ),
        StrategyDimension(
            name="法人籌碼",
            objective="辨識三大法人風險偏好與資金溫度。",
            checkpoints=[
                "外資、投信、自營商買賣超方向與規模",
                "外資期貨多空淨額與台幣匯率含意",
                "成交量能是否擴張、權值股是否帶動",
            ],
        ),
        StrategyDimension(
            name="主流類股",
            objective="提煉可交易主流與須迴避方向。",
            checkpoints=[
                "領漲類股是否有事件或營收催化（半導體、AI/HPC、電子零組件）",
                "費半 SOX 與美股科技股對台股科技類股的連動",
                "領跌類股是否擴散、傳產與金融的相對表現",
            ],
        ),
    ],
    action_framework=[
        "進攻：加權/櫃買共振上行 + 量能放大 + 法人同步偏多 + 主流類股強化。",
        "均衡：指數分化或量縮盤整，控制部位並等待確認。",
        "防守：指數轉弱 + 法人轉賣 + 領跌擴散，優先風控與減碼。",
    ],
)

US_BLUEPRINT = MarketStrategyBlueprint(
    region="us",
    title="US Market Regime Strategy",
    positioning="Focus on index trend, macro narrative, and sector rotation to define next-session risk posture.",
    principles=[
        "Read market regime from S&P 500, Nasdaq, and Dow alignment first.",
        "Separate beta move from theme-driven alpha rotation.",
        "Translate recap into actionable risk-on/risk-off stance with clear invalidation points.",
    ],
    dimensions=[
        StrategyDimension(
            name="Trend Regime",
            objective="Classify the market as momentum, range, or risk-off.",
            checkpoints=[
                "Are SPX/NDX/DJI directionally aligned",
                "Did volume confirm the move",
                "Are key index levels reclaimed or lost",
            ],
        ),
        StrategyDimension(
            name="Macro & Flows",
            objective="Map policy/rates narrative into equity risk appetite.",
            checkpoints=[
                "Treasury yield and USD implications",
                "Breadth and leadership concentration",
                "Defensive vs growth factor rotation",
            ],
        ),
        StrategyDimension(
            name="Sector Themes",
            objective="Identify persistent leaders and vulnerable laggards.",
            checkpoints=[
                "AI/semiconductor/software trend persistence",
                "Energy/financials sensitivity to macro data",
                "Volatility signals from VIX and large-cap earnings",
            ],
        ),
    ],
    action_framework=[
        "Risk-on: broad index breakout with expanding participation.",
        "Neutral: mixed index signals; focus on selective relative strength.",
        "Risk-off: failed breakouts and rising volatility; prioritize capital preservation.",
    ],
)


def get_market_strategy_blueprint(region: str) -> MarketStrategyBlueprint:
    """Return strategy blueprint by market region."""
    if region == "us":
        return US_BLUEPRINT
    return TW_BLUEPRINT
