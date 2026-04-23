# Blackbelt-NorthLadder Mismatch Detection Pipeline

Production-ready pipeline to detect and correct IMEI/model mismatches between Blackbelt device testing data and NorthLadder inventory.

## Features

✅ **Three-layer matching engine**
- Exact IMEI matching
- Alternate IMEI (`IMEI2`) detection  
- Fuzzy brand/model/spec matching

✅ **Confidence-tiered reporting**
- High confidence (≥90%) — auto-safe corrections
- Medium confidence (70-89%) — review before applying
- Low confidence (60-69%) — manual investigation
- Unmatched — no Blackbelt record found

✅ **Analyst review interface**
- Interactive decision tool
- Correction script generation
- Summary statistics

✅ **Robust Excel parsing**
- Handles corrupted Excel validation rules
- Supports both Blackbelt and company file formats
- Fallback loaders

## Files

| File | Purpose |
|------|---------|
| `blackbelt_mismatch_pipeline.py` | Main matching engine |
| `review_and_apply.py` | Analyst review & correction tool |
| `requirements.txt` | Python dependencies |
| `RESULTS_SUMMARY.md` | This run's findings & recommendations |
| `output/` | Generated CSV reports |

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Run the Pipeline

```bash
python blackbelt_mismatch_pipeline.py \
  --blackbelt "C:/path/to/Blackbelt.xlsx" \
  --company "C:/path/to/NorthLadder.xlsx" \
  --output output
```

**Output**: 4 CSV files in `output/`
- `high_confidence_matches.csv` (if any found)
- `medium_confidence_matches.csv` (if any found)  
- `low_confidence_matches.csv` (fuzzy candidates)
- `unmatched.csv` (no match found)

### 2. View Summary

```bash
python review_and_apply.py --output-dir output --summary
```

Prints match statistics:
```
=== MATCHING SUMMARY ===
High Confidence Matches: 0 (0.0%)
Medium Confidence Matches: 0 (0.0%)
Low Confidence Matches: 117 (2.9%)
Unmatched: 3,853 (97.1%)
Total Records: 3,970
```

### 3. Review & Approve Corrections

Interactive mode — approve or reject suggested corrections:

```bash
python review_and_apply.py --output-dir output --level low
```

For each record, choose:
- `A` = Approve correction
- `R` = Reject  
- `S` = Skip to next
- `Q` = Quit

Output: `corrections_low.csv` with approved corrections

## How It Works

### Matching Algorithm

**Layer 1: Exact IMEI (100% confidence)**
```
IF company.IMEI == Blackbelt.IMEI
  → MATCH (return immediately)
```

**Layer 2: Alternate IMEI (100% confidence, indicates human error)**
```
IF company.IMEI == Blackbelt.IMEI2
  → MATCH (likely scanned wrong IMEI)
```

**Layer 3: Fuzzy Matching (≥60% confidence)**
```
FOR each Blackbelt record:
  IF brand_similarity ≥ 40% AND 
     (storage matches OR not specified) AND
     computed_score ≥ 60%
    → CANDIDATE (return top match)
```

### Scoring Formula

Weighted attributes:
- Brand match: 25%
- Model match: 35%
- Storage match: 15%
- Color match: 10%
- Serial/ID match: 15%

## Output Format

Each report CSV includes:

| Column | Meaning |
|--------|---------|
| `decision` | `AUTO_CORRECT`, `REVIEW`, or `MANUAL_REVIEW` |
| `confidence_score` | 0-100 match quality |
| `match_reason` | `exact_imei`, `exact_imei2`, `fuzzy_model`, `no_match` |
| `correction_needed` | `YES` if data conflicts; `NO` if consistent |
| `suggested_correction` | Specific change to apply |
| `company_*` | Current data in NorthLadder |
| `blackbelt_*` | Matching record from Blackbelt |

## Common Issues

### 97%+ Unmatched Records?

Likely causes:
1. **IMEI format mismatch** — Check if company uses different identifier (device ID vs IMEI)
2. **Data source lag** — Company inventory may not have been sent to Blackbelt yet
3. **Different time periods** — Blackbelt data = tested devices; Company = recently purchased
4. **Dealer/batch isolation** — Different inventory sources

**Resolution**: See `RESULTS_SUMMARY.md` for investigation steps

### Pipeline Runs Slowly?

The algorithm filters candidates before fuzzy matching:
- Brand similarity ≥40% (required)
- Storage must match exactly (if present)
- Only top 10,000 Blackbelt records evaluated per company record

To optimize further, can:
- Increase brand similarity threshold
- Pre-group by device category
- Use serial/barcode matching first

### Excel Loading Errors?

Pipeline includes fallback handlers for corrupted validation rules (common in automated exports). If still failing, verify:
- File is valid XLSX
- Sheet name is correct
- For company file, check BulkSell sheet exists

## Advanced: Custom Matching

Extend the pipeline by modifying `find_matches()` or `compute_match_score()`:

```python
def compute_match_score(company, blackbelt, match_type):
    score = 0.0
    # Add your custom matching logic
    if company.serial == blackbelt.serial:
        score += 30.0
    return score
```

## Data Fields Extracted

### From Blackbelt
- `IMEI/MEID` (primary ID)
- `IMEI2` (alternate, if dual-SIM)
- `Manufacturer`, `Model`, `Model Number`
- `Device Colour`, `Serial Number`
- `Handset Memory Size`

### From NorthLadder
- `IMEI Number` (primary ID)
- `Brand`, `Asset Label`
- `Barcode`, `QR Code`
- `Sell Grade`, `Latest Assessed Grade`
- Parsed storage & color from `Asset Label`

## Future Enhancements

- [ ] Barcode/QR code matching
- [ ] Machine learning classifier (logistic regression, XGBoost)
- [ ] Real-time monitoring dashboard
- [ ] Batch processing with progress tracking
- [ ] Database backend (PostgreSQL) for large-scale reconciliation
- [ ] API endpoint for real-time IMEI lookup
- [ ] Ethereum-style audit trail for corrections

## License

Internal use only. NorthLadder, 2026.

"# North-ladder-balcbelt-vs-backend-" 
