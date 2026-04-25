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
        } else if (!uploadedFiles.master && (n.includes('Master') || n.includes('StockTake'))) {
            const dt = new DataTransfer(); dt.items.add(file);
            masterInput.files = dt.files;
            handleMasterSelect({ target: { files: dt.files } });
        } else if (!uploadedFiles.stack && (n.includes('Stack') || n.includes('Upload') || n.includes('BulkSell'))) {
            const dt = new DataTransfer(); dt.items.add(file);
            stackInput.files = dt.files;
            handleStackSelect({ target: { files: dt.files } });
        }
    }
}

function updateUploadButton() {
    // Required: Blackbelt + Master Template. Stack Bulk is optional.
    if (uploadedFiles.blackbelt && uploadedFiles.master) {
        uploadBtn.disabled = false;
        uploadBtn.style.cursor = 'pointer';
    } else {
        uploadBtn.disabled = true;
        uploadBtn.style.cursor = 'not-allowed';
    }
}

// ============================================================================
// Upload & Processing
// ============================================================================

async function handleUpload() {
    if (!uploadedFiles.blackbelt || !uploadedFiles.master) {
        alert('Please select the Blackbelt file and Master Template (Stack Bulk is optional)');
        return;
    }

    const formData = new FormData();
    formData.append('blackbelt_file', blackbeltInput.files[0]);
    // Master Template is the primary "company" input for the detector.
    formData.append('company_file',   masterInput.files[0]);
    if (uploadedFiles.stack && stackInput.files[0]) {
        formData.append('stack_file', stackInput.files[0]);
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
    
    // Update cards
    const matches = results.matches;
    document.getElementById('highCount').textContent = matches.high_confidence.count;
    document.getElementById('mediumCount').textContent = matches.medium_confidence.count;
    document.getElementById('lowCount').textContent = matches.low_confidence.count;
    document.getElementById('unmatchedCount').textContent = matches.unmatched.count;
    
    // Update recommendations
    displayRecommendations(results.recommendations);
    
    // Create charts
    createCharts(matches);
    
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

function createCharts(matches) {
    // Distribution Chart
    const distCtx = document.getElementById('distributionChart').getContext('2d');
    new Chart(distCtx, {
        type: 'doughnut',
        data: {
            labels: ['Confirmed Errors', 'Likely Errors', 'Advisory Flags', 'Clean Rows'],
            datasets: [{
                data: [
                    matches.high_confidence.count,
                    matches.medium_confidence.count,
                    matches.low_confidence.count,
                    matches.unmatched.count,
                ],
                backgroundColor: [
                    '#ff6b6b',
                    '#ff922b',
                    '#ffd43b',
                    '#51cf66',
                ],
                borderColor: '#050812',
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e0e0e0',
                        padding: 15,
                    },
                },
            },
        },
    });
    
    // Confidence Breakdown
    const total = matches.high_confidence.count + matches.medium_confidence.count + 
                  matches.low_confidence.count + matches.unmatched.count;
    
    const confCtx = document.getElementById('confidenceChart').getContext('2d');
    new Chart(confCtx, {
        type: 'bar',
        data: {
            labels: ['Confirmed', 'Likely', 'Advisory', 'Clean'],
            datasets: [{
                label: 'Rows',
                data: [
                    matches.high_confidence.count,
                    matches.medium_confidence.count,
                    matches.low_confidence.count,
                    matches.unmatched.count,
                ],
                backgroundColor: [
                    '#ff6b6b',
                    '#ff922b',
                    '#ffd43b',
                    '#51cf66',
                ],
                borderRadius: 8,
            }],
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    ticks: { color: '#e0e0e0' },
                    grid: { color: '#1a1a2e' },
                },
                y: {
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
    document.getElementById('downloadHighBtn').onclick = (e) => {
        e.preventDefault();
        downloadReport('high');
    };
    document.getElementById('downloadMediumBtn').onclick = (e) => {
        e.preventDefault();
        downloadReport('medium');
    };
    document.getElementById('downloadLowBtn').onclick = (e) => {
        e.preventDefault();
        downloadReport('low');
    };
    document.getElementById('downloadUnmatchedBtn').onclick = (e) => {
        e.preventDefault();
        downloadReport('unmatched');
    };
    document.getElementById('downloadAllBtn').onclick = (e) => {
        e.preventDefault();
        downloadAllReports();
    };
}

function downloadReport(type) {
    const link = document.createElement('a');
    link.href = `/api/download/${currentJobId}/${type}`;
    link.download = `mismatch_${type}_${currentJobId}.csv`;
    link.click();
}

function downloadAllReports() {
    const link = document.createElement('a');
    link.href = `/api/export/${currentJobId}`;
    link.download = `mismatch_results_${currentJobId}.zip`;
    link.click();
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
    document.getElementById('masterName').textContent    = 'Master Template: Not selected';
    document.getElementById('stackName').textContent     = 'Stack Bulk: Not selected (optional)';
    document.getElementById('blackbeltCheck').textContent = '○';
    document.getElementById('masterCheck').textContent    = '○';
    document.getElementById('stackCheck').textContent     = '○';
    document.getElementById('blackbeltCheck').style.color = '';
    document.getElementById('masterCheck').style.color    = '';
    document.getElementById('stackCheck').style.color     = '';
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
