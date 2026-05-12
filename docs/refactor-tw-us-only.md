# 重構計畫:只保留台股 + 美股(移除 A 股 / 港股)

> 狀態:**Stage 1–7 已完成**(branch `refactor/tw-us-only`)。決策已拍板(見第 2 節)。離線測試全綠(`pytest -m "not network"` 1699 passed)、flake8 critical 0、`scripts/test.sh code/yfinance` 通過。

## 0. 進度(逐 commit)

| commit | 內容 | 狀態 |
| --- | --- | --- |
| `docs: plan` | 本文件 | ✅ |
| `refactor(market)` | Stage 1+2:market_context / market_strategy(+TW_BLUEPRINT)/ market_profile(+TW_PROFILE)/ market_analyzer / market_review / trading_calendar / config / config_registry(MARKET_REVIEW_REGION→tw/us/both,預設 tw)/ stock_code_utils / search_service(台股→zh-hant 新聞) | ✅ |
| `refactor(data-provider)` ×2 | Stage 3:刪 7 個 CN/HK fetcher、DataFetcherManager 只註冊 yfinance+finmind、get_daily_data 拒非 TW/US 代碼、gut tickflow、`data_provider/__init__` 收斂;再清 `get_realtime_quote`/`get_daily_data` 死路由、`normalize_stock_code` TW/US-only、`_market_tag` TW-first、`yfinance_fetcher._convert_stock_code` TW/US-only(+ `_get_hk_main_indices` 刪)、移除 `is_bse_code/is_st_stock/is_kc_cy_stock/_is_hk_market` | ✅ |
| `test: drop ... / update ...` | Stage 7:刪 18 個只測已移除資料源/HK/BSE 的測試檔;重寫 market-layer + stock-code + analysis-API + import-parser + config + history-loader + portfolio + search-news + bot-market 測試為 TW/US;`scripts/test.sh` 重寫 | ✅ |
| 前端/桌面端 | apps/dsa-web:Market 型別→TW/US/INDEX/ETF、portfolio market→us/tw、PortfolioPage 改台股/TWD、settingsHelp、SuggestionsList badge、相關前端測試(101 過、build 過);桌面端純 wrapper 無 CN/HK | ✅ |
| `docs: ...` | README(zh/cht/en)/full-guide/FAQ/DEPLOY/INDEX/bot-command/bot-config/zeabur/api_spec.json/.env.example/requirements.txt/daily_analysis.yml/CHANGELOG;刪 `scripts/fetch_tushare_stock_list.py` + `docs/TUSHARE_STOCK_LIST_GUIDE.md`;`check_env.py`/`generate_index_from_csv.py` 標頭 | ✅ |

## 剩餘待辦(已知 debt,後續 PR;均不影響現有測試/功能)

