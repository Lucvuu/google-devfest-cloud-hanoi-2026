import csv
import datetime
import io
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google.adk.agents import Agent, LoopAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import (
    ToolContext,
    agent_tool,
    exit_loop,
    load_artifacts,
    load_memory,
    preload_memory,
)
from google.adk.memory.memory_entry import MemoryEntry
from google.genai import types

# Load environment configuration
load_dotenv()

MODEL = os.getenv("MODEL", "gemini-3.8-flash")


# ==============================================================================
# 🎨 LIFECYCLE CALLBACKS: User State Defaults & Auto Long-Term Memory
# Slide 17: "Store user preferences under user: session state keys" & "Memory Bank"
# ==============================================================================

async def initialize_devfest_state_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """Ensures persistent `user:` state keys exist from the very first turn."""
    defaults = {
        "user:author_name": "Luc Vu • GDG Cloud Hanoi Architect",
        "user:writing_style": "Deep Technical, Practical, Engaging with Architecture & Code",
        "user:language": "Vietnamese (with standard English Cloud/AI terms)",
        "user:target_audience": "Cloud Engineers, AI Developers & Tech Leads",
        "user:tech_stack": "Google ADK, Gemini 3.8 Flash, MCP, Cloud Run, Vertex AI",
        "user:theme_edition": "GDG DevFest Cloud Hanoi 2026 Special Edition",
    }
    for key, val in defaults.items():
        if key not in callback_context.state:
            callback_context.state[key] = val
    # Refreshed every turn: a module-level date goes stale on a long-running Cloud Run instance.
    callback_context.state["current_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
    return None


async def auto_persist_session_memory_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """Automatically saves conversation history to Long-Term Memory after each turn."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        # Gracefully continue if an external memory service is not attached
        pass
    return None


# ==============================================================================
# 🎯 FEATURE 1: Personalization with `user:` Session State Keys
# ==============================================================================

def configure_author_profile(
    author_name: str,
    writing_style: str,
    language: str,
    target_audience: str,
    tech_stack: str,
    tool_context: ToolContext,
) -> str:
    """Configures persistent user preferences stored under `user:` session state keys.

    Args:
        author_name: Tên hoặc bút danh tác giả (ví dụ: 'Luc Vu - Cloud AI Architect').
        writing_style: Phong cách viết (ví dụ: 'Thực chiến, sâu sắc, có sơ đồ Mermaid & code mẫu').
        language: Ngôn ngữ bài viết ('Vietnamese' hoặc 'English' hoặc 'Bilingual').
        target_audience: Độc giả mục tiêu (ví dụ: 'Senior Software Engineers & Cloud Architects').
        tech_stack: Công nghệ trọng tâm (ví dụ: 'Google ADK, Gemini 3.8 Flash, Cloud Run, MCP').
    """
    tool_context.state["user:author_name"] = author_name
    tool_context.state["user:writing_style"] = writing_style
    tool_context.state["user:language"] = language
    tool_context.state["user:target_audience"] = target_audience
    tool_context.state["user:tech_stack"] = tech_stack
    return (
        "✅ [Personalization State Updated] Đã lưu cấu hình vào `user:` session state:\n"
        f"• user:author_name = {author_name}\n"
        f"• user:writing_style = {writing_style}\n"
        f"• user:language = {language}\n"
        f"• user:target_audience = {target_audience}\n"
        f"• user:tech_stack = {tech_stack}"
    )


# ==============================================================================
# 🧠 FEATURE 2: Explicit Fact Storage into Long-Term Memory Bank
# ==============================================================================

async def save_note_to_memory(
    topic: str,
    key_insight: str,
    tool_context: ToolContext,
) -> str:
    """Saves an important technical fact, preference, or past blog summary into Long-Term Memory.

    Args:
        topic: Chủ đề hoặc tiêu đề cần ghi nhớ.
        key_insight: Nội dung chi tiết hoặc bài học rút ra cần lưu vào bộ nhớ dài hạn.
    """
    notes = tool_context.state.get("user:memory_notes", [])
    if not isinstance(notes, list):
        notes = []
    entry_str = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] {topic}: {key_insight}"
    notes.append(entry_str)
    tool_context.state["user:memory_notes"] = notes

    try:
        await tool_context.add_session_to_memory()
    except Exception:
        pass

    return f"🧠 Đã ghi nhớ vào Long-Term Memory Bank: {entry_str}"


# ==============================================================================
# 🔍 FEATURE 3: Architecture Diagram & Context Builder
# ==============================================================================

def inject_architecture_context(
    system_title: str,
    mermaid_diagram_code: str,
    key_code_snippet: str,
    tool_context: ToolContext,
) -> str:
    """Saves an architecture Mermaid diagram and code snippet into `codebase_context` state
    so the BlogPlanner and BlogWriter automatically weave them into the article.

    Args:
        system_title: Tên kiến trúc hệ thống.
        mermaid_diagram_code: Mã sơ đồ Mermaid (ví dụ: flowchart TD ...).
        key_code_snippet: Đoạn code mẫu cốt lõi cần đưa vào bài blog.
    """
    context_md = (
        f"### Architecture Context: {system_title}\n\n"
        f"```mermaid\n{mermaid_diagram_code.strip()}\n```\n\n"
        f"### Key Implementation Snippet:\n"
        f"```python\n{key_code_snippet.strip()}\n```\n"
    )
    tool_context.state["codebase_context"] = context_md
    return f"📐 Đã nạp sơ đồ kiến trúc '{system_title}' và code mẫu vào `codebase_context`."


# ==============================================================================
# 📊 FEATURE 4: Technical SEO & Readability Analyzer
# ==============================================================================

CONCLUSION_RE = re.compile(r"kết luận|tổng kết|conclusion|takeaway|wrap.?up|lời kết", re.IGNORECASE)


def compute_seo_metrics(post: str) -> dict:
    """Pure scoring of a Markdown post: every point is earned by a named check."""
    code_blocks = re.findall(r"```[\s\S]*?```", post)
    # Headings are scanned outside code fences, otherwise a Python `# comment` counts as an H1.
    prose = re.sub(r"```[\s\S]*?```", "", post)
    h1_list = re.findall(r"^#\s+(.+)$", prose, flags=re.MULTILINE)
    h2_list = re.findall(r"^##\s+(.+)$", prose, flags=re.MULTILINE)
    h3_list = re.findall(r"^###\s+(.+)$", prose, flags=re.MULTILINE)
    mermaid_blocks = [b for b in code_blocks if b.startswith("```mermaid")]
    word_count = len(re.findall(r"\w+", post))
    title = h1_list[0].strip() if h1_list else ""

    checks = [  # (description, passed, weight) — weights sum to 100
        ("Đúng 1 tiêu đề H1", len(h1_list) == 1, 10),
        ("Tiêu đề dài 30–90 ký tự", 30 <= len(title) <= 90, 10),
        ("Bài ≥ 800 từ", word_count >= 800, 20),
        ("4–8 mục H2", 4 <= len(h2_list) <= 8, 15),
        ("≥ 2 mục con H3", len(h3_list) >= 2, 10),
        ("≥ 1 code snippet", len(code_blocks) - len(mermaid_blocks) >= 1, 15),
        ("Mọi code block có khai báo ngôn ngữ", bool(code_blocks) and all(re.match(r"```\w", b) for b in code_blocks), 5),
        ("≥ 1 sơ đồ Mermaid", len(mermaid_blocks) >= 1, 10),
        ("Có mục Kết luận / Takeaways", any(CONCLUSION_RE.search(h) for h in h2_list), 5),
    ]
    score = sum(w for _, ok, w in checks if ok)
    grade = "A+" if score >= 90 else "A" if score >= 75 else "B" if score >= 60 else "C"

    return {
        "title": title or "Technical Blog Post",
        "word_count": word_count,
        "reading_time_minutes": max(1, round(word_count / 200)),
        "h2_sections_count": len(h2_list),
        "h2_sections": h2_list,
        "h3_subsections_count": len(h3_list),
        "code_snippets_count": len(code_blocks) - len(mermaid_blocks),
        "mermaid_diagrams_count": len(mermaid_blocks),
        "technical_seo_score": score,
        "grade": grade,
        "quality_gate": "PASSED" if score >= 75 else "NEEDS WORK",
        "passed_checks": [d for d, ok, _ in checks if ok],
        "improvement_suggestions": [f"{d} (+{w} điểm)" for d, ok, w in checks if not ok],
    }


def analyze_seo_and_readability(tool_context: ToolContext) -> dict:
    """Analyzes the generated `blog_post` in state for SEO score, reading time,
    heading structure, and technical depth, saving the metrics to `seo_metrics`.
    Returns concrete improvement suggestions for every failed check.
    """
    post = tool_context.state.get("blog_post", "") or ""
    if not post.strip():
        return {"error": "Chưa có `blog_post` trong state. Hãy chạy writer_tool trước."}
    metrics = compute_seo_metrics(post)
    tool_context.state["seo_metrics"] = metrics
    return metrics


# ==============================================================================
# 📦 FEATURE 5: Multi-Format Artifacts Exporter (.MD + .CSV Report + DevFest .HTML)
# Slide 17: "return downloadable reports or CSVs stored through GcsArtifactService"
# ==============================================================================

def _render_devfest_magazine_html(
    title: str,
    author: str,
    style: str,
    tech_stack: str,
    metrics: dict,
    markdown_body: str,
) -> str:
    """Renders a Google DevFest Cloud Hanoi 2026 themed HTML Magazine article."""
    import html as html_lib
    import json

    # JSON (not html.escape) inside <script>: textContent never decodes entities, so
    # html.escape turned every `"` in code blocks into a literal `&quot;`.
    md_json = json.dumps(markdown_body).replace("</", "<\\/")
    score = metrics.get("technical_seo_score", 0)
    words = metrics.get("word_count", 0)
    read_min = metrics.get("reading_time_minutes", 1)
    code_cnt = metrics.get("code_snippets_count", 0) + metrics.get("mermaid_diagrams_count", 0)
    h2_cnt = metrics.get("h2_sections_count", 0)
    gate = metrics.get("quality_gate", "PASSED")
    gate_color = "#4ade80" if gate == "PASSED" else "#facc15"
    date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html_lib.escape(title)} | GDG DevFest Cloud Hanoi 2026</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
  <style>
    :root {{
      --g-blue: #4285F4;
      --g-red: #EA4335;
      --g-yellow: #FBBC04;
      --g-green: #34A853;
      --bg-dark: #0f172a;
      --card-bg: #1e293b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: 'Google Sans', system-ui, -apple-system, sans-serif;
      background: radial-gradient(circle at top right, #1e293b 0%, #0f172a 60%, #090d16 100%);
      color: var(--text-main);
      line-height: 1.75;
    }}
    .google-color-bar {{
      height: 6px;
      background: linear-gradient(90deg,
        var(--g-blue) 0%, var(--g-blue) 25%,
        var(--g-red) 25%, var(--g-red) 50%,
        var(--g-yellow) 50%, var(--g-yellow) 75%,
        var(--g-green) 75%, var(--g-green) 100%);
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .container {{
      max-width: 960px;
      margin: 36px auto;
      padding: 0 24px 64px;
    }}
    .hero-card {{
      background: linear-gradient(135deg, rgba(66,133,244,0.16) 0%, rgba(52,168,83,0.12) 50%, rgba(251,188,4,0.10) 100%);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 24px;
      padding: 32px 36px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.45);
      margin-bottom: 28px;
      position: relative;
      overflow: hidden;
    }}
    .devfest-badge-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-bottom: 16px;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.3px;
    }}
    .pill-blue {{ background: rgba(66,133,244,0.22); color: #93c5fd; border: 1px solid var(--g-blue); }}
    .pill-green {{ background: rgba(52,168,83,0.22); color: #86efac; border: 1px solid var(--g-green); }}
    .pill-yellow {{ background: rgba(251,188,4,0.22); color: #fde047; border: 1px solid var(--g-yellow); }}
    .pill-red {{ background: rgba(234,67,53,0.22); color: #fca5a5; border: 1px solid var(--g-red); }}
    .hero-title {{
      font-size: 32px;
      font-weight: 700;
      margin: 8px 0 16px;
      background: linear-gradient(90deg, #ffffff, #93c5fd, #fde047);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
      margin-top: 20px;
    }}
    .stat-box {{
      background: rgba(15, 23, 42, 0.72);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 14px;
      padding: 12px 16px;
    }}
    .stat-label {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; }}
    .stat-value {{ font-size: 20px; font-weight: 700; margin-top: 2px; color: #fff; }}
    .article-card {{
      background: rgba(30, 41, 59, 0.85);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 24px;
      padding: 40px 44px;
      box-shadow: 0 16px 40px rgba(0,0,0,0.35);
    }}
    .article-card h1, .article-card h2, .article-card h3 {{
      color: #f8fafc;
      margin-top: 1.6em;
    }}
    .article-card h2 {{
      border-left: 4px solid var(--g-blue);
      padding-left: 14px;
    }}
    .article-card pre {{
      background: #090d16;
      border: 1px solid rgba(66,133,244,0.35);
      border-radius: 12px;
      padding: 18px;
      overflow-x: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
    }}
    .article-card code {{
      font-family: 'JetBrains Mono', monospace;
      background: rgba(66,133,244,0.15);
      color: #93c5fd;
      padding: 2px 6px;
      border-radius: 6px;
    }}
    .article-card pre code {{
      background: transparent;
      padding: 0;
      color: #e2e8f0;
    }}
    .footer {{
      text-align: center;
      margin-top: 32px;
      color: var(--text-muted);
      font-size: 14px;
    }}
  </style>
</head>
<body>
  <div class="google-color-bar"></div>
  <div class="container">
    <div class="hero-card">
      <div class="devfest-badge-row">
        <span class="pill pill-blue">{{ DevFest }} Cloud • Hanoi 2026</span>
        <span class="pill pill-green">⚡ Powered by Google ADK & {html_lib.escape(MODEL)}</span>
        <span class="pill pill-yellow">🏆 SEO Score: {score}/100</span>
        <span class="pill pill-red">⏱️ {read_min} min read</span>
      </div>
      <div class="hero-title">{html_lib.escape(title)}</div>
      <div style="color:#cbd5e1; font-size:15px;">
        ✍️ <strong>Author:</strong> {html_lib.escape(author)} &nbsp;|&nbsp;
        🎨 <strong>Style:</strong> {html_lib.escape(style)} &nbsp;|&nbsp;
        🛠️ <strong>Stack:</strong> {html_lib.escape(tech_stack)} &nbsp;|&nbsp;
        📅 {date_str}
      </div>
      <div class="meta-grid">
        <div class="stat-box">
          <div class="stat-label">Word Count</div>
          <div class="stat-value" style="color:#60a5fa;">{words} words</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Main Sections (H2)</div>
          <div class="stat-value" style="color:#f87171;">{h2_cnt} sections</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Code & Diagrams</div>
          <div class="stat-value" style="color:#facc15;">{code_cnt} blocks</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Quality Gate</div>
          <div class="stat-value" style="color:{gate_color};">{gate}</div>
        </div>
      </div>
    </div>

    <div class="article-card" id="content"></div>

    <div class="footer">
      Generated with ❤️ by <strong>Blogger Multi-Agent System</strong> • GDG DevFest Cloud Hanoi 2026
    </div>
  </div>
  <script>
    const el = document.getElementById('content');
    el.innerHTML = marked.parse({md_json});
    el.querySelectorAll('code.language-mermaid').forEach(code => {{
      const div = document.createElement('div');
      div.className = 'mermaid';
      div.textContent = code.textContent;
      code.parentElement.replaceWith(div);
    }});
    mermaid.initialize({{ startOnLoad: false, theme: 'dark' }});
    mermaid.run();
  </script>
</body>
</html>"""


async def export_blog_artifacts(
    filename_slug: str,
    tool_context: ToolContext,
) -> str:
    """Packages and exports 3 downloadable artifacts into the ADK Artifact Service:
    1) Markdown article (.md)
    2) SEO & Section Analytics Report (.csv) - per Slide 17 requirement!
    3) Google DevFest Cloud Hanoi 2026 HTML Magazine Preview (.html)

    Args:
        filename_slug: Tên định danh ngắn gọn cho bộ file (ví dụ: 'adk_multi_agent').
    """
    post_content = tool_context.state.get("blog_post", "") or ""
    if not post_content.strip():
        return "⚠️ Chưa có nội dung `blog_post` trong state để xuất artifact."

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", filename_slug.strip().lower()).strip("_") or "devfest_blog"

    # Compute SEO metrics first
    metrics = analyze_seo_and_readability(tool_context)

    author = tool_context.state.get("user:author_name", "GDG Cloud Hanoi Developer")
    style = tool_context.state.get("user:writing_style", "Technical & Practical")
    tech_stack = tool_context.state.get("user:tech_stack", "Google ADK, Gemini 3.8 Flash")
    title = metrics.get("title", "DevFest Cloud Hanoi 2026 Technical Article")

    # 1. Save Markdown Artifact (.md)
    md_filename = f"{slug}_article.md"
    md_part = types.Part.from_bytes(
        data=post_content.encode("utf-8"),
        mime_type="text/markdown",
    )
    v_md = await tool_context.save_artifact(filename=md_filename, artifact=md_part)

    # 2. Save SEO & Section Breakdown CSV Artifact (.csv) - Slide 17 requirement!
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow([
        "Section_Index",
        "Section_Heading",
        "Estimated_Words",
        "Has_Code_Snippet",
        "Author",
        "SEO_Score",
        "Quality_Gate_Status",
    ])
    sections = re.split(r"(?=^##\s+)", post_content, flags=re.MULTILINE)
    sec_idx = 0
    for sec in sections:
        if not sec.strip():
            continue
        sec_idx += 1
        first_line = sec.strip().splitlines()[0].lstrip("#").strip()
        sec_words = len(re.findall(r"\w+", sec))
        has_code = "Yes" if "```" in sec else "No"
        writer.writerow([
            sec_idx,
            first_line[:80],
            sec_words,
            has_code,
            author,
            metrics.get("technical_seo_score", 0),
            metrics.get("quality_gate", ""),
        ])

    csv_filename = f"{slug}_seo_report.csv"
    csv_part = types.Part.from_bytes(
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        mime_type="text/csv",
    )
    v_csv = await tool_context.save_artifact(filename=csv_filename, artifact=csv_part)

    # 3. Save Google DevFest Magazine HTML Artifact (.html)
    html_content = _render_devfest_magazine_html(
        title=title,
        author=str(author),
        style=str(style),
        tech_stack=str(tech_stack),
        metrics=metrics,
        markdown_body=post_content,
    )
    html_filename = f"{slug}_devfest_magazine.html"
    html_part = types.Part.from_bytes(
        data=html_content.encode("utf-8"),
        mime_type="text/html",
    )
    v_html = await tool_context.save_artifact(filename=html_filename, artifact=html_part)

    return (
        "🎉 Đã xuất thành công bộ 3 Artifacts chuẩn DevFest Cloud Hanoi 2026 (mở tab 'Artifacts' trên Web UI để tải về):\n"
        f"1. 📄 `{md_filename}` (v{v_md}) — Bài viết Markdown gốc\n"
        f"2. 📊 `{csv_filename}` (v{v_csv}) — Báo cáo phân tích SEO & cấu trúc từng mục (CSV)\n"
        f"3. 🎨 `{html_filename}` (v{v_html}) — Giao diện Tạp chí Google DevFest 4 màu tuyệt đẹp (HTML)\n"
        f"🏆 Điểm SEO Kỹ thuật: {metrics.get('technical_seo_score')}/100 ({metrics.get('grade')}, {metrics.get('quality_gate')})\n"
        + ("💡 Gợi ý cải thiện: " + "; ".join(metrics["improvement_suggestions"]) if metrics.get("improvement_suggestions") else "")
    )


# ==============================================================================
# 🎪 FEATURE 6: DevFest Cloud Hanoi 2026 Event Context Lookup
# ==============================================================================

def get_devfest_hanoi_context(topic_filter: str = "") -> str:
    """Provides official session & speaker details from GDG DevFest Cloud Hanoi 2026
    so the blog post can cite real talks and technologies from the event.

    Args:
        topic_filter: Từ khóa lọc (ví dụ: 'mcp', 'antigravity', 'adk', 'firebase', 'spatial').
    """
    talks = [
        "13:30-14:10 | Techtalk: MCP? I Hardly Know Her! — Mr. Weiyuan Liu (Director of Engineering @ Ascenda; GDE Cloud & AI)",
        "14:10-14:25 | Techtalk: Google Antigravity – The Enterprise Agent-first Developer Platform — Mr. Huy Nguyen (Customer Solutions Consultant @ Google Cloud)",
        "14:25-14:55 | Codelab: Build an AI Agent with Google ADK (Memory, State user:, Artifacts) — Mr. Nguyen Anh Duong (Founder & CEO @ ZenAI; GDE ML)",
        "15:15-15:55 | Techtalk: Untrusted Devices, Trusted AI with Firebase AI Logic — Ms. Cleo (GDE Firebase, Cloud AI & Maps; EM @ Factory)",
        "15:55-16:40 | Techtalk: Gemini, What Am I Looking At? Shipping a Spatial AI App with AI Studio, Gemini 3.8 Flash and Cloud Run — Ms. Nguyen Khanh Linh (GDE AI/ML; Head of AI @ Obello)",
        "16:40-17:15 | DevFest Cloud Buildathon: Top 3 Project Presentations & Awards",
    ]
    q = topic_filter.strip().lower()
    if q:
        matched = [t for t in talks if q in t.lower()]
        if matched:
            return "🎪 DevFest Cloud Hanoi 2026 Sessions:\n" + "\n".join(matched)
    return "🎪 GDG DevFest Cloud Hanoi 2026 Full Agenda:\n" + "\n".join(talks)


# ==============================================================================
# 📝 SUB-AGENT 1: BlogPlanner & RobustBlogPlanner Loop
# ==============================================================================

blog_planner = Agent(
    name="BlogPlanner",
    model=MODEL,
    description="Creates a practical, skimmable outline in Markdown tailored to user preferences.",
    instruction="""
You are a technical content strategist at GDG DevFest Cloud Hanoi 2026.
Produce a clear Markdown outline with:
- Title
- Short intro
- 4–6 main sections (each with 2–3 bullets)
- Conclusion

Personalization Preferences (from `user:` session state):
- Author: {user:author_name?}
- Writing Style: {user:writing_style?}
- Preferred Language: {user:language?}
- Target Audience: {user:target_audience?}
- Core Tech Stack: {user:tech_stack?}

Optional Architecture / Codebase Context in state:
{codebase_context?}

If `codebase_context` or uploaded artifacts exist, weave in specific sections, Mermaid diagrams, or code snippets.

Reviewer feedback from the previous attempt (if it is not "ok", fix every listed issue):
{outline_feedback?}

Return only the outline in Markdown.
""",
    output_key="blog_outline",
    tools=[load_artifacts],
)


class OutlineValidationChecker(Agent):
    def __init__(self):
        super().__init__(
            name="OutlineValidationChecker",
            model=MODEL,
            description="Validates that the outline is usable and exits the planning loop when valid.",
            instruction="""
Check the outline in state `blog_outline`:
---
{blog_outline?}
---
If it has a title, intro, 4–6 sections, and a conclusion:
1. Call the `exit_loop` tool immediately so the loop finishes without redundant retries.
2. Respond with "ok".

Otherwise respond "retry" followed by a bullet list of missing pieces (the planner reads this).
""",
            output_key="outline_feedback",
            tools=[exit_loop],
            generate_content_config=types.GenerateContentConfig(temperature=0.1),
        )


robust_blog_planner = LoopAgent(
    name="RobustBlogPlanner",
    description="Plans and validates the blog outline (up to 3 iterations).",
    sub_agents=[blog_planner, OutlineValidationChecker()],
    max_iterations=3,
)


# ==============================================================================
# ✍️ SUB-AGENT 2: BlogWriter & RobustBlogWriter Loop
# ==============================================================================

blog_writer = Agent(
    name="BlogWriter",
    model=MODEL,
    description="Writes a complete technical blog post from the validated outline.",
    instruction="""
Write a complete, publication-ready Markdown article from the outline in `blog_outline`:
---
{blog_outline?}
---

Personalization Preferences (from `user:` session state):
- Author Name: {user:author_name?}
- Writing Style: {user:writing_style?}
- Output Language: {user:language?}
- Target Audience: {user:target_audience?}
- Core Tech Stack: {user:tech_stack?}

Additional Codebase / Architecture Context (if any):
{codebase_context?}

Reviewer feedback from the previous attempt (if it is not "ok", fix every listed issue):
{post_feedback?}

Revision mode: if the request you received asks to revise/edit/shorten/translate the existing article,
start from the current article below and change only what was asked, keeping everything else intact.
For a brand-new topic, ignore it.
---
{blog_post?}
---

Guidelines:
- Audience: software engineers; skip trivial basics and focus on practical insight and real-world architecture.
- Explain both the 'how' and the 'why', including trade-offs and when NOT to use the approach.
- Include concise, runnable code snippets with a language tag on every fence (```python, ```bash, ...).
- Include at least one Mermaid architecture diagram (```mermaid) using only valid Mermaid syntax.
- Follow the outline's structure: exactly one H1 title (30–90 characters), 4–8 H2 sections, H3 subsections,
  and a final H2 conclusion/takeaways section. Aim for 1000–1800 words.
- Never invent API names, flags or benchmark numbers; if unsure, say so explicitly.
- Output only the final article in Markdown (no outer code fence around the whole post).
""",
    output_key="blog_post",
    tools=[load_artifacts],
)


class BlogPostValidationChecker(Agent):
    def __init__(self):
        super().__init__(
            name="BlogPostValidationChecker",
            model=MODEL,
            description="Validates the final blog post and exits the writing loop when valid.",
            instruction="""
Check `blog_post` in state for: intro, clear sections matching the outline, conclusion, technical clarity,
language tags on every code fence, at least one Mermaid diagram, and no obviously invented APIs:
---
{blog_post?}
---
If it passes validation:
1. Call the `exit_loop` tool immediately to finish the writing loop.
2. Respond with "ok".

Else respond "retry" followed by a bullet list of specific fixes (the writer reads this).
""",
            output_key="post_feedback",
            tools=[exit_loop],
            generate_content_config=types.GenerateContentConfig(temperature=0.1),
        )


robust_blog_writer = LoopAgent(
    name="RobustBlogWriter",
    description="Writes and validates the full technical blog post (up to 3 iterations).",
    sub_agents=[blog_writer, BlogPostValidationChecker()],
    max_iterations=3,
)

# Expose planner/writer as tools so the root agent can call them explicitly
planner_tool = agent_tool.AgentTool(agent=robust_blog_planner)
writer_tool = agent_tool.AgentTool(agent=robust_blog_writer)


# ==============================================================================
# 👑 ROOT AGENT: Blogger (DevFest Cloud Hanoi 2026 Flagship Edition)
# ==============================================================================

root_agent = Agent(
    name="Blogger",
    model=MODEL,
    description="GDG DevFest Cloud Hanoi 2026 Multi-Agent Blogger with Personalization State, Memory Bank, SEO Analytics & Multi-Artifact Export.",
    before_agent_callback=initialize_devfest_state_callback,
    after_agent_callback=auto_persist_session_memory_callback,
    instruction=f"""
You are **Blogger Studio AI** — the flagship multi-agent technical publishing system built for **GDG DevFest Cloud Hanoi 2026**!

### Active Personalization Profile (`user:` Session State)
- **Author:** {{user:author_name?}}
- **Style:** {{user:writing_style?}}
- **Language:** {{user:language?}}
- **Audience:** {{user:target_audience?}}
- **Tech Stack:** {{user:tech_stack?}}

### Current Session State Snapshot
- **Latest Validated Article (`blog_post`):**
{{blog_post?}}

### How to Handle User Requests
1. **When the user wants to set or update their persona/preferences:**
   Call `configure_author_profile` to persist their preferences under `user:` state keys, and optionally `save_note_to_memory`.
2. **When the user gives a blog topic:**
   - *(Optional)* If the topic relates to DevFest Hanoi, call `get_devfest_hanoi_context` to enrich with real speaker/session facts.
   - **Step 1:** Call `RobustBlogPlanner` (`planner_tool`) to generate and validate the Markdown outline.
   - **Step 2:** Call `RobustBlogWriter` (`writer_tool`) to write and validate the full technical article.
   - **Step 3:** Call `export_blog_artifacts` to automatically generate and save the 3 downloadable artifacts (`.md` article, `.csv` SEO analytics report, and `.html` Google DevFest Magazine preview) into the ADK Artifact Service!
   - **Step 4:** Present the complete Markdown article from `blog_post`, followed by:
     - 📊 A summary table of the **Technical SEO Score & Metrics**
     - 🎯 **3 Alternate High-CTR Titles**
     - 🐦 **2 Tweet-length Hooks** (with `#DevFestHanoi2026 #GoogleADK #Gemini`)
     - 📦 A note guiding the user to click the **Artifacts** tab in the Web UI to download the `.md`, `.csv`, and `.html` files!
   - If the SEO quality gate is "NEEDS WORK", list the `improvement_suggestions` and offer to fix them.
3. **When the user asks to edit the existing article** (sửa, rút gọn, thêm mục, dịch, fix SEO suggestions...):
   Do NOT re-run the planner. Call `RobustBlogWriter` with a request starting with "REVISE:" plus the exact changes,
   then call `export_blog_artifacts` again with the same slug (artifacts get a new version).

### Rules
- Present `blog_post` verbatim; never rewrite the article yourself outside the writer tool.
- Report SEO numbers exactly as the tools return them; never inflate scores.

Date: {{current_date?}}
""",
    tools=[
        planner_tool,                  # calls RobustBlogPlanner (LoopAgent)
        writer_tool,                   # calls RobustBlogWriter (LoopAgent)
        configure_author_profile,      # updates `user:` state keys
        export_blog_artifacts,         # saves .md, .csv, .html via save_artifact()
        analyze_seo_and_readability,   # computes SEO score & reading metrics
        inject_architecture_context,   # injects Mermaid diagram & code snippet into state
        get_devfest_hanoi_context,     # looks up DevFest Cloud Hanoi 2026 agenda
        save_note_to_memory,           # saves notes to Long-Term Memory
        load_memory,                   # ADK built-in memory search tool
        preload_memory,                # ADK built-in memory preloader
        load_artifacts,                # ADK built-in file/image upload reader
    ],
)
