# Quick Start Guide

## What You Have

A complete data mismatch detection system for NorthLadder, consisting of:

1. **mismatch_pipeline.py** — Compares your inventory (company data) against Blackbelt quality data
2. **review_and_apply.py** — Interface for analysts to approve/reject suggested corrections
3. **Output reports** — CSVs categorized by match confidence
4. **Documentation** — README, this guide, and findings summary

## Three Simple Steps

### Step 1: Run the Pipeline (2-5 minutes)

Place your two Excel files in a known location, then:

```bash
cd c:\Users\dharm\Desktop\Blackbelt
python blackbelt_mismatch_pipeline.py \
  --blackbelt "C:\path\to\Blackbelt.xlsx" \
  --company "C:\path\to\NorthLadder.xlsx" \
  --output output
```

**What happens:**
- Matches company records against Blackbelt data
- Finds 3 types of matches: exact IMEI, alternate IMEI, fuzzy model
- Generates 4 CSVs in `output/` folder

### Step 2: Check Summary (1 minute)

```bash
python review_and_apply.py --output-dir output --summary
```

**You'll see:**
```
High confidence matches: X (auto-safe to apply)
Medium confidence matches: Y (review before applying)
Low confidence matches: Z (manual investigation)
Unmatched: W (no Blackbelt record)
```

### Step 3: Review & Approve (5-30 minutes depending on quantity)

For low-confidence matches:
```bash
python review_and_apply.py --output-dir output --level low
```

For each record, you'll see:
- Company data (current)
- Blackbelt data (what we found)
- Suggested correction
- Confidence score

Then decide: **A**pprove, **R**eject, **S**kip, or **Q**uit

Output: `corrections_low.csv` with your approvals

## Example Workflow

Below is a real example from your April 11, 2026 data run:

### Scenario 1: Low-Confidence Match (60.1%)

```
Company Record:
  IMEI: 353243101331899
  Model: Apple iPhone 11 Pro (2019) 256GB
  Color: (not specified)

Blackbelt Record:
  IMEI: 355780877026128
  Model: Apple iPhone 14 Pro
  Color: Black

Suggested Correction:
  Update company IMEI from 353243101331899 to 355780877026128

Your Decision: 
  REVIEW — Model mismatch (11 Pro vs 14 Pro) suggests different device.
  Reject the correction.
```

### Scenario 2: Unmatched Record (0%)

```
Company Record:
  IMEI: 5W9049039
  Model: Garmin Forerunner 945 (47mm)
  Storage: (smartwatch, no storage)

Blackbelt Record:
  (none found)

Suggested Correction:
  Manual research required

Your Decision:
  INVESTIGATE — Check if:
    - IMEI format is correct (doesn't look like standard IMEI)
    - Device has been sent to Blackbelt yet
    - Device is in a different Blackbelt batch
```

## Understanding Your Results

### Why 97% unmatched?

If most records are unmatched, likely causes are:

1. **IMEI format issue**
   - Company: `5W9049039` (looks like device ID)
   - Blackbelt: `868958071613954` (standard 15-digit IMEI)
   - **Fix**: Verify IMEI column contains actual IMEI, not device ID

2. **Data source lag**
   - Your inventory system may receive devices before they're tested in Blackbelt
   - **Fix**: Sync timing — ensure company records match Blackbelt's testing schedule

3. **Different batches/dealers**
   - Company may purchase from different suppliers than devices tested in Blackbelt
   - **Fix**: Add dealer/batch metadata to match by source

4. **Time period mismatch**
   - Blackbelt = tested devices (may be older)
   - Company = recently purchased devices
   - **Fix**: Filter to same time period

### What does "correction_needed" mean?

- **YES** = Brand or model differs between systems → potential error
- **NO** = Data is consistent → safer to apply
- **N/A** = No match found → nothing to correct

## Common Corrections

| Correction Type | How Often | Priority |
|---|---|---|
| IMEI differs, brand/model same | Rare but safe | HIGH |
| Brand/model differs, IMEI same | Indicates error | HIGH |
| All attributes differ | Data not related | LOW — reject |
| IMEI2 present in Blackbelt | Alternate IMEI scanned | HIGH — apply |

## File Locations

After running, you'll have:

```
c:\Users\dharm\Desktop\Blackbelt\
├── output/
│   ├── high_confidence_matches.csv    (if any found)
│   ├── medium_confidence_matches.csv  (if any found)
│   ├── low_confidence_matches.csv     (fuzzy candidates)
│   ├── unmatched.csv                  (no match)
│   ├── corrections_high.csv           (if reviewed)
│   ├── corrections_medium.csv         (if reviewed)
│   └── corrections_low.csv            (if reviewed)
├── blackbelt_mismatch_pipeline.py     (main script)
├── review_and_apply.py                (review tool)
├── README.md                          (full docs)
└── RESULTS_SUMMARY.md                 (findings from this run)
```

## Applying Corrections

Once you've approved corrections in `corrections_*.csv`:

1. **Export to your system**
   - Most inventory systems support bulk update via CSV
   - Map `suggested_correction` column to your system's update format

2. **Example SQL** (if using database):
   ```sql
   UPDATE company_inventory 
   SET imei = 'new_imei' 
   WHERE asset_id = 'company_row_index'
   ```

3. **Example Python** (if using dataframe):
   ```python
   corrections = pd.read_csv('corrections_low.csv')
   for _, row in corrections.iterrows():
       inventory.loc[inventory.index == row['company_row_index'], 'imei'] = row['to_imei']
   ```

## Troubleshooting

### "Command not found: python"

Make sure you're in the Blackbelt directory:
```bash
cd c:\Users\dharm\Desktop\Blackbelt
```

Or use full path:
```bash
c:\Users\dharm\AppData\Local\Programs\Python\Python313\python.exe blackbelt_mismatch_pipeline.py ...
```

### Excel loading errors

The pipeline handles most Excel issues automatically. If it still fails:
- Verify file path is correct
- Check file is not open in Excel
- Try exporting as fresh XLSX if file is corrupted

### "No matches found"

Likely the two datasets don't overlap. See "Why 97% unmatched?" above.

## Next: Scaling Up

Once you've validated the process:

1. **Automate**: Schedule weekly pipeline runs
2. **Monitor**: Track correction success rate over time
3. **Enhance**: Add barcode/QR/serial matching
4. **Integrate**: Push Blackbelt `AssetId` back to company system for permanent linking

---

**Questions?** Check [README.md](README.md) or [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md)

**Need help?** Examine sample output CSVs — column names are self-explanatory.
