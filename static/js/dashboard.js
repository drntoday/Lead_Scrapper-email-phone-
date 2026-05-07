let currentPage = 1;
const perPage = 50;

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadLeads(currentPage);
});

function loadStats() {
    fetch('/api/leads/count')
        .then(response => response.json())
        .then(data => {
            document.getElementById('totalLeads').textContent = data.total;
            document.getElementById('verifiedLeads').textContent = data.verified;
            document.getElementById('unverifiedLeads').textContent = data.unverified;
            document.getElementById('catchAllLeads').textContent = data.catch_all;
        })
        .catch(error => console.error('Error loading stats:', error));
}

function loadLeads(page) {
    currentPage = page;
    document.getElementById('leadsTableBody').innerHTML = 
        '<tr><td colspan="8" class="text-center">Loading...</td></tr>';
    
    fetch(`/api/leads?page=${page}&per_page=${perPage}`)
        .then(response => response.json())
        .then(data => {
            renderLeads(data.leads);
            renderPagination(data.pages, data.current_page);
            document.getElementById('leadCountInfo').textContent = 
                `Showing ${data.leads.length} of ${data.total} leads`;
        })
        .catch(error => {
            console.error('Error loading leads:', error);
            document.getElementById('leadsTableBody').innerHTML = 
                '<tr><td colspan="8" class="text-center text-danger">Failed to load leads</td></tr>';
        });
}

function renderLeads(leads) {
    const tbody = document.getElementById('leadsTableBody');
    
    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No leads found</td></tr>';
        return;
    }
    
    tbody.innerHTML = leads.map(lead => {
        const fullName = [lead.first_name, lead.last_name].filter(Boolean).join(' ') || 'N/A';
        
        let confidenceClass = 'confidence-low';
        if (lead.confidence_score >= 80) confidenceClass = 'confidence-high';
        else if (lead.confidence_score >= 50) confidenceClass = 'confidence-medium';
        
        let statusClass = 'status-unverified';
        let statusText = 'Unverified';
        if (lead.is_catch_all) {
            statusClass = 'status-catchall';
            statusText = 'Catch-All';
        } else if (lead.verification_status === 'Verified') {
            statusClass = 'status-verified';
            statusText = 'Verified';
        }
        
        return `
            <tr>
                <td>${fullName}</td>
                <td>${lead.company || 'N/A'}</td>
                <td>${lead.job_title || 'N/A'}</td>
                <td><small>${lead.email}</small></td>
                <td><small>${lead.phone || 'N/A'}</small></td>
                <td>${lead.source || 'N/A'}</td>
                <td><span class="confidence-badge ${confidenceClass}">${lead.confidence_score}%</span></td>
                <td><span class="${statusClass}">${statusText}</span></td>
            </tr>
        `;
    }).join('');
}

function renderPagination(totalPages, currentPage) {
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadLeads(${currentPage - 1})">Previous</a></li>`;
    
    for (let i = 1; i <= totalPages; i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="loadLeads(${i})">${i}</a></li>`;
    }
    
    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadLeads(${currentPage + 1})">Next</a></li>`;
    
    pagination.innerHTML = html;
}
