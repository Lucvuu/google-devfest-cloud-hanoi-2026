"""
DevFest Cloud Hanoi 2026 - MCP Demo Server
Speaker: Mr. Weiyuan Liu (Ascenda / GDE Cloud & AI)
Sample MCP 2.x Server exposing tools and resources for Cloud & AI developers.
"""

from mcp.server import MCPServer

# Khởi tạo MCP Server (MCP 2.x API)
mcp = MCPServer(name="DevFest-Hanoi-Cloud-Assistant")


@mcp.tool()
def get_session_info(session_id: str) -> str:
    """Tra cứu thông tin session trong DevFest Hanoi 2026 theo ID."""
    agenda = {
        "mcp": "Techtalk: MCP? I Hardly Know Her! (13:30 - 14:10)",
        "antigravity": "Techtalk: Google Antigravity - The Enterprise Agent-first Developer Platform (14:10 - 14:25)",
        "adk": "Codelab: Build an AI Agent with Google ADK (14:25 - 14:55)",
        "firebase": "Techtalk: Untrusted Devices, Trusted AI with Firebase AI Logic (15:15 - 15:55)",
        "spatial": "Techtalk: Gemini, What Am I Looking At? Spatial AI App with Gemini 3.8 Flash (15:55 - 16:40)",
        "buildathon": "DevFest Cloud Buildathon: Top 3 Presentations & Awards (16:40 - 17:15)",
    }
    return agenda.get(session_id.lower(), f"Session '{session_id}' không tìm thấy trong Agenda.")


@mcp.tool()
def calculate_cloud_cost(vcpus: int, ram_gb: int, hours_per_month: int = 730) -> dict:
    """Ước tính chi phí serverless compute trên Google Cloud Run / Dataproc Serverless."""
    vcpu_rate = 0.000024  # $ per vCPU-second ước tính
    ram_rate = 0.0000025  # $ per GiB-second ước tính
    total_seconds = hours_per_month * 3600
    cpu_cost = vcpus * total_seconds * vcpu_rate
    mem_cost = ram_gb * total_seconds * ram_rate
    total = cpu_cost + mem_cost
    return {
        "vcpus": vcpus,
        "ram_gb": ram_gb,
        "monthly_hours": hours_per_month,
        "estimated_cost_usd": round(total, 2),
    }


@mcp.resource("devfest://agenda/full")
def full_agenda() -> str:
    """Trả về toàn bộ nội dung Agenda của DevFest Cloud Hanoi."""
    return """
DevFest Cloud Hanoi 2026:
- 12:30 - 13:20: Check-in & Networking
- 13:30 - 14:10: Techtalk: MCP? I Hardly Know Her! (Mr. Weiyuan Liu)
- 14:10 - 14:25: Techtalk: Google Antigravity - Enterprise Agent-first Developer Platform (Mr. Huy Nguyen)
- 14:25 - 14:55: Codelab: Build an AI Agent with Google ADK (Mr. Nguyen Anh Duong)
- 14:55 - 15:15: Tea break & Networking
- 15:15 - 15:55: Techtalk: Untrusted Devices, Trusted AI with Firebase AI Logic (Ms. Cleo)
- 15:55 - 16:40: Techtalk: Gemini 3.8 Flash & Spatial AI on Cloud Run (Ms. Nguyen Khanh Linh)
- 16:40 - 17:15: Buildathon Presentations & Awards
- 17:15 - 17:30: Closing & Photo
    """


if __name__ == "__main__":
    print("Khởi động DevFest Cloud Hanoi MCP Server qua stdio...")
    mcp.run(transport="stdio")
