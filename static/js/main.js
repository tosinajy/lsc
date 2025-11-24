// Small Claims Calculator Logic
function checkSmallClaims(stateLimit) {
    const input = document.getElementById('claimAmount');
    const resultDiv = document.getElementById('calcResult');
    const infoDiv = document.getElementById('smallClaimsInfo'); // Get the hidden info div
    const amount = parseFloat(input.value);

    if (!amount || amount < 0) {
        alert("Please enter a valid dollar amount.");
        // Hide info if input is invalid
        if (infoDiv) infoDiv.classList.add('d-none');
        return;
    }

    resultDiv.classList.remove('d-none', 'alert-success', 'alert-danger', 'alert-warning');
    resultDiv.classList.add('alert', 'border-0', 'shadow-sm');

    // Format the amount with commas for display
    const formattedAmount = amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    // Format state limit for consistency in display logic if needed
    const formattedLimit = stateLimit.toLocaleString('en-US', { style: 'currency', currency: 'USD' });

    if (amount <= stateLimit) {
        resultDiv.classList.add('alert-success');
        resultDiv.innerHTML = `<i class="fas fa-check-circle me-2"></i> <strong>Eligible!</strong><br>Your claim of ${formattedAmount} is within the ${formattedLimit} limit.`;
    } else {
        resultDiv.classList.add('alert-warning');
        resultDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i> <strong>Too High.</strong><br>Your claim of ${formattedAmount} exceeds the ${formattedLimit} limit for Small Claims.`;
    }

    // Show the info box after valid calculation
    if (infoDiv) {
        infoDiv.classList.remove('d-none');
    }
}

// Report Issue AJAX
function submitReport() {
    const details = document.getElementById('issueDetails').value;
    const email = document.getElementById('reporterEmail').value; // Re-added
    const officialSource = document.getElementById('officialSource').value;
    const context = document.getElementById('pageContext').value;

    if(!details || details.trim() === "") {
        alert("Please describe the issue or correction needed.");
        return;
    }

    fetch('/report-issue', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            details: details, 
            email: email, // Re-added
            official_source: officialSource,
            url: context 
        }),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        
        if (data.status === 'success') {
            // Close modal (using Bootstrap 5 API)
            const modalEl = document.getElementById('reportModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            modal.hide();
            document.getElementById('reportForm').reset();
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        alert("An error occurred. Please try again.");
    });
}