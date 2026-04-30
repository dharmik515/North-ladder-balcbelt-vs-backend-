/**
 * NorthLadder Mismatch Detection System - Frontend
 * Handles file uploads, real-time progress, and results visualization
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Blackbelt system...');
    
// ============================================================================
// Global State
// ============================================================================

let currentJobId = null;
let uploadedFiles = {
    blackbelt: false,
    master: false,
    stack: false,
};
let statusPolling = null;

// ============================================================================
// DOM Elements
// ============================================================================

const uploadBox = document.getElementById('uploadBox');
const uploadForm = document.getElementById('uploadForm');
const blackbeltInput = document.getElementById('blackbeltFile');
const masterInput    = document.getElementById('masterFile');
const stackInput     = document.getElementById('stackFile');
const uploadBtn = document.getElementById('uploadBtn');
const fileStatus = document.getElementById('fileStatus');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');

const heroSection = document.getElementById('hero');
const processingSection = document.getElementById('processing');
const resultsSection = document.getElementById('results');

const progressBar = document.getElementById('progressBar');
const progressLabel = document.getElementById('progressLabel');
const progressPercent = document.getElementById('progressPercent');
const loadingOverlay = document.getElementById('loadingOverlay');

// ============================================================================
// EVENT LISTENERS
// ============================================================================

// File selection buttons
const selectBlackbeltBtn = document.getElementById('selectBlackbeltBtn');
const selectMasterBtn    = document.getElementById('selectMasterBtn');
const selectStackBtn     = document.getElementById('selectStackBtn');

selectBlackbeltBtn.addEventListener('click', function(e) {
    e.preventDefault();
    blackbeltInput.click();
});
selectMasterBtn.addEventListener('click', function(e) {
    e.preventDefault();
    masterInput.click();
});
selectStackBtn.addEventListener('click', function(e) {
    e.preventDefault();
    stackInput.click();
});

// Drag and drop on upload box
uploadBox.addEventListener('click', () => {
    // Allow clicking on the box for file selection
});

uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = '#00ffff';
    uploadBox.style.background = 'rgba(0, 212, 255, 0.1)';
});

uploadBox.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = '';
    uploadBox.style.background = '';
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = '';
    uploadBox.style.background = '';
    
    const files = e.dataTransfer.files;
    handleDroppedFiles(files);
});

blackbeltInput.addEventListener('change', handleBlackbeltSelect);
masterInput.addEventListener('change', handleMasterSelect);
stackInput.addEventListener('change', handleStackSelect);
uploadBtn.addEventListener('click', handleUpload);
if (newAnalysisBtn) {
    newAnalysisBtn.addEventListener('click', resetUI);
}

// ============================================================================
// File Handling
// ============================================================================

function _markSelected(slot, file, labelEl, checkEl, prefix) {
    uploadedFiles[slot] = true;
    labelEl.textContent = `${prefix}: ${file.name}`;
    checkEl.textContent = '✓';
    checkEl.style.color = '#51cf66';
    fileStatus.style.display = 'flex';
    console.log('File selected:', slot, 'uploadedFiles:', uploadedFiles);
    updateUploadButton();
}

function handleBlackbeltSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    _markSelected('blackbelt', file,
        document.getElementById('blackbeltName'),
        document.getElementById('blackbeltCheck'),
        'Blackbelt');
}

function handleMasterSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    _markSelected('master', file,
        document.getElementById('masterName'),
        document.getElementById('masterCheck'),
        'Master Template');
}

function handleStackSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    _markSelected('stack', file,
        document.getElementById('stackName'),
        document.getElementById('stackCheck'),
        'Stack Bulk');
}

function handleDroppedFiles(files) {
    // Route by filename hints into the three explicit slots.
    for (let file of files) {
        const n = file.name;
        if (!uploadedFiles.blackbelt && (n.includes('Blackbelt') || n.includes('ExcelReports'))) {
            const dt = new DataTransfer(); dt.items.add(file);
            blackbeltInput.files = dt.files;
            handleBlackbeltSelect({ target: { files: dt.files } });
        } else if (!uploadedFiles.stack && (n.includes('Stack') || n.includes('Upload') || n.includes('BulkSell'))) {
            const dt = new DataTransfer(); dt.items.add(file);
            stackInput.files = dt.files;
            handleStackSelect({ target: { files: dt.files } });
        } else if (!uploadedFiles.master && (n.includes('Master') || n.includes('StockTake'))) {
            const dt = new DataTransfer(); dt.items.add(file);
            masterInput.files = dt.files;
            handleMasterSelect({ target: { files: dt.files } });
        }
    }
}

function updateUploadButton() {
    // Required: Blackbelt + Stack Bulk. Master Template is optional.
    console.log('updateUploadButton called. uploadedFiles:', uploadedFiles);
    console.log('blackbelt:', uploadedFiles.blackbelt, 'stack:', uploadedFiles.stack);
    if (uploadedFiles.blackbelt && uploadedFiles.stack) {
        uploadBtn.disabled = false;
        uploadBtn.style.cursor = 'pointer';
        console.log('Button enabled!');
    } else {
        uploadBtn.disabled = true;
        uploadBtn.style.cursor = 'not-allowed';
        console.log('Button disabled - missing required files');
    }
}

// ============================================================================
// Upload & Processing
// ============================================================================

async function handleUpload() {
    if (!uploadedFiles.blackbelt || !uploadedFiles.stack) {
        alert('Please select the Blackbelt file and Stack Bulk Upload (Master Template is optional)');
        return;
    }

    const formData = new FormData();
    formData.append('blackbelt_file', blackbeltInput.files[0]);
    // Stack Bulk is the primary "company" input for the detector.
    formData.append('company_file',   stackInput.files[0]);
    if (uploadedFiles.master && masterInput.files[0]) {
        formData.append('stack_file', masterInput.files[0]);
    }
    
    try {
        loadingOverlay.style.display = 'flex';
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentJobId = data.job_id;
            showProcessing();
            startStatusPolling();
        } else {
            alert('Upload failed: ' + data.detail);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Upload failed: ' + error.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

function showProcessing() {
    heroSection.classList.add('hidden');
    processingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
}

function startStatusPolling() {
    statusPolling = setInterval(async () => {
        try {
            const response = await fetch(`/api/job/${currentJobId}`);
            const job = await response.json();
            
            updateProgressUI(job);
            
            if (job.status === 'completed' || job.status === 'failed') {
                clearInterval(statusPolling);
                
                if (job.status === 'completed') {
                    setTimeout(() => showResults(job.results), 1000);
                } else {
                    // Clean up error message (remove newlines, extra spaces)
                    const cleanError = (job.error || 'Unknown error').replace(/[\n\r]/g, ' ').trim();
                    console.error('Processing error:', cleanError);
                    alert('Processing failed:\n\n' + cleanError);
                    resetUI();
                }
            }
        } catch (error) {
            console.error('Status polling error:', error);
        }
    }, 500);
}

function updateProgressUI(job) {
    const progress = job.progress;
    progressBar.style.width = progress + '%';
    progressPercent.textContent = progress + '%';
    
    // Update step indicators and labels
    if (progress < 50) {
        progressLabel.textContent = 'Loading and normalizing data...';
        updateSteps([true, true, false, false]);
    } else if (progress < 80) {
        progressLabel.textContent = 'Matching records against Blackbelt database...';
        updateSteps([true, true, true, false]);
    } else {
        progressLabel.textContent = 'Generating reports and insights...';
        updateSteps([true, true, true, true]);
    }
}

function updateSteps(states) {
    const steps = document.querySelectorAll('.step');
    steps.forEach((step, idx) => {
        step.classList.remove('active');
        if (states[idx]) {
            step.classList.add('completed');
        }
    });
    if (states.filter(s => s).length < states.length) {
        steps[states.filter(s => s).length].classList.add('active');
    }
}

// ============================================================================
// Results Display
// ============================================================================

function showResults(results) {
    processingSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');
    
    // Update timestamp
    const date = new Date(results.processed_at);
    document.getElementById('timestamp').textContent = 
        `Processed on ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}`;
    
    // Update summary cards
    const matches = results.matches;
    document.getElementById('totalCount').textContent = results.total_processed;
    document.getElementById('unmatchedCount').textContent = matches.unmatched.count;
    
    // Update model difference breakdown
    const modelDiff = results.model_difference_breakdown || {brand_only: 0, model_only: 0, storage_only: 0};
    document.getElementById('brandOnlyCount').textContent = modelDiff.brand_only;
    document.getElementById('modelOnlyCount').textContent = modelDiff.model_only;
    document.getElementById('storageOnlyCount').textContent = modelDiff.storage_only;
    
    // Update additional metrics
    document.getElementById('gradeMismatchCount').textContent = results.categories.grade_mismatch.count;
    document.getElementById('notInBlackbeltCount').textContent = results.categories.not_in_blackbelt.count;
    
    // Create charts (Stack comparison and Age distribution only)
    createCharts(matches, results);
    
    // Setup age bucket selector
    setupAgeBucketSelector(results.product_age);
    
    // Update action buttons
    setupDownloadButtons();
    
    // Update insights
    updateInsights(results);
    
    // Scroll to results
    setTimeout(() => {
        document.querySelector('.results-header').scrollIntoView({ behavior: 'smooth' });
    }, 100);
}

const BUCKET_LABELS = {
    verified:  '🚨 Confirmed Error',
    likely:    '⚠ Likely Error',
    uncertain: '🔎 Advisory',
    summary:   '📊 Overall',
};

function displayRecommendations(recommendations) {
    const list = document.getElementById('recommendationsList');
    list.innerHTML = '';

    recommendations.forEach((rec, idx) => {
        // Backward-compat: older summary.json files had plain strings.
        const text   = typeof rec === 'string' ? rec : rec.text;
        const bucket = typeof rec === 'string' ? 'summary' : (rec.bucket || 'summary');

        const item = document.createElement('div');
        item.className = `recommendation-item rec-${bucket}`;
        item.style.animationDelay = `${idx * 0.1}s`;

        const pill = document.createElement('span');
        pill.className = `rec-bucket-pill pill-${bucket}`;
        pill.textContent = BUCKET_LABELS[bucket] || bucket;

        const textEl = document.createElement('span');
        textEl.className = 'rec-text';
        textEl.textContent = text;

        item.appendChild(pill);
        item.appendChild(textEl);
        list.appendChild(item);
    });
}

function createCharts(matches, results) {
    // Stack vs Model Comparison Chart - showing all flagged devices
    const wrongModel = results.wrong_model_comparison || {total_mismatches: 0, already_flagged_in_stack: 0};
    const stackCtx = document.getElementById('stackComparisonChart').getContext('2d');
    new Chart(stackCtx, {
        type: 'bar',
        data: {
            labels: ['Total Flagged Devices', 'Already Flagged in Stack'],
            datasets: [{
                label: 'Device Count',
                data: [wrongModel.total_mismatches, wrongModel.already_flagged_in_stack],
                backgroundColor: ['#ff922b', '#00d4ff'],
                borderRadius: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#e0e0e0' },
                    grid: { color: '#1a1a2e' },
                },
                x: {
                    ticks: { color: '#e0e0e0' },
                    grid: { color: '#1a1a2e' },
                },
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y + ' devices';
                        }
                    }
                }
            },
        },
    });
    
    // Age Distribution Chart (Line Chart)
    const ageDist = results.product_age?.distribution || {'0-3mo': 0, '3-6mo': 0, '6-12mo': 0, '12+mo': 0};
    const ageCtx = document.getElementById('ageDistributionChart').getContext('2d');
    new Chart(ageCtx, {
        type: 'line',
        data: {
            labels: ['0-3 months', '3-6 months', '6-12 months', '12+ months'],
            datasets: [{
                label: 'Number of Devices',
                data: [ageDist['0-3mo'], ageDist['3-6mo'], ageDist['6-12mo'], ageDist['12+mo']],
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBackgroundColor: '#00d4ff',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#e0e0e0' },
                    grid: { color: '#1a1a2e' },
                },
                x: {
                    ticks: { color: '#e0e0e0' },
                    grid: { color: '#1a1a2e' },
                },
            },
            plugins: {
                legend: {
                    labels: { color: '#e0e0e0' },
                },
            },
        },
    });
}

function setupDownloadButtons() {
    document.getElementById('downloadBrandBtn').onclick = (e) => {
        e.preventDefault();
        downloadCategoryReport('brand_mismatch');
    };
    document.getElementById('downloadModelBtn').onclick = (e) => {
        e.preventDefault();
        downloadCategoryReport('model_mismatch');
    };
    document.getElementById('downloadStorageBtn').onclick = (e) => {
        e.preventDefault();
        downloadCategoryReport('storage_mismatch');
    };
    document.getElementById('downloadGradeBtn').onclick = (e) => {
        e.preventDefault();
        downloadCategoryReport('grade_mismatch');
    };
    document.getElementById('downloadNotInBlackbeltBtn').onclick = (e) => {
        e.preventDefault();
        downloadCategoryReport('not_in_blackbelt');
    };
    document.getElementById('downloadAllBtn').onclick = (e) => {
        e.preventDefault();
        downloadAllReports();
    };
}

function downloadCategoryReport(category) {
    const link = document.createElement('a');
    link.href = `/api/download/${currentJobId}/${category}`;
    link.download = `${category}_${currentJobId}.xlsx`;
    link.click();
}

function downloadAllReports() {
    const link = document.createElement('a');
    link.href = `/api/export/${currentJobId}`;
    link.download = `mismatch_results_${currentJobId}.zip`;
    link.click();
}

function setupAgeBucketSelector(productAge) {
    if (!productAge) return;
    
    const bucketTypeSelect = document.getElementById('bucketTypeSelect');
    const bucketValueSelect = document.getElementById('bucketValueSelect');
    const downloadBtn = document.getElementById('downloadAgeBucketBtn');
    
    // Store the product age data globally for access
    window.productAgeData = productAge;
    
    // Update bucket values when type changes
    bucketTypeSelect.addEventListener('change', function() {
        const type = this.value;
        bucketValueSelect.innerHTML = '<option value="">Select period...</option>';
        
        let buckets = [];
        if (type === 'monthly') {
            buckets = productAge.monthly || [];
        } else if (type === 'quarterly') {
            buckets = productAge.quarterly || [];
        } else if (type === 'semi_annual') {
            buckets = productAge.semi_annual || [];
        } else if (type === 'annual') {
            buckets = productAge.annual || [];
        }
        
        // Sort buckets in reverse chronological order (newest first)
        buckets.sort((a, b) => b.bucket.localeCompare(a.bucket));
        
        buckets.forEach(item => {
            const option = document.createElement('option');
            option.value = item.bucket;
            option.textContent = `${item.bucket} (${item.count} devices)`;
            bucketValueSelect.appendChild(option);
        });
        
        downloadBtn.disabled = true;
    });
    
    // Enable download button when value is selected
    bucketValueSelect.addEventListener('change', function() {
        downloadBtn.disabled = !this.value;
    });
    
    // Handle download
    downloadBtn.addEventListener('click', function() {
        const bucketType = bucketTypeSelect.value;
        const bucketValue = bucketValueSelect.value;
        
        if (!bucketValue) {
            alert('Please select a time period');
            return;
        }
        
        const link = document.createElement('a');
        link.href = `/api/download_age/${currentJobId}/${bucketType}/${encodeURIComponent(bucketValue)}`;
        link.click();
    });
    
    // Trigger initial load
    bucketTypeSelect.dispatchEvent(new Event('change'));
}

function updateInsights(results) {
    const total = results.total_processed;
    const matches = results.matches;
    const confirmedPct = ((matches.high_confidence.count / total) * 100).toFixed(1);
    const likelyPct    = ((matches.medium_confidence.count / total) * 100).toFixed(1);
    const advisoryPct  = ((matches.low_confidence.count / total) * 100).toFixed(1);
    const cleanPct     = ((matches.unmatched.count / total) * 100).toFixed(1);
    const flaggedPct   = (100 - parseFloat(cleanPct)).toFixed(1);

    let quality;
    if (flaggedPct < 10)      quality = 'Excellent';
    else if (flaggedPct < 25) quality = 'Good';
    else if (flaggedPct < 50) quality = 'Needs review';
    else                      quality = 'Widespread issues';

    document.getElementById('dataQuality').innerHTML = `
        <strong>${quality}</strong> data quality — ${flaggedPct}% of rows were flagged.<br>
        <span style="color: #a0a0a0; font-size: 0.9rem;">
            ${confirmedPct}% confirmed errors, ${likelyPct}% likely errors,
            ${advisoryPct}% advisory, ${cleanPct}% clean
        </span>
    `;
}

// ============================================================================
// Reset
// ============================================================================

function resetUI() {
    currentJobId = null;
    uploadedFiles = { blackbelt: false, master: false, stack: false };

    heroSection.classList.remove('hidden');
    processingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');

    blackbeltInput.value = '';
    masterInput.value    = '';
    stackInput.value     = '';
    document.getElementById('blackbeltName').textContent = 'Blackbelt: Not selected';
    document.getElementById('stackName').textContent     = 'Stack Bulk: Not selected';
    document.getElementById('masterName').textContent    = 'Master Template: Not selected (optional)';
    document.getElementById('blackbeltCheck').textContent = '○';
    document.getElementById('stackCheck').textContent     = '○';
    document.getElementById('masterCheck').textContent    = '○';
    document.getElementById('blackbeltCheck').style.color = '';
    document.getElementById('stackCheck').style.color     = '';
    document.getElementById('masterCheck').style.color    = '';
    fileStatus.style.display = 'none';
    uploadBtn.disabled = true;

    if (statusPolling) clearInterval(statusPolling);

    window.scrollTo(0, 0);
}

}); // End of main DOMContentLoaded

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Mismatch Detection UI loaded');
});
