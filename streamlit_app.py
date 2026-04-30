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

st.markdown("### Step 1 — Upload your files")
st.caption("Blackbelt + Stack Bulk are enough to run. Master Template is optional — "
           "include it for an extra cross-check between Master and Stack.")

up1, up2, up3 = st.columns(3)
with up1:
    bb_file = st.file_uploader(
        "Blackbelt report  (required)",
        type=["xlsx"], key="bb",
        help="The reference file from Blackbelt's device testing.",
    )
with up2:
    stack_file = st.file_uploader(
        "Stack Bulk Upload  (required)",
        type=["xlsx"], key="stack",
        help="The backend listing — the file we want to clean up.",
    )
with up3:
    master_file = st.file_uploader(
        "Master Template  (optional)",
        type=["xlsx"], key="master",
        help="Optional. When provided, Master is audited and Stack is used as cross-check.",
    )

ready = bb_file is not None and stack_file is not None
run_clicked = st.button(
    "🚀 Run Analysis",
    type="primary",
    disabled=not ready,
)
if not ready:
    st.info("Pick the Blackbelt file and the Stack Bulk Upload above, then click **Run Analysis**.")


# ---------------------------------------------------------------------------
# Cached run wrapper — keyed on file bytes
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _run_detector_cached(bb_bytes, stack_bytes, master_bytes):
    """Routing rules:
      - BB + Stack only           -> audit Stack directly (co_path=stack)
      - BB + Stack + Master       -> audit Master, cross-check via Stack (L19)
    """
    work = Path(tempfile.mkdtemp(prefix="blackbelt_"))
    bb_path    = work / "blackbelt.xlsx"; bb_path.write_bytes(bb_bytes)
    stack_path = work / "stack.xlsx";     stack_path.write_bytes(stack_bytes)
    master_path = None
    if master_bytes:
        master_path = work / "master.xlsx"; master_path.write_bytes(master_bytes)

    out_dir = work / "out"
    if master_path is not None:
        # Three-file mode: audit Master, cross-ref via Stack
        summary = run_detector(
            str(bb_path), str(master_path), out_dir,
            stack_path=str(stack_path),
        )
    else:
        # Two-file mode: audit Stack directly, no L19 cross-ref
        summary = run_detector(
            str(bb_path), str(stack_path), out_dir,
            stack_path=None,
        )
    return summary, str(out_dir)


