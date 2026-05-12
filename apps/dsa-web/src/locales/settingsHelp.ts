import type { SystemConfigDocLink } from '../types/systemConfig';

export interface SettingsHelpContent {
  title: string;
  summary?: string;
  usage?: string;
  valueNotes?: string[];
  impact?: string[];
  notes?: string[];
  docs?: SystemConfigDocLink[];
}

type SettingsHelpMap = Record<string, SettingsHelpContent>;

const settingsHelpZhCN: SettingsHelpMap = {
  'settings.base.STOCK_LIST': {
    title: '自選股列表',
    summary: '配置需要分析的股票程式碼列表，是手動分析、定時任務和通知報告的基礎輸入。',
    usage: '多個股票程式碼使用英文逗號分隔。A 股可直接填寫 6 位程式碼，港股可使用 hk 字首，美股可填寫 ticker。',
    valueNotes: [
      '定時模式每次觸發前會重新讀取當前儲存的 STOCK_LIST。',
      '如果命令列臨時傳入 --stocks，隻影響本次手動執行，不會鎖定後續計劃任務。',
      '郵件分組裡的 STOCK_GROUP_N 應寫成 STOCK_LIST 的子集，隻影響郵件收件人，不改變分析範圍。',
    ],
    impact: [
      '影響主分析任務、市場報告中的個股範圍、通知推送內容和歷史報告記錄。',
    ],
    notes: [
      '股票程式碼之間不要使用中文逗號。',
      '修改後儲存配置即可供後續任務讀取。',
    ],
  },
  'settings.ai_model.LITELLM_MODEL': {
    title: '主模型',
    summary: '指定普通分析流程預設使用的 LLM 模型。',
    usage: '推薦使用 provider/model 格式，例如 deepseek/deepseek-v4-flash、gemini/gemini-3.1-pro-preview 或 ollama/qwen3:8b。',
    valueNotes: [
      '系統配置優先順序為 LITELLM_CONFIG > LLM_CHANNELS > legacy provider keys。',
      '如果留空，系統會嘗試根據已配置的 API Key 或渠道宣告自動推斷。',
      'Agent 可通過 AGENT_LITELLM_MODEL 單獨指定模型；留空時繼承主模型。',
    ],
    impact: [
      '影響普通個股分析、大盤覆盤、報告生成，以及未單獨覆蓋模型的 Agent 呼叫。',
    ],
    notes: [
      '無 provider 字首時，LiteLLM 可能無法判斷應該使用哪組 API Key。',
      'Ollama 本地模型應配合 OLLAMA_API_BASE 或 Ollama 渠道使用，不要誤用 OPENAI_BASE_URL。',
    ],
  },
  'settings.ai_model.LLM_CHANNELS': {
    title: 'LLM 渠道列表',
    summary: '宣告多個模型渠道，用於多 provider、多 Key、備用模型和視覺化渠道管理。',
    usage: '填寫逗號分隔的渠道名，例如 deepseek,aihubmix；每個渠道再配置 LLM_<NAME>_BASE_URL、LLM_<NAME>_API_KEY(S)、LLM_<NAME>_MODELS 等欄位。',
    valueNotes: [
      '啟用渠道模式後，同層執行時優先讀取渠道配置。',
      '在 Docker 或 GitHub Actions 中顯式注入的環境變數會覆蓋 Web 設定頁寫入的 .env。',
      '渠道編輯器儲存時只更新本次提交的 key，不會靜默遷移整個舊配置。',
    ],
    impact: [
      '影響主模型、Agent 模型、fallback 模型和 Vision 模型的可選來源。',
    ],
    notes: [
      '不要把極簡 legacy key 和 Channels 混用後期待兩邊同時生效。',
      '自定義渠道名在 GitHub Actions 中通常還需要 workflow 顯式對映對應環境變數。',
    ],
  },
  'settings.notification.FEISHU_WEBHOOK_URL': {
    title: '飛書群機器人 Webhook',
    summary: '配置飛書自定義群機器人，用於把分析報告推送到指定飛書群。',
    usage: '在飛書群中新增自定義機器人後，複製 open-apis/bot/v2/hook 開頭的 Webhook URL 到這裡。',
    valueNotes: [
      '如果機器人開啟“簽名校驗”，還需要填寫 FEISHU_WEBHOOK_SECRET。',
      '如果機器人開啟“關鍵詞”，還需要填寫 FEISHU_WEBHOOK_KEYWORD，系統會自動補到訊息前。',
      'FEISHU_APP_ID / FEISHU_APP_SECRET 用於飛書應用、雲文件或 Stream Bot，不會直接啟用群 Webhook 推送。',
    ],
    impact: [
      '影響飛書通知渠道；失敗時不應拖垮主分析流程，隻影響該渠道送達。',
    ],
    notes: [
      '不要把 FEISHU_APP_SECRET 當作 FEISHU_WEBHOOK_SECRET 使用。',
      '如果飛書側配置 IP 白名單，需要確認當前執行環境出口 IP 已加入白名單。',
    ],
  },
  'settings.system.WEBUI_HOST': {
    title: 'WebUI 監聽地址',
    summary: '控制 WebUI 服務繫結在哪個網路地址上。',
    usage: '本機訪問通常使用 127.0.0.1；雲伺服器、Docker 或需要外部訪問時通常使用 0.0.0.0。',
    valueNotes: [
      '.env 裡的 WEBUI_HOST 在程序啟動讀取時優先順序高於命令列 --host 引數。',
      '在設定頁儲存後，只會寫入 .env 並重載執行時配置物件，不會讓當前 WebUI/API 程序重新繫結監聽地址。',
      'Docker Compose 中通常會在容器內使用 0.0.0.0，宿主機訪問還取決於埠對映。',
    ],
    impact: [
      '影響重啟後瀏覽器能否從本機、區域網或公網訪問 WebUI。',
    ],
    notes: [
      '修改 WEBUI_HOST 後需要重啟當前程序、Docker 容器或服務管理器才會生效。',
      '直連公網時建議同時啟用 ADMIN_AUTH_ENABLED。',
      '如果部署在反向代理後面，登入限流與真實 IP 識別還需要評估 TRUST_X_FORWARDED_FOR。',
    ],
  },
};

