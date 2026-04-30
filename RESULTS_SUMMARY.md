# Pipeline Execution Results - April 11, 2026

## Executive Summary

The mismatch detection pipeline processed **3,970 company records** against **367 Blackbelt records** and identified:

- **High confidence matches**: 0 (0.0%) — Records with 90%+ confidence (auto-safe to correct)
- **Medium confidence matches**: 0 (0.0%) — Records with 70-89% confidence (reviewed before applying)
- **Low confidence matches**: 117 (2.9%) — Candidates matching at 60-69% (manual review recommended)
- **Unmatched records**: 3,853 (97.1%) — No matching Blackbelt record found

## Key Findings

### 1. Low Match Rate Indicates Data Misalignment

The 97.1% unmatched rate suggests:
- Company inventory may contain devices **not yet tested in Blackbelt** (devices from different procurement batches, dealers, or time periods)
- IMEI column may be populated differently between systems (e.g., normalized vs. raw format)
- Possible different data sources or inventory systems

### 2. Low Confidence Matches (117 records)

These are brand-and-model candidates found despite IMEI mismatch:
- **Apple iPhone 11 Pro** → incorrectly paired with **iPhone 14 Pro** (different models)
- All 117 suggest company has outdated or incorrect model information
- IMEI differences indicate devices truly are different

### 3. ~3,853 Completely Unmatched

**Possible causes:**
- Devices in company inventory haven't been analyzed through Blackbelt yet
- IMEI format incompatibility (e.g., Garmin smartwatch shows as "5W9049039" vs Blackbelt format)
- Company inventory includes devices outside Blackbelt's testing scope
- Data synchronization lag

## Output Files Generated

| File | Records | Purpose |
|------|---------|---------|
| `low_confidence_matches.csv` | 117 | Fuzzy matches for analyst review |
| `unmatched.csv` | 3,853 | Records with no Blackbelt match |

## What the Columns Mean

### Decision Columns
- **decision**: `MANUAL_REVIEW` = human approval needed
- **correction_needed**: `YES` = conflicting brand/model data; `NO` = consistent
- **suggested_correction**: Specific change (e.g., "Update company IMEI from X to Y")

### Match Quality
- **confidence_score**: 0-100. Only scores ≥95 are auto-safe.
- **match_reason**: `exact_imei`, `exact_imei2` (alternate IMEI), or `fuzzy_model`
- **description**: Human-readable explanation

## Recommended Next Steps

### 1. Investigate Unmatched Records (~3,853)

**Option A: Check IMEI format**
```python
# Check if company IMEIs are in a different format
company_imei_sample = "5W9049039"  # Could be a device ID, not IMEI
blackbelt_imei = 868958071613954  # Standard 15-digit IMEI
# If you see this pattern, may need format conversion logic
```

**Option B: Verify data sources**
- Are company records from a different period or dealer than Blackbelt data?
- Do you receive inventory data **before** it's sent to Blackbelt?

**Option C: Check for upcoming device batches**
- If NorthLadder purchases devices in batches, unmatched records may be awaiting Blackbelt analysis

### 2. Review Low-Confidence Matches (117 records)

Use the review tool:
```bash
python review_and_apply.py --output-dir output --level low --summary
```

Then interactively approve/reject suggested corrections.

### 3. Enhance the Model

Current matching uses:
- Exact IMEI
- Brand + Model similarity
- Storage + Color attributes

Could add:
- **Barcode/QR matching** (both datasets have these)
- **Serial number matching**
- **Device grade** mapping
- **Device age** constraints
- **Batch/dealer** associations

### 4. Data Quality Audit

Check company data quality:
```python
# Quick audit
- How many company IMEIs are empty/null?
- How many have non-standard format?
- Are model names parsed from asset label or explicit field?
- Are color/storage consistently populated?
```

## Confidence Level Thresholds

| Threshold | Action | Rationale |
|-----------|--------|-----------|
| **≥95** | AUTO_CORRECT | High certainty, safe to apply immediately |
| **70-94** | REVIEW_THEN_APPLY | Likely correct, but human sign-off needed |
| **60-69** | MANUAL_REVIEW | Candidate match; analyst must investigate |
| **<60** | REJECT | Too low confidence; require manual research |

## Long-term Strategy

1. **Batch-wise alignment**: Ensure company batches align with Blackbelt batches
2. **Real-time linking**: Assign Blackbelt asset IDs (`AssetId`) to company records at point-of-entry
3. **Automated feeds**: Consider ETL pipeline to push NorthLadder inventory → Blackbelt  
4. **Duplicate detection**: Use model to identify when same IMEI appears multiple times across both datasets

---

**Generated**: April 11, 2026  
**Pipeline**: `blackbelt_mismatch_pipeline.py v1.0`  
**Records Processed**: 3,970 company vs. 367 Blackbelt
