"""
DevFest Cloud Hanoi 2026 - Assistant Agent
Built using Google Agent Development Kit (ADK)
Instructor: Mr. Nguyen Anh Duong (ZenAI / GDE ML)
"""

from typing import List, Dict, Any
from google.adk.agents.llm_agent import Agent

# ==========================================
# 1. Định nghĩa các Tools (Hàm nghiệp vụ)
# ==========================================

def get_agenda_schedule(keyword: str = "") -> str:
    """Tra cứu các phiên họp và techtalk trong sự kiện DevFest Cloud Hanoi 2026.
    
    Args:
        keyword: Từ khóa tìm kiếm (ví dụ: 'mcp', 'adk', 'firebase', 'gemini', 'buildathon' hoặc để trống để xem tất cả).
    """
    schedule = [
        {"time": "12:30 - 13:20", "title": "Check-in & Networking", "speaker": "Ban tổ chức GDG Cloud Hanoi"},
        {"time": "13:30 - 14:10", "title": "Techtalk: MCP? I Hardly Know Her!", "speaker": "Mr. Weiyuan Liu (Ascenda / GDE Cloud & AI)"},
        {"time": "14:10 - 14:25", "title": "Techtalk: Google Antigravity - The Enterprise Agent-first Developer Platform", "speaker": "Mr. Huy Nguyen (Google Cloud)"},
        {"time": "14:25 - 14:55", "title": "Codelab: Build an AI Agent with Google ADK", "speaker": "Mr. Nguyen Anh Duong (ZenAI / GDE ML)"},
        {"time": "14:55 - 15:15", "title": "Tea break & Networking", "speaker": "Nghỉ giải lao & giao lưu"},
        {"time": "15:15 - 15:55", "title": "Techtalk: Untrusted Devices, Trusted AI with Firebase AI Logic", "speaker": "Ms. Cleo (Factory / GDE Firebase & Cloud AI)"},
        {"time": "15:55 - 16:40", "title": "Techtalk: Gemini, What Am I Looking At? Spatial AI App with AI Studio, Gemini 3.8 Flash and Cloud Run", "speaker": "Ms. Nguyen Khanh Linh (Obello / GDE AI/ML)"},
        {"time": "16:40 - 17:15", "title": "DevFest Cloud Buildathon: Top 3 Project Presentations & Awards", "speaker": "Top 3 Selected Teams"},
        {"time": "17:15 - 17:30", "title": "Closing Session & Group Photo", "speaker": "Toàn thể hội trường & Diễn giả"}
    ]
    
    keyword_clean = keyword.strip().lower()
    if not keyword_clean:
        lines = [f"📅 {item['time']} | {item['title']} (Diễn giả: {item['speaker']})" for item in schedule]
        return "Lịch trình toàn bộ sự kiện DevFest Cloud Hanoi:\n" + "\n".join(lines)
    
    matched = [item for item in schedule if keyword_clean in item["title"].lower() or keyword_clean in item["speaker"].lower()]
    if not matched:
        return f"Không tìm thấy phiên nào với từ khóa '{keyword}'. Bạn có thể xem toàn bộ lịch trình."
    
    lines = [f"🎯 {item['time']} | {item['title']} (Diễn giả: {item['speaker']})" for item in matched]
    return f"Kết quả tìm kiếm cho '{keyword}':\n" + "\n".join(lines)


def get_speaker_details(speaker_name: str) -> str:
    """Xem thông tin chi tiết tiểu sử của diễn giả tại DevFest Cloud Hanoi 2026.
    
    Args:
        speaker_name: Tên của diễn giả (ví dụ: Weiyuan, Huy Nguyen, Anh Duong, Cleo, Khanh Linh).
    """
    speakers = {
        "weiyuan": "Mr. Weiyuan Liu: Director of Engineering tại Ascenda, Google Developer Expert (GDE) về Cloud và AI. Chuyên gia về kiến trúc đám mây và giao thức Model Context Protocol (MCP).",
        "huy": "Mr. Huy Nguyen: Customer Solutions Consultant tại Google Cloud. Chuyên gia tư vấn giải pháp AI doanh nghiệp và nền tảng Google Antigravity.",
        "duong": "Mr. Nguyen Anh Duong: Founder & CEO tại ZenAI, Google Developer Expert (GDE) về Machine Learning. Giảng viên phụ trách Codelab xây dựng AI Agent với Google ADK.",
        "cleo": "Ms. Cleo: Engineering Manager tại Factory, Google Developer Expert (GDE) về Firebase, Cloud AI và Google Maps. Chuyên gia về kiến trúc AI an toàn trên thiết bị client.",
        "linh": "Ms. Nguyen Khanh Linh: Head of AI tại Obello, Google Developer Expert (GDE) về AI/ML. Tác giả bài chia sẻ về Spatial AI, Gemini 3.8 Flash và Cloud Run."
    }
    
    key = speaker_name.lower()
    for name_key, bio in speakers.items():
        if name_key in key:
            return bio
    return f"Chưa có thông tin hồ sơ cho diễn giả '{speaker_name}'. Vui lòng thử tìm: Weiyuan, Huy, Duong, Cleo, Linh."


def register_buildathon_idea(team_name: str, project_title: str, tech_stack: str) -> str:
    """Đăng ký ý tưởng dự thi DevFest Cloud Buildathon 2026.
    
    Args:
        team_name: Tên đội thi.
        project_title: Tiêu đề dự án AI / Cloud.
        tech_stack: Công nghệ sử dụng (ví dụ: Google ADK, Gemini 3.8 Flash, Firebase AI Logic, Cloud Run).
    """
    return (
        f"✅ Đăng ký dự thi thành công cho Đội: '{team_name}'!\n"
        f"💡 Tên dự án: {project_title}\n"
        f"🛠️ Tech stack: {tech_stack}\n"
        f"🏆 Hãy chuẩn bị sẵn sàng cho phần Thuyết trình Top 3 lúc 16:40 nhé!"
    )


# ==========================================
# 2. Khởi tạo Root Agent với Google ADK
# ==========================================

root_agent = Agent(
    name="devfest_hanoi_assistant",
    model="gemini-2.5-flash",
    description="Trợ lý AI đa năng dành cho người tham gia DevFest Cloud Hanoi 2026.",
    instruction=(
        "Bạn là DevFest Hanoi AI Companion - trợ lý AI đồng hành thông minh, thân thiện và am hiểu công nghệ "
        "tại sự kiện GDG DevFest Cloud Hanoi 2026.\n"
        "Nhiệm vụ của bạn:\n"
        "1. Luôn sử dụng các công cụ đã được cung cấp (get_agenda_schedule, get_speaker_details, register_buildathon_idea) "
        "để tra cứu chính xác lịch trình, thông tin diễn giả hoặc đăng ký dự thi.\n"
        "2. Giải thích dễ hiểu các khái niệm kỹ thuật trong sự kiện như Model Context Protocol (MCP), Google Antigravity, "
        "Google Agent Development Kit (ADK), Firebase AI Logic, và Spatial AI với Gemini 3.8 Flash.\n"
        "3. Trả lời bằng tiếng Việt tự nhiên, nhiệt tình và hào hứng!"
    ),
    tools=[
        get_agenda_schedule,
        get_speaker_details,
        register_buildathon_idea
    ]
)

