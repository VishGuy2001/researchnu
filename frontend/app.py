import streamlit as st
import httpx
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ASSETS = Path(__file__).parent / "assets"
API    = "http://localhost:8000"

# ── email helper ──────────────────────────────────────────────────────────────
def send_email(subject: str, body: str) -> bool:
    try:
        gmail_user     = os.getenv("GMAIL_FROM", "vishnusekar20@gmail.com")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")
        if not gmail_password:
            return False
        msg            = MIMEMultipart()
        msg["From"]    = gmail_user
        msg["To"]      = gmail_user
        msg["Subject"] = f"[ResearchNu] {subject}"
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, gmail_user, msg.as_string())
        return True
    except Exception:
        return False

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchNu",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ── base ── */
.stApp { background: #0d1117; color: #e6edf3; }

/* ── sidebar — lighter so text is readable ── */
section[data-testid="stSidebar"] {
    background: #1c2128;
    border-right: 1px solid #30363d;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown { color: #cdd9e5 !important; }

/* ── search box — bigger + brighter ── */
.stTextArea textarea {
    background: #1c2128 !important;
    color: #ffffff !important;
    border: 1.5px solid #388bfd !important;
    border-radius: 10px !important;
    font-size: 17px !important;
    padding: 14px !important;
}
.stTextArea textarea::placeholder { color: #8b949e !important; }
.stTextArea textarea:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.2) !important;
}
.stTextArea label {
    color: #cdd9e5 !important;
    font-size: 16px !important;
    font-weight: 600 !important;
}
.stTextInput input {
    background: #1c2128 !important;
    color: #ffffff !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    font-size: 15px !important;
}
.stTextInput label { color: #cdd9e5 !important; font-size: 14px !important; }
.stSelectbox > div > div {
    background: #1c2128 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
}

/* ── buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #1f6feb, #1158c7) !important;
    color: white !important; font-weight: 600 !important;
    border-radius: 8px !important; border: none !important;
    padding: 10px 24px !important; transition: all 0.2s !important;
    font-size: 14px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #388bfd, #1f6feb) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: #21262d !important;
    border: 1px solid #30363d !important;
}

/* ── cards ── */
.result-card {
    background: #1c2128; border: 1px solid #30363d; border-radius: 12px;
    padding: 20px 24px; margin: 12px 0;
}
.cite-item {
    background: #1c2128; border: 1px solid #30363d; border-radius: 8px;
    padding: 10px 14px; margin: 6px 0; font-size: 13px;
    border-left: 3px solid #1f6feb;
}
.source-tag {
    display: inline-block; background: rgba(31,111,235,0.15);
    color: #58a6ff; padding: 3px 10px; border-radius: 12px;
    font-size: 12px; margin: 2px; border: 1px solid rgba(31,111,235,0.3);
}
.novelty-badge-high { color: #3fb950; font-size: 52px; font-weight: 800; line-height: 1; }
.novelty-badge-mid  { color: #d29922; font-size: 52px; font-weight: 800; line-height: 1; }
.novelty-badge-low  { color: #f85149; font-size: 52px; font-weight: 800; line-height: 1; }
.novelty-bar-bg   { background: #21262d; border-radius: 8px; height: 10px; width: 100%; margin: 8px 0; }
.novelty-bar-fill { height: 10px; border-radius: 8px; transition: width 0.5s; }

/* ── section headers ── */
.section-header {
    font-size: 13px; font-weight: 600; color: #8b949e;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin: 16px 0 8px 0; padding-bottom: 4px;
    border-bottom: 1px solid #30363d;
}

/* ── about / stat cards ── */
.about-card {
    background: #1c2128; border: 1px solid #30363d; border-radius: 12px;
    padding: 12px 16px; margin: 6px 0;
}
.about-card h3 { color: #58a6ff; margin: 0 0 6px 0; font-size: 14px; }
.about-card p  { color: #cdd9e5; font-size: 12px; line-height: 1.5; margin: 0; }
.stat-box {
    background: #1c2128; border: 1px solid #30363d; border-radius: 10px;
    padding: 14px; text-align: center;
}
.stat-box .stat-num   { font-size: 26px; font-weight: 700; color: #58a6ff; }
.stat-box .stat-label { font-size: 12px; color: #8b949e; margin-top: 4px; }

/* ── sidebar logo ── */
.sidebar-logo-name { font-size: 22px; font-weight: 800; color: #e6edf3; letter-spacing: -0.3px; margin: 0; }
.sidebar-logo-sub  { font-size: 12px; color: #8b949e; margin-top: 2px; }

/* ── main title ── */
.main-title    { font-size: 42px; font-weight: 800; color: #e6edf3; letter-spacing: -0.5px; margin: 0 0 6px 0; }
.main-subtitle { color: #8b949e; font-size: 16px; margin-top: 0; }

/* ── hide streamlit branding ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] { background: #1c2128; border-radius: 8px; padding: 4px; gap: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #8b949e; border-radius: 6px; font-weight: 500; }
.stTabs [aria-selected="true"] { background: #21262d !important; color: #e6edf3 !important; }
hr { border-color: #30363d !important; }
.streamlit-expanderHeader { background: #1c2128 !important; border: 1px solid #30363d !important; border-radius: 8px !important; color: #e6edf3 !important; }

/* ── builder profile ── */
.profile-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 24px 0 8px 0;
}
.profile-wrapper img {
    border-radius: 50% !important;
    width: 160px !important;
    height: 160px !important;
    object-fit: cover !important;
    border: 3px solid #30363d;
    margin-bottom: 16px;
}
.profile-name   { font-size: 26px; font-weight: 800; color: #e6edf3; margin: 0 0 4px 0; }
.profile-sub    { font-size: 14px; color: #8b949e; margin: 0 0 4px 0; }
.profile-links  { margin-top: 10px; }
.profile-links a { color: #58a6ff; font-size: 14px; font-weight: 600; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_path = ASSETS / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=240)
    else:
        st.markdown("<span style='font-size:120px'>🔬</span>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:24px;font-weight:900;color:#e6edf3;margin:6px 0 2px 0;letter-spacing:-0.5px'>ResearchNu</p>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e;font-size:12px;margin:0'>Free agentic AI research intelligence</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown('<div style="font-size:15px;font-weight:700;color:#cdd9e5;margin:16px 0 8px 0">Search Mode</div>', unsafe_allow_html=True)
    user_type = st.selectbox(
        "Mode",
        ["researcher", "founder", "grant", "all"],
        format_func=lambda x: {
            "researcher": "🔬 Researcher",
            "founder":    "🚀 Startup Founder",
            "grant":      "💰 Grant Seeker",
            "all":        "🌐 All Sources"
        }[x],
        label_visibility="collapsed"
    )

    st.markdown('<div class="section-header">Options</div>', unsafe_allow_html=True)
    privacy_mode = st.toggle("🔒 Privacy Mode", value=False,
        help="Query stays on our servers only — never sent to third-party AI")
    if privacy_mode:
        st.info("🔒 Local inference active")

    st.divider()
    st.markdown('<div class="section-header">Active Sources</div>', unsafe_allow_html=True)
    source_map = {
        "researcher": ["PubMed","arXiv","OpenAlex","Europe PMC","CORE","CrossRef","NIH","NSF","ClinicalTrials","Google Patents","CourtListener"],
        "founder":    ["arXiv","OpenAlex","Lens.org","Google Patents","Y Combinator","Product Hunt","Alpha Vantage","News"],
        "grant":      ["PubMed","OpenAlex","NIH","NSF","UKRI","ClinicalTrials","Europe PMC","CORE"],
        "all":        ["All 20+ Sources"]
    }
    for s in source_map.get(user_type, []):
        st.markdown(f"<p style='color:#cdd9e5;font-size:13px;margin:2px 0'>✓ {s}</p>", unsafe_allow_html=True)

    st.divider()
    debug = st.checkbox("🛠 Debug mode", value=False)

# ── top header bar ────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:16px;padding:18px 0 10px 0;border-bottom:1px solid #30363d;margin-bottom:16px">
    <div>
        <span style="font-size:38px;font-weight:900;background:linear-gradient(90deg,#58a6ff,#1f6feb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-1px">ResearchNu</span>
        <span style="font-size:14px;color:#8b949e;margin-left:14px">Free agentic AI research intelligence</span>
    </div>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔍 Search", "💡 Idea Analyzer", "📊 Funding Odds", "📖 How It Works", "ℹ️ About", "👤 Builder", "💬 Contact"])

# ══════════════════════════════════════════
# TAB 1 — SEARCH
# ══════════════════════════════════════════
with tabs[0]:
    st.markdown("<p class='main-title'>ResearchNu</p>", unsafe_allow_html=True)
    st.markdown("<p class='main-subtitle'>Free agentic AI — papers, patents, grants and market insights globally</p>", unsafe_allow_html=True)
    st.divider()

    query = st.text_area(
        "What do you want to explore?",
        placeholder="e.g. Using ML to predict orthopedic implant failure in total knee arthroplasty\n\nPress Ctrl+Enter to analyze",
        height=120,
        key="main_query"
    )

    col1, col2, col3 = st.columns([1, 1, 5])
    with col1:
        run = st.button("🔍 Analyze", type="primary", use_container_width=True)
    with col2:
        clear = st.button("🗑 Clear", use_container_width=True)
    if clear:
        st.rerun()

    if query and query.endswith("\n") and not run:
        run   = True
        query = query.strip()

    if run and query.strip():
        with st.spinner("Running agents across all sources..."):
            try:
                resp = httpx.post(f"{API}/query", json={
                    "query":        query.strip(),
                    "user_type":    user_type,
                    "privacy_mode": privacy_mode
                }, timeout=120)
                r = resp.json()
                if debug:
                    st.json(r)
                st.divider()

                score = round(float(r.get("novelty_score", 0)), 1)
                if score > 60:
                    badge_cls, bar_color, verdict, verdict_color = "novelty-badge-high","#3fb950","Highly Novel","#3fb950"
                elif score > 35:
                    badge_cls, bar_color, verdict, verdict_color = "novelty-badge-mid","#d29922","Partially Novel","#d29922"
                else:
                    badge_cls, bar_color, verdict, verdict_color = "novelty-badge-low","#f85149","Well Covered","#f85149"

                col_score, col_analysis = st.columns([1, 3])
                with col_score:
                    st.markdown(f"""
                    <div class="result-card" style="text-align:center">
                        <p style="color:#8b949e;font-size:12px;margin:0;text-transform:uppercase;letter-spacing:0.08em">Novelty Score</p>
                        <div class="{badge_cls}">{score}</div>
                        <p style="color:#8b949e;font-size:12px;margin:0">/ 100</p>
                        <div class="novelty-bar-bg">
                            <div class="novelty-bar-fill" style="width:{score}%;background:{bar_color}"></div>
                        </div>
                        <p style="color:{verdict_color};font-size:13px;font-weight:600;margin:4px 0 0 0">{verdict}</p>
                    </div>""", unsafe_allow_html=True)
                    with st.expander("📊 Score Breakdown"):
                        st.markdown("""<div style="font-size:13px;color:#cdd9e5">
                        <p><span style="color:#f85149">●</span> <b>0–30</b>: Well Covered</p>
                        <p><span style="color:#d29922">●</span> <b>31–60</b>: Partially Novel</p>
                        <p><span style="color:#3fb950">●</span> <b>61–100</b>: Highly Novel</p>
                        <hr><p style="color:#8b949e;font-size:12px">Score based on overlap with existing works found across all sources.</p>
                        </div>""", unsafe_allow_html=True)

                with col_analysis:
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    st.markdown("**🔍 Novelty Analysis**")
                    report = r.get("novelty_report", "")
                    display = (report[:600] + "...") if len(report) > 600 else report
                    st.markdown(f"<p style='color:#cdd9e5;font-size:14px'>{display}</p>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                st.divider()
                st.markdown("### 📝 Plain English Summary")
                st.success(r.get("summary", ""))

                with st.expander("🔬 Detailed Technical Analysis"):
                    st.markdown(r.get("detailed_answer", ""))

                citations = r.get("citations", [])
                with st.expander(f"📚 Citations ({len(citations)} sources found)"):
                    for c in citations:
                        st.markdown(f"""<div class="cite-item">
                            <a href="{c['url']}" target="_blank" style="color:#58a6ff;font-weight:600;text-decoration:none">{c['title']}</a><br>
                            <span style="color:#8b949e;font-size:12px">{c['source']} · {c['year']}</span>
                        </div>""", unsafe_allow_html=True)

                sources_used = r.get("sources_used", [])
                if sources_used:
                    st.markdown("**Sources queried:** " + " ".join([
                        f'<span class="source-tag">{s}</span>' for s in sources_used
                    ]), unsafe_allow_html=True)

            except httpx.ConnectError:
                st.error("Cannot connect to API. Make sure uvicorn is running on port 8000.")
            except Exception as e:
                st.error(f"Error: {e}")
    elif run:
        st.warning("Please enter a research question.")

# ══════════════════════════════════════════
# TAB 2 — IDEA ANALYZER
# ══════════════════════════════════════════
with tabs[1]:
    st.markdown("<p class='main-title' style='font-size:32px'>💡 Idea Analyzer</p>", unsafe_allow_html=True)
    st.markdown("<p class='main-subtitle'>Analyze your startup idea, research concept, or product — get a full landscape report</p>", unsafe_allow_html=True)
    st.divider()

    idea      = st.text_area("Describe your idea", placeholder="e.g. A wearable device that uses ML to predict scoliosis progression in adolescents using IMU sensors", height=120, key="idea_input")
    idea_type = st.selectbox("Idea type", ["Research Project", "Startup / Product", "Patent / IP", "Grant Application"])

    if st.button("🧠 Analyze Idea", type="primary"):
        if idea.strip():
            with st.spinner("Analyzing idea across all sources..."):
                try:
                    utype = {"Research Project":"researcher","Startup / Product":"founder","Patent / IP":"founder","Grant Application":"grant"}[idea_type]
                    resp  = httpx.post(f"{API}/query", json={"query": idea.strip(), "user_type": utype, "privacy_mode": False}, timeout=120)
                    r     = resp.json()
                    score = round(float(r.get("novelty_score", 0)), 1)

                    col1, col2, col3 = st.columns(3)
                    for col, num, label in [
                        (col1, score,                        "Novelty Score / 100"),
                        (col2, len(r.get("citations",[])),   "Related Works Found"),
                        (col3, len(r.get("sources_used",[])), "Sources Searched")
                    ]:
                        with col:
                            st.markdown(f"""<div class="stat-box">
                                <div class="stat-num">{num}</div>
                                <div class="stat-label">{label}</div>
                            </div>""", unsafe_allow_html=True)

                    st.divider()
                    st.markdown("### Landscape Report")
                    st.markdown(r.get("detailed_answer", ""))
                    st.markdown("### Summary")
                    st.success(r.get("summary", ""))
                    with st.expander("📚 Related Works"):
                        for c in r.get("citations", []):
                            st.markdown(f"""<div class="cite-item">
                                <a href="{c['url']}" target="_blank" style="color:#58a6ff">{c['title']}</a>
                                <span style="color:#8b949e;font-size:12px"> · {c['source']} · {c['year']}</span>
                            </div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please describe your idea.")

# ══════════════════════════════════════════
# TAB 3 — FUNDING ODDS
# ══════════════════════════════════════════
with tabs[2]:
    st.markdown("<p class='main-title' style='font-size:32px'>📊 Funding & Grant Odds</p>", unsafe_allow_html=True)
    st.markdown("<p class='main-subtitle'>Estimate your chances of getting funded based on current trends, active grants, and startup activity</p>", unsafe_allow_html=True)
    st.divider()

    fund_idea = st.text_area("Describe your project or startup", placeholder="e.g. AI-powered drug discovery platform for rare diseases using graph neural networks", height=100, key="fund_input")
    fund_type = st.selectbox("Funding type", ["Academic Grant (NIH/NSF)", "EU Horizon Grant", "Startup Seed Funding", "Patent Filing", "All of the above"])

    if st.button("📊 Estimate Funding Odds", type="primary"):
        if fund_idea.strip():
            with st.spinner("Analyzing funding landscape..."):
                try:
                    utype = "grant" if "Grant" in fund_type else "founder" if "Startup" in fund_type else "all"
                    resp  = httpx.post(f"{API}/query", json={"query": fund_idea.strip() + " funding grant investment", "user_type": utype, "privacy_mode": False}, timeout=120)
                    r     = resp.json()
                    score = round(float(r.get("novelty_score", 0)), 1)

                    if score > 60:
                        odds, odds_color, rationale = "High (65–80%)",        "#3fb950", "High novelty + low competition = strong funding candidate"
                    elif score > 35:
                        odds, odds_color, rationale = "Moderate (35–60%)",    "#d29922", "Some competition exists — differentiation is key"
                    else:
                        odds, odds_color, rationale = "Competitive (15–35%)", "#f85149", "Well-covered area — need strong differentiation to stand out"

                    st.markdown(f"""<div class="result-card">
                        <p style="color:#8b949e;font-size:13px;margin:0">Estimated Funding Probability</p>
                        <p style="color:{odds_color};font-size:32px;font-weight:700;margin:4px 0">{odds}</p>
                        <p style="color:#cdd9e5;font-size:13px">{rationale}</p>
                    </div>""", unsafe_allow_html=True)

                    st.markdown("### Active Funding Landscape")
                    st.markdown(r.get("detailed_answer", ""))
                    with st.expander("📚 Related Grants & Funded Projects"):
                        for c in r.get("citations", []):
                            st.markdown(f"""<div class="cite-item">
                                <a href="{c['url']}" target="_blank" style="color:#58a6ff">{c['title']}</a>
                                <span style="color:#8b949e;font-size:12px"> · {c['source']} · {c['year']}</span>
                            </div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please describe your project.")

# ══════════════════════════════════════════
# TAB 4 — HOW IT WORKS
# ══════════════════════════════════════════
with tabs[3]:
    st.markdown("<p class='main-title' style='font-size:32px'>📖 How It Works</p>", unsafe_allow_html=True)
    st.divider()

    for step, desc in [
        ("1. Choose your mode",   "Select Researcher, Founder, Grant Seeker, or All Sources from the sidebar. Each mode activates a different set of sources optimized for your needs."),
        ("2. Enter your query",   "Type your research question, startup idea, or topic. Be specific for better results. Press Ctrl+Enter or click Analyze."),
        ("3. Read your results",  "ResearchNu searches 20+ sources simultaneously, synthesizes findings with a 7-agent AI pipeline, and gives you a novelty score, plain English summary, and full citations."),
        ("4. Use Idea Analyzer",  "Have a startup idea or research concept? Get a full landscape report across academic, patent, and market sources."),
        ("5. Check Funding Odds", "Estimate your chances of getting funded based on how novel your idea is and what is currently being funded."),
    ]:
        st.markdown(f"""<div class="about-card"><h3>{step}</h3><p>{desc}</p></div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### Understanding the Novelty Score")
    st.markdown("""<div class="result-card">
        <p style="color:#cdd9e5;font-size:14px;line-height:1.7">
        <span style="color:#f85149">● 0–30 (Well Covered)</span> — Many papers, patents, or products already exist. Hard to differentiate.<br>
        <span style="color:#d29922">● 31–60 (Partially Novel)</span> — Some work exists but gaps remain. Good opportunity with the right angle.<br>
        <span style="color:#3fb950">● 61–100 (Highly Novel)</span> — Very few or no existing works found. Strong opportunity for new research or IP.<br><br>
        Computed by our AI novelty agent which cross-references all retrieved sources, measures overlap with your query, and weighs recency and relevance.
        </p>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 5 — ABOUT
# ══════════════════════════════════════════
with tabs[4]:
    st.markdown("<p class='main-title' style='font-size:32px'>ℹ️ About ResearchNu</p>", unsafe_allow_html=True)
    st.divider()

    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown("""<div class="about-card">
            <h3>What is ResearchNu?</h3>
            <p>ResearchNu is a free agentic AI platform that searches 20+ academic, patent, grant, clinical, and market sources simultaneously — synthesizing findings, scoring novelty, and surfacing gaps that matter to researchers, founders, and R&D teams globally.<br><br>
            Unlike search engines, ResearchNu reads, reasons, and synthesizes using a <b style="color:#58a6ff">7-agent AI pipeline</b>: planner, retriever, grader, rewriter, synthesis+novelty scorer, hallucination checker, and summarizer.</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="about-card">
            <h3>Who is it for?</h3>
            <p>
            <b style="color:#58a6ff">Researchers</b> — Find related work, identify gaps, check novelty before writing a paper or applying for a grant.<br><br>
            <b style="color:#58a6ff">Startup Founders</b> — Scan patents, funded startups, and market signals to validate ideas and find white space.<br><br>
            <b style="color:#58a6ff">Grant Seekers</b> — Search active funding across NIH, NSF, EU Horizon, and UKRI simultaneously.<br><br>
            <b style="color:#58a6ff">R&D Teams</b> — Stay on top of emerging research and competitive landscape across any domain.
            </p>
        </div>""", unsafe_allow_html=True)

    with col_right:
        st.markdown("""<div class="about-card">
            <h3>Roadmap</h3>
            <p>
            ✅ 20+ free sources (academic, patent, grant, clinical, market)<br>
            ✅ Hybrid BM25 + semantic search with RRF fusion<br>
            ✅ 7-agent LangGraph pipeline<br>
            ✅ Novelty scoring and gap detection<br>
            🔜 React frontend with advanced filtering<br>
            🔜 Weekly research alerts via email<br>
            🔜 Upload your paper — get gap analysis<br>
            🔜 Fine-tuned domain LLM (PubMedQA)<br>
            🔜 Global patent offices (JPO, CIPO, KIPO)
            </p>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="about-card" style="text-align:center">
            <h3>Stats</h3>
        </div>""", unsafe_allow_html=True)
        stat_cols = st.columns(2)
        for i, (num, label) in enumerate([("20+","Data Sources"),("7","AI Agents"),("$0","Cost to Use"),("Apache 2.0","License")]):
            with stat_cols[i % 2]:
                st.markdown(f"""<div class="stat-box" style="margin:4px 0">
                    <div class="stat-num">{num}</div>
                    <div class="stat-label">{label}</div>
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 6 — BUILDER
# ══════════════════════════════════════════
with tabs[5]:
    st.markdown("<p class='main-title' style='font-size:32px'>👤 Builder</p>", unsafe_allow_html=True)
    st.divider()

    photo_path = ASSETS / "photo.jpeg"

    # ── Left-aligned profile block ──
    col_photo, col_gap = st.columns([1, 3])
    with col_photo:
        if photo_path.exists():
            st.image(str(photo_path), width=200)
        st.markdown("""
        <div style="text-align:left;margin-top:14px">
            <p style="font-size:22px;font-weight:800;color:#e6edf3;margin:0 0 5px 0">Vishnu Sekar</p>
            <p style="font-size:16px;color:#8b949e;margin:0 0 3px 0">Age 25 · Philadelphia, PA</p>
            <p style="font-size:15px;color:#8b949e;margin:0 0 12px 0">MS Machine Learning Engineering · Drexel University</p>
            <a href="https://github.com/VishGuy2001/researchnu" target="_blank"
               style="color:#58a6ff;font-size:15px;font-weight:600;text-decoration:none">GitHub</a>
            &nbsp;&nbsp;·&nbsp;&nbsp;
            <a href="https://www.linkedin.com/in/vishnusekar/" target="_blank"
               style="color:#58a6ff;font-size:15px;font-weight:600;text-decoration:none">LinkedIn</a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)

    # ── Bio cards full width below ──
    st.markdown("""<div class="about-card">
        <h3 style="font-size:17px">Background</h3>
        <p style="font-size:15px;line-height:1.7">MS Machine Learning Engineering, Drexel University — graduating June 2026. Graduate ML Researcher with experience in applied machine learning. Interests include AI agents, LLM-powered systems, agentic pipelines with LangGraph, local inference with Ollama, RAG architectures, and building open-source tools that make AI accessible.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="about-card">
        <h3 style="font-size:17px">How ResearchNu Started</h3>
        <p style="font-size:15px;line-height:1.7">While working as a graduate ML researcher, I kept seeing the same problem: researchers spending hours manually searching across PubMed, arXiv, patent databases, grant portals, and startup trackers just to answer one question. Tools for this existed, but they were either paywalled or built exclusively for well-funded institutions — not for the average researcher or early-stage founder.<br><br>
        I wanted to build something different: a free, open-source tool that anyone could use and contribute to. ResearchNu is built entirely on public APIs and open databases — no paywalls, no cost to the user, and openly extensible by the community.<br><br>
        And the name? A small twist on my own — <b style="color:#58a6ff">Vishnu → ResearchNu</b>. A bit on the nose, but it stuck. 😄</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="about-card">
        <h3 style="font-size:17px">Outside of Work</h3>
        <p style="font-size:15px;line-height:1.7">Cooking, baking, basketball, squash, and running.</p>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# TAB 7 — CONTACT
# ══════════════════════════════════════════
with tabs[6]:
    st.markdown("<p class='main-title' style='font-size:32px'>💬 Contact & Feedback</p>", unsafe_allow_html=True)
    st.divider()

    col_form, col_info = st.columns([2, 1])

    with col_form:
        contact_type     = st.selectbox("Type", ["General Message", "Feature Request", "New Source Suggestion", "Bug Report"])
        contact_name     = st.text_input("Name *", key="c_name")
        contact_email    = st.text_input("Your Email *", key="c_email")
        contact_linkedin = st.text_input("LinkedIn (optional)", placeholder="https://linkedin.com/in/yourname", key="c_linkedin")
        contact_subject  = st.text_input("Subject *", key="c_subject")
        contact_message  = st.text_area("Message *", placeholder="Your message here...", height=180, key="contact_msg")

        chars = len(contact_message)
        if chars > 0:
            color = "#f85149" if chars > 1000 else "#8b949e"
            st.markdown(f"<p style='color:{color};font-size:12px;text-align:right'>{chars}/1000</p>", unsafe_allow_html=True)

        if st.button("📤 Send", type="primary"):
            if not all([contact_name.strip(), contact_email.strip(), contact_subject.strip(), contact_message.strip()]):
                st.warning("Please fill in all required fields.")
            elif chars > 1000:
                st.warning("Please shorten your message to under 1000 characters.")
            else:
                body = f"""New {contact_type} via ResearchNu:

Name:     {contact_name}
Email:    {contact_email}
LinkedIn: {contact_linkedin if contact_linkedin.strip() else 'Not provided'}
Type:     {contact_type}
Subject:  {contact_subject}

Message:
{contact_message}
"""
                ok = send_email(f"{contact_type}: {contact_subject}", body)
                if ok:
                    st.success("✅ Sent! We'll get back to you soon.")
                else:
                    st.error("Could not send right now. Try again later or reach out via GitHub.")

    with col_info:
        st.markdown("""<div class="about-card">
            <h3>📬 We read everything</h3>
            <p>Whether it's a bug, a feature idea, or just a note — fill out the form and it goes straight to us.</p>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="about-card">
            <h3>🤝 Contribute</h3>
            <p>ResearchNu is open source (Apache 2.0). Fork us and open a PR.<br><br>
            <a href="https://github.com/VishGuy2001/researchnu" target="_blank" style="color:#58a6ff">github.com/VishGuy2001/researchnu</a></p>
        </div>""", unsafe_allow_html=True)