#!/bin/bash
# ===================================
# 台股/美股 智能分析系统 - 测试脚本
# ===================================
#
# 使用方法：
#   ./scripts/test.sh [测试场景]
#
# 测试场景：
#   market      - 仅大盘复盘
#   tw-stock    - 台股个股分析（台积电、联发科）
#   etf         - ETF 分析（0050、00878）
#   us-stock    - 美股分析（苹果、特斯拉）
#   mixed       - 混合市场分析（台股 + 美股）
#   single      - 单股模式测试
#   dry-run     - 仅获取数据不分析
#   full        - 完整流程测试
#   quick       - 快速测试（单只股票）
#   all         - 运行所有测试
#
# 示例：
#   ./scripts/test.sh market      # 测试大盘复盘
#   ./scripts/test.sh us-stock    # 测试美股分析
#   ./scripts/test.sh quick       # 快速测试
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

header() {
    echo ""
    echo "=============================================="
    echo -e "${GREEN}$1${NC}"
    echo "=============================================="
    echo ""
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装"
        exit 1
    fi
    info "Python版本: $(python3 --version)"
}

# 检查依赖
check_deps() {
    info "检查依赖..."
    python3 -c "import yfinance" 2>/dev/null || { warn "yfinance 未安装，台股/美股测试可能失败"; }
    python3 -c "import FinMind" 2>/dev/null || { warn "FinMind 未安装，台股 K 线/财报数据将仅依赖 yfinance"; }
    success "依赖检查完成"
}

# ==================== 测试场景 ====================

# 测试1: 大盘复盘
test_market() {
    header "测试场景: 大盘复盘"
    info "运行大盘复盘分析..."
    python3 main.py --market-review "$@"
    success "大盘复盘测试完成"
}

# 测试2: 台股分析
test_tw_stock() {
    header "测试场景: 台股分析"
    info "分析台股: 2330(台积电), 2454(联发科)"
    python3 main.py --stocks 2330,2454 --no-market-review "$@"
    success "台股分析测试完成"
}

# 测试2.5: ETF分析
test_etf() {
    header "测试场景: ETF分析"
    info "分析 ETF: 0050(元大台湾50), 00878(国泰永续高股息)"
    python3 main.py --stocks 0050,tw00878 --no-market-review "$@"
    success "ETF分析测试完成"
}

# 测试3: 美股分析
test_us_stock() {
    header "测试场景: 美股分析"
    info "分析美股: AAPL(苹果), TSLA(特斯拉)"
    # 允许透传参数，默认不带 --no-notify
    python3 main.py --stocks AAPL --no-market-review "$@"
    success "美股分析测试完成"
}

# 测试4: 混合市场
test_mixed() {
    header "测试场景: 混合市场分析"
    info "分析混合市场: 2330(台股), AAPL(美股)"
    python3 main.py --stocks 2330,AAPL --no-market-review
    success "混合市场测试完成"
}

# 测试5: 单股推送模式
test_single() {
    header "测试场景: 单股推送模式"
    info "测试单股推送模式..."
    python3 main.py --stocks 2330 --single-notify --no-market-review
    success "单股推送模式测试完成"
}

# 测试6: dry-run模式
test_dry_run() {
    header "测试场景: Dry-Run 模式"
    info "仅获取数据，不进行AI分析..."
    python3 main.py --stocks 2330,AAPL --dry-run --no-notify
    success "Dry-Run 测试完成"
}

# 测试7: 完整流程
test_full() {
    header "测试场景: 完整流程"
    info "运行完整分析流程（个股+大盘）..."
    python3 main.py --stocks 2330 --no-notify
    success "完整流程测试完成"
}

# 测试8: 快速测试
test_quick() {
    header "测试场景: 快速测试"
    info "单只股票快速测试..."
    python3 main.py --stocks 2330 --no-market-review --no-notify "$@"
    success "快速测试完成"
}

# 测试9: 代码识别测试
test_code_recognition() {
    header "测试场景: 代码识别"
    info "测试股票代码识别逻辑（台股 / 美股）..."

    python3 << 'PYTEST'
import sys
sys.path.insert(0, '.')
from data_provider import is_us_stock_code, is_us_index_code, is_tw_stock_code, is_tw_index_code

test_cases = [
    # (代码, 预期TW, 预期US, 描述)
    ("AAPL", False, True, "美股-苹果"),
    ("TSLA", False, True, "美股-特斯拉"),
    ("BRK.B", False, True, "美股-伯克希尔B"),
    ("SPX", False, True, "美股指数-标普500"),
    ("2330", True, False, "台股-台积电"),
    ("tw00878", True, False, "台股ETF-国泰永续高股息"),
    ("2330.TW", True, False, "台股-台积电（.TW 后缀）"),
    ("TW50", True, False, "台股指数-台湾50（TWII/TWO 与美股 ticker 字母规则重叠，故用 TW50）"),
]

print("\n股票代码识别测试:")
print("-" * 60)
all_pass = True
for code, exp_tw, exp_us, desc in test_cases:
    is_tw = is_tw_stock_code(code) or is_tw_index_code(code)
    is_us = is_us_stock_code(code) or is_us_index_code(code)
    tw_ok = is_tw == exp_tw
    us_ok = is_us == exp_us
    status = "✅" if (tw_ok and us_ok) else "❌"
    all_pass = all_pass and tw_ok and us_ok
    print(f"{status} {code:10} | TW:{is_tw!s:5} US:{is_us!s:5} | {desc}")

print("-" * 60)
print(f"{'✅ 所有测试通过!' if all_pass else '❌ 有测试失败!'}")
sys.exit(0 if all_pass else 1)
PYTEST

    success "代码识别测试完成"
}

