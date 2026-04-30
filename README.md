# Blackbelt-NorthLadder Mismatch Detection Pipeline

Production-ready web application to detect and correct IMEI/model mismatches between Blackbelt device testing data and NorthLadder inventory.

## Features

✅ **Modern Web Interface**
- Drag-and-drop file upload
- Real-time progress tracking
- Interactive dashboard with charts
- Category-based error reporting
- Product age analysis

✅ **Intelligent Detection Engine**
- Exact IMEI matching
- Brand, model, and storage validation
- Grade mismatch detection
- Blackbelt reference checking
- Duplicate detection

✅ **Comprehensive Reporting**
- Brand mismatches
- Model mismatches
- Storage mismatches
- Grade mismatches
- Devices not in Blackbelt
- Product age distribution
- Clean rows (no issues)

✅ **Export Options**
- Download by category (Excel)
- Product age analysis
- Complete ZIP bundle
- Summary JSON

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run the Web Application

```bash
python app.py
```

Then open your browser to: **http://localhost:8000**

### Using the Web Interface

1. **Upload Files:**
   - Blackbelt Excel Report (required)
   - Stack Bulk Upload (required)
   - Master Template (optional)

2. **Start Analysis:**
   - Click "Start Analysis" button
   - Watch real-time progress

3. **View Results:**
   - See summary statistics
   - Review charts and breakdowns
   - Download category-specific reports

4. **Export Data:**
   - Download individual category files
   - Get product age analysis
   - Export everything as ZIP

## How It Works

### Detection Categories

**1. Brand Mismatch**
- Compares backend brand with Blackbelt's reading
- Flags discrepancies for correction

**2. Model Mismatch**
- Validates asset label against Blackbelt model
- Detects wrong model entries

**3. Storage Mismatch**
- Checks storage capacity consistency
- Identifies incorrect storage specifications

**4. Grade Mismatch**
- Compares backend grade with Blackbelt's automated grading
- Highlights grading inconsistencies

**5. Not in Blackbelt**
- Identifies devices with valid IMEI not found in Blackbelt
- May indicate untested devices or data sync issues

### Output Format

Each Excel report includes:

| Column | Description |
|--------|-------------|
| `Deal ID` | Unique transaction identifier |
| `IMEI` | Device IMEI number |
| `Blackbelt` | Data from Blackbelt reference |
| `Stack Bulk` | Data from inventory system |
| `Location` | Device location |
| `Stack ID` | Internal inventory ID |
| `VAT Type` | VAT classification |
| `Problem` | Issue description |
| `Field` | Affected field name |
| `Current Value` | Current incorrect value |

## API Endpoints

The application provides RESTful API endpoints:

- `GET /` - Web interface
- `POST /api/upload` - Upload files and start analysis
- `GET /api/job/{job_id}` - Check job status
- `GET /api/results/{job_id}` - Get analysis results
- `GET /api/download/{job_id}/{report_type}` - Download specific report
- `GET /api/export/{job_id}` - Download all results as ZIP

## Architecture

```
app.py                          # FastAPI web server
├── static/
│   ├── index.html             # Web interface
│   ├── app.js                 # Frontend logic
│   └── style.css              # Styling
├── mismatch_detector.py       # Core detection engine
├── blackbelt_mismatch_pipeline.py  # Pipeline logic
└── requirements.txt           # Dependencies
```

## Troubleshooting

### Port Already in Use

If port 8000 is busy:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Or change the port in app.py
uvicorn.run("app:app", host="0.0.0.0", port=8001)
```

### Excel Loading Errors

- Ensure files are valid XLSX format
- Check that required sheets exist
- Verify file permissions

### Processing Takes Too Long

- Large files (10,000+ rows) may take 2-3 minutes
- Progress bar shows real-time status
- Results are cached for repeated access

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
