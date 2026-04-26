"""
Streamlit front-end for the NorthLadder data-quality detector.

Mirrors the look-and-feel of the FastAPI version (static/index.html + style.css)
as closely as Streamlit allows: same dark glassmorphism palette, same emoji-led
labels, same severity buckets, same per-button download surface. Pure-Python so
it deploys to Streamlit Cloud without a separate web server.
"""

import io
import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

from mismatch_detector import run as run_detector


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="NorthLadder — Data-Quality Detection",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Custom CSS — port the glassmorphism palette from static/style.css
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
:root {
    --primary: #00d4ff;
    --primary-dark: #0099cc;
    --success: #51cf66;
    --warning: #ffd43b;
    --danger:  #ff6b6b;
    --dark:    #0a0e27;
    --darker:  #050812;
    --text:    #e0e0e0;
    --text-secondary: #a0a0a0;
    --glass-bg: rgba(15, 23, 42, 0.7);
    --glass-border: rgba(255, 255, 255, 0.1);
}

/* Page background */
.stApp {
    background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%) fixed;
    color: var(--text);
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Navbar-style banner */
.nl-nav {
    display: flex; justify-content: space-between; align-items: center;
    padding: 18px 28px; margin-bottom: 24px;
    background: var(--glass-bg);
    border-bottom: 1px solid var(--glass-border);
    backdrop-filter: blur(10px);
    border-radius: 12px;
}
.nl-logo {
    font-size: 1.6rem; font-weight: 700;
    background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.nl-subtitle { color: var(--text-secondary); font-size: 0.95rem; }

/* Hero / section card */
.nl-card {
    background: var(--glass-bg);
    border: 1px dashed var(--glass-border);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 22px;
    backdrop-filter: blur(10px);
}

/* Headings */
h1.nl-h1 {
    font-size: 2.4rem; font-weight: 800; margin-bottom: 6px;
    background: linear-gradient(135deg, #00d4ff 0%, #51cf66 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.nl-sub { color: var(--text-secondary); margin-bottom: 22px; }

/* Severity cards */
.nl-stat-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px; margin: 18px 0 24px 0;
}
.nl-stat {
    border-radius: 14px; padding: 22px;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(10px);
    transition: transform .2s ease;
}
.nl-stat:hover { transform: translateY(-3px); }
.nl-stat .ic { font-size: 2.0rem; margin-bottom: 6px; }
.nl-stat .lbl { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 4px; }
.nl-stat .val { font-size: 2.4rem; font-weight: 800; line-height: 1.0; }
.nl-stat .desc { color: var(--text-secondary); font-size: 0.82rem; margin-top: 6px; }
.nl-stat.high   { border-left: 4px solid var(--danger);   }
.nl-stat.med    { border-left: 4px solid var(--warning);  }
.nl-stat.low    { border-left: 4px solid #ff922b;         }
.nl-stat.clean  { border-left: 4px solid var(--success);  }

/* Recommendations */
.nl-rec { padding: 12px 14px; margin-bottom: 8px; border-radius: 10px;
          background: rgba(255,255,255,.04); border: 1px solid var(--glass-border); }
.nl-rec.verified  { border-left: 4px solid var(--danger); }
.nl-rec.likely    { border-left: 4px solid var(--warning); }
.nl-rec.uncertain { border-left: 4px solid #ff922b; }
.nl-rec.summary   { border-left: 4px solid var(--primary); }

/* Streamlit widget styling — push closer to the dark/glass aesthetic */
section[data-testid="stFileUploaderDropzone"] {
    background: var(--glass-bg) !important;
    border: 2px dashed var(--primary) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
}
section[data-testid="stFileUploaderDropzone"] * { color: var(--text) !important; }

div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: #001019; font-weight: 700; border: 0;
    box-shadow: 0 4px 18px rgba(0, 212, 255, .35);
}
div.stButton > button[kind="primary"]:hover { transform: translateY(-1px); }

div.stDownloadButton > button {
    background: var(--glass-bg);
    color: var(--text);
    border: 1px solid var(--glass-border);
    transition: all .2s ease;
}
div.stDownloadButton > button:hover {
    border-color: var(--primary);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, .2);
}

/* Metric default — we use our own .nl-stat instead, but normalize anyway */
[data-testid="stMetricValue"] { color: var(--text); }
[data-testid="stMetricLabel"] { color: var(--text-secondary); }

/* Progress bar */
.stProgress > div > div { background: linear-gradient(90deg, #00d4ff, #51cf66); }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="nl-nav">
      <div class="nl-logo">⚡ NorthLadder</div>
      <div class="nl-subtitle">Data-Quality Detection Platform</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h1 class="nl-h1">Electronics Inventory Reconciliation</h1>
    <div class="nl-sub">
      Automatically detect wrong entries, scan errors and inconsistencies in
      your inventory, using Blackbelt as the truth reference. Mobile phones
      and tablets only.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Upload section
# ---------------------------------------------------------------------------

st.markdown('<div class="nl-card">', unsafe_allow_html=True)
st.markdown("#### 📁 Upload your files")
st.caption("Blackbelt and Master Template are required. Stack Bulk is optional.")

up1, up2, up3 = st.columns(3)
with up1:
    bb_file = st.file_uploader(
        "📋 Blackbelt Excel Report",
        type=["xlsx"], key="bb",
        help="Reference file — required",
    )
with up2:
    master_file = st.file_uploader(
        "🗂 Master Template",
        type=["xlsx"], key="master",
        help="Primary inventory file — required",
    )
with up3:
    stack_file = st.file_uploader(
        "📦 Stack Bulk Upload",
        type=["xlsx"], key="stack",
        help="Optional secondary reference",
    )

st.markdown('</div>', unsafe_allow_html=True)

ready = bb_file is not None and master_file is not None
run_clicked = st.button(
    "🚀 Start Analysis",
    type="primary", disabled=not ready, use_container_width=False,
)


# ---------------------------------------------------------------------------
# Cached run helper — keyed on file bytes so re-runs don't reprocess
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _run_detector_cached(bb_bytes: bytes, master_bytes: bytes, stack_bytes):
    work = Path(tempfile.mkdtemp(prefix="blackbelt_"))
    bb_path     = work / "blackbelt.xlsx"; bb_path.write_bytes(bb_bytes)
    master_path = work / "master.xlsx";    master_path.write_bytes(master_bytes)
    stack_path = None
    if stack_bytes:
        stack_path = work / "stack.xlsx"; stack_path.write_bytes(stack_bytes)
    out_dir = work / "out"
    summary = run_detector(
        str(bb_path), str(master_path), out_dir,
        stack_path=str(stack_path) if stack_path else None,
    )
    return summary, str(out_dir)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if run_clicked and ready:
    progress = st.progress(0, text="Loading files…")
    try:
        progress.progress(20, text="Loading and normalising data…")
        summary, out_dir = _run_detector_cached(
            bb_file.getvalue(),
            master_file.getvalue(),
            stack_file.getvalue() if stack_file else None,
        )
        progress.progress(100, text="Complete")
        progress.empty()
        st.session_state["summary"] = summary
        st.session_state["out_dir"] = out_dir
    except Exception as exc:
        progress.empty()
        st.error(f"Analysis failed: {exc}")
        st.stop()


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

def _render_stat(cls: str, icon: str, label: str, count: int, desc: str):
    return f"""
    <div class="nl-stat {cls}">
      <div class="ic">{icon}</div>
      <div class="lbl">{label}</div>
      <div class="val">{count:,}</div>
      <div class="desc">{desc}</div>
    </div>
    """


if "summary" in st.session_state:
    summary = st.session_state["summary"]
    out_dir = Path(st.session_state["out_dir"])
    matches = summary["matches"]

    st.markdown("### Analysis complete")
    st.caption(
        f"Processed {summary['total_processed']:,} mobile-phone + tablet rows "
        f"against {summary['total_blackbelt']:,} Blackbelt rows."
    )

    st.markdown(
        '<div class="nl-stat-grid">'
        + _render_stat("high",  "🚨", "Confirmed Errors",
                       matches["high_confidence"]["count"],
                       matches["high_confidence"]["description"])
        + _render_stat("med",   "⚠",  "Likely Errors",
                       matches["medium_confidence"]["count"],
                       matches["medium_confidence"]["description"])
        + _render_stat("low",   "🔎", "Advisory Flags",
                       matches["low_confidence"]["count"],
                       matches["low_confidence"]["description"])
        + _render_stat("clean", "✅", "Clean Rows",
                       matches["unmatched"]["count"],
                       matches["unmatched"]["description"])
        + "</div>",
        unsafe_allow_html=True,
    )

    # Recommendations
    recs = summary.get("recommendations", [])
    if recs:
        st.markdown("#### 📋 Recommended actions")
        for rec in recs:
            text   = rec["text"] if isinstance(rec, dict) else str(rec)
            bucket = rec.get("bucket", "summary") if isinstance(rec, dict) else "summary"
            st.markdown(
                f'<div class="nl-rec {bucket}">{text}</div>',
                unsafe_allow_html=True,
            )

    # Per-issue breakdown
    by_issue = summary.get("detector", {}).get("by_issue", {})
    if by_issue:
        with st.expander("🔬 Per-check breakdown"):
            issue_df = pd.DataFrame(
                sorted(by_issue.items(), key=lambda x: -x[1]),
                columns=["Issue", "Rows flagged"],
            )
            st.dataframe(issue_df, use_container_width=True, hide_index=True)

    # Downloads
    st.markdown("#### 📥 Downloads")

    download_files = [
        ("🚨 Confirmed Errors",  "verified_matches.xlsx",   "confirmed_errors.xlsx"),
        ("⚠ Likely Errors",      "likely_matches.xlsx",     "likely_errors.xlsx"),
        ("🔎 Advisory Flags",    "uncertain_matches.xlsx",  "advisory_flags.xlsx"),
        ("✅ Clean Rows",         "clean_rows.xlsx",         "clean_rows.xlsx"),
    ]
    cols = st.columns(len(download_files) + 1)
    for (label, src_name, archive_name), col in zip(download_files, cols[:-1]):
        path = out_dir / src_name
        if path.exists():
            col.download_button(
                label,
                data=path.read_bytes(),
                file_name=archive_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"dl_{src_name}",
            )
        else:
            col.button(label, disabled=True, use_container_width=True,
                       key=f"dl_disabled_{src_name}")

    # ZIP of everything
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for _, src_name, archive_name in download_files:
            p = out_dir / src_name
            if p.exists():
                zf.write(p, archive_name)
        sp = out_dir / "summary.json"
        if sp.exists():
            zf.write(sp, "summary.json")
    cols[-1].download_button(
        "📦 Download all (ZIP)",
        data=zip_buf.getvalue(),
        file_name="mismatch_results.zip",
        mime="application/zip",
        use_container_width=True,
        key="dl_zip",
    )

else:
    if not ready:
        st.info("👈 Upload Blackbelt + Master Template (and optionally Stack Bulk), then click **Start Analysis**.")
