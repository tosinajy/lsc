// Small Claims Calculator Logic
function checkSmallClaims(stateLimit) {
    const input = document.getElementById('claimAmount');
    const resultDiv = document.getElementById('calcResult');
    const amount = parseFloat(input.value);

    if (!amount || amount < 0) {
        alert("Please enter a valid dollar amount.");
        return;
    }

    resultDiv.classList.remove('d-none', 'alert-success', 'alert-danger');
    resultDiv.classList.add('alert');

    if (amount <= stateLimit) {
        resultDiv.classList.add('alert-success');
        resultDiv.innerHTML = `<i class="fas fa-check-circle"></i> <strong>Eligible!</strong><br>Your claim is within the $${stateLimit} limit.`;
    } else {
        resultDiv.classList.add('alert-warning');
        resultDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> <strong>Too High.</strong><br>Your claim exceeds the $${stateLimit} limit for Small Claims.`;
    }
}

// Report Issue AJAX
function submitReport() {
    const details = document.getElementById('issueDetails').value;
    const email = document.getElementById('reporterEmail').value;
    const context = document.getElementById('pageContext').value;

    if(!details) return alert("Please describe the issue.");

    fetch('/report-issue', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ details: details, email: email, url: context }),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        // Close modal (using Bootstrap 5 API)
        const modalEl = document.getElementById('reportModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        document.getElementById('reportForm').reset();
    })
    .catch((error) => {
        console.error('Error:', error);
        alert("An error occurred. Please try again.");
    });
}