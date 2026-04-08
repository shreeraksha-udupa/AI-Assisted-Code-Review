"""
Auto-DevOps: Self-Healing Code Reviewer — Streamlit UI
Run with: streamlit run app.py
"""

import streamlit as st
import json
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Auto-DevOps · Code Reviewer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1117 0%, #1a1d2e 100%);
    border-right: 1px solid #2d2d3d;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stSelectbox select {
    background: #1e2235 !important;
    border: 1px solid #3d3d5c !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

/* ── Brand header ── */
.brand-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 0 1.5rem 0;
    border-bottom: 1px solid #2d2d3d;
    margin-bottom: 1.5rem;
}
.brand-icon {
    font-size: 2rem;
    line-height: 1;
}
.brand-text h1 {
    font-size: 1.1rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0;
    letter-spacing: -0.02em;
}
.brand-text p {
    font-size: 0.72rem;
    color: #64748b;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Step badges ── */
.step-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px 4px 8px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 3px 0;
}
.step-pending  { background: #1e293b; color: #64748b; border: 1px solid #334155; }
.step-running  { background: #1e3a5f; color: #60a5fa; border: 1px solid #3b82f6; }
.step-done     { background: #14532d; color: #4ade80; border: 1px solid #22c55e; }
.step-error    { background: #450a0a; color: #f87171; border: 1px solid #ef4444; }

/* ── Issue cards ── */
.issue-card {
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
    border-left: 4px solid;
    background: #0f1117;
}
.sev-critical { border-color: #ef4444; background: #1a0a0a; }
.sev-high     { border-color: #f97316; background: #1a100a; }
.sev-medium   { border-color: #eab308; background: #1a180a; }
.sev-low      { border-color: #3b82f6; background: #0a0f1a; }

.issue-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0.5rem;
}
.issue-type-badge {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 2px 8px;
    border-radius: 4px;
}
.type-security    { background: #7f1d1d; color: #fca5a5; }
.type-bug         { background: #713f12; color: #fcd34d; }
.type-performance { background: #1e3a5f; color: #93c5fd; }
.type-style       { background: #1e293b; color: #94a3b8; }

.sev-pill {
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 10px;
    text-transform: uppercase;
}
.pill-critical { background: #ef4444; color: #fff; }
.pill-high     { background: #f97316; color: #fff; }
.pill-medium   { background: #eab308; color: #000; }
.pill-low      { background: #3b82f6; color: #fff; }

.issue-explanation { font-size: 0.88rem; color: #cbd5e1; margin: 0.4rem 0; }
.issue-why { font-size: 0.82rem; color: #94a3b8; font-style: italic; }
.issue-file { font-size: 0.75rem; color: #475569; font-family: 'JetBrains Mono', monospace; }

/* ── Code blocks ── */
.code-fix {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #a5f3fc;
    white-space: pre-wrap;
    word-break: break-all;
    margin-top: 0.6rem;
}

/* ── Decision banner ── */
.decision-banner {
    border-radius: 14px;
    padding: 1.5rem 2rem;
    margin: 1.5rem 0;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}
.decision-accepted    { background: #052e16; border: 1px solid #16a34a; }
.decision-warnings    { background: #1c1917; border: 1px solid #d97706; }
.decision-review_only { background: #1e3a5f; border: 1px solid #2563eb; }
.decision-rejected    { background: #450a0a; border: 1px solid #dc2626; }

.decision-icon  { font-size: 2.2rem; }
.decision-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem; }
.decision-body  { font-size: 0.88rem; color: #94a3b8; }

/* ── RAG context pills ── */
.rag-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    color: #94a3b8;
    margin: 3px;
}
.rag-score { color: #34d399; font-weight: 600; }

/* ── Metric cards ── */
.metric-row {
    display: flex;
    gap: 12px;
    margin: 1rem 0;
}
.metric-card {
    flex: 1;
    background: #0f1117;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.metric-value { font-size: 1.8rem; font-weight: 700; }
.metric-label { font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px; }

/* ── Progress log ── */
.log-line {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    padding: 3px 0;
    color: #94a3b8;
    border-bottom: 1px solid #1e293b;
}
.log-line.ok   { color: #4ade80; }
.log-line.warn { color: #fbbf24; }
.log-line.err  { color: #f87171; }
.log-line.info { color: #60a5fa; }

/* ── Diff viewer ── */
.diff-line-add { background: #1a2e1a; color: #4ade80; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; padding: 1px 8px; display: block; }
.diff-line-rem { background: #2e1a1a; color: #f87171; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; padding: 1px 8px; display: block; }
.diff-line-ctx { color: #475569; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; padding: 1px 8px; display: block; }
.diff-header   { color: #818cf8; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; padding: 1px 8px; display: block; background: #1e1b4b; }

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #0f1117;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 6px 18px;
    color: #64748b;
    font-weight: 500;
    font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    background: #1e293b !important;
    color: #f1f5f9 !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    border: none !important;
    transition: all 0.15s !important;
}
.stButton > button:hover { transform: translateY(-1px); filter: brightness(1.1); }

/* ── File path display ── */
.file-path {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #818cf8;
    background: #1e1b4b22;
    padding: 2px 6px;
    border-radius: 4px;
}

/* ── Section headings ── */
.section-heading {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #475569;
    margin: 1.5rem 0 0.75rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-heading::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1e293b;
}

/* ── Overall risk badge ── */
.risk-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.risk-critical { background: #ef4444; color: #fff; }
.risk-high     { background: #f97316; color: #fff; }
.risk-medium   { background: #eab308; color: #000; }
.risk-low      { background: #22c55e; color: #000; }
.risk-safe     { background: #10b981; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────────────────
for key, default in {
    "review_result": None,
    "agent_state": None,
    "ingestion_done": False,
    "running": False,
    "log_lines": [],
    "step_states": {i: "pending" for i in range(1, 9)},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Helpers ────────────────────────────────────────────────────────────────────
STEP_LABELS = {
    1: "Analyze diff",
    2: "RAG retrieval",
    3: "Cross-file reasoning",
    4: "Generate review (LLM)",
    5: "Create Git branch",
    6: "Apply fix",
    7: "Run tests",
    8: "Final decision",
}

SEVERITY_ICONS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
DECISION_META = {
    "accepted":               ("✅", "decision-accepted",    "No Issues Found", "The code is clean — no bugs, security issues, or performance problems detected."),
    "accepted_with_warnings": ("⚠️", "decision-warnings",   "Warnings Only",   "Low/medium issues detected. No auto-fix applied. Review recommended."),
    "fix_accepted":           ("✅", "decision-accepted",    "Fix Accepted",    "Critical issue found, fix applied, tests passed. Branch created."),
    "review_only":            ("📋", "decision-review_only", "Review Only",     "Issues found and reported. Manual fix recommended."),
    "fix_rejected":           ("❌", "decision-rejected",    "Fix Rejected",    "Fix was applied but tests failed. Branch preserved for manual inspection."),
    "rejected":               ("❌", "decision-rejected",    "Rejected",        "Review could not complete."),
}

SAMPLE_DIFF = """--- a/app/auth.py
+++ b/app/auth.py
@@ -12,7 +12,7 @@ import db

 def login(username, password):
-    query = "SELECT * FROM users WHERE username=? AND password=?"
-    result = db.execute(query, (username, password))
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    result = db.execute(query)
     if result:
         return generate_token(result[0])
     return None
--- a/app/api.py
+++ b/app/api.py
@@ -8,6 +8,9 @@ from flask import request, jsonify

 @app.route("/user/<int:user_id>")
 def get_user(user_id):
+    # TODO: remove debug logging before prod
+    print(f"Fetching user {user_id}, token={request.headers.get('Authorization')}")
     user = User.query.get(user_id)
     if not user:
         return jsonify({"error": "not found"}), 404
"""

CLEAN_SAMPLE_DIFF = """--- a/app/utils.py
+++ b/app/utils.py
@@ -5,10 +5,18 @@ from datetime import datetime

 def format_date(dt: datetime) -> str:
-    return dt.strftime("%Y/%m/%d")
+    \"\"\"Return ISO-8601 formatted date string (YYYY-MM-DD).\"\"\"
+    return dt.strftime("%Y-%m-%d")

+def clamp(value: float, min_val: float, max_val: float) -> float:
+    \"\"\"Clamp a numeric value to [min_val, max_val].\"\"\"
+    return max(min_val, min(max_val, value))
+
--- a/app/models.py
+++ b/app/models.py
@@ -22,6 +22,10 @@ class Product(db.Model):

     def to_dict(self) -> dict:
-        return {"id": self.id, "name": self.name}
+        return {
+            "id":    self.id,
+            "name":  self.name,
+            "price": round(float(self.price), 2),
+            "stock": self.stock,
+        }
"""

def add_log(msg: str, kind: str = ""):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_lines.append((ts, msg, kind))

def render_diff(diff_text: str):
    html = []
    for line in diff_text.splitlines():
        esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if line.startswith("@@"):
            html.append(f'<span class="diff-header">{esc}</span>')
        elif line.startswith("+") and not line.startswith("+++"):
            html.append(f'<span class="diff-line-add">{esc}</span>')
        elif line.startswith("-") and not line.startswith("---"):
            html.append(f'<span class="diff-line-rem">{esc}</span>')
        else:
            html.append(f'<span class="diff-line-ctx">{esc}</span>')
    return '<div style="background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:1rem;overflow-x:auto;">' + "".join(html) + "</div>"

def severity_counts(issues):
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for i in issues:
        s = i.get("severity", "low")
        if s in counts:
            counts[s] += 1
    return counts

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="brand-header">
        <div class="brand-icon">🛡️</div>
        <div class="brand-text">
            <h1>Auto-DevOps</h1>
            <p>Self-Healing Code Reviewer</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-heading">⚙️ Configuration</div>', unsafe_allow_html=True)

    groq_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Get your free key at console.groq.com"
    )

    model_choice = st.selectbox(
        "Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        help="llama-3.3-70b gives best review quality"
    )

    st.markdown('<div class="section-heading">📦 Repository</div>', unsafe_allow_html=True)

    repo_url = st.text_input(
        "GitHub Repo URL",
        value="https://github.com/pallets/flask",
        placeholder="https://github.com/user/repo"
    )

    repo_dest = st.text_input("Local clone path", value="./repo")

    col1, col2 = st.columns(2)
    with col1:
        do_ingest = st.button("⬇️ Ingest Repo", use_container_width=True, type="primary")
    with col2:
        if st.button("🗑️ Clear DB", use_container_width=True):
            import shutil
            if os.path.exists("./chroma_db"):
                shutil.rmtree("./chroma_db")
            st.session_state.ingestion_done = False
            st.success("ChromaDB cleared")

    if st.session_state.ingestion_done:
        st.markdown('✅ <span style="color:#4ade80;font-size:0.82rem">Vector DB ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('⚪ <span style="color:#64748b;font-size:0.82rem">Not ingested yet</span>', unsafe_allow_html=True)

    st.markdown('<div class="section-heading">🔧 Agent Settings</div>', unsafe_allow_html=True)

    top_k = st.slider("RAG top-K chunks", 3, 10, 5, help="How many similar code chunks to retrieve")
    auto_fix = st.checkbox("Enable auto-fix", value=True, help="Attempt to apply fixes for critical/high issues")
    run_tests_flag = st.checkbox("Run tests after fix", value=True)

    st.markdown("---")
    st.markdown('<p style="font-size:0.72rem;color:#334155;text-align:center">Powered by Groq + ChromaDB + sentence-transformers</p>', unsafe_allow_html=True)

# ── Ingestion handler ─────────────────────────────────────────────────────────
if do_ingest:
    if not groq_key:
        st.sidebar.error("Enter your Groq API key first")
    else:
        os.environ["GROQ_API_KEY"] = groq_key

        with st.sidebar:
            ingest_bar = st.progress(0, text="Starting ingestion...")

        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from ingestion.repo_cloner import clone_or_load
            from ingestion.chunker import chunk_all_files
            from ingestion.embedder import embed_and_store

            ingest_bar.progress(10, text="Cloning repository...")
            files = clone_or_load(repo_url, repo_dest)

            ingest_bar.progress(40, text=f"Chunking {len(files)} files...")
            chunks = chunk_all_files(files)

            ingest_bar.progress(70, text=f"Embedding {len(chunks)} chunks...")
            embed_and_store(chunks)

            ingest_bar.progress(100, text="Done!")
            st.session_state.ingestion_done = True
            time.sleep(0.5)
            ingest_bar.empty()
            st.sidebar.success(f"✅ Ingested {len(files)} files → {len(chunks)} chunks")

        except Exception as e:
            st.sidebar.error(f"Ingestion failed: {e}")

# ── Main area ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:1.5rem">
    <h1 style="font-size:1.6rem;font-weight:700;color:#f1f5f9;margin:0">
        🛡️ Code Review Agent
    </h1>
    <p style="color:#64748b;font-size:0.88rem;margin:4px 0 0">
        Paste a git diff below — the agent will analyze it, retrieve repo context via RAG, and propose fixes.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Input tabs ────────────────────────────────────────────────────────────────
tab_input, tab_pipeline, tab_results, tab_report = st.tabs([
    "📝 Diff Input", "⚙️ Agent Pipeline", "📊 Results", "📄 JSON Report"
])

with tab_input:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="section-heading">📋 Paste Diff</div>', unsafe_allow_html=True)

        sample_choice = st.radio(
            "Load a sample diff",
            ["✏️ Paste my own diff", "🐛 Buggy diff (SQL injection demo)", "✅ Clean diff (no issues demo)"],
            index=0,
            horizontal=False,
        )

        if sample_choice == "🐛 Buggy diff (SQL injection demo)":
            diff_text = SAMPLE_DIFF
            st.markdown(render_diff(SAMPLE_DIFF), unsafe_allow_html=True)
        elif sample_choice == "✅ Clean diff (no issues demo)":
            diff_text = CLEAN_SAMPLE_DIFF
            st.markdown(render_diff(CLEAN_SAMPLE_DIFF), unsafe_allow_html=True)
        else:
            diff_text = st.text_area(
                "Unified diff",
                height=380,
                placeholder="Paste your git diff here...\n\n--- a/file.py\n+++ b/file.py\n@@...",
                label_visibility="collapsed"
            )

        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

        btn_col1, btn_col2 = st.columns([2, 1])
        with btn_col1:
            run_review = st.button(
                "🚀 Run Agent Review",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.running
            )
        with btn_col2:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.review_result = None
                st.session_state.agent_state = None
                st.session_state.log_lines = []
                st.session_state.step_states = {i: "pending" for i in range(1, 9)}
                st.rerun()

    with col_right:
        st.markdown('<div class="section-heading">📖 How It Works</div>', unsafe_allow_html=True)

        steps_info = [
            ("1", "🔍", "Analyze diff",          "Parses the unified diff into structured hunks"),
            ("2", "🗄️", "RAG retrieval",         "Queries ChromaDB for semantically similar code"),
            ("3", "🧠", "Cross-file reasoning",   "Maps impact across files using retrieved context"),
            ("4", "🤖", "LLM review",             "Groq LLM generates structured JSON review"),
            ("5", "🌿", "Create branch",          "Opens a new git branch for the fix"),
            ("6", "🔧", "Apply fix",              "Writes the suggested fix to the target file"),
            ("7", "🧪", "Run tests",              "Runs pytest / npm test (or simulates)"),
            ("8", "✅", "Final decision",         "Accepts or rejects the fix based on results"),
        ]

        for num, icon, title, desc in steps_info:
            st.markdown(f"""
            <div style="display:flex;gap:10px;margin:8px 0;align-items:flex-start">
                <div style="width:24px;height:24px;border-radius:50%;background:#1e293b;
                    display:flex;align-items:center;justify-content:center;
                    font-size:0.7rem;font-weight:700;color:#60a5fa;flex-shrink:0;margin-top:1px">{num}</div>
                <div>
                    <div style="font-size:0.85rem;font-weight:600;color:#e2e8f0">{icon} {title}</div>
                    <div style="font-size:0.78rem;color:#64748b">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── Run the agent ─────────────────────────────────────────────────────────────
if run_review:
    if not groq_key:
        st.error("⚠️ Enter your Groq API key in the sidebar first.")
    elif not diff_text or not diff_text.strip():
        st.error("⚠️ Please paste a diff or enable the sample diff.")
    elif not st.session_state.ingestion_done:
        st.warning("⚠️ Repo not ingested yet. Click **⬇️ Ingest Repo** in the sidebar first.")
    else:
        os.environ["GROQ_API_KEY"] = groq_key
        st.session_state.running = True
        st.session_state.log_lines = []
        st.session_state.step_states = {i: "pending" for i in range(1, 9)}
        st.session_state.review_result = None
        st.session_state.agent_state = None

        # Import project modules
        sys.path.insert(0, os.path.dirname(__file__))
        from review.diff_parser import parse_diff, summarize_diff
        from review.reviewer import review_diff
        from agent.git_ops import create_branch, apply_fix, get_file_content
        from tests.test_runner import run_tests
        from retrieval.retriever import retrieve_context, get_collection
        import config.settings as cfg

        # Patch settings at runtime
        cfg.GROQ_API_KEY = groq_key
        cfg.MODEL = model_choice
        cfg.RETRIEVAL_TOP_K = top_k

        state = {
            "diff": diff_text, "hunks": [], "context_chunks": [],
            "review": {}, "branch_created": False, "fix_applied": False,
            "tests_passed": False, "test_output": "", "decision": "rejected",
            "explanation": ""
        }

        # Switch to pipeline tab (rerun will handle it)
        with tab_pipeline:
            progress_placeholder = st.empty()
            step_placeholder     = st.empty()
            log_placeholder      = st.empty()

        def render_steps():
            html = '<div style="margin:1rem 0">'
            icons = {"pending": "⏸", "running": "⟳", "done": "✓", "error": "✗"}
            for i in range(1, 9):
                s = st.session_state.step_states[i]
                html += f'<div class="step-badge step-{s}">{icons[s]} Step {i}: {STEP_LABELS[i]}</div><br>'
            html += "</div>"
            return html

        def render_logs():
            if not st.session_state.log_lines:
                return ""
            html = '<div style="background:#0d1117;border:1px solid #1e293b;border-radius:10px;padding:1rem;max-height:300px;overflow-y:auto">'
            for ts, msg, kind in st.session_state.log_lines[-40:]:
                html += f'<div class="log-line {kind}"><span style="color:#334155">[{ts}]</span> {msg}</div>'
            html += "</div>"
            return html

        def set_step(n, status):
            st.session_state.step_states[n] = status

        def run_pipeline():
            try:
                # STEP 1
                set_step(1, "running")
                add_log("Parsing diff...", "info")
                step_placeholder.markdown(render_steps(), unsafe_allow_html=True)
                log_placeholder.markdown(render_logs(), unsafe_allow_html=True)

                state["hunks"] = parse_diff(diff_text)
                summary = summarize_diff(state["hunks"])
                add_log(f"Found {len(state['hunks'])} hunk(s): {summary}", "ok")
                set_step(1, "done")

                if not state["hunks"]:
                    add_log("No hunks found — nothing to review", "warn")
                    state["decision"] = "rejected"
                    state["explanation"] = "Empty diff"
                    return

                # STEP 2
                set_step(2, "running")
                add_log("Querying ChromaDB for related code...", "info")
                step_placeholder.markdown(render_steps(), unsafe_allow_html=True)
                log_placeholder.markdown(render_logs(), unsafe_allow_html=True)

                rag_query = "\n".join([l for h in state["hunks"] for l in h["added_lines"]])[:600]
                try:
                    collection = get_collection()
                    state["context_chunks"] = retrieve_context(rag_query, collection=collection, top_k=top_k)
                    add_log(f"Retrieved {len(state['context_chunks'])} chunks from {len({c['path'] for c in state['context_chunks']})} files", "ok")
                    for c in state["context_chunks"]:
                        add_log(f"  ↳ {c['path']} (lines {c['start_line']}–{c['end_line']}) relevance={c['relevance_score']}", "")
                except Exception as e:
                    add_log(f"RAG retrieval failed: {e}", "warn")
                set_step(2, "done")

                # STEP 3
                set_step(3, "running")
                step_placeholder.markdown(render_steps(), unsafe_allow_html=True)
                log_placeholder.markdown(render_logs(), unsafe_allow_html=True)
                files_ctx = {c["path"] for c in state["context_chunks"]}
                add_log(f"Cross-file context spans: {', '.join(files_ctx) or 'none'}", "info")
                set_step(3, "done")

                # STEP 4
                set_step(4, "running")
                add_log(f"Sending to Groq ({model_choice})...", "info")
                step_placeholder.markdown(render_steps(), unsafe_allow_html=True)
                log_placeholder.markdown(render_logs(), unsafe_allow_html=True)

                state["review"] = review_diff(diff_text, collection=collection if state["context_chunks"] else None)
                issues = state["review"].get("issues", [])
                risk   = state["review"].get("overall_risk", "unknown")
                add_log(f"Review complete — {len(issues)} issue(s) found, overall risk: {risk}", "ok" if risk in ("safe","low") else "warn")
                set_step(4, "done")

                if not issues:
                    state["decision"] = "accepted"
                    state["explanation"] = state["review"].get("summary", "No issues detected.")
                    add_log("No issues — accepting as-is", "ok")
                    return

                critical_issues = [i for i in issues if i.get("severity") in ("critical", "high")]
                if not critical_issues or not auto_fix:
                    state["decision"] = "accepted_with_warnings"
                    state["explanation"] = state["review"].get("summary", "Minor issues only.")
                    add_log("Only low/medium issues — no auto-fix applied", "warn")
                    for step in [5, 6, 7, 8]:
                        set_step(step, "done")
                    return

                first_issue  = critical_issues[0]
                target_file  = first_issue.get("file", "")

                # STEP 5
                set_step(5, "running")
                add_log(f"Creating branch autofix/code-review-agent...", "info")
                step_placeholder.markdown(render_steps(), unsafe_allow_html=True)
                log_placeholder.markdown(render_logs(), unsafe_allow_html=True)
                state["branch_created"] = create_branch(repo_dest, "autofix/code-review-agent")
                if state["branch_created"]:
                    add_log("Branch created", "ok")
                else:
                    add_log("Branch creation failed (may already exist)", "warn")
                set_step(5, "done")

                # STEP 6
                set_step(6, "running")
                step_placeholder.markdown(render_steps(), unsafe_allow_html=True)
                log_placeholder.markdown(render_logs(), unsafe_allow_html=True)
                if target_file:
                    try:
                        original = get_file_content(repo_dest, target_file)
                        fixed    = first_issue.get("suggested_fix", "")
                        if fixed:
                            state["fix_applied"] = apply_fix(repo_dest, target_file, original, fixed)
                            add_log(f"Fix applied to {target_file}", "ok")
                        else:
                            add_log("No suggested_fix in LLM response", "warn")
                    except Exception as e:
                        add_log(f"Fix failed: {e}", "err")
                else:
                    add_log("No target file — skipping fix", "warn")
                set_step(6, "done")

                # STEP 7
                set_step(7, "running")
                add_log("Running tests...", "info")
                step_placeholder.markdown(render_steps(), unsafe_allow_html=True)
                log_placeholder.markdown(render_logs(), unsafe_allow_html=True)
                if run_tests_flag:
                    test_result = run_tests(repo_dest)
                    state["tests_passed"] = test_result["passed"]
                    state["test_output"]  = test_result["output"]
                    if test_result.get("simulated"):
                        add_log("Tests simulated (no test runner found)", "warn")
                    elif test_result["passed"]:
                        add_log("Tests passed ✓", "ok")
                    else:
                        add_log("Tests failed ✗", "err")
                else:
                    state["tests_passed"] = True
                    state["test_output"] = "Test run disabled by user."
                    add_log("Tests skipped (disabled in settings)", "warn")
                set_step(7, "done")

                # STEP 8
                set_step(8, "running")
                step_placeholder.markdown(render_steps(), unsafe_allow_html=True)
                log_placeholder.markdown(render_logs(), unsafe_allow_html=True)

                if state["tests_passed"] and state["fix_applied"]:
                    state["decision"] = "fix_accepted"
                    state["explanation"] = f"Fix applied to '{target_file}'. Tests passed."
                    add_log("Decision: FIX ACCEPTED ✅", "ok")
                elif state["tests_passed"] and not state["fix_applied"]:
                    state["decision"] = "review_only"
                    state["explanation"] = "Issues found. Manual fix recommended."
                    add_log("Decision: REVIEW ONLY 📋", "warn")
                else:
                    state["decision"] = "fix_rejected"
                    state["explanation"] = "Fix applied but tests failed. Manual review needed."
                    add_log("Decision: FIX REJECTED ❌", "err")
                set_step(8, "done")

            except Exception as e:
                add_log(f"Pipeline error: {e}", "err")
                state["decision"] = "rejected"
                state["explanation"] = str(e)

        # Run synchronously (Streamlit doesn't support async well)
        run_pipeline()
        st.session_state.agent_state  = state
        st.session_state.review_result = state.get("review", {})
        st.session_state.running = False
        st.rerun()

# ── Pipeline tab (live view) ─────────────────────────────────────────────────
with tab_pipeline:
    if not st.session_state.agent_state and not st.session_state.running:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#475569">
            <div style="font-size:3rem">⚙️</div>
            <div style="font-size:1rem;font-weight:600;margin-top:1rem">Pipeline not started</div>
            <div style="font-size:0.85rem;margin-top:0.5rem">Go to the Diff Input tab and click Run Agent Review</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_steps, col_logs = st.columns([1, 2], gap="large")

        with col_steps:
            st.markdown('<div class="section-heading">🔄 Agent Steps</div>', unsafe_allow_html=True)
            icons = {"pending": "⏸", "running": "⟳", "done": "✓", "error": "✗"}
            for i in range(1, 9):
                s = st.session_state.step_states.get(i, "pending")
                st.markdown(
                    f'<div class="step-badge step-{s}">{icons[s]} Step {i}: {STEP_LABELS[i]}</div><br>',
                    unsafe_allow_html=True
                )

        with col_logs:
            st.markdown('<div class="section-heading">📟 Activity Log</div>', unsafe_allow_html=True)
            if st.session_state.log_lines:
                html = '<div style="background:#0d1117;border:1px solid #1e293b;border-radius:10px;padding:1rem;max-height:420px;overflow-y:auto">'
                for ts, msg, kind in st.session_state.log_lines:
                    html += f'<div class="log-line {kind}"><span style="color:#334155">[{ts}]</span> {msg}</div>'
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#334155;font-size:0.85rem">No logs yet</p>', unsafe_allow_html=True)

        # RAG context used
        if st.session_state.agent_state and st.session_state.agent_state.get("context_chunks"):
            st.markdown('<div class="section-heading">🗄️ RAG Context Retrieved</div>', unsafe_allow_html=True)
            pills_html = ""
            for c in st.session_state.agent_state["context_chunks"]:
                pills_html += f'<span class="rag-pill">📄 {c["path"]} <span class="rag-score">{c["relevance_score"]}</span></span>'
            st.markdown(f'<div style="margin:0.5rem 0">{pills_html}</div>', unsafe_allow_html=True)

# ── Results tab ───────────────────────────────────────────────────────────────
with tab_results:
    state = st.session_state.agent_state
    review = st.session_state.review_result

    if not state:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#475569">
            <div style="font-size:3rem">📊</div>
            <div style="font-size:1rem;font-weight:600;margin-top:1rem">No results yet</div>
            <div style="font-size:0.85rem;margin-top:0.5rem">Run a review to see results here</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        decision = state.get("decision", "rejected")
        icon, cls, title, default_desc = DECISION_META.get(decision, DECISION_META["rejected"])

        # Decision banner
        st.markdown(f"""
        <div class="decision-banner {cls}">
            <div class="decision-icon">{icon}</div>
            <div>
                <div class="decision-title">{title}</div>
                <div class="decision-body">{state.get("explanation", default_desc)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Metric row
        issues = review.get("issues", []) if review else []
        sc = severity_counts(issues)
        risk = review.get("overall_risk", "—") if review else "—"

        risk_color = {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#22c55e", "safe": "#10b981"}.get(risk, "#64748b")

        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-value" style="color:{risk_color}">{risk.upper() if risk != '—' else '—'}</div>
                <div class="metric-label">Overall Risk</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color:#ef4444">{sc['critical'] + sc['high']}</div>
                <div class="metric-label">Critical / High</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color:#eab308">{sc['medium']}</div>
                <div class="metric-label">Medium</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color:#3b82f6">{sc['low']}</div>
                <div class="metric-label">Low</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color:#{"4ade80" if state.get("tests_passed") else "f87171"}">
                    {"✓" if state.get("tests_passed") else "✗"}
                </div>
                <div class="metric-label">Tests</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Summary
        if review and review.get("summary"):
            st.markdown(f"""
            <div style="background:#0f1117;border:1px solid #1e293b;border-radius:10px;padding:1rem 1.2rem;margin:0.5rem 0">
                <span style="font-size:0.72rem;color:#475569;text-transform:uppercase;letter-spacing:0.1em">Summary</span>
                <p style="color:#e2e8f0;font-size:0.9rem;margin:0.4rem 0 0">{review['summary']}</p>
            </div>
            """, unsafe_allow_html=True)

        # Issues
        if issues:
            st.markdown('<div class="section-heading">🐛 Issues Found</div>', unsafe_allow_html=True)

            for issue in issues:
                sev  = issue.get("severity", "low")
                itype = issue.get("issue_type", "bug")
                icon_s = SEVERITY_ICONS.get(sev, "⚪")

                st.markdown(f"""
                <div class="issue-card sev-{sev}">
                    <div class="issue-header">
                        <span class="issue-type-badge type-{itype}">{itype}</span>
                        <span class="sev-pill pill-{sev}">{icon_s} {sev}</span>
                        <span class="issue-file">📄 {issue.get('file','?')} {('· line ' + str(issue.get('line_hint',''))) if issue.get('line_hint') else ''}</span>
                    </div>
                    <div class="issue-explanation">🔍 {issue.get('explanation','')}</div>
                    <div class="issue-why">⚡ {issue.get('why_this_matters','')}</div>
                </div>
                """, unsafe_allow_html=True)

                if issue.get("suggested_fix"):
                    with st.expander(f"💡 View suggested fix ({itype})"):
                        st.code(issue["suggested_fix"], language="python")
        else:
            st.success("✅ No issues found — code looks clean!")

        # RAG context
        if state.get("context_chunks"):
            st.markdown('<div class="section-heading">🗄️ RAG Context Used</div>', unsafe_allow_html=True)
            for c in state["context_chunks"]:
                with st.expander(f"📄 {c['path']} — relevance: {c['relevance_score']}"):
                    st.code(c["text"], language="python")

        # Test output
        if state.get("test_output"):
            st.markdown('<div class="section-heading">🧪 Test Output</div>', unsafe_allow_html=True)
            st.code(state["test_output"], language="text")

# ── JSON Report tab ───────────────────────────────────────────────────────────
with tab_report:
    state = st.session_state.agent_state

    if not state:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#475569">
            <div style="font-size:3rem">📄</div>
            <div style="font-size:1rem;font-weight:600;margin-top:1rem">No report yet</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "decision": state.get("decision"),
            "explanation": state.get("explanation"),
            "overall_risk": state.get("review", {}).get("overall_risk"),
            "summary": state.get("review", {}).get("summary"),
            "issues": state.get("review", {}).get("issues", []),
            "rag_context_used": [
                {"path": c["path"], "relevance": c["relevance_score"]}
                for c in state.get("context_chunks", [])
            ],
            "fix_applied": state.get("fix_applied"),
            "tests_passed": state.get("tests_passed"),
            "branch_created": state.get("branch_created"),
        }

        report_json = json.dumps(report, indent=2)

        col_a, col_b = st.columns([3, 1])
        with col_b:
            st.download_button(
                "⬇️ Download JSON",
                data=report_json,
                file_name=f"review_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                type="primary"
            )

        st.code(report_json, language="json")