if run_clicked and ready:
    progress = st.progress(0, text="Loading files…")
    try:
        progress.progress(20, text="Reading and normalising data…")
        summary, out_dir = _run_detector_cached(
            bb_file.getvalue(),
            stack_file.getvalue(),
            master_file.getvalue() if master_file else None,
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
    "category_model_mismatch":          "Category doesn't match the product",
    "brand_token_absent":               "Brand and Asset Label disagree",
    "storage_unseen_in_bb":             "Storage size Blackbelt has never seen for this model",
    "duplicate_imei":                   "Same IMEI on more than one row",
    "duplicate_asset_id_imei_pair":     "Same Asset ID + IMEI listed twice",
    "same_deal_id_multi_imei":          "Same Deal ID has more than one IMEI",
    "possible_imei1_imei2_pair":        "Same phone listed twice (using both its IMEIs)",
    "placeholder_imei":                 "Fake/test IMEI in production data",
    "brand_invalid_value":              "Brand field has junk in it",
    "brand_missing":                    "Brand field is empty",
    "imei_identity_contradiction":      "Same IMEI claims to be two different phones",
    "tac_cohort_anomaly":               "IMEI was probably scanned off a different phone",
    "model_number_mismatch":            "Model code in the label doesn't match the model name",
    "color_not_in_bb_catalog":          "Colour Blackbelt has never seen for this model",
    "two_storages_in_label":            "Asset Label has two different storage sizes",
    "grade_contradicts_damage":         "Grade says good but label mentions damage",
    "qr_code_contradicts_imei":         "QR code holds a different IMEI",
    "brand_model_not_in_bb_catalog":    "Model not in Blackbelt's catalogue",
    "not_in_blackbelt":                 "Device hasn't been Blackbelt-tested yet",
    "bb_brand_mismatch":                "Backend brand disagrees with Blackbelt",
    "bb_model_mismatch":                "Backend model disagrees with Blackbelt",
    "bb_storage_mismatch":              "Backend storage disagrees with Blackbelt",
    "bb_grade_mismatch":                "Backend grade disagrees with Blackbelt",
    "bb_color_mismatch":                "Backend colour disagrees with Blackbelt",
    "bb_model_number_mismatch":         "Backend model code disagrees with Blackbelt",
    "master_stack_grade_mismatch":      "Master and Stack disagree on grade",
    "master_stack_vat_mismatch":        "Master and Stack disagree on VAT",
    "master_stack_country_mismatch":    "Master and Stack disagree on country",
    "master_imei_disagrees_with_stack": "Master and Stack record different IMEIs for the same Deal",
    "master_not_in_stack":              "Device in Master but missing from Stack",
    "stale_inventory":                  "In stock for more than 12 months",
    "bb_test_failed":                   "Blackbelt failed a hardware test on this device",
    "bb_refurbished_parts":             "Blackbelt detected non-original parts",
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
    categories = summary.get("categories") or {}
    wm = summary.get("wrong_model_comparison") or {}
    age_block = summary.get("product_age") or {}

    st.divider()
    st.markdown("### Step 2 — What we found")
    st.caption(
        f"Checked **{summary['total_processed']:,}** of your phones and tablets "
        f"against **{summary['total_blackbelt']:,}** Blackbelt records."
    )

    # --- Five category KPI cards (the only checks visible per current scope) ---
    cat_keys = ["brand_mismatch", "model_mismatch", "storage_mismatch",
                "grade_mismatch", "not_in_blackbelt"]
    cat_icons = {"brand_mismatch": "🏭", "model_mismatch": "📱",
                 "storage_mismatch": "💾", "grade_mismatch": "🏷",
                 "not_in_blackbelt": "📡"}
    cat_help = {
        "brand_mismatch":   "Backend brand doesn't match Blackbelt's reading.",
        "model_mismatch":   "Backend asset/model name doesn't match Blackbelt's reading.",
        "storage_mismatch": "Backend storage size disagrees with Blackbelt's reading.",
        "grade_mismatch":   "Backend grade disagrees with Blackbelt's automated grading.",
        "not_in_blackbelt": "IMEI looks valid but doesn't appear in the Blackbelt file.",
    }
    kcols = st.columns(len(cat_keys) + 1)
    for key, col in zip(cat_keys, kcols[:-1]):
        meta = categories.get(key) or {}
        col.metric(f"{cat_icons[key]} {meta.get('label', key)}",
                   f"{int(meta.get('count', 0)):,}",
                   help=cat_help[key])
    kcols[-1].metric("✅ All good",
                     f"{matches['unmatched']['count']:,}",
                     help="No issues in any of the five tracked categories.")

    # --- Grade-mismatch dedicated panel (kept — it's the priority cleanup) ---
    grade_block = summary.get("grade_mismatches") or {}
    grade_count = int(grade_block.get("count", 0))
    if grade_count > 0:
        st.markdown("#### 🏷 Grade mismatches (backend vs. Blackbelt)")
        matrix = grade_block.get("matrix") or []
        if matrix:
            mat_df = pd.DataFrame(matrix).rename(columns={"count": "Devices"})
            mat_df = mat_df[["Backend Grade", "Blackbelt Grade", "Devices"]]
            gc1, gc2 = st.columns([3, 2])
            with gc1:
                st.dataframe(mat_df, use_container_width=True, hide_index=True,
                             height=min(40 + 35 * len(mat_df), 360))
            with gc2:
                pivot = mat_df.pivot_table(index="Backend Grade",
                                           columns="Blackbelt Grade",
                                           values="Devices", fill_value=0)
                fig = go.Figure()
                for bb_grade in pivot.columns:
                    fig.add_bar(name=f"BB={bb_grade}", x=pivot.index,
                                y=pivot[bb_grade].values)
                fig.update_layout(
                    barmode="stack",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e0e0e0",
                    margin=dict(l=10, r=10, t=20, b=10),
                    height=320,
                    legend=dict(orientation="h", y=-0.2),
                    xaxis=dict(title="Backend grade"),
                    yaxis=dict(title="Devices", gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig, use_container_width=True)
        st.caption("Blackbelt's grade comes from the automated test machine, so "
                   "treat it as authoritative. Download the dedicated file below to "
                   "fix these in the backend.")

    # --- Wrong Model comparison: stack-tagged vs auto-flagged ---
    st.markdown("#### 🆚 Wrong-model coverage")
    wm_stack = int(wm.get("stack_tagged_count", 0))
    wm_auto  = int(wm.get("model_flagged_count", 0))
    wmc1, wmc2 = st.columns([3, 2])
    with wmc1:
        wm_fig = go.Figure(go.Bar(
            x=["Already tagged in Stack", "Newly flagged by model"],
            y=[wm_stack, wm_auto],
            text=[f"{wm_stack:,}", f"{wm_auto:,}"],
            textposition="outside",
            marker=dict(color=["#a0a0a0", "#ff6b6b"]),
            hovertemplate="<b>%{x}</b><br>%{y:,} devices<extra></extra>",
        ))
        wm_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e0e0",
            margin=dict(l=10, r=10, t=20, b=10),
            height=280,
            yaxis=dict(title="Devices", gridcolor="#1a1a2e"),
        )
        st.plotly_chart(wm_fig, use_container_width=True)
    with wmc2:
        st.metric("Stack-tagged 'Wrong Model'", f"{wm_stack:,}",
                  help="Rows your team had already manually marked as wrong model "
                       "in Stack — these are skipped from auto-flagging.")
        st.metric("Auto-flagged Model mismatch", f"{wm_auto:,}",
                  help="New model mismatches the detector found beyond the team's "
                       "manual list.")
        if wm_stack + wm_auto > 0:
            new_pct = 100 * wm_auto / max(wm_stack + wm_auto, 1)
            st.caption(f"The detector found **{new_pct:.0f}%** more wrong-model "
                       f"rows than the team had pre-tagged.")

    # --- Product Age section ---
    if age_block.get("total_with_date", 0) > 0:
        st.markdown("#### 📅 Product age")
        st.caption("How long ago each device was traded in. Pick a granularity to "
                   "see the inventory profile by that interval.")
        age_choice = st.radio(
            "Bucket size",
            options=["Monthly", "Quarterly", "Semi-annual", "Annual"],
            horizontal=True, key="age_choice",
        )
        bucket_key = {
            "Monthly": "monthly", "Quarterly": "quarterly",
            "Semi-annual": "semi_annual", "Annual": "annual",
        }[age_choice]
        rows = age_block.get(bucket_key) or []
        if rows:
            adf = pd.DataFrame(rows)
            adf = adf.sort_values("bucket")
            age_fig = go.Figure(go.Bar(
                x=adf["bucket"].tolist(),
                y=adf["count"].tolist(),
                text=adf["count"].tolist(),
                textposition="outside",
                marker=dict(color="#00d4ff"),
                hovertemplate="<b>%{x}</b><br>%{y:,} devices<extra></extra>",
            ))
            age_fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e0e0",
                margin=dict(l=10, r=10, t=20, b=10),
                height=320,
                xaxis=dict(title=age_choice + " bucket"),
                yaxis=dict(title="Devices", gridcolor="#1a1a2e"),
            )
            st.plotly_chart(age_fig, use_container_width=True)
        else:
            st.info("No trade-in dates could be parsed from the Deal IDs.")

    # --- Downloads ---
    st.divider()
    st.markdown("### Step 3 — Download by category")
    st.caption(
        "One Excel per category. Each file has Deal ID, IMEI, Blackbelt, "
        "Stack Bulk, Location, Stack ID, VAT Type, Problem, Field, Current Value."
    )

    download_files = [
        ("🏭 Brand mismatch",   "category_brand_mismatch.xlsx",    "brand_mismatch.xlsx"),
        ("📱 Model mismatch",    "category_model_mismatch.xlsx",    "model_mismatch.xlsx"),
        ("💾 Storage mismatch",  "category_storage_mismatch.xlsx",  "storage_mismatch.xlsx"),
        ("🏷 Grade mismatch",    "category_grade_mismatch.xlsx",    "grade_mismatch.xlsx"),
        ("📡 Not in Blackbelt", "category_not_in_blackbelt.xlsx",  "not_in_blackbelt.xlsx"),
        ("📅 Product age",       "product_age.xlsx",                "product_age.xlsx"),
        ("✅ All good",           "clean_rows.xlsx",                 "clean_rows.xlsx"),
    ]
    # Render in two rows so the buttons don't get squashed: the 5 categories
    # in the first row, the operational files (Product Age / Clean / ZIP) in the second.
    def _render_dl_row(items):
        cols = st.columns(len(items))
        for (label, src_name, archive_name), col in zip(items, cols):
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
    _render_dl_row(download_files[:5])
    _render_dl_row(download_files[5:])

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for _, src_name, archive_name in download_files:
            p = out_dir / src_name
            if p.exists():
                zf.write(p, archive_name)
        sp = out_dir / "summary.json"
        if sp.exists():
            zf.write(sp, "summary.json")
    st.download_button(
        "📦 All files (ZIP)",
        data=zip_buf.getvalue(),
        file_name="northladder_quality_check.zip",
        mime="application/zip",
        use_container_width=True,
        key="dl_zip",
    )
