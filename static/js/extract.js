document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('extractionForm').addEventListener('submit', function(e) {
        e.preventDefault();
        startExtraction();
    });
});

function startExtraction() {
    const sourceType = document.getElementById('sourceType').value;
    const searchQuery = document.getElementById('searchQuery').value;
    const maxResults = document.getElementById('maxResults').value;
    
    if (!sourceType || !searchQuery) {
        showToast('Please fill all required fields', 'warning');
        return;
    }
    
    const progressDiv = document.getElementById('extractionProgress');
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const logDiv = document.getElementById('extractionLog');
    const submitBtn = document.querySelector('#extractionForm button[type="submit"]');
    
    progressDiv.classList.remove('d-none');
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';
    logDiv.innerHTML = '';
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Extracting...';
    
    addLog('info', `Starting extraction from ${sourceType}...`);
    addLog('info', `Query: ${searchQuery}`);
    addLog('info', `Max results: ${maxResults}`);
    
    fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            source_type: sourceType,
            search_query: searchQuery,
            max_results: parseInt(maxResults)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addLog('success', `Extraction complete! ${data.leads_found} leads found.`);
            addLog('success', `${data.leads_added} new leads added to database.`);
            if (data.errors && data.errors.length > 0) {
                data.errors.forEach(err => addLog('warning', `Warning: ${err}`));
            }
            showToast(`Extraction complete! ${data.leads_added} leads added.`, 'success');
        } else {
            addLog('error', `Extraction failed: ${data.message}`);
            showToast('Extraction failed', 'error');
        }
    })
    .catch(error => {
        addLog('error', `Error: ${error.message}`);
        showToast('Extraction error occurred', 'error');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-play-fill"></i> Start Extraction';
        progressBar.style.width = '100%';
        progressPercent.textContent = '100%';
        setTimeout(() => {
            document.getElementById('extractionProgress').classList.add('d-none');
        }, 2000);
    });
}

function addLog(type, message) {
    const logDiv = document.getElementById('extractionLog');
    const timestamp = new Date().toLocaleTimeString();
    const colors = {
        info: 'text-info',
        success: 'text-success',
        warning: 'text-warning',
        error: 'text-danger'
    };
    const logEntry = document.createElement('div');
    logEntry.innerHTML = `<span class="text-muted">[${timestamp}]</span> <span class="${colors[type] || ''}">${message}</span>`;
    logDiv.appendChild(logEntry);
    logDiv.scrollTop = logDiv.scrollHeight;
}
