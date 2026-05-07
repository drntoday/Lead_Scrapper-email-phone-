document.addEventListener('DOMContentLoaded', () => {
    loadUnverifiedLeads();
});

function loadUnverifiedLeads() {
    fetch('/api/leads?per_page=100')
        .then(response => response.json())
        .then(data => {
            const unverified = data.leads.filter(lead => 
                lead.verification_status !== 'Verified' || lead.is_catch_all
            );
            renderUnverifiedList(unverified);
        })
        .catch(error => console.error('Error loading unverified leads:', error));
}

function renderUnverifiedList(leads) {
    const container = document.getElementById('unverifiedList');
    
    if (leads.length === 0) {
        container.innerHTML = '<p class="text-success">All leads are verified!</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Status</th>
                        <th>Confidence</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${leads.map(lead => `
                        <tr id="lead-row-${lead.id}">
                            <td><small>${lead.email}</small></td>
                            <td>
                                <span class="${lead.is_catch_all ? 'status-catchall' : 'status-unverified'}">
                                    ${lead.is_catch_all ? 'Catch-All' : 'Unverified'}
                                </span>
                            </td>
                            <td>${lead.confidence_score}%</td>
                            <td>
                                <button class="btn btn-sm btn-success" onclick="validateLead(${lead.id}, '${lead.email}')">
                                    <i class="bi bi-check-lg"></i> Validate
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function validateSingleEmail() {
    const email = document.getElementById('singleEmail').value;
    const resultDiv = document.getElementById('singleEmailResult');
    
    if (!email) {
        resultDiv.innerHTML = '<span class="text-warning">Please enter an email address</span>';
        return;
    }
    
    resultDiv.innerHTML = '<span class="text-info">Validating...</span>';
    
    fetch('/api/validate/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        if (data.is_valid) {
            resultDiv.innerHTML = `
                <div class="alert alert-success py-2">
                    <strong>Valid</strong> | Score: ${data.confidence_score}% | 
                    MX: ${data.mx_valid ? '✅' : '❌'} | SMTP: ${data.smtp_valid ? '✅' : '❌'}
                    ${data.is_catch_all ? '<br><span class="text-warning">⚠️ Catch-all domain detected</span>' : ''}
                </div>`;
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger py-2">
                    <strong>Invalid</strong> - ${data.reason || 'Failed validation'}
                </div>`;
        }
    })
    .catch(error => {
        resultDiv.innerHTML = '<span class="text-danger">Validation error occurred</span>';
    });
}

function validateLead(id, email) {
    const row = document.getElementById(`lead-row-${id}`);
    row.querySelector('button').disabled = true;
    row.querySelector('button').innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    
    fetch('/api/validate/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, lead_id: id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.is_valid) {
            showToast(`${email} verified successfully`, 'success');
        } else {
            showToast(`${email} validation failed`, 'warning');
        }
        loadUnverifiedLeads();
    })
    .catch(error => {
        showToast('Validation error', 'error');
        loadUnverifiedLeads();
    });
}

function validateAllUnverified() {
    if (!confirm('Start validating all unverified leads? This may take a while.')) return;
    
    showToast('Batch validation started...', 'info');
    
    fetch('/api/validate/all', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            showToast(`Validation complete! ${data.validated} leads processed.`, 'success');
            loadUnverifiedLeads();
        })
        .catch(error => {
            showToast('Batch validation failed', 'error');
        });
}

function clearAllLeads() {
    if (!confirm('Are you sure you want to delete ALL leads? This cannot be undone.')) return;
    
    fetch('/api/leads/clear', { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            showToast(`Deleted ${data.deleted} leads`, 'success');
            loadUnverifiedLeads();
        })
        .catch(error => {
            showToast('Failed to clear leads', 'error');
        });
}
