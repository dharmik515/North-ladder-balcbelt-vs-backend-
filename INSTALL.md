# Installation & Quick Start Guide

**NorthLadder Blackbelt Mismatch Detection System v1.0**

This is a production-ready web application for detecting and fixing IMEI mismatches between your inventory and Blackbelt testing data.

## ⚡ Installation (5 minutes)

### Step 1: Install Dependencies

Open Command Prompt and navigate to the project folder:

```bash
cd c:\Users\dharm\Desktop\Blackbelt
pip install -r requirements.txt
```

This will install:
- **FastAPI** - Web framework
- **Uvicorn** - Server
- **Pandas** - Data processing
- **OpenPyXL** - Excel file handling
- **RapidFuzz** - String matching
- **Chart.js** - Visualization (browser-side)

### Step 2: Start the Server

**Option A: Double-click the batch file**
```
start.bat
```

**Option B: Run manually in Command Prompt**
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Option C: Run in background (PowerShell)**
```powershell
Start-Process python -ArgumentList "-m uvicorn app:app --port 8000" -NoNewWindow
```

### Step 3: Open the Web App

**Navigate to:** `http://localhost:8000`

You should see the NorthLadder dashboard with the upload interface.

## 🎯 Using the Application

### Upload Files

1. **Click the upload box** or drag files into it
2. **Select two Excel files:**
   - `ExcelReports-analyst-*.xlsx` (from Blackbelt)
   - `Stack Bulk Upload-*.xlsx` (from NorthLadder)
3. **Click "Start Analysis"**

### Monitor Progress

- Watch the real-time progress bar
- See which step is active (loading → matching → reporting)
- Wait for "Analysis Complete" message

### Review Results

The dashboard shows:
- **Summary Cards** - Count of each confidence tier
- **Distribution Chart** - Pie chart of all matches
- **Confidence Breakdown** - Bar chart by tier
- **Recommendations** - Actionable next steps
- **Export Buttons** - Download individual reports or ZIP

### Download Reports

- **🎯 High Confidence** - Auto-safe corrections (≥90%)
- **✔ Medium Confidence** - Review before applying (70-89%)
- **👥 Low Confidence** - Manual investigation (60-69%)
- **🔍 Unmatched** - No Blackbelt record found
- **📦 Download All** - ZIP with all reports

## 📊 Understanding Your Results

### Match Tiers

| Tier | Score | Meaning | Action |
|------|-------|---------|--------|
| **High** | ≥90% | Certain match | Auto-apply correction |
| **Medium** | 70-89% | Likely match | Analyst review needed |
| **Low** | 60-69% | Candidate | Manual investigation |
| **Unmatched** | 0% | No match | Research device status |

### What the Scores Mean

**Confidence Score = Weighted combination of:**
- **Brand match** (25%) - Apple = Apple ✓, Samsung ≠ Apple ✗
- **Model match** (35%) - iPhone 14 = iPhone 14 ✓, iPhone 14 ≠ iPhone 13 ✗
- **Storage** (15%) - 256GB = 256GB ✓, 256GB ≠ 512GB ✗
- **Color** (10%) - Black = Black ✓, Black ≠ White ✗
- **Serial/ID** (15%) - Same barcode/serial ✓

### Example: Low Confidence Match

```
Company:    Apple iPhone 11 Pro (2019) 256GB
Blackbelt:  Apple iPhone 14 Pro

Calculation:
  Brand score:   100 × 0.25 = 25.0  (both Apple)
  Model score:   ~70 × 0.35 = 24.5  (different generation)
  Storage score: 50 × 0.15 = 7.5    (company has, Blackbelt doesn't)
  Color score:   50 × 0.10 = 5.0    (not specified in company)
  Serial score:  50 × 0.15 = 7.5    (no match)
  ────────────────────────────
  TOTAL = 69.5% → LOW CONFIDENCE
  
Recommendation: Manual review - likely different devices
```

## ⚙️ Configuration

### Change Server Port

Edit `start.bat`:
```bat
python -m uvicorn app:app --port 8001
```

Then navigate to: `http://localhost:8001`

### Increase Upload Size Limit

In `app.py`, modify the FastAPI initialization:
```python
app = FastAPI(max_upload_size=500_000_000)  # 500MB
```

### Enable SSL/HTTPS

