# Teams Push Job Message Forwarder

自動監控 Microsoft Teams 聊天室中的「push job」請求，並轉發至指定的群組聊天室。

## 功能特色

- **動態聊天室監控**：自動獲取所有聊天室，無需手動設定 chat ID
- **智慧訊息過濾**：
  - 一對一聊天：檢查所有新訊息
  - 群組聊天：只檢查 @mention 的訊息
- **可自訂正規表達式**：支援多種 push 請求格式
- **LLM 擴充介面**：預留介面供未來 LLM 整合
- **重複檢查**：三層防重複機制
- **檔案持久化**：重啟後保留狀態

## 系統需求

- Python 3.9+
- Microsoft Azure AD 應用程式註冊
- 已授權的 Graph API 權限：
  - `Chat.Read` (讀取聊天)
  - `ChatMessage.Send` (傳送訊息)

## 安裝

```bash
# 克隆專案
git clone <repository-url>
cd Teams_automation

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

## 設定

1. 複製設定檔範本：

```bash
cp config.json.example config.json
```

2. 編輯 `config.json`：

```json
{
  "target_push_chat_id": "19:your-push-chat@thread.v2",
  "poll_interval_seconds": 60,
  "my_display_name": "Your Name",
  "patterns": [
    "(?i)(?:please\\s+)?(?:help\\s+)?(?:to\\s+)?push\\s+['\"]?([\\w-]+)['\"]?",
    "(?i)push\\s+(?:job\\s+)?['\"]?([\\w-]+)['\"]?"
  ],
  "azure_ad": {
    "client_id": "YOUR_CLIENT_ID",
    "tenant_id": "YOUR_TENANT_ID"
  }
}
```

### 設定說明

| 欄位 | 說明 |
|------|------|
| `target_push_chat_id` | 目標 push job 群組的 chat ID |
| `poll_interval_seconds` | 輪詢間隔（秒） |
| `my_display_name` | 您在 Teams 的顯示名稱 |
| `patterns` | 正規表達式清單，需包含 job ID 的擷取群組 |
| `azure_ad.client_id` | Azure AD 應用程式 ID |
| `azure_ad.tenant_id` | Azure AD 租戶 ID |

## 使用方式

```bash
# 從專案根目錄執行
python -m src.main
```

首次執行時會開啟瀏覽器進行 Azure AD 登入，之後會使用快取的 Token。

## 專案結構

```
Teams_automation/
├── src/
│   ├── __init__.py
│   ├── main.py                    # 主程式入口
│   ├── config.py                  # 設定管理
│   ├── graph_client.py            # MS Graph API 客戶端
│   ├── chat_fetcher.py            # 動態聊天室獲取
│   ├── message_monitor.py         # 訊息監控
│   ├── message_detector.py        # 訊息識別（可替換介面）
│   ├── duplicate_checker.py       # 重複檢查
│   ├── forwarder.py               # 訊息轉發
│   └── persistence.py             # 檔案持久化
├── tests/
│   ├── test_message_detector.py   # 訊息識別測試
│   └── test_duplicate_checker.py  # 重複檢查測試
├── config.json                    # 設定檔（請勿提交至 Git）
├── requirements.txt               # Python 依賴
└── README.md
```

## 測試

```bash
# 安裝測試依賴
pip install pytest pytest-asyncio

# 執行測試
pytest tests/ -v
```

## 自訂正規表達式

在 `config.json` 的 `patterns` 欄位中新增正規表達式：

```json
"patterns": [
  "(?i)push\\s+['\"]?([\\w-]+)['\"]?",
  "(?i)prioritize\\s+([\\w-]+)",
  "(?i)幫忙\\s*push\\s+([\\w-]+)"
]
```

- 使用 `(?i)` 啟用大小寫不分
- 使用 `([\\w-]+)` 擷取 job ID

## 未來擴充：LLM 整合

`message_detector.py` 中的 `LLMMessageDetector` 類別提供了 LLM 整合介面：

```python
from src.message_detector import LLMMessageDetector

# 實作您的 LLM 客戶端
class MyLLMDetector(LLMMessageDetector):
    def detect(self, message_content, attachments):
        # 呼叫您的 LLM API
        ...
```

## 注意事項

- **Beta API**：使用的 `forwardToChat` 端點目前為 Beta 版本
- **權限**：僅支援委派權限（Delegated Permissions）
- **GitHub 部署**：此程式需在企業內部網路環境執行

## License

MIT
