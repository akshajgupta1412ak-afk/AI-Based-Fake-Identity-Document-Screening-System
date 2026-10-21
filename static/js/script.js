/* 
   ====================================================================
   AI-Based Fake Identity & Document Screening System
   Interactive Behaviors, Drag-and-Drop, Preview, and Mobile Drawer
   ====================================================================
*/

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 0. Theme Toggle System (Sun-to-Moon Active Theme Toggle)
    // -------------------------------------------------------------
    const themeBtn = document.getElementById('theme-toggle-btn');
    const themeIcon = document.getElementById('theme-toggle-icon');

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        try {
            localStorage.setItem('docsec_theme', theme);
        } catch (e) {}

        if (themeIcon) {
            if (theme === 'light') {
                // Light mode active: display sun icon
                themeIcon.className = 'fa-solid fa-sun';
                if (themeBtn) {
                    themeBtn.setAttribute('title', 'Switch to Dark Mode');
                    themeBtn.setAttribute('aria-label', 'Current theme: light. Click to switch to dark mode.');
                }
            } else {
                // Dark mode active: display moon icon
                themeIcon.className = 'fa-solid fa-moon';
                if (themeBtn) {
                    themeBtn.setAttribute('title', 'Switch to Light Mode');
                    themeBtn.setAttribute('aria-label', 'Current theme: dark. Click to switch to light mode.');
                }
            }
        }
    }

    function initTheme() {
        let savedTheme = 'dark';
        try {
            savedTheme = localStorage.getItem('docsec_theme') || 'dark';
        } catch (e) {}
        applyTheme(savedTheme);

        if (themeBtn) {
            themeBtn.addEventListener('click', () => {
                const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
                const nextTheme = (currentTheme === 'light') ? 'dark' : 'light';
                applyTheme(nextTheme);
            });
        }
    }

    initTheme();

    // -------------------------------------------------------------
    // 1. Mobile Sidebar Navigation Drawer
    // -------------------------------------------------------------
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.querySelector('.sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    function toggleMobileMenu() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.toggle('show');
            sidebarOverlay.classList.toggle('active');
        }
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', toggleMobileMenu);
    }

    // -------------------------------------------------------------
    // 2. Drag & Drop File Upload with Instant Client-Side Preview
    // -------------------------------------------------------------
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('document_file');
    const previewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const previewFilename = document.getElementById('preview-filename');
    const previewFilesize = document.getElementById('preview-filesize');
    const removeFileBtn = document.getElementById('remove-file-btn');
    const uploadForm = document.getElementById('upload-form');
    const submitBtn = document.getElementById('start-screening-btn');

    if (dropzone && fileInput) {
        ['dragenter', 'dragover'].forEach(evtName => {
            dropzone.addEventListener(evtName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(evtName => {
            dropzone.addEventListener(evtName, (e) => {
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
                handleFileSelection(files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files.length > 0) {
                handleFileSelection(fileInput.files[0]);
            }
        });
    }

    function handleFileSelection(file) {
        if (!file) return;

        // Size check: 5MB limit
        if (file.size > 5 * 1024 * 1024) {
            alert("File size exceeds 5 MB. Please select a smaller document image.");
            if (fileInput) fileInput.value = '';
            if (previewContainer) previewContainer.classList.add('d-none');
            return;
        }

        if (previewFilename) previewFilename.textContent = file.name;
        if (previewFilesize) {
            const kb = (file.size / 1024).toFixed(1);
            previewFilesize.textContent = kb > 1024 ? `${(kb / 1024).toFixed(2)} MB` : `${kb} KB`;
        }

        // Reset previous preview states
        const existingPdfBadge = document.getElementById('pdf-thumbnail-placeholder');
        if (existingPdfBadge) existingPdfBadge.style.display = 'none';

        // Display image thumbnail preview
        if (file.type.startsWith('image/') && imagePreview) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                if (previewContainer) previewContainer.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        } else if (file.type === 'application/pdf' || (file.name && file.name.toLowerCase().endsWith('.pdf'))) {
            if (imagePreview) {
                imagePreview.style.display = 'none';
            }
            let pdfBadge = document.getElementById('pdf-thumbnail-placeholder');
            if (!pdfBadge && previewContainer) {
                pdfBadge = document.createElement('div');
                pdfBadge.id = 'pdf-thumbnail-placeholder';
                pdfBadge.className = 'py-4 text-center';
                pdfBadge.innerHTML = '<i class="fa-solid fa-file-pdf fa-4x text-danger mb-2"></i><div class="fw-semibold text-primary">PDF Document Ingestion</div><div class="small text-muted">Multi-page analysis & optical extraction active</div>';
                imagePreview.parentNode.insertBefore(pdfBadge, imagePreview);
            } else if (pdfBadge) {
                pdfBadge.style.display = 'block';
            }
            if (previewContainer) previewContainer.classList.remove('d-none');
        }
    }

    // Window global hook for file selection
    window.handleImageSelection = function(input) {
        if (input.files && input.files[0]) {
            handleFileSelection(input.files[0]);
        }
    };

    // Remove / Replace file action
    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (fileInput) fileInput.value = '';
            if (previewContainer) previewContainer.classList.add('d-none');
            if (imagePreview) imagePreview.src = '#';
            const pdfBadge = document.getElementById('pdf-thumbnail-placeholder');
            if (pdfBadge) pdfBadge.style.display = 'none';
        });
    }

    // Submit Loading State
    if (uploadForm && submitBtn) {
        uploadForm.addEventListener('submit', () => {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Screening Document... Running Checkpoints';
        });
    }

    // -------------------------------------------------------------
    // 3. Pre-Filter History Table via URL Query Params
    // -------------------------------------------------------------
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

    // -------------------------------------------------------------
    // 4. Auto-Dismiss Alert Banners
    // -------------------------------------------------------------
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (err) {}
        }, 6000);
    });
});

// Helper: Filter History Table (real-time search and dropdown filters)
function filterTable() {
    const searchVal = (document.getElementById('search-input')?.value || '').toLowerCase().trim();
    const typeVal = document.getElementById('filter-type')?.value || 'ALL';
    const riskVal = document.getElementById('filter-risk')?.value || 'ALL';
    
    const rows = document.querySelectorAll('.history-row');
    let visibleCount = 0;

    rows.forEach(row => {
        const id = (row.getAttribute('data-id') || '').toLowerCase();
        const type = row.getAttribute('data-type') || '';
        const result = (row.getAttribute('data-result') || '').toUpperCase();

        const matchesSearch = !searchVal || id.includes(searchVal) || type.toLowerCase().includes(searchVal);
        const matchesType = (typeVal === 'ALL') || (type === typeVal);
        const matchesRisk = (riskVal === 'ALL') || result.includes(riskVal);

        if (matchesSearch && matchesType && matchesRisk) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    const countBadge = document.getElementById('record-count');
    if (countBadge) {
        countBadge.textContent = `${visibleCount} Records Displayed`;
    }
}

// Helper: Copy text to clipboard
function copyToClipboard(text) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard: ' + text);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}
