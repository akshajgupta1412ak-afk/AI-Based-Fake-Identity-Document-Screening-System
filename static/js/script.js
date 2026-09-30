/* 
   AI-Based Fake Identity & Document Screening System
   Clean Modern Interactive Behaviors & Filtering
*/

document.addEventListener('DOMContentLoaded', () => {
    // 1. File Upload Drag-and-Drop Handler
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('document_file');
    const filePreview = document.getElementById('file-preview');
    const fileNameSpan = document.getElementById('file-name');
    const fileSizeSpan = document.getElementById('file-size');

    if (dropzone && fileInput) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                fileInput.files = files;
                updateFilePreview(files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files.length > 0) {
                updateFilePreview(fileInput.files[0]);
            }
        });
    }

    function updateFilePreview(file) {
        if (!file) return;
        if (fileNameSpan) fileNameSpan.textContent = file.name;
        if (fileSizeSpan) {
            const kb = (file.size / 1024).toFixed(1);
            fileSizeSpan.textContent = kb > 1024 ? `${(kb / 1024).toFixed(2)} MB` : `${kb} KB`;
        }
        if (filePreview) filePreview.classList.remove('d-none');
    }

    // 2. Pre-filter History Table based on URL Query Parameters (?filter_risk=GENUINE)
    const urlParams = new URLSearchParams(window.location.search);
    const filterRiskParam = urlParams.get('filter_risk');
    const filterTypeParam = urlParams.get('filter_type');
    
    const riskSelect = document.getElementById('filter-risk');
    const typeSelect = document.getElementById('filter-type');
    
    if (filterRiskParam && riskSelect) {
        riskSelect.value = filterRiskParam;
        if (typeof filterTable === 'function') filterTable();
    }
    if (filterTypeParam && typeSelect) {
        typeSelect.value = filterTypeParam;
        if (typeof filterTable === 'function') filterTable();
    }

    // 3. Auto-dismiss Alert Banners
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (err) {}
        }, 5000);
    });
});

// Helper: Copy text to clipboard
function copyToClipboard(text) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard: ' + text);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}