- **`realtime_types.py`**:`RealtimeSource` enum 仍列 EFINANCE/AKSHARE_*/TUSHARE/TENCENT/SINA/STOOQ/LONGBRIDGE 等 — 已無 fetcher 引用,屬死值;STOOQ 可能還是 yfinance 內部的美股兜底,需確認後刪其餘。
- **`fundamental_adapter.py`**:`AkshareFundamentalAdapter` 現已退化為 `not_supported`(akshare 移除後 `import akshare` 失敗→優雅降級),應改接 FinMind / yfinance 基本面或正式移除;`base.py` 內 `get_belong_boards`/`get_capital_flow_context` 等 A 股專屬方法現恒回 not_supported(`_market_tag(...) != "cn"` 守衛恒為真)。
- **`src/config.py` / `config_registry.py` dead keys**:`TUSHARE_TOKEN`(含一個指向已刪文件的 dead href)、`TICKFLOW_API_KEY`、`PYTDX_HOST/PORT/SERVERS`、`REALTIME_SOURCE_PRIORITY` 的 tushare auto-inject、`tushare_token` 的 info 驗證訊息 — 仍在(無作用,但會產生誤導性提示),清理需連動 `test_config_*` / system_config API。
- **`base.py` `_is_etf_code` / `ETF_PREFIXES`**:A 股 ETF 前綴判定,對 TW/US 代碼恒為 False(死碼);TW ETF(0050/00878)目前無專用 ETF 路由。
- **`src/core/pipeline.py` / `bot/` / `src/agent/`**:殘留 `market == 'cn'/'hk'` 的死分支(現 `get_market_for_stock` 回 None,不會踩到);`pipeline` 對不支援市場標的的「軟拒絕/略過」目前靠 `get_daily_data` 丟 `DataFetchError`,被 per-stock 錯誤處理吞掉,可更明確。
- **`apps/dsa-web/public/stocks.index.json`(+ `static/` 鏡像)**:仍含 5191 CN / 2723 HK / 300 BSE — 要重跑 `scripts/generate_stock_index.py`,而 `src/data/stock_mapping.py` `STOCK_NAME_MAP` 也以 CN 為主,需一併瘦身為台股/美股清單;`scripts/generate_index_from_csv.py` 是舊 CN-CSV 工具,僅加了註記未重寫。前端對未知市場 badge 會走 error boundary 降級為純輸入框,故功能不受影響。
- **`docs/openclaw-skill-integration.md`、`docs/architecture/api_spec.json` `example` 欄位、`EXTRACT_PROMPT`(`src/services/image_stock_extractor.py`)**:仍含 CN 範例,故意未動(分別為外部集成文件、疑似 auto-gen、需另案調整;`docs/image-extract-prompt.md` 已加 heads-up)。
- **最終 CI 證據**:本地以 repo 內 `.venv` 跑了 `py_compile` + flake8 critical(0)+ `pytest -m "not network"`(1699 passed)+ `scripts/test.sh code/yfinance`(通過);`scripts/test.sh quick`(個股實跑)與 `pytest -m network` 需在配置 API key 的環境驗證,並補 PR CI 結論。

> 狀態原註:本文件落地後依「階段」逐步執行,每階段跑驗證閘,不一次砍。

## 1. 目標

服務只支援 **台股(TW)** 與 **美股(US)**。移除 A 股(CN)、港股(HK)相關:市場偵測分支、資料源、報告/分析分支、前端型別、桌面端、文件、測試。

「移除 CN/HK」是反向枚舉,容易漏。以下用**正向「要保留什麼」**界定:

| 層 | 保留 | 移除 |
| --- | --- | --- |
| data_provider | `yfinance_fetcher`、`finmind_fetcher`、`tw_market`、`us_index_mapping`、`fundamental_adapter`(瘦身)、`base`(瘦身)、`realtime_types`(瘦身) | `akshare_fetcher`、`tushare_fetcher`、`efinance_fetcher`、`pytdx_fetcher`、`baostock_fetcher`、`longbridge_fetcher`、`tickflow_fetcher` |
| market layer | `us`/`tw` 分支 | `cn`/`hk` blueprint、profile、guidelines、role |
| 偵測 | `is_tw_*`、`is_us_*` | `_is_hk_market`、`is_bse_code`、`is_kc_cy_stock`、A 股 ETF prefix、ST 股 |
| 前端 | `'US'`、`'TW'` | `'CN'`、`'HK'`、`'BSE'`、A 股 `'ETF'` |
| 文件 | 台股/美股說明 | A 股/港股段落、Tushare/Longbridge/akshare 等設定 |

## 2. 決策(已拍板)

1. **TW 流程目前是壞的** → ✅ **這次一起補齊**:新增 `TW_BLUEPRINT`(台股三段式:加權/櫃買 → 三大法人資金 → 月營收/類股),新增 `TW_PROFILE`(mood index = TWII),`market_analyzer` / `market_review` 接受 `region="tw"`。
2. **既有用戶資料含 CN/HK 標的** → ✅ **軟拒絕,不動 DB**:讀到 CN/HK 代碼時標記為「不支援的市場」並略過,不寫 migration。
3. **`longbridge_fetcher`** → ✅ **一起砍**(連帶 `.env.example` Longbridge 全段、`requirements.txt` longbridge、相關設定/測試)。美股量比/換手率/PE 改由 yfinance 提供或標記缺值。
4. **`tickflow_fetcher`** → ✅ **一起砍**(檔頭明寫 "market review only" / "A-share market review stability",純 A 股;連帶 `requirements.txt` tickflow、`config_registry`/`config` 內 tickflow 設定、`test_tickflow_*`)。
5. **Repo 名** → 不改;**README 標題/描述** → 改為「台股/美股自選股智能分析系統」。
6. **`MARKET_REVIEW_REGION`** → 可選值收斂為 `tw` / `us` / `both`(=TW+US);預設值改為 `tw`。`daily_analysis.yml` 同步。

