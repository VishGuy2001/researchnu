import streamlit as st
import httpx

st.set_page_config(
    page_title="ResearchNu",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp { background: #0f1117; }
.stButton>button {
    background: #0D7377; color: white; font-weight: 600;
    border-radius: 8px; border: none; padding: 10px 24px;
    transition: all 0.2s;
}
.stButton>button:hover { background: #0A5C60; transform: translateY(-1px); }
.result-box {
    background: #1a2030; border-radius: 12px; padding: 24px;
    border-left: 4px solid #0D7377; margin: 12px 0;
}
.cite-box {
    background: #1a2030; border-radius: 8px; padding: 12px;
    border-left: 3px solid #0D7377; margin: 6px 0; font-size: 14px;
}
.novelty-high { color: #27AE60; font-size: 48px; font-weight: 700; }
.novelty-mid  { color: #F39C12; font-size: 48px; font-weight: 700; }
.novelty-low  { color: #E74C3C; font-size: 48px; font-weight: 700; }
.source-tag {
    display: inline-block; background: rgba(13,115,119,0.2);
    color: #0D7377; padding: 3px 10px; border-radius: 12px;
    font-size: 12px; margin: 2px; border: 1px solid rgba(13,115,119,0.3);
}
</style>
""", unsafe_allow_html=True)

API = "http://localhost:8000"

with st.sidebar:
    st.markdown("## Settings")
    user_type = st.selectbox(
        "I am a...",
        ["researcher", "founder", "grant", "all"],
        format_func=lambda x: {
            "researcher": "Researcher",
            "founder": "Startup Founder",
            "grant": "Grant Seeker",
            "all": "All Sources"
        }[x]
    )
    privacy_mode = st.toggle("Privacy Mode", value=False,
        help="Query processed locally via Ollama -- never sent to cloud LLMs")

    if privacy_mode:
        st.info("Your query stays on our servers only.")

    st.divider()
    st.markdown("**Active Sources:**")
    source_map = {
        "researcher": ["PubMed", "arXiv", "OpenAlex", "Semantic Scholar", "Europe PMC", "CORE", "CrossRef", "NIH", "NSF", "USPTO", "ClinicalTrials"],
        "founder":    ["arXiv", "OpenAlex", "USPTO", "WIPO", "EPO", "Lens.org", "Y Combinator", "Product Hunt"],
        "grant":      ["PubMed", "OpenAlex", "NIH", "NSF", "EU Horizon", "UKRI", "ClinicalTrials", "WHO ICTRP"],
        "all":        ["All 20 Sources"]
    }
    for s in source_map.get(user_type, []):
        st.markdown(f"✅ {s}")

    st.divider()
    debug = st.checkbox("Show raw JSON")

st.markdown("# ResearchNu")
st.markdown("*Free agentic AI -- papers, patents, grants and market insights globally*")
st.divider()

query = st.text_area(
    "What do you want to explore?",
    placeholder="e.g. Using ML to predict orthopedic implant failure in total knee arthroplasty",
    height=100,
    key="query_input"
)

# enter to submit
if query and query.endswith("\n"):
    query = query.strip()
    run = True

col1, col2 = st.columns([1, 5])
with col1:
    run = st.button("Analyze", type="primary", use_container_width=True)
with col2:
    clear = st.button("Clear", use_container_width=True)

if clear:
    st.rerun()

if run and query.strip():
    with st.spinner("Running agents -- fetching from all sources..."):
        try:
            resp = httpx.post(
                f"{API}/query",
                json={
                    "query": query,
                    "user_type": user_type,
                    "privacy_mode": privacy_mode
                },
                timeout=120
            )
            r = resp.json()

            if debug:
                st.json(r)

            st.divider()

            col1, col2 = st.columns([1, 3])
            with col1:
                score = r.get("novelty_score", 0)
                cls = "novelty-high" if score > 60 else "novelty-mid" if score > 35 else "novelty-low"
                st.markdown(f'<div style="text-align:center"><p style="color:#888;margin:0">Novelty Score</p><div class="{cls}">{score}</div><p style="color:#888;margin:0">/ 100</p></div>', unsafe_allow_html=True)
            with col2:
                st.markdown("**Novelty Analysis**")
                st.write(r.get("novelty_report", "")[:500])

            st.divider()
            st.markdown("### Plain English Summary")
            st.success(r.get("summary", ""))

            with st.expander("Detailed Technical Analysis"):
                st.markdown(r.get("detailed_answer", ""))

            citations = r.get("citations", [])
            st.markdown(f"### Citations ({len(citations)} sources)")
            for c in citations:
                st.markdown(f'''<div class="cite-box">
                    <a href="{c["url"]}" target="_blank" style="color:#0D7377"><b>{c["title"]}</b></a><br>
                    <small>{c["source"]} · {c["year"]}</small>
                </div>''', unsafe_allow_html=True)

            st.markdown("**Sources queried:** " + " ".join([
                f'<span class="source-tag">{s}</span>'
                for s in r.get("sources_used", [])
            ]), unsafe_allow_html=True)

        except httpx.ConnectError:
            st.error("Cannot connect to API. Make sure uvicorn is running on port 8000.")
        except Exception as e:
            st.error(f"Error: {e}")

elif run:
    st.warning("Please enter a research question.")