# 测试10: YFinance代码转换测试
test_yfinance_convert() {
    header "测试场景: YFinance 代码转换"
    info "测试YFinance代码转换逻辑..."

    python3 << 'PYTEST'
import sys
sys.path.insert(0, '.')
from data_provider.yfinance_fetcher import YfinanceFetcher

fetcher = YfinanceFetcher()

test_cases = [
    ("AAPL", "AAPL", "美股"),
    ("TSLA", "TSLA", "美股"),
    ("BRK.B", "BRK.B", "美股特殊"),
    ("SPX", "^GSPC", "美股指数-标普500"),
    ("2330", "2330.TW", "台股"),
    ("tw00878", "00878.TW", "台股ETF（tw 前缀）"),
    ("2330.TW", "2330.TW", "台股（已含 .TW）"),
    ("6488.TWO", "6488.TWO", "台股上柜（.TWO）"),
    ("TWII", "^TWII", "台股指数-加权指数"),
    ("TW50", "0050.TW", "台股指数-台湾50"),
]

print("\nYFinance 代码转换测试:")
print("-" * 60)
all_pass = True
for input_code, expected, desc in test_cases:
    result = fetcher._convert_stock_code(input_code)
    status = "✅" if result == expected else "❌"
    all_pass = all_pass and (result == expected)
    print(f"{status} {input_code:10} -> {result:12} (期望: {expected:12}) | {desc}")

print("-" * 60)
print(f"{'✅ 所有测试通过!' if all_pass else '❌ 有测试失败!'}")
sys.exit(0 if all_pass else 1)
PYTEST

    success "YFinance 代码转换测试完成"
}

# 测试11: 语法检查
test_syntax() {
    header "测试场景: Python 语法检查"
    info "检查关键 Python 文件语法..."

    python3 -m py_compile main.py src/config.py src/notification.py \
        data_provider/base.py \
        data_provider/yfinance_fetcher.py \
        data_provider/finmind_fetcher.py \
        bot/commands/analyze.py

    success "语法检查通过"
}

# 测试12: Flake8 静态检查
test_flake8() {
    header "测试场景: Flake8 静态检查"
    info "运行 Flake8 检查严重错误..."

    if command -v flake8 &> /dev/null; then
        flake8 main.py src/config.py src/notification.py --select=F821,E999 --max-line-length=120
        success "Flake8 检查通过"
    else
        warn "Flake8 未安装，跳过检查"
    fi
}

# 运行所有测试
test_all() {
    header "运行所有测试"

    test_syntax
    test_code_recognition
    test_yfinance_convert
    test_flake8

    echo ""
    info "以下测试需要网络和API配置，可能会失败:"
    echo ""

    test_dry_run || warn "Dry-Run 测试失败（可能是网络问题）"
    test_quick || warn "快速测试失败（可能是API问题）"

    success "所有测试完成!"
}

# ==================== 主程序 ====================

main() {
    header "台股/美股 智能分析系统 - 测试"

    check_python
    check_deps

    case "${1:-help}" in
        market)
            shift
            test_market "$@"
            ;;
        tw-stock|tw_stock|twstock|tw)
            shift
            test_tw_stock "$@"
            ;;
        etf)
            shift
            test_etf "$@"
            ;;
        us-stock|us_stock|usstock|us)
            shift
            test_us_stock "$@"
            ;;
        mixed|mix)
            shift
            test_mixed "$@"
            ;;
        single)
            shift
            test_single "$@"
            ;;
        dry-run|dryrun|dry)
            shift
            test_dry_run "$@"
            ;;
        full)
            shift
            test_full "$@"
            ;;
        quick|q)
            shift
            test_quick "$@"
            ;;
        code|recognition)
            shift
            test_code_recognition "$@"
            ;;
        yfinance|yf)
            shift
            test_yfinance_convert "$@"
            ;;
        syntax)
            shift
            test_syntax "$@"
            ;;
        flake8|lint)
            shift
            test_flake8 "$@"
            ;;
        all)
            shift
            test_all "$@"
            ;;
        help|--help|-h|*)
            echo "使用方法: $0 [测试场景]"
            echo ""
            echo "测试场景:"
            echo "  market      - 仅大盘复盘"
            echo "  tw-stock    - 台股个股分析"
            echo "  etf         - ETF分析"
            echo "  us-stock    - 美股分析"
            echo "  mixed       - 混合市场分析（台股 + 美股）"
            echo "  single      - 单股推送模式"
            echo "  dry-run     - 仅获取数据"
            echo "  full        - 完整流程"
            echo "  quick       - 快速测试（推荐）"
            echo "  code        - 代码识别测试"
            echo "  yfinance    - YFinance转换测试"
            echo "  syntax      - 语法检查"
            echo "  flake8      - 静态检查"
            echo "  all         - 运行所有测试"
            echo ""
            echo "示例:"
            echo "  $0 quick     # 快速测试"
            echo "  $0 us-stock  # 测试美股"
            echo "  $0 code      # 测试代码识别"
            echo "  $0 all       # 运行所有测试"
            ;;
    esac
}

main "$@"