## 3. 階段順序(由上往下,每階段 build 仍可跑)

> bottom-up(先砍 fetcher)會立刻炸 import 鏈;top-down 每階段可 `python -m py_compile` 通過。

### Stage 0 — 計畫簽收(本文件)
- user 確認方向 + 回答第 2 節決策。

### Stage 1 — 入口 / 驗證層(先拒輸入,底層先不動)
- `main.py` CLI `--stocks` 範例與解析、`src/cli/`(若有)
- API request schema:`api/v1/**`、`src/schemas/**` —— 拒絕 CN/HK 代碼
- portfolio market enum(後端):`src/services/portfolio*`、`src/repositories/portfolio*`
- `src/config.py` / `config_registry.py`:`MARKET_REVIEW_REGION` 可選值收斂為 `tw/us/both`
- 驗證:`./scripts/ci_gate.sh`(或至少 `py_compile` + 相關 pytest)

### Stage 2 — 報告 / 分析層
- `src/market_context.py`:`_MARKET_ROLES`、`_MARKET_GUIDELINES` 砍 cn/hk;`detect_market` 只回 us/tw
- `src/core/market_strategy.py`:砍 `CN_BLUEPRINT`、`HK_BLUEPRINT`;依決策 1 補 `TW_BLUEPRINT` 或讓 TW 用 US
- `src/core/market_profile.py`:砍 `CN_PROFILE`、`HK_PROFILE`;補 `TW_PROFILE`(或沿用)
- `src/core/market_review.py`、`src/market_analyzer.py`:`region` 收斂為 us/tw
- `src/search_service.py`:砍 A 股/港股新聞維度與中文偏好對 CN 的特判
- `src/analyzer.py`:確認 `get_market_role/guidelines` 呼叫端不假設 cn
- `src/services/image_stock_extractor.py` `EXTRACT_PROMPT`:若提及 A 股/港股需更新(PR 描述須附完整最新 prompt)
- `src/core/trading_calendar.py`:`MARKET_EXCHANGE` / `MARKET_TIMEZONE` 砍 cn/hk
- `bot/commands/market.py`、`bot/commands/analyze.py` 等:市場參數收斂
- 驗證:`./scripts/ci_gate.sh` + 受影響 pytest(`test_market_*`、`test_search_*`、`test_analyzer_*`)

### Stage 3 — 資料源層
- 刪檔:`akshare_fetcher.py`、`tushare_fetcher.py`、`efinance_fetcher.py`、`pytdx_fetcher.py`、`baostock_fetcher.py`、(`longbridge_fetcher.py` 依決策 3)
- `data_provider/__init__.py`:移除上述 import / `__all__` / 優先級註解
- `data_provider/base.py`:`DataFetcherManager` 註冊清單瘦身;砍 `_is_hk_market`、`is_bse_code`、`is_kc_cy_stock`、A 股 ETF prefix、`is_st_stock`、A 股 `normalize_stock_code` 分支
- `data_provider/realtime_types.py`:`RealtimeSource` 砍 EFINANCE/AKSHARE_*/TUSHARE/TENCENT/SINA/STOOQ;留下美股/台股實際用的
- `data_provider/fundamental_adapter.py`:瘦身 CN/HK 路徑
- `data_provider/akshare_realtime*`、`stooq*` 等附屬:確認後刪
- `scripts/fetch_tushare_stock_list.py`、`scripts/generate_stock_index.py`(若依賴 akshare/tushare)
- 驗證:`./scripts/ci_gate.sh` + Docker build smoke(`docker-build` CI job)

### Stage 4 — 前端(apps/dsa-web)
- `src/types/stockIndex.ts`:`Market` 收斂為 `'US' | 'TW' | 'INDEX'`(確認 ETF 是否還要)
- `src/types/portfolio.ts`:market 收斂為 `'us' | 'tw'`
- `src/utils/stockIndexLoader.ts`、`src/locales/settingsHelp.ts` 文案
- 市場篩選/分組 UI 元件:移除 CN/HK 選項
- 驗證:`cd apps/dsa-web && npm ci && npm run lint && npm run build`

