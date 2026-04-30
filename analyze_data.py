"""
Fresh analysis: understand the real relationship between Blackbelt (truth) and
Company (backend) data, and surface what's actually stored wrong.

Reads both files, normalizes, joins on IMEI / IMEI2 / Serial,
then reports concrete discrepancies (brand/model/storage/color/category),
identifier-type confusion, and duplicates.
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

# Patch corrupt validation rules
_orig = DataValidation.__init__
def _patched(self, *a, **kw):
    try: _orig(self, *a, **kw)
    except ValueError: pass
DataValidation.__init__ = _patched

BB_PATH = r"C:\Users\dharm\Downloads\ExcelReports-analyst-14-04-2026-12-12-18.xlsx"
CO_PATH = r"C:\Users\dharm\Downloads\Stack Bulk Upload - 2026-04-14T153918.672.xlsx"

OUT_DIR = Path("results_new")
OUT_DIR.mkdir(exist_ok=True)


# ---------- Normalizers ----------

def norm_text(v):
    if pd.isna(v): return ""
    return re.sub(r"\s+", " ", str(v)).strip().lower()

def norm_id(v):
    """Strip non-alphanum. Used for IMEIs AND serials (they share a column)."""
    if pd.isna(v) or v == "": return ""
    return re.sub(r"[^0-9A-Za-z]", "", str(v)).upper()

def is_numeric_imei(v):
    """Real IMEIs are 14-16 digit numeric strings."""
    return bool(v) and v.isdigit() and 14 <= len(v) <= 16

def extract_storage(text):
    """Pull GB/TB from free text. Returns int GB, or None."""
    if not text: return None
    s = str(text).upper()
    m = re.search(r"(\d+)\s*(TB|GB)", s)
    if not m: return None
    n = int(m.group(1))
    return n * 1024 if m.group(2) == "TB" else n

def brand_canonical(s):
    s = norm_text(s)
    # common aliases
    aliases = {
        "apple inc": "apple", "samsung electronics": "samsung",
        "google inc": "google", "xiaomi corp": "xiaomi",
    }
    return aliases.get(s, s)


# ---------- Load ----------

print("Loading Blackbelt…")
bb = pd.read_excel(BB_PATH, sheet_name="Sheet1")
print(f"  {len(bb)} rows, {len(bb.columns)} columns")

print("Loading Company…")
co = pd.read_excel(CO_PATH, sheet_name="BulkSell")
print(f"  {len(co)} rows, {len(co.columns)} columns")


# ---------- Extract canonical fields ----------

bb_clean = pd.DataFrame({
    "bb_row": bb.index,
    "imei":   bb["IMEI/MEID"].map(norm_id),
    "imei2":  bb["IMEI2"].map(norm_id),
    "serial": bb["Serial Number"].map(norm_id),
    "brand":  bb["Manufacturer"].map(brand_canonical),
    "model":  bb["Model"].map(norm_text),
    "model_number": bb["Model Number"].map(norm_text),
    "storage_gb": bb["Handset Memory Size"].map(extract_storage),
    "color":  bb["Device Colour"].map(norm_text),
    "grade":  bb["Device Grade"].map(norm_text) if "Device Grade" in bb.columns else "",
})

co_clean = pd.DataFrame({
    "co_row": co.index,
    "imei_field": co["IMEI Number"].map(norm_id),
    "barcode": co["Barcode"].map(norm_id),
    "brand":   co["Brand"].map(brand_canonical),
    "asset_label": co["Asset Label"].map(norm_text),
    "category": co["Category"].map(norm_text),
    "grade":    co["Latest Assessed Grade"].map(norm_text),
    "asset_id": co["AssetId"].astype(str),
})
co_clean["storage_gb"] = co_clean["asset_label"].map(extract_storage)
# classify the IMEI Number field: real IMEI vs. serial-in-imei-slot
co_clean["imei_type"] = co_clean["imei_field"].map(
    lambda v: "imei" if is_numeric_imei(v) else ("serial_in_imei_col" if v else "empty")
)


# ---------- Findings 0: identifier-type confusion ----------

print("\n" + "=" * 70)
print("FINDING 0 — What's actually in the company `IMEI Number` column")
print("=" * 70)
print(co_clean["imei_type"].value_counts().to_string())


# ---------- Build Blackbelt lookups ----------

bb_by_imei = {}
bb_by_serial = {}
for _, r in bb_clean.iterrows():
    if r["imei"]:   bb_by_imei.setdefault(r["imei"], []).append(r)
    if r["imei2"]:  bb_by_imei.setdefault(r["imei2"], []).append(r)
    if r["serial"]: bb_by_serial.setdefault(r["serial"], []).append(r)


# ---------- Match ----------

def match_company_row(row):
    """Return (matched_bb_row, match_key) or (None, None)."""
    v = row["imei_field"]
    if not v:
        return None, None
    if is_numeric_imei(v):
        if v in bb_by_imei:
            return bb_by_imei[v][0], "imei"
    else:
        # non-numeric value sitting in IMEI column -> probably a serial
        if v in bb_by_serial:
            return bb_by_serial[v][0], "serial_via_imei_col"
    # fallback: try barcode against serials
    bc = row["barcode"]
    if bc and bc in bb_by_serial:
        return bb_by_serial[bc][0], "barcode_to_serial"
    return None, None


matches = []
for _, r in co_clean.iterrows():
    bbm, key = match_company_row(r)
    matches.append((bbm, key))

co_clean["match_key"] = [m[1] for m in matches]
co_clean["bb_row"]    = [m[0]["bb_row"] if m[0] is not None else None for m in matches]


# ---------- Findings 1: match coverage ----------

print("\n" + "=" * 70)
print("FINDING 1 — Match coverage (company rows joined to Blackbelt)")
print("=" * 70)
total = len(co_clean)
match_counts = co_clean["match_key"].fillna("no_match").value_counts()
print(match_counts.to_string())
print(f"\nTotal company rows: {total}")
print(f"Matched: {co_clean['bb_row'].notna().sum()} "
      f"({100 * co_clean['bb_row'].notna().mean():.1f}%)")
print(f"Blackbelt rows available: {len(bb_clean)}")
print("NOTE: Blackbelt only covers a subset; unmatched is EXPECTED, not an error.")


# ---------- Findings 2: field-level mismatches on matched pairs ----------

matched = co_clean[co_clean["bb_row"].notna()].copy()
matched["bb_row"] = matched["bb_row"].astype(int)
joined = matched.merge(
    bb_clean.add_prefix("bb_"),
    left_on="bb_row", right_on="bb_bb_row",
    how="left",
)

issues = []
for _, r in joined.iterrows():
    row_issues = []
    # Brand check
    if r["brand"] and r["bb_brand"] and r["brand"] != r["bb_brand"]:
        row_issues.append(("brand_mismatch",
                           f"company='{r['brand']}' vs blackbelt='{r['bb_brand']}'"))
    # Storage check
    if r["storage_gb"] and r["bb_storage_gb"] and r["storage_gb"] != r["bb_storage_gb"]:
        row_issues.append(("storage_mismatch",
                           f"company={r['storage_gb']}GB vs blackbelt={r['bb_storage_gb']}GB"))
    # Model presence check: the company Asset Label should mention the BB model's key tokens
    if r["bb_model"]:
        bb_tokens = [t for t in re.split(r"[^a-z0-9]+", r["bb_model"]) if len(t) >= 3]
        if bb_tokens and not any(t in r["asset_label"] for t in bb_tokens):
            row_issues.append(("model_not_in_asset_label",
                               f"bb_model='{r['bb_model']}' absent from asset_label='{r['asset_label']}'"))
    # Category sanity check
    if r["category"] and r["bb_model"]:
        cat = r["category"]
        m = r["bb_model"]
        if "tablet" in cat and "ipad" not in m and "tab" not in m:
            row_issues.append(("category_mismatch",
                               f"category='tablet' but bb_model='{m}'"))
        if "mobile" in cat and ("ipad" in m or m.startswith("tab ")):
            row_issues.append(("category_mismatch",
                               f"category='mobile' but bb_model='{m}' (looks like tablet)"))
    # IMEI-in-serial-column confusion — flag for review
    if r["match_key"] == "serial_via_imei_col" and r["category"] in ("mobile phone",):
        row_issues.append(("wrong_imei_value",
                           f"company IMEI column has serial '{r['imei_field']}' but "
                           f"Blackbelt has a real IMEI '{r['bb_imei']}' for this device"))
    for itype, detail in row_issues:
        issues.append({
            "co_row": int(r["co_row"]),
            "asset_id": r["asset_id"],
            "imei_field": r["imei_field"],
            "match_key": r["match_key"],
            "issue_type": itype,
            "detail": detail,
            "company_brand": r["brand"],
            "company_asset_label": r["asset_label"],
            "company_category": r["category"],
            "bb_brand": r["bb_brand"],
            "bb_model": r["bb_model"],
            "bb_model_number": r["bb_model_number"],
            "bb_storage_gb": r["bb_storage_gb"],
            "bb_imei": r["bb_imei"],
            "bb_serial": r["bb_serial"],
        })

issues_df = pd.DataFrame(issues)

print("\n" + "=" * 70)
print("FINDING 2 — Field-level issues on matched pairs")
print("=" * 70)
if len(issues_df):
    print(issues_df["issue_type"].value_counts().to_string())
    print(f"\nTotal issue rows flagged: {len(issues_df)}")
    print(f"Distinct company rows with issues: {issues_df['co_row'].nunique()}")
else:
    print("No field-level issues detected on matched rows.")


# ---------- Findings 3: duplicates within company data ----------

dup_imei = (
    co_clean[co_clean["imei_field"] != ""]
    .groupby("imei_field")
    .size()
    .loc[lambda s: s > 1]
    .sort_values(ascending=False)
)
print("\n" + "=" * 70)
print("FINDING 3 — Duplicate identifier values within company data")
print("=" * 70)
print(f"Company IMEI values that appear more than once: {len(dup_imei)}")
if len(dup_imei):
    print("Top 10:")
    print(dup_imei.head(10).to_string())


# ---------- Findings 4: malformed IMEIs in the phone category ----------

mobile = co_clean[co_clean["category"] == "mobile phone"]
bad_phone_imei = mobile[(mobile["imei_field"] != "") & (mobile["imei_type"] != "imei")]
print("\n" + "=" * 70)
print("FINDING 4 — Mobile Phone rows where IMEI field isn't a real IMEI")
print("=" * 70)
print(f"{len(bad_phone_imei)} of {len(mobile)} 'Mobile Phone' rows "
      f"({100 * len(bad_phone_imei) / max(len(mobile), 1):.1f}%) have a non-numeric "
      f"value in the IMEI Number column.")
print("Sample:")
print(bad_phone_imei[["co_row", "asset_id", "imei_field", "brand", "asset_label"]].head(10).to_string(index=False))


# ---------- Findings 5: brand/category plausibility ----------

impl = co_clean[co_clean["brand"] == "apple"]
non_apple_label = impl[~impl["asset_label"].str.contains("apple|iphone|ipad|macbook|watch|airpod", na=False)]
print("\n" + "=" * 70)
print("FINDING 5 — Apple-branded rows whose asset label doesn't mention an Apple product")
print("=" * 70)
print(f"{len(non_apple_label)} suspect rows")
if len(non_apple_label):
    print(non_apple_label[["co_row", "asset_id", "brand", "asset_label", "category"]].head(10).to_string(index=False))


# ---------- Save outputs ----------

co_clean.to_csv(OUT_DIR / "company_clean.csv", index=False)
bb_clean.to_csv(OUT_DIR / "blackbelt_clean.csv", index=False)
if len(issues_df):
    issues_df.to_csv(OUT_DIR / "flagged_issues.csv", index=False)
print(f"\nArtifacts written to: {OUT_DIR.resolve()}")
