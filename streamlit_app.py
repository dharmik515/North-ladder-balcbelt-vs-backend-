"""
Streamlit front-end for the NorthLadder data-quality detector.

Built with non-technical users in mind: friendly labels, charts in place of
raw numbers, and zero exposed jargon. Uses Streamlit's native widgets so it
deploys reliably to Streamlit Cloud.
"""

import io
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

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
# Theme: dark glassmorphism, no raw HTML in the body
# ---------------------------------------------------------------------------

THEME_CSS = """
<style>
:root {
    --primary: #00d4ff;
    --primary-dark: #0099cc;
    --success: #51cf66;
    --warning: #ffd43b;
    --danger:  #ff6b6b;
    --orange:  #ff922b;
    --dark:    #0a0e27;
    --darker:  #050812;
    --text:    #e0e0e0;
    --text-secondary: #a0a0a0;
    --glass-bg: rgba(15, 23, 42, 0.7);
    --glass-border: rgba(255, 255, 255, 0.1);
}
.stApp {
    background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%) fixed;
    color: var(--text);
}
#MainMenu, footer, header { visibility: hidden; }

/* File uploader */
section[data-testid="stFileUploaderDropzone"] {
    background: var(--glass-bg) !important;
    border: 2px dashed var(--primary) !important;
    border-radius: 12px !important;
}
section[data-testid="stFileUploaderDropzone"] * { color: var(--text) !important; }

/* Buttons */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: #001019; font-weight: 700; border: 0;
    box-shadow: 0 4px 18px rgba(0, 212, 255, .35);
}
div.stDownloadButton > button {
    background: var(--glass-bg);
    color: var(--text);
    border: 1px solid var(--glass-border);
}
div.stDownloadButton > button:hover {
    border-color: var(--primary);
    box-shadow: 0 0 0 2px rgba(0, 212, 255, .2);
}

/* Streamlit's metric — colour-tune for the dark theme */
[data-testid="stMetricValue"] { color: var(--text); font-weight: 700; }
[data-testid="stMetricLabel"] { color: var(--text-secondary); }

/* Section spacing */
.block-container { padding-top: 1.4rem; padding-bottom: 2rem; }

/* Progress bar */
.stProgress > div > div { background: linear-gradient(90deg, #00d4ff, #51cf66); }
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown("## ⚡ NorthLadder — Data-Quality Check")
st.caption(
    "Cross-checks your inventory against Blackbelt (the device-test reference) "
    "and Stack Bulk Upload (the sell-side record). Catches scan errors, wrong "
    "specs, and devices that haven't been quality-tested yet."
)
st.divider()


# ---------------------------------------------------------------------------
# Step 1 — Uploads
# ---------------------------------------------------------------------------

st.markdown("### Step 1 — Upload your three files")

up1, up2, up3 = st.columns(3)
with up1:
    bb_file = st.file_uploader(
        "Blackbelt report  (required)",
        type=["xlsx"], key="bb",
        help="The reference file from Blackbelt's device testing.",
    )
with up2:
    master_file = st.file_uploader(
        "Master Template  (required)",
        type=["xlsx"], key="master",
        help="Your inventory file — the one we want to clean up.",
    )
with up3:
    stack_file = st.file_uploader(
        "Stack Bulk Upload  (optional)",
        type=["xlsx"], key="stack",
        help="The sell-side listing. Helps catch more errors when included.",
    )

ready = bb_file is not None and master_file is not None
run_clicked = st.button(
    "🚀 Run Analysis",
    type="primary",
    disabled=not ready,
)
if not ready:
    st.info("Pick the Blackbelt file and the Master Template above, then click **Run Analysis**.")


# ---------------------------------------------------------------------------
# Cached run wrapper — keyed on file bytes
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _run_detector_cached(bb_bytes, master_bytes, stack_bytes):
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


if run_clicked and ready:
    progress = st.progress(0, text="Loading files…")
    try:
        progress.progress(20, text="Reading and normalising data…")
        summary, out_dir = _run_detector_cached(
            bb_file.getvalue(),
            master_file.getvalue(),
            stack_file.getvalue() if stack_file else None,
        )
        progress.progress(100, text="Done")
        progress.empty()
        st.session_state["summary"] = summary
        st.session_state["out_dir"] = out_dir
    except Exception as exc:
        progress.empty()
        st.error(f"Analysis failed: {exc}")
        st.stop()


# ---------------------------------------------------------------------------
# Friendly issue-name dictionary so the dashboard shows plain English
# ---------------------------------------------------------------------------

ISSUE_FRIENDLY = {
    "imei_missing":                     "IMEI is missing",
    "imei_luhn_fail":                   "IMEI fails the standard digit check",
    "imei_wrong_length":                "IMEI is the wrong length",
    "looks_like_imeisv":                "16-digit IMEISV instead of 15-digit IMEI",
    "serial_in_imei_slot":              "Serial number written into the IMEI column",
    "imei_in_barcode_slot":             "IMEI written into the Barcode column",
    "imei_equals_barcode":              "IMEI and Barcode hold the same value",
    "category_model_mismatch":          "Category doesn't match the model name",
    "brand_token_absent":               "Brand isn't mentioned in the model name",
    "storage_unseen_in_bb":             "Storage size unknown to Blackbelt for this model",
    "duplicate_imei":                   "Same IMEI on more than one row",
    "duplicate_asset_id_imei_pair":     "Same Asset ID + IMEI listed twice",
    "same_deal_id_multi_imei":          "Same Deal ID has more than one IMEI",
    "possible_imei1_imei2_pair":        "Same phone listed twice (IMEI1 + IMEI2)",
    "placeholder_imei":                 "Test/fake IMEI in production data",
    "brand_invalid_value":              "Brand field has a junk value",
    "brand_missing":                    "Brand field is empty",
    "imei_identity_contradiction":      "Same IMEI claimed by two different devices",
    "tac_cohort_anomaly":               "IMEI prefix doesn't match the rest of the batch",
    "model_number_mismatch":            "Model-number code doesn't match the model",
    "color_not_in_bb_catalog":          "Colour not in Blackbelt's records for this model",
    "two_storages_in_label":            "Two different storage sizes in the same label",
    "grade_contradicts_damage":         "Grade is high but label mentions damage",
    "qr_code_contradicts_imei":         "QR code holds a different IMEI",
    "brand_model_not_in_bb_catalog":    "Model not found in Blackbelt's catalog",
    "not_in_blackbelt":                 "Device hasn't been tested by Blackbelt yet",
    "bb_brand_mismatch":                "Brand differs from Blackbelt's reading",
    "bb_model_mismatch":                "Model differs from Blackbelt's reading",
    "bb_storage_mismatch":              "Storage differs from Blackbelt's reading",
    "bb_grade_mismatch":                "Grade differs from Blackbelt's grading",
    "bb_color_mismatch":                "Colour differs from Blackbelt's reading",
    "bb_model_number_mismatch":         "Model-number differs from Blackbelt's reading",
    "master_stack_grade_mismatch":      "Master and Stack disagree on grade",
    "master_stack_vat_mismatch":        "Master and Stack disagree on VAT",
    "master_stack_country_mismatch":    "Master and Stack disagree on country",
    "master_imei_disagrees_with_stack": "Master and Stack disagree on IMEI for the same Deal",
    "master_not_in_stack":              "Device in Master but missing from Stack",
    "stale_inventory":                  "In stock for more than 12 months",
    "bb_test_failed":                   "Blackbelt recorded a hardware test failure",
    "bb_refurbished_parts":             "Blackbelt detected non-genuine parts",
    "storage_missing":                  "Storage size missing from the label",
}


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def severity_donut(matches: dict):
    counts = [
        matches["high_confidence"]["count"],
        matches["medium_confidence"]["count"],
        matches["low_confidence"]["count"],
        matches["unmatched"]["count"],
    ]
    labels = ["Need fixing", "Worth checking", "Just FYI", "All good"]
    colors = ["#ff6b6b", "#ff922b", "#ffd43b", "#51cf66"]
    fig = go.Figure(go.Pie(
        labels=labels, values=counts, hole=0.55,
        marker=dict(colors=colors, line=dict(color="#050812", width=2)),
        textinfo="label+percent", textposition="outside",
        hovertemplate="<b>%{label}</b><br>%{value:,} rows<br>%{percent}<extra></extra>",
    ))
    total = sum(counts)
    flagged_pct = 100 * (total - counts[3]) / max(total, 1)
    fig.update_layout(
        showlegend=False,
        annotations=[dict(text=f"<b>{total:,}</b><br><span style='font-size:14px;color:#a0a0a0'>devices</span>",
                          x=0.5, y=0.5, font_size=22, showarrow=False, font_color="#e0e0e0")],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(l=10, r=10, t=20, b=10),
        height=360,
    )
    return fig, flagged_pct


def top_issues_bar(by_issue: dict, n: int = 10):
    if not by_issue:
        return None
    items = sorted(by_issue.items(), key=lambda x: -x[1])[:n]
    labels = [ISSUE_FRIENDLY.get(k, k.replace("_", " ").title()) for k, _ in items]
    values = [v for _, v in items]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=values, colorscale=[[0, "#51cf66"], [0.5, "#ffd43b"], [1, "#ff6b6b"]]),
        text=values, textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:,} rows flagged<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        xaxis=dict(showgrid=True, gridcolor="#1a1a2e", title=""),
        yaxis=dict(autorange="reversed", title=""),
        margin=dict(l=10, r=40, t=20, b=10),
        height=max(360, 38 * len(items)),
    )
    return fig


def health_gauge(matches: dict):
    total = sum(matches[k]["count"] for k in
                ("high_confidence", "medium_confidence", "low_confidence", "unmatched"))
    clean_pct = 100 * matches["unmatched"]["count"] / max(total, 1)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=clean_pct,
        number=dict(suffix="%", font=dict(size=44, color="#e0e0e0")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#a0a0a0", tickwidth=1),
            bar=dict(color="#00d4ff"),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            steps=[
                dict(range=[0, 50],   color="rgba(255, 107, 107, 0.25)"),
                dict(range=[50, 80],  color="rgba(255, 212, 59, 0.25)"),
                dict(range=[80, 100], color="rgba(81, 207, 102, 0.25)"),
            ],
        ),
        title=dict(text="<span style='color:#a0a0a0'>Clean rows</span>", font=dict(size=14)),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        margin=dict(l=10, r=10, t=40, b=10),
        height=260,
    )
    return fig


# ---------------------------------------------------------------------------
# Step 2 — Results dashboard
# ---------------------------------------------------------------------------

if "summary" in st.session_state:
    summary = st.session_state["summary"]
    out_dir = Path(st.session_state["out_dir"])
    matches = summary["matches"]
    by_issue = summary.get("detector", {}).get("by_issue", {})

    st.divider()
    st.markdown("### Step 2 — What we found")
    st.caption(
        f"Checked **{summary['total_processed']:,}** of your phones and tablets "
        f"against **{summary['total_blackbelt']:,}** Blackbelt records."
    )

    # --- Top KPI strip ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🚨 Need fixing",        f"{matches['high_confidence']['count']:,}",
              help="Definite errors — fix at the source as soon as possible.")
    k2.metric("⚠ Worth checking",      f"{matches['medium_confidence']['count']:,}",
              help="Probable errors — an analyst should verify before fixing.")
    k3.metric("🔎 Just FYI",            f"{matches['low_confidence']['count']:,}",
              help="Weak signals — usually fine, worth a glance.")
    k4.metric("✅ All good",             f"{matches['unmatched']['count']:,}",
              help="No issues detected — no action needed.")

    # --- Charts row ---
    st.markdown("#### 📊 Overview")
    c1, c2 = st.columns([3, 2])
    with c1:
        donut, flagged_pct = severity_donut(matches)
        st.plotly_chart(donut, use_container_width=True)
    with c2:
        st.plotly_chart(health_gauge(matches), use_container_width=True)
        st.caption(
            f"**{flagged_pct:.1f}%** of devices have at least one issue. "
            f"Higher scores mean cleaner data."
        )

    # --- Top issues ---
    if by_issue:
        st.markdown("#### 🔬 The most common problems we found")
        top_chart = top_issues_bar(by_issue, n=10)
        if top_chart:
            st.plotly_chart(top_chart, use_container_width=True)

    # --- Recommendations ---
    recs = summary.get("recommendations", [])
    if recs:
        st.markdown("#### 📋 What to do next")
        for rec in recs:
            text   = rec["text"] if isinstance(rec, dict) else str(rec)
            bucket = rec.get("bucket", "summary") if isinstance(rec, dict) else "summary"
            if bucket == "verified":
                st.error(text, icon="🚨")
            elif bucket == "likely":
                st.warning(text, icon="⚠")
            elif bucket == "uncertain":
                st.info(text, icon="🔎")
            else:
                st.success(text, icon="📊")

    # --- Optional drill-down ---
    if by_issue:
        with st.expander("🧮 See every check (full breakdown)"):
            full_df = pd.DataFrame(
                [(ISSUE_FRIENDLY.get(k, k.replace("_", " ").title()), v)
                 for k, v in sorted(by_issue.items(), key=lambda x: -x[1])],
                columns=["Issue", "Rows flagged"],
            )
            st.dataframe(full_df, use_container_width=True, hide_index=True)

    # --- Downloads ---
    st.divider()
    st.markdown("### Step 3 — Download the corrected lists")
    st.caption(
        "Each file has the same columns: Deal ID, IMEI, what Blackbelt says, "
        "what Stack Bulk says, location, and the specific problem."
    )

    download_files = [
        ("🚨 Need fixing",     "verified_matches.xlsx",   "issues_to_fix.xlsx"),
        ("⚠ Worth checking",   "likely_matches.xlsx",     "probable_issues.xlsx"),
        ("🔎 Just FYI",         "uncertain_matches.xlsx",  "advisory_flags.xlsx"),
        ("✅ All good",          "clean_rows.xlsx",         "clean_rows.xlsx"),
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
        "📦 All files (ZIP)",
        data=zip_buf.getvalue(),
        file_name="northladder_quality_check.zip",
        mime="application/zip",
        use_container_width=True,
        key="dl_zip",
    )