### Stage 5 — 桌面端(apps/dsa-desktop)
- 鏡像 Stage 4 的型別/文案改動
- 驗證:先 build web,再 `cd apps/dsa-desktop && npm install && npm run build`

### Stage 6 — 文件 / 設定 / 依賴
- `README.md`、`docs/README_CHT.md`:標題與「多市場」描述改為台股/美股
- `.env.example`:刪 `TUSHARE_TOKEN`、Longbridge 全段(依決策 3)、`*_PRIORITY` 中 CN 源、`REALTIME_SOURCE_PRIORITY` 範例、`MARKET_REVIEW_REGION` 註解;保留 `FINMIND_TOKEN`
- `requirements.txt`:刪 `efinance`、`akshare`、`tushare`、`pytdx`、`baostock`、`longbridge`(依決策 3);保留 `yfinance`、`FinMind`、`exchange-calendars`、`tickflow`(依決策 4)
- `docs/*.md`:資料源、市場、配置相關專題文件
- `.github/workflows/daily_analysis.yml`:`MARKET_REVIEW_REGION` 預設改值;`STOCK_LIST` 預設 `600519` 改台股/美股範例
- `docs/CHANGELOG.md` `[Unreleased]`:加一行(類型待決策 6 之外另議,暫定 `- [改进] 移除 A 股 / 港股支援,服務聚焦台股與美股`)
- 驗證:`python scripts/check_ai_assets.py`(若動到治理資產);文件命令對照

### Stage 7 — 測試
- 刪 CN/HK-only 測試(候選):`test_stock_code_bse.py`、`test_akshare_realtime_logging.py`、`test_efinance_main_indices.py`、`test_tushare_fetcher_*.py`、`test_longbridge_fetcher.py`(依決策 3)、`test_pytdx*`、`test_baostock*`、`test_hk_realtime_routing.py`、`test_hk_stock_name_fallback.py`、`test_yfinance_hk_indices.py`、`test_pipeline_related_boards.py`(A 股板块)、`test_chip_structure_fallback.py`(確認)、`test_stooq_fallback.py`
- 改:`test_market_strategy.py`、`test_market_review*.py`、`test_market_analyzer_generate_text.py`、`test_trading_calendar.py`、`test_realtime_types.py`、`test_stock_code_utils.py`、`test_bot_market_command.py`、`test_portfolio_*.py`、`test_us_index_mapping.py`(確認)
- 補:TW blueprint/profile 測試(依決策 1)
- 驗證:`python -m pytest -m "not network"`

## 4. 探勘待補(計畫執行前要逐一掃)

- `tests/` 完整分類:哪些純 CN/HK、哪些混用
- `bot/` 是否有 CN-only 推送通道行為(企業微信/釘釘對 A 股的特判)
- `data/stock_analysis.db`、`apps/dsa-web/public/*.json`(`stocks.index.json` 之類):預設 watchlist / 序列化資料是否含 CN/HK
- `apps/dsa-web/src/.../stocks.index.json` 來源與重生方式
- `scripts/generate_stock_index.py`、`scripts/generate_index_from_csv.py`:資料源依賴
- `src/agent/tools/market_tools.py`、`src/agent/`:agent 工具的市場假設
- 既有歷史報告 JSON schema 是否硬編 region 列舉

## 5. 風險與回滾

- **最大阻塞**:TW 端 market_strategy/profile/analyzer 未接 —— 不先補,交付後台股大盤復盤直接壞。優先級高於「移除 CN/HK」本身。
- **資料源剩 2 個**:yfinance(US/TW)+ FinMind(TW)。yfinance 不穩時台股還有 FinMind,美股則無兜底(原本 longbridge 兜底)。決策 3 要權衡。
- **既有部署**:設了 `TUSHARE_TOKEN` / Longbridge / `MARKET_REVIEW_REGION=cn` 的用戶升級後行為變化 —— 文件需明確 breaking change 說明。
- **回滾**:整個重構走獨立分支,分階段 commit;每階段 commit 可單獨 revert。最終以 PR 合入,不直推 main。
