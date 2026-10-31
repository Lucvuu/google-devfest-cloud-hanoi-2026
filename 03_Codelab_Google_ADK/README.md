# 🛠️ Codelab: Build an AI Agent with Google ADK
**Speaker / Instructor:** Mr. Nguyen Anh Duong – Founder & CEO @ ZenAI; Google Developer Expert @ ML  
**Time:** 14:25 - 14:55 (30 minutes hands-on)

---

## 1. Giới thiệu Google Agent Development Kit (ADK)
**Google ADK (`google-adk`)** là framework mã nguồn mở ưu tiên code-first (code-first framework) từ Google, giúp lập trình viên phát triển, đánh giá (evaluate), gỡ lỗi (debug) và triển khai các hệ thống AI Agent và Multi-Agent phức tạp lên Google Cloud (Cloud Run, Vertex AI Agent Engine).

### Các ưu điểm vượt trội của ADK:
1. **Tích hợp sâu với Gemini Models:** Tối ưu hóa việc tận dụng mô hình Gemini (Gemini 2.5 Flash, Gemini 3.8 Flash) thông qua thư viện chuẩn `google-genai`.
2. **Khai báo Tool tự nhiên:** Viết hàm Python tiêu chuẩn với type hint và docstring, ADK tự động sinh schema và xử lý function calling.
3. **Multi-Agent Orchestration:** Dễ dàng phân cấp tác vụ thông qua thuộc tính `sub_agents`. Agent cha tự động giao việc cho agent con phù hợp.
4. **Developer Tooling mạnh mẽ:** Cung cấp CLI `adk run` (chạy interactive trên terminal) và `adk web` (giao diện web trực quan để chat, xem trace cây suy nghĩ và kiểm tra session memory).

---

## 2. Cấu trúc thư mục chuẩn của một ADK Agent

```
my_agent_app/
├── __init__.py       # Package init
├── agent.py          # Khai báo root_agent và các tools/sub-agents
└── .env              # Thiết lập biến môi trường (GOOGLE_API_KEY)
```

---

## 3. Khởi chạy nhanh Agent mẫu

Trong thư mục này đã chuẩn bị sẵn 2 Agent:
1. `starter_agent`: Agent cơ bản đơn giản.
2. `devfest_assistant_agent`: Agent thông minh phục vụ người tham dự DevFest Cloud Hanoi (tra cứu lịch trình, diễn giả, ước tính chi phí, nộp ý tưởng Buildathon).

### Bước 1: Cấu hình API Key
Mở file `.env` trong thư mục agent (ví dụ: `devfest_assistant_agent/.env`) và điền Gemini API Key của bạn:
```env
GOOGLE_GENAI_USE_ENTERPRISE=0
GOOGLE_API_KEY=your_actual_gemini_api_key_here
```
> *(Nếu chưa có API Key, lấy miễn phí tại [Google AI Studio](https://aistudio.google.com/apikey))*

### Bước 2: Chạy thử trên Terminal (CLI Mode)
```powershell
# Từ thư mục gốc dự án:
$env:PYTHONUTF8=1
.\.venv\Scripts\adk.exe run 03_Codelab_Google_ADK/devfest_assistant_agent
```

### Bước 3: Mở Web UI trực quan (Web Mode)
```powershell
# Chạy web server cục bộ
$env:PYTHONUTF8=1
.\.venv\Scripts\adk.exe web 03_Codelab_Google_ADK/devfest_assistant_agent
```
Sau đó mở trình duyệt tại: **http://127.0.0.1:8000** để trải nghiệm giao diện Web UI!

---

## 4. Cách tự định nghĩa Tool cho Agent trong Python

```python
from google.adk.agents.llm_agent import Agent

# 1. Định nghĩa Tool bằng hàm Python thuần túy
def tra_cuu_thoi_tiet(thanh_pho: str) -> str:
    """Tra cứu tình hình thời tiết hiện tại của một thành phố.
    
    Args:
        thanh_pho: Tên thành phố (ví dụ: Hanoi, Ho Chi Minh)
    """
    return f"Thời tiết tại {thanh_pho} hôm nay mát mẻ, nhiệt độ 26°C, rất lý tưởng cho DevFest!"

# 2. Gán Tool vào Agent
root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    description="Agent hỗ trợ thông tin thời tiết.",
    instruction="Bạn là trợ lý thân thiện, luôn dùng tool tra_cuu_thoi_tiet khi người dùng hỏi thời tiết.",
    tools=[tra_cuu_thoi_tiet]
)
```

---

## 5. Kiến trúc Multi-Agent (Hợp tác đa Agent)

```python
# Agent chuyên phân tích kỹ thuật
tech_agent = Agent(
    name="tech_agent",
    model="gemini-2.5-flash",
    description="Chuyên giải đáp chi tiết kiến trúc Cloud và AI",
    instruction="Giải thích sâu về MCP, Kubernetes, Cloud Run...",
)

# Agent điều phối chính (Root Agent)
root_agent = Agent(
    name="coordinator_agent",
    model="gemini-2.5-flash",
    description="Agent tiếp nhận và điều phối câu hỏi",
    instruction="Tiếp nhận câu hỏi từ người dùng và chuyển cho tech_agent nếu cần kiến thức chuyên sâu.",
    sub_agents=[tech_agent]
)
```