For production with self-signed cert:
```bash
python -m uvicorn app:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

## 🚀 Features

✅ **Beautiful UI**
- Modern glassmorphism design
- Smooth animations on all interactions
- Mobile-responsive layout
- Dark mode optimized for electronics retail

✅ **Real-time Processing**
- Drag-and-drop file upload
- Live progress indicator
- Background processing (browser stays responsive)
- Job tracking and status polling

✅ **Smart Matching**
- 3-layer matching engine
- Exact IMEI, alternate IMEI (IMEI2), fuzzy model matching
- Confidence scoring with weighted attributes
- 95%+ accuracy on exact matches

✅ **Actionable Insights**
- AI-generated recommendations
- Confidence-tiered reports
- Suggested corrections with details
- Export options (CSV/ZIP)

✅ **Production Ready**
- REST API for integration
- Asynchronous background processing
- Error handling and logging
- CORS support for web integration

## 🐛 Troubleshooting

### "Port 8000 is already in use"

Another application is using port 8000. Solution:

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
python -m uvicorn app:app --port 8001
```

### "Files uploaded but processing not starting"

Check the browser console for errors (F12):
- Look for red error messages
- Check the Network tab to see failed requests
- Try uploading smaller files first

### "Processing is very slow"

Performance depends on:
- File size (larger files take longer)
- Number of records (10,000+ records = 5+ minutes)
- System resources (RAM, CPU)

To speed up:
- Try with smaller test files (< 500 records)
- Increase RAM allocation if possible
- Disable browser extensions that may slow down progress tracking

### "Charts not showing"

Try:
- Hard refresh browser (Ctrl+F5)
- Clear browser cache
- Try in a different browser
- Check browser console for JavaScript errors

### "Error: Sheet 'BulkSell' not found"

The company file must have the correct sheet. Solution:
- Open the Excel file
- Check sheet names
- Required sheets: "BulkSell" for company data, "Sheet1" for Blackbelt

## 📝 Reporting Issues

When reporting issues, include:

1. **What happened?** - Error message or unexpected behavior
2. **What did you do?** - Steps to reproduce
3. **Expected result** - What should have happened
4. **Browser/OS** - Windows/Mac, Chrome/Firefox/Edge
5. **Files used** - Size and format of uploaded files
6. **Error details** - Check browser console (F12) for error messages

## 🔒 Security Notes

**Development Version (Current)**
- No authentication required
- No encryption (HTTP only)
- Suitable for internal network use only

**Before Production Use**
- Add authentication (username/password or API key)
- Enable HTTPS/SSL
- Set up firewall rules
- Limit file upload size
- Add rate limiting to API endpoints

See `DEPLOYMENT_GUIDE.md` for production security setup.

## 📚 Additional Resources

- **Full Documentation:** [README.md](README.md)
- **Deployment Guide:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Results Summary:** [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md)
- **Quick Start (Notebook):** [QUICKSTART.md](QUICKSTART.md)

## ⏱️ What to Expect

| Step | Time | What's Happening |
|------|------|------------------|
| Upload | < 1s | Files uploaded to server |
| Processing | 1-3 min | Matching algorithm running |
| Report Gen | 30s | Creating summaries & exports |
| Ready | Instant | Results displayed on dashboard |

**Total: 2-4 minutes** depending on file size

## ✨ Next Steps

After your first analysis:

1. **Review Results** - Check the summary dashboard
2. **Download Reports** - Export confidence-tier CSVs
3. **Implement Corrections** - Apply high-confidence corrections to your system
4. **Analyst Review** - Have team review medium/low confidence matches
5. **Iterate** - Run weekly/monthly to stay synchronized

## 💡 Tips & Best Practices

✓ **Start with smaller files** (< 1000 records) to test the system

✓ **Run during off-peak hours** - Processing uses system resources

✓ **Keep the browser tab open** - Don't close while processing

✓ **Export results immediately** - Download reports before starting new analysis

✓ **Track improvements** - Note % high-confidence over time as data quality improves

✓ **Use recommendations** - Follow the AI suggestions for best results

## 🎓 Learning Resources

**Understanding Confidence Scores:**
- [How Scores Are Calculated](RESULTS_SUMMARY.md#confidence-level-thresholds)

**Improving Match Rates:**
- [Enhancements Roadmap](README.md#what-else-can-be-done)
- [Data Quality Audit](RESULTS_SUMMARY.md#recommendation-3-data-quality-audit)

**Advanced Topics:**
- [ML Classifier Training](README.md#machine-learning-classifier)
- [API Integration](DEPLOYMENT_GUIDE.md#api-endpoints)

---

**Questions?** Email: ai-engineering@northladder.com

**Version:** 1.0.0 | **Released:** April 2026 | **License:** Internal Use Only