const settingsHelpEnUS: SettingsHelpMap = {
  'settings.base.STOCK_LIST': {
    title: 'Watchlist',
    summary: 'Defines the stock codes used by analysis jobs and notification reports.',
    usage: 'Separate symbols with commas. A-shares can use six-digit codes, HK stocks can use the hk prefix, and US stocks can use ticker symbols.',
    valueNotes: [
      'Scheduled mode rereads the saved STOCK_LIST before each run.',
      'A temporary --stocks argument only affects that manual run.',
      'STOCK_GROUP_N should be a subset of STOCK_LIST and only affects grouped email routing.',
    ],
    impact: ['Affects analysis scope, notification content, and saved history reports.'],
    notes: ['Use English commas between symbols.', 'Save the setting before later tasks can read it.'],
  },
  'settings.ai_model.LITELLM_MODEL': {
    title: 'Primary Model',
    summary: 'Selects the default LLM model for regular analysis flows.',
    usage: 'Use provider/model format, such as deepseek/deepseek-v4-flash, gemini/gemini-3.1-pro-preview, or ollama/qwen3:8b.',
    valueNotes: [
      'Runtime priority is LITELLM_CONFIG > LLM_CHANNELS > legacy provider keys.',
      'When empty, the system tries to infer a model from available API keys or channels.',
      'Agent can use AGENT_LITELLM_MODEL; when empty, it inherits the primary model.',
    ],
    impact: ['Affects regular stock analysis, market review, report generation, and Agent calls without a dedicated model.'],
    notes: [
      'Without a provider prefix, LiteLLM may not know which API key to use.',
      'For Ollama, use OLLAMA_API_BASE or an Ollama channel instead of OPENAI_BASE_URL.',
    ],
  },
  'settings.ai_model.LLM_CHANNELS': {
    title: 'LLM Channels',
    summary: 'Declares model channels for multiple providers, keys, fallbacks, and visual channel management.',
    usage: 'Use comma-separated names such as deepseek,aihubmix; then configure LLM_<NAME>_BASE_URL, LLM_<NAME>_API_KEY(S), and LLM_<NAME>_MODELS for each channel.',
    valueNotes: [
      'Once channel mode is active, runtime selection reads channel configuration first.',
      'Environment variables injected by Docker or GitHub Actions can override values saved from the Web settings page.',
      'Saving in the channel editor updates submitted keys only and does not silently migrate all old config.',
    ],
    impact: ['Affects available sources for primary, Agent, fallback, and Vision models.'],
    notes: [
      'Do not expect legacy keys and Channels to be active at the same time.',
      'Custom channel names in GitHub Actions usually need explicit workflow env mappings.',
    ],
  },
  'settings.notification.FEISHU_WEBHOOK_URL': {
    title: 'Feishu Webhook URL',
    summary: 'Sends analysis reports to a Feishu group through a custom bot webhook.',
    usage: 'Create a custom bot in the target Feishu group and paste the open-apis/bot/v2/hook webhook URL here.',
    valueNotes: [
      'If signing is enabled, also set FEISHU_WEBHOOK_SECRET.',
      'If keyword protection is enabled, also set FEISHU_WEBHOOK_KEYWORD; the sender prepends it automatically.',
      'FEISHU_APP_ID / FEISHU_APP_SECRET are for app, cloud-doc, or Stream Bot modes and do not enable group webhook delivery.',
    ],
    impact: ['Affects only the Feishu notification channel; delivery failure should not block the main analysis flow.'],
    notes: [
      'Do not use FEISHU_APP_SECRET as FEISHU_WEBHOOK_SECRET.',
      'If IP allowlisting is enabled in Feishu, add the outbound IP of your runtime environment.',
    ],
  },
  'settings.system.WEBUI_HOST': {
    title: 'WebUI Host',
    summary: 'Controls the network address the WebUI service binds to.',
    usage: 'Use 127.0.0.1 for local-only access. Use 0.0.0.0 for cloud, Docker, or external access.',
    valueNotes: [
      'WEBUI_HOST in .env has higher priority than the --host command-line argument when the process starts.',
      'Saving it from the settings page writes .env and reloads runtime config objects, but the running WebUI/API process will not rebind its host.',
      'Docker Compose commonly binds 0.0.0.0 inside the container; host access also depends on port mapping.',
    ],
    impact: ['Affects whether the WebUI can be reached locally, on the LAN, or from the public internet after restart.'],
    notes: [
      'Restart the process, Docker container, or service manager after changing WEBUI_HOST.',
      'Enable ADMIN_AUTH_ENABLED when exposing the service publicly.',
      'Behind a reverse proxy, also evaluate TRUST_X_FORWARDED_FOR for login rate limiting and real IP detection.',
    ],
  },
};

function getPreferredHelpMap(locale?: string | null): SettingsHelpMap {
  if (locale?.toLowerCase().startsWith('en')) {
    return settingsHelpEnUS;
  }
  return settingsHelpZhCN;
}

export function getSettingsHelpContent(
  helpKey?: string | null,
  fallbackDescription?: string,
  locale?: string | null,
): SettingsHelpContent | null {
  if (!helpKey) {
    return null;
  }

  const localized = getPreferredHelpMap(locale)[helpKey] ?? settingsHelpZhCN[helpKey];
  if (localized) {
    return localized;
  }

  if (fallbackDescription) {
    return {
      title: '配置說明',
      summary: fallbackDescription,
    };
  }

  return null;
}
