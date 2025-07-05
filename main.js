// Enhanced Interactive Dashboard JavaScript

// Global variables with enhanced state management
let hasHiredData = false;
let hasFinalData = false;
let currentDashboard = 'hired';
let currentUploadId = null;
let filterState = {};
let chartInstances = {};
let isRealTimeMode = false;
let animationQueue = [];

// Initialize application with enhanced interactivity
document.addEventListener('DOMContentLoaded', function() {
    initializeUpload();
    initializeInteractiveFilters();
    initializeEnhancedTabs();
    initializeDataView();
    initializeMatrix();
    initializeMLFeatures();
    initializeRealTimeFeatures();
    loadRecentUploads();
    loadDatabaseStats();
    setupKeyboardShortcuts();
    initializeTheme();
});

// Enhanced Upload with Progress and Validation
function initializeUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const progressBar = document.querySelector('.progress-bar');
    const progressDiv = document.getElementById('uploadProgress');

    // Enhanced drag and drop with visual feedback
    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
        uploadArea.style.transform = 'scale(1.02)';
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        uploadArea.style.transform = 'scale(1)';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        uploadArea.style.transform = 'scale(1)';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            validateAndUploadFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            validateAndUploadFile(e.target.files[0]);
        }
    });
}

function validateAndUploadFile(file) {
    // Enhanced file validation
    const validTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
    ];
    
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls)$/i)) {
        showEnhancedAlert('Invalid file type. Please upload an Excel file (.xlsx or .xls)', 'error');
        return;
    }
    
    if (file.size > maxSize) {
        showEnhancedAlert('File too large. Maximum size is 16MB.', 'error');
        return;
    }
    
    handleEnhancedFileUpload(file);
}

function handleEnhancedFileUpload(file) {
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.querySelector('.progress-bar');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Show upload progress
    progressDiv.classList.remove('d-none');
    
    // Simulate upload progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        
        progressBar.style.width = progress + '%';
        progressBar.setAttribute('aria-valuenow', progress);
    }, 200);

    // Create FormData with additional metadata
    const formData = new FormData();
    formData.append('file', file);
    formData.append('upload_time', new Date().toISOString());
    formData.append('file_size', file.size);

    // Enhanced upload with better error handling
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        
        return response.json();
    })
    .then(data => {
        setTimeout(() => {
            progressDiv.classList.add('d-none');
            progressBar.style.width = '0%';
            
            if (data.success) {
                hasHiredData = data.has_hired;
                hasFinalData = data.has_final;
                currentUploadId = data.upload_id;
                
                showEnhancedAlert(data.message, 'success');
                animateDataLoad();
                setupEnhancedDashboard();
                loadFilterOptions();
                loadRecentUploads();
                loadDatabaseStats();
                
                // Update tab badges
                updateTabBadges();
                
                // Auto-switch to first available tab
                if (hasHiredData) {
                    switchToTab('hired');
                } else if (hasFinalData) {
                    switchToTab('pipeline');
                }
            } else {
                showEnhancedAlert(data.error || 'Upload failed', 'error');
            }
        }, 500);
    })
    .catch(error => {
        clearInterval(progressInterval);
        progressDiv.classList.add('d-none');
        showEnhancedAlert('Upload failed: ' + error.message, 'error');
    });
}

// Enhanced Alert System
function showEnhancedAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('uploadStatus');
    
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger', 
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const icon = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    }[type] || 'fas fa-info-circle';
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert ${alertClass} alert-dismissible fade show animated-alert`;
    alertElement.innerHTML = `
        <i class="${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alertElement);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (alertElement.parentNode) {
            alertElement.classList.remove('show');
            setTimeout(() => {
                if (alertElement.parentNode) {
                    alertElement.remove();
                }
            }, 300);
        }
    }, duration);
}

// Interactive Filters System
function initializeInteractiveFilters() {
    const filterInputs = document.querySelectorAll('.filter-search');
    
    filterInputs.forEach(input => {
        const dropdownId = input.id.replace('search', 'dropdown');
        const optionsId = input.id.replace('search', 'options');
        const dropdown = document.getElementById(dropdownId);
        const optionsContainer = document.getElementById(optionsId);
        
        // Enhanced search functionality
        input.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            handleFilterSearch(searchTerm, dropdown, optionsContainer, input);
        });
        
        input.addEventListener('focus', () => {
            dropdown.classList.add('show');
        });
        
        input.addEventListener('blur', (e) => {
            // Delay hiding to allow clicking on options
            setTimeout(() => {
                if (!dropdown.contains(document.activeElement)) {
                    dropdown.classList.remove('show');
                }
            }, 200);
        });
    });
    
    // Date presets functionality
    document.querySelectorAll('.date-preset').forEach(preset => {
        preset.addEventListener('click', (e) => {
            const days = parseInt(e.target.dataset.range);
            setDateRange(days);
            
            // Visual feedback
            document.querySelectorAll('.date-preset').forEach(p => p.classList.remove('active'));
            e.target.classList.add('active');
        });
    });
    
    // Filter toggle
    document.getElementById('toggleFilters').addEventListener('click', toggleFilterPanel);
    
    // Real-time filtering
    document.getElementById('applyFilters').addEventListener('click', applyFiltersWithAnimation);
    document.getElementById('resetFilters').addEventListener('click', resetFiltersWithAnimation);
    document.getElementById('saveFilters').addEventListener('click', saveCurrentFilters);
}

function handleFilterSearch(searchTerm, dropdown, optionsContainer, input) {
    const filterType = input.id.replace('search', '').toLowerCase();
    
    // Get current filter options
    fetch(`/api/filter-options/${currentDashboard}?upload_id=${currentUploadId}`)
    .then(response => response.json())
    .then(data => {
        const options = data[filterType.replace('hiringmanager', 'hiring_manager').replace('tapartner', 'ta_partner')] || [];
        
        // Filter options based on search
        const filteredOptions = options.filter(option => 
            option.toLowerCase().includes(searchTerm)
        );
        
        // Render filtered options
        renderFilterOptions(filteredOptions, optionsContainer, input, filterType);
        dropdown.classList.add('show');
    });
}

function renderFilterOptions(options, container, input, filterType) {
    container.innerHTML = '';
    
    options.forEach(option => {
        const optionElement = document.createElement('div');
        optionElement.className = 'filter-option';
        optionElement.innerHTML = `
            <i class="fas fa-check" style="opacity: 0;"></i>
            <span>${option}</span>
        `;
        
        optionElement.addEventListener('click', () => {
            selectFilterOption(option, input, filterType, optionElement);
        });
        
        container.appendChild(optionElement);
    });
    
    if (options.length === 0) {
        container.innerHTML = '<div class="filter-option text-muted">No matches found</div>';
    }
}

function selectFilterOption(option, input, filterType, optionElement) {
    // Add to filter state
    if (!filterState[filterType]) {
        filterState[filterType] = [];
    }
    
    if (!filterState[filterType].includes(option)) {
        filterState[filterType].push(option);
        addFilterChip(option, filterType);
        
        // Visual feedback
        optionElement.classList.add('selected');
        optionElement.querySelector('.fas').style.opacity = '1';
    }
    
    input.value = '';
    updateFilterResultCount();
}

function addFilterChip(value, type) {
    const chipsContainer = document.getElementById('filterChips');
    
    const chip = document.createElement('div');
    chip.className = 'filter-chip';
    chip.innerHTML = `
        <span>${value}</span>
        <div class="remove-chip" onclick="removeFilterChip('${value}', '${type}', this)">
            <i class="fas fa-times" style="font-size: 10px;"></i>
        </div>
    `;
    
    chip.style.transform = 'scale(0)';
    chipsContainer.appendChild(chip);
    
    // Animate in
    requestAnimationFrame(() => {
        chip.style.transform = 'scale(1)';
        chip.style.transition = 'transform 0.3s ease';
    });
}

function removeFilterChip(value, type, element) {
    // Remove from filter state
    if (filterState[type]) {
        filterState[type] = filterState[type].filter(v => v !== value);
        if (filterState[type].length === 0) {
            delete filterState[type];
        }
    }
    
    // Animate out and remove
    const chip = element.closest('.filter-chip');
    chip.style.transform = 'scale(0)';
    chip.style.opacity = '0';
    
    setTimeout(() => {
        chip.remove();
        updateFilterResultCount();
    }, 300);
}

function setDateRange(days) {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);
    
    document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
}

function toggleFilterPanel() {
    const panel = document.getElementById('filterPanel');
    const icon = document.getElementById('filterToggleIcon');
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        panel.style.animation = 'slideDown 0.3s ease';
    } else {
        panel.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
    }
}

function applyFiltersWithAnimation() {
    const button = document.getElementById('applyFilters');
    const originalHTML = button.innerHTML;
    
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Applying...';
    button.disabled = true;
    
    // Simulate processing time for better UX
    setTimeout(() => {
        loadDashboardData();
        
        button.innerHTML = originalHTML;
        button.disabled = false;
        
        // Success animation
        button.style.background = 'var(--secondary-color)';
        setTimeout(() => {
            button.style.background = '';
        }, 1000);
    }, 800);
}

function resetFiltersWithAnimation() {
    // Clear filter state
    filterState = {};
    
    // Clear filter chips with animation
    const chips = document.querySelectorAll('.filter-chip');
    chips.forEach((chip, index) => {
        setTimeout(() => {
            chip.style.transform = 'scale(0)';
            chip.style.opacity = '0';
            setTimeout(() => chip.remove(), 300);
        }, index * 100);
    });
    
    // Clear form inputs
    document.querySelectorAll('.filter-search').forEach(input => {
        input.value = '';
    });
    
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    
    // Remove active states from presets
    document.querySelectorAll('.date-preset').forEach(p => p.classList.remove('active'));
    
    setTimeout(() => {
        loadDashboardData();
        updateFilterResultCount();
    }, 500);
}

function updateFilterResultCount() {
    const filterCount = Object.keys(filterState).length;
    const countElement = document.getElementById('filterResultCount');
    
    if (filterCount > 0) {
        countElement.textContent = `${filterCount} filter${filterCount > 1 ? 's' : ''} applied`;
        countElement.className = 'text-primary';
    } else {
        countElement.textContent = 'Ready to filter data';
        countElement.className = 'text-muted';
    }
}

// Enhanced Tab System
function initializeEnhancedTabs() {
    const tabs = document.querySelectorAll('.tab-button');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            const tabId = tab.id.replace('-tab', '');
            switchToTab(tabId);
        });
        
        // Add hover effects
        tab.addEventListener('mouseenter', () => {
            if (!tab.classList.contains('active')) {
                tab.style.transform = 'translateY(-3px)';
            }
        });
        
        tab.addEventListener('mouseleave', () => {
            if (!tab.classList.contains('active')) {
                tab.style.transform = 'translateY(0)';
            }
        });
    });
}

function switchToTab(tabType) {
    // Update current dashboard
    currentDashboard = tabType === 'hired' ? 'hired' : 
                     tabType === 'pipeline' ? 'pipeline' : currentDashboard;
    
    // Update tab states with animation
    document.querySelectorAll('.tab-button').forEach(tab => {
        tab.classList.remove('active');
        tab.style.transform = 'translateY(0)';
    });
    
    const activeTab = document.getElementById(`${tabType}-tab`);
    if (activeTab) {
        activeTab.classList.add('active');
        activeTab.style.transform = 'translateY(0)';
    }
    
    // Load appropriate data
    if (tabType === 'hired' || tabType === 'pipeline') {
        loadFilterOptions();
    }
}

function updateTabBadges() {
    // This would be called after data load to show counts
    if (hasHiredData) {
        document.getElementById('hiredTabBadge').textContent = '●';
        document.getElementById('hiredTabBadge').style.background = 'var(--secondary-color)';
    }
    
    if (hasFinalData) {
        document.getElementById('pipelineTabBadge').textContent = '●';
        document.getElementById('pipelineTabBadge').style.background = 'var(--accent-3)';
    }
}

// Enhanced Dashboard Setup
function setupEnhancedDashboard() {
    document.getElementById('dashboardSection').classList.remove('d-none');
    document.getElementById('exportBtn').disabled = false;
    
    // Animate dashboard appearance
    const dashboardSection = document.getElementById('dashboardSection');
    dashboardSection.style.opacity = '0';
    dashboardSection.style.transform = 'translateY(20px)';
    
    requestAnimationFrame(() => {
        dashboardSection.style.transition = 'all 0.6s ease';
        dashboardSection.style.opacity = '1';
        dashboardSection.style.transform = 'translateY(0)';
    });
}

function animateDataLoad() {
    // Create a wave animation across KPI cards
    const kpiCards = document.querySelectorAll('.interactive-kpi');
    
    kpiCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.transform = 'translateY(-10px)';
            card.style.boxShadow = '0 20px 40px rgba(0,0,0,0.2)';
            
            setTimeout(() => {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '';
            }, 400);
        }, index * 200);
    });
}

// Enhanced KPI Interactions
function initializeKPIInteractions() {
    document.querySelectorAll('.interactive-kpi').forEach(kpi => {
        kpi.addEventListener('click', () => {
            const metric = kpi.dataset.metric;
            drillDownMetric(metric);
        });
        
        // Add tooltip functionality
        kpi.addEventListener('mouseenter', (e) => {
            showKPITooltip(e.target, kpi.dataset.metric);
        });
        
        kpi.addEventListener('mouseleave', () => {
            hideKPITooltip();
        });
    });
}

function drillDownMetric(metric) {
    // Create modal or panel for detailed drill-down
    console.log(`Drilling down into ${metric}`);
    // Implementation for detailed analysis
}

// Real-time Features
function initializeRealTimeFeatures() {
    // Auto-refresh functionality
    const autoRefreshToggle = document.createElement('div');
    autoRefreshToggle.innerHTML = `
        <div class="form-check form-switch">
            <input class="form-check-input" type="checkbox" id="autoRefresh">
            <label class="form-check-label" for="autoRefresh">
                <i class="fas fa-sync me-1"></i>Auto-refresh
            </label>
        </div>
    `;
    
    // Add to filter controls (if needed)
    // document.querySelector('.filter-controls').appendChild(autoRefreshToggle);
    
    document.getElementById('autoRefresh')?.addEventListener('change', (e) => {
        isRealTimeMode = e.target.checked;
        if (isRealTimeMode) {
            startRealTimeUpdates();
        } else {
            stopRealTimeUpdates();
        }
    });
}

let realTimeInterval;

function startRealTimeUpdates() {
    realTimeInterval = setInterval(() => {
        loadDashboardData();
    }, 30000); // Refresh every 30 seconds
}

function stopRealTimeUpdates() {
    if (realTimeInterval) {
        clearInterval(realTimeInterval);
    }
}

// Keyboard Shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+1-5 for tab switching
        if (e.ctrlKey && e.key >= '1' && e.key <= '5') {
            e.preventDefault();
            const tabs = ['hired', 'pipeline', 'data-view', 'matrix', 'ml-insights'];
            const tabIndex = parseInt(e.key) - 1;
            if (tabs[tabIndex]) {
                switchToTab(tabs[tabIndex]);
            }
        }
        
        // Ctrl+F for filter focus
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            document.querySelector('.filter-search').focus();
        }
        
        // Escape to close dropdowns
        if (e.key === 'Escape') {
            document.querySelectorAll('.filter-dropdown.show').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });
}

// Theme Management
function initializeTheme() {
    // Check for saved theme preference or default to light
    const savedTheme = localStorage.getItem('dashboard-theme') || 'light';
    applyTheme(savedTheme);
    
    // Add theme toggle if needed
    const themeToggle = document.createElement('button');
    themeToggle.className = 'btn btn-sm btn-outline-secondary';
    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    themeToggle.onclick = toggleTheme;
    
    // Add to header if desired
    // document.querySelector('.navbar-nav').appendChild(themeToggle);
}

function toggleTheme() {
    const currentTheme = document.body.dataset.theme || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    applyTheme(newTheme);
    localStorage.setItem('dashboard-theme', newTheme);
}

function applyTheme(theme) {
    document.body.dataset.theme = theme;
    
    if (theme === 'dark') {
        document.body.style.background = '#1a202c';
        document.body.style.color = '#e2e8f0';
    } else {
        document.body.style.background = '#ffffff';
        document.body.style.color = '#333';
    }
}

// ML Features Initialization
function initializeMLFeatures() {
    // ML Insights tab
    document.getElementById('ml-insights-tab').addEventListener('click', () => {
        if (hasHiredData || hasFinalData) {
            loadMLStatus();
            setupPredictionInputs();
        }
    });
    
    // Prediction button
    document.getElementById('getPredictions').addEventListener('click', function() {
        const role = document.getElementById('predictionRole').value;
        const taPartner = document.getElementById('predictionTA').value;
        const budget = document.getElementById('predictionBudget').value;
        
        if (!role || !taPartner || !budget) {
            showAlert('Please fill all prediction fields', 'warning');
            return;
        }
        
        getPredictions({
            role: role,
            ta_partner: taPartner,
            max_budget: parseFloat(budget),
            pos_created: new Date().toISOString().split('T')[0],
            country: 'United States',
            project: 'Sample Project'
        });
    });
    
    // Anomaly detection
    document.getElementById('detectAnomalies').addEventListener('click', detectAnomalies);
    
    // Recommendations
    document.getElementById('getRecommendations').addEventListener('click', getRecommendations);
    
    // Model retraining
    document.getElementById('retrainModels').addEventListener('click', retrainModels);
}

function loadMLStatus() {
    fetch('/api/ml-status')
    .then(response => response.json())
    .then(data => {
        displayMLStatus(data);
    })
    .catch(error => {
        console.error('Error loading ML status:', error);
        document.getElementById('mlStatus').innerHTML = '<p class="text-danger">Error loading AI status</p>';
    });
}

function displayMLStatus(status) {
    const statusDiv = document.getElementById('mlStatus');
    
    if (status.is_trained) {
        const modelsHTML = Object.entries(status.models)
            .map(([model, trained]) => 
                `<span class="badge ${trained ? 'bg-success' : 'bg-secondary'} me-2">
                    ${model.replace('_', ' ').toUpperCase()}: ${trained ? 'Active' : 'Inactive'}
                </span>`
            ).join('');
        
        statusDiv.innerHTML = `
            <div class="alert alert-success">
                <h6><i class="fas fa-check-circle me-2"></i>AI Intelligence: ACTIVE</h6>
                <p class="mb-2">Models trained and ready for predictions</p>
                <div class="mb-3">${modelsHTML}</div>
                <div>
                    <strong>Capabilities:</strong>
                    <ul class="mb-0">
                        ${status.capabilities.map(cap => `<li>${cap}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    } else {
        statusDiv.innerHTML = `
            <div class="alert alert-warning">
                <h6><i class="fas fa-exclamation-circle me-2"></i>AI Intelligence: LEARNING</h6>
                <p class="mb-2">${status.training_requirements}</p>
                <p class="mb-0">Upload more historical data to activate AI features</p>
            </div>
        `;
    }
}

function setupPredictionInputs() {
    // Populate TA Partner dropdown from current data
    const filterParams = new URLSearchParams();
    if (currentUploadId) {
        filterParams.append('upload_id', currentUploadId);
    }
    
    fetch(`/api/filter-options/${currentDashboard}?${filterParams}`)
    .then(response => response.json())
    .then(data => {
        const select = document.getElementById('predictionTA');
        select.innerHTML = '<option value="">Select TA Partner</option>';
        
        if (data.ta_partner) {
            data.ta_partner.forEach(ta => {
                select.innerHTML += `<option value="${ta}">${ta}</option>`;
            });
        }
    })
    .catch(error => {
        console.error('Error loading TA partners:', error);
    });
}

function getPredictions(positionData) {
    const resultsDiv = document.getElementById('predictionResults');
    resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm" role="status"></div> Generating predictions...</div>';
    
    fetch('/api/ml-predictions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(positionData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }
        
        displayPredictions(data);
    })
    .catch(error => {
        console.error('Error getting predictions:', error);
        resultsDiv.innerHTML = '<div class="alert alert-danger">Error detecting anomalies</div>';
    });
}

function displayAnomalies(data) {
    const resultsDiv = document.getElementById('anomalyResults');
    
    if (data.anomalies.length === 0) {
        resultsDiv.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle me-2"></i>
                No anomalies detected in ${data.total_positions} positions. All positions appear normal.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="mb-3">
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Found ${data.anomalies.length} anomalous positions (${data.anomaly_rate.toFixed(1)}% of total)
            </div>
        </div>
    `;
    
    data.anomalies.slice(0, 5).forEach((anomaly, index) => {
        const severity = Math.abs(anomaly.anomaly_score) > 0.5 ? 'danger' : 'warning';
        html += `
            <div class="card border-${severity} mb-2">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="card-title text-${severity} mb-1">
                                Anomaly #${index + 1}: ${anomaly.position_details.role}
                            </h6>
                            <p class="mb-2"><strong>Reason:</strong> ${anomaly.reason}</p>
                            <div class="row text-sm">
                                <div class="col-md-6">
                                    <small><strong>TA Partner:</strong> ${anomaly.position_details.ta_partner}</small><br>
                                    <small><strong>Created:</strong> ${anomaly.position_details.pos_created}</small>
                                </div>
                                <div class="col-md-6">
                                    ${anomaly.position_details.time_to_fill ? `<small><strong>TTF:</strong> ${anomaly.position_details.time_to_fill} days</small><br>` : ''}
                                    ${anomaly.position_details.budget_variance_pct ? `<small><strong>Budget Var:</strong> ${anomaly.position_details.budget_variance_pct.toFixed(1)}%</small>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-${severity}">
                                Score: ${anomaly.anomaly_score.toFixed(2)}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    if (data.anomalies.length > 5) {
        html += `<p class="text-muted text-center">Showing top 5 of ${data.anomalies.length} anomalies</p>`;
    }
    
    resultsDiv.innerHTML = html;
}

function getRecommendations() {
    const resultsDiv = document.getElementById('recommendationResults');
    resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm" role="status"></div> Generating AI recommendations...</div>';
    
    const params = new URLSearchParams();
    if (currentUploadId) {
        params.append('upload_id', currentUploadId);
    }
    
    fetch(`/api/ml-recommendations?${params}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }
        
        displayRecommendations(data);
    })
    .catch(error => {
        console.error('Error getting recommendations:', error);
        resultsDiv.innerHTML = '<div class="alert alert-danger">Error generating recommendations</div>';
    });
}

function displayRecommendations(data) {
    const resultsDiv = document.getElementById('recommendationResults');
    
    if (!data.recommendations || data.recommendations.length === 0) {
        resultsDiv.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No specific recommendations at this time. Your recruitment process appears to be performing well!
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="mb-3">
            <small class="text-muted">Generated: ${new Date(data.generated_at).toLocaleString()}</small>
        </div>
    `;
    
    data.recommendations.forEach((rec, index) => {
        const priorityColor = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'info'
        }[rec.priority] || 'secondary';
        
        const typeIcon = {
            'performance': 'fas fa-chart-line',
            'budget': 'fas fa-dollar-sign',
            'sourcing': 'fas fa-users',
            'pipeline': 'fas fa-stream',
            'process': 'fas fa-cogs'
        }[rec.type] || 'fas fa-lightbulb';
        
        html += `
            <div class="card border-${priorityColor} mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title text-${priorityColor} mb-0">
                            <i class="${typeIcon} me-2"></i>${rec.title}
                        </h6>
                        <span class="badge bg-${priorityColor}">${rec.priority.toUpperCase()}</span>
                    </div>
                    <p class="card-text mb-2">${rec.description}</p>
                    <div class="row">
                        <div class="col-md-8">
                            <strong>Recommended Action:</strong><br>
                            <span class="text-muted">${rec.action}</span>
                        </div>
                        <div class="col-md-4">
                            <strong>Expected Impact:</strong><br>
                            <span class="text-success">${rec.impact}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsDiv.innerHTML = html;
}

// Enhanced Chart Creation with Interactivity
function createEnhancedFunnelChart(elementId, data) {
    const container = document.getElementById(elementId);
    
    // Create responsive funnel with enhanced interactivity
    const trace = {
        type: 'funnel',
        y: data.stages,
        x: data.values,
        textinfo: 'value+percent initial+percent previous',
        textfont: { size: 14, color: '#333' },
        marker: {
            color: COLORS.slice(0, data.stages.length),
            line: {
                width: 2,
                color: '#ffffff'
            }
        },
        connector: {
            line: {
                color: 'rgba(0,0,0,0.3)',
                width: 3
            }
        },
        hovertemplate: 
            '<b>%{y}</b><br>' +
            'Count: %{x:,}<br>' +
            'Conversion: %{percentInitial}<br>' +
            '<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Interactive Recruitment Funnel',
            font: { size: 20, color: COLORS[0] },
            x: 0.5
        },
        margin: { t: 80, l: 50, r: 50, b: 50 },
        font: { family: 'Segoe UI, Arial, sans-serif', size: 12 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        annotations: []
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToAdd: [
            {
                name: 'Download as PNG',
                icon: Plotly.Icons.camera,
                click: function(gd) {
                    Plotly.downloadImage(gd, {
                        format: 'png',
                        width: 1200,
                        height: 800,
                        filename: 'recruitment-funnel'
                    });
                }
            }
        ],
        modeBarButtonsToRemove: ['pan2d', 'lasso2d']
    };

    Plotly.newPlot(elementId, [trace], layout, config);
    
    // Add click interactions
    container.on('plotly_click', function(data) {
        const pointIndex = data.points[0].pointIndex;
        const stage = data.points[0].y;
        drillDownStage(stage, pointIndex);
    });
    
    // Add hover effects
    container.on('plotly_hover', function(data) {
        const update = {'marker.line.width': 4};
        Plotly.restyle(elementId, update, [data.points[0].curveNumber]);
    });
    
    container.on('plotly_unhover', function(data) {
        const update = {'marker.line.width': 2};
        Plotly.restyle(elementId, update, [data.points[0].curveNumber]);
    });
    
    // Store chart instance for updates
    chartInstances[elementId] = { type: 'funnel', data: trace, layout: layout };
}

function createEnhancedTTFChart(elementId, data) {
    const groupBy = document.getElementById('ttfGroupBy')?.value || 'role';
    
    const trace = {
        type: 'bar',
        x: data.values,
        y: data.roles,
        orientation: 'h',
        marker: {
            color: data.values,
            colorscale: [
                [0, COLORS[4]], 
                [0.5, COLORS[1]], 
                [1, COLORS[0]]
            ],
            colorbar: {
                title: 'Days',
                titleside: 'right'
            },
            line: {
                color: '#ffffff',
                width: 1
            }
        },
        text: data.values.map(v => `${v} days`),
        textposition: 'inside',
        textfont: { color: 'white', size: 12 },
        hovertemplate: 
            '<b>%{y}</b><br>' +
            'Avg Time-to-Fill: %{x} days<br>' +
            '<extra></extra>'
    };

    const layout = {
        title: {
            text: `Time-to-Fill Analysis by ${groupBy.replace('_', ' ').toUpperCase()}`,
            font: { size: 18, color: COLORS[0] }
        },
        xaxis: { 
            title: 'Average Days',
            gridcolor: 'rgba(0,0,0,0.1)',
            showline: true,
            linecolor: 'rgba(0,0,0,0.3)'
        },
        yaxis: { 
            title: 'Categories',
            automargin: true
        },
        margin: { t: 80, l: 150, r: 80, b: 60 },
        font: { family: 'Segoe UI, Arial, sans-serif' },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        showlegend: false
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToAdd: [
            {
                name: 'Switch View',
                icon: Plotly.Icons.pencil,
                click: function(gd) {
                    switchTTFView();
                }
            }
        ]
    };

    Plotly.newPlot(elementId, [trace], layout, config);
    
    // Add benchmark line
    const benchmarkLine = {
        type: 'scatter',
        x: [45, 45],
        y: [0, data.roles.length - 1],
        mode: 'lines',
        line: {
            color: 'red',
            width: 2,
            dash: 'dash'
        },
        name: 'Industry Benchmark (45 days)',
        hovertemplate: 'Industry Benchmark: 45 days<extra></extra>'
    };
    
    Plotly.addTraces(elementId, [benchmarkLine]);
    
    chartInstances[elementId] = { type: 'ttf', data: trace, layout: layout };
}

function createEnhancedFinancialCharts(data) {
    createBudgetScatterChart(data);
    createVarianceHistogram(data);
}

function createBudgetScatterChart(data) {
    if (!data.budget_data || data.budget_data.length === 0) return;
    
    const scatterTrace = {
        type: 'scatter',
        mode: 'markers',
        x: data.budget_data.map(d => d.max_budget),
        y: data.budget_data.map(d => d.accepted_salary),
        marker: {
            size: 10,
            color: data.budget_data.map(d => d.accepted_salary - d.max_budget),
            colorscale: [
                [0, COLORS[4]], 
                [0.5, COLORS[1]], 
                [1, COLORS[0]]
            ],
            colorbar: {
                title: 'Variance ($)',
                titleside: 'right'
            },
            opacity: 0.8,
            line: {
                width: 1,
                color: '#ffffff'
            }
        },
        text: data.budget_data.map((d, i) => `Position ${i + 1}`),
        hovertemplate: 
            '<b>%{text}</b><br>' +
            'Budget: $%{x:,.0f}<br>' +
            'Actual: $%{y:,.0f}<br>' +
            'Variance: $%{marker.color:,.0f}<br>' +
            '<extra></extra>',
        name: 'Positions'
    };

    // Add diagonal reference line
    const minVal = Math.min(...data.budget_data.map(d => Math.min(d.max_budget, d.accepted_salary)));
    const maxVal = Math.max(...data.budget_data.map(d => Math.max(d.max_budget, d.accepted_salary)));
    
    const referenceLine = {
        type: 'scatter',
        mode: 'lines',
        x: [minVal, maxVal],
        y: [minVal, maxVal],
        line: {
            color: 'rgba(255, 0, 0, 0.8)',
            width: 2,
            dash: 'dash'
        },
        name: 'Budget = Actual',
        hovertemplate: 'Perfect Budget Match<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Budget vs Actual Salary Analysis',
            font: { size: 16, color: COLORS[0] }
        },
        xaxis: { 
            title: 'Max Budget ($)',
            tickformat: ',.0f'
        },
        yaxis: { 
            title: 'Accepted Salary ($)',
            tickformat: ',.0f'
        },
        margin: { t: 60, l: 80, r: 80, b: 60 },
        showlegend: true,
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.8)',
            bordercolor: 'rgba(0,0,0,0.2)',
            borderwidth: 1
        }
    };

    Plotly.newPlot('budgetScatterChart', [scatterTrace, referenceLine], layout, {responsive: true});
}

function createVarianceHistogram(data) {
    if (!data.variance_data || data.variance_data.length === 0) return;
    
    const histTrace = {
        type: 'histogram',
        x: data.variance_data,
        nbinsx: 20,
        marker: {
            color: COLORS[1],
            opacity: 0.8,
            line: {
                color: COLORS[0],
                width: 1
            }
        },
        hovertemplate: 
            'Range: %{x}%<br>' +
            'Count: %{y}<br>' +
            '<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Budget Variance Distribution',
            font: { size: 16, color: COLORS[0] }
        },
        xaxis: { 
            title: 'Budget Variance (%)',
            ticksuffix: '%'
        },
        yaxis: { 
            title: 'Number of Positions'
        },
        margin: { t: 60, l: 60, r: 60, b: 60 },
        shapes: [
            // Add reference lines for target ranges
            {
                type: 'line',
                x0: -5, x1: -5,
                y0: 0, y1: 1,
                yref: 'paper',
                line: { color: 'green', width: 2, dash: 'dash' }
            },
            {
                type: 'line',
                x0: 5, x1: 5,
                y0: 0, y1: 1,
                yref: 'paper',
                line: { color: 'green', width: 2, dash: 'dash' }
            }
        ],
        annotations: [
            {
                x: 0,
                y: 1.1,
                yref: 'paper',
                text: 'Target Range: ±5%',
                showarrow: false,
                font: { color: 'green', size: 12 }
            }
        ]
    };

    Plotly.newPlot('varianceHistChart', [histTrace], layout, {responsive: true});
}

// Enhanced Leaderboard with Interactive Features
function createEnhancedLeaderboard(elementId, data) {
    if (!data || data.length === 0) {
        document.getElementById(elementId).innerHTML = 
            '<div class="text-center p-4"><i class="fas fa-trophy fa-3x text-muted mb-3"></i><p class="text-muted">No leaderboard data available</p></div>';
        return;
    }

    let tableHTML = `
        <div class="leaderboard-container">
            <div class="leaderboard-header">
                <h6><i class="fas fa-trophy me-2"></i>Performance Rankings</h6>
                <div class="leaderboard-controls">
                    <select class="form-select form-select-sm" id="leaderboardSort">
                        <option value="ttf">Sort by Time-to-Fill</option>
                        <option value="conversion">Sort by Conversion Rate</option>
                        <option value="volume">Sort by Volume</option>
                    </select>
                </div>
            </div>
            <div class="leaderboard-table">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>TA Partner</th>
                            <th>Performance Score</th>
                            <th>Avg TTF</th>
                            <th>Conversion Rate</th>
                            <th>Total Positions</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    data.forEach((partner, index) => {
        const rank = index + 1;
        const rankClass = rank === 1 ? 'rank-gold' : rank === 2 ? 'rank-silver' : rank === 3 ? 'rank-bronze' : '';
        const rankIcon = rank === 1 ? 'fas fa-crown' : rank === 2 ? 'fas fa-medal' : rank === 3 ? 'fas fa-award' : 'fas fa-user';
        
        // Calculate performance score (simplified)
        const performanceScore = Math.round(
            (partner.cv_interview_rate || 50) + 
            (60 - Math.min(partner.avg_ttf || 60, 60)) + 
            Math.min(partner.total_positions || 0, 20)
        );
        
        tableHTML += `
            <tr class="leaderboard-row ${rankClass}" data-partner="${partner.ta_partner}">
                <td class="rank-cell">
                    <div class="rank-badge">
                        <i class="${rankIcon}"></i>
                        <span>${rank}</span>
                    </div>
                </td>
                <td class="partner-cell">
                    <div class="partner-info">
                        <strong>${partner.ta_partner}</strong>
                        <div class="partner-badge">
                            ${performanceScore >= 80 ? 'Top Performer' : performanceScore >= 60 ? 'Good' : 'Needs Focus'}
                        </div>
                    </div>
                </td>
                <td class="score-cell">
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${Math.min(performanceScore, 100)}%"></div>
                        <span class="score-text">${performanceScore}/100</span>
                    </div>
                </td>
                <td class="metric-cell">
                    <span class="metric-value">${partner.avg_ttf || 'N/A'}</span>
                    <span class="metric-unit">days</span>
                </td>
                <td class="metric-cell">
                    <span class="metric-value">${partner.cv_interview_rate || 'N/A'}</span>
                    <span class="metric-unit">%</span>
                </td>
                <td class="metric-cell">
                    <span class="metric-value">${partner.total_positions}</span>
                    <span class="metric-unit">positions</span>
                </td>
                <td class="actions-cell">
                    <button class="btn btn-sm btn-outline-primary" onclick="viewPartnerDetails('${partner.ta_partner}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="sharePartnerStats('${partner.ta_partner}')">
                        <i class="fas fa-share"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    tableHTML += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    document.getElementById(elementId).innerHTML = tableHTML;
    
    // Add sorting functionality
    document.getElementById('leaderboardSort').addEventListener('change', function() {
        sortLeaderboard(this.value);
    });
    
    // Add row click handlers
    document.querySelectorAll('.leaderboard-row').forEach(row => {
        row.addEventListener('click', function() {
            const partner = this.dataset.partner;
            highlightPartnerPerformance(partner);
        });
    });
}

// Chart Update Functions
function updateChartsWithAnimation() {
    Object.keys(chartInstances).forEach(chartId => {
        const chart = chartInstances[chartId];
        if (chart && document.getElementById(chartId)) {
            animateChartUpdate(chartId, chart);
        }
    });
}

function animateChartUpdate(chartId, chart) {
    // Fade out
    const element = document.getElementById(chartId);
    element.style.opacity = '0.5';
    
    // Update after short delay
    setTimeout(() => {
        Plotly.redraw(chartId);
        element.style.opacity = '1';
    }, 300);
}

// Interactive Chart Controls
function setupChartControls() {
    // Funnel view toggle
    document.querySelectorAll('input[name="funnelView"]').forEach(radio => {
        radio.addEventListener('change', function() {
            updateFunnelView(this.value);
        });
    });
    
    // TTF grouping
    document.getElementById('ttfGroupBy')?.addEventListener('change', function() {
        reloadTTFChart(this.value);
    });
    
    // Financial view toggle
    document.querySelectorAll('input[name="financialView"]').forEach(radio => {
        radio.addEventListener('change', function() {
            updateFinancialView(this.value);
        });
    });
}

function updateFunnelView(viewType) {
    // Toggle between percentage and absolute values
    console.log(`Switching funnel view to: ${viewType}`);
    // Implementation for view switching
}

function reloadTTFChart(groupBy) {
    // Reload TTF chart with new grouping
    console.log(`Reloading TTF chart grouped by: ${groupBy}`);
    // Implementation for chart reload
}

// Drill-down Functions
function drillDownStage(stage, index) {
    showModal('Stage Analysis', `
        <div class="stage-analysis">
            <h5>Detailed Analysis: ${stage}</h5>
            <p>Drilling down into ${stage} stage performance...</p>
            <!-- Add detailed metrics here -->
        </div>
    `);
}

function viewPartnerDetails(partner) {
    showModal('Partner Performance', `
        <div class="partner-details">
            <h5>${partner} - Detailed Performance</h5>
            <!-- Add detailed partner metrics here -->
        </div>
    `);
}

// Utility Functions
function showModal(title, content) {
    // Create and show modal with the given content
    console.log(`Showing modal: ${title}`);
    // Modal implementation
}

// Initialize all enhanced features
function initializeEnhancedCharts() {
    setupChartControls();
    initializeKPIInteractions();
}

function displayPredictions(predictions) {
    const resultsDiv = document.getElementById('predictionResults');
    
    let html = '<div class="row g-3">';
    
    if (predictions.time_to_fill) {
        const pred = predictions.time_to_fill;
        html += `
            <div class="col-12">
                <div class="card border-primary">
                    <div class="card-body p-3">
                        <h6 class="card-title text-primary mb-2">
                            <i class="fas fa-clock me-2"></i>Time-to-Fill Prediction
                        </h6>
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h4 class="mb-0 text-primary">${pred.prediction} days</h4>
                                <small class="text-muted">Confidence: ${pred.confidence}</small>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-primary">${pred.confidence}</span>
                            </div>
                        </div>
                        <p class="mb-0 mt-2"><small>${pred.explanation}</small></p>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (predictions.budget_variance) {
        const pred = predictions.budget_variance;
        const isPositive = pred.prediction > 0;
        html += `
            <div class="col-12">
                <div class="card border-${isPositive ? 'warning' : 'success'}">
                    <div class="card-body p-3">
                        <h6 class="card-title text-${isPositive ? 'warning' : 'success'} mb-2">
                            <i class="fas fa-dollar-sign me-2"></i>Budget Variance Prediction
                        </h6>
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h4 class="mb-0 text-${isPositive ? 'warning' : 'success'}">
                                    ${pred.prediction > 0 ? '+' : ''}${pred.prediction}%
                                </h4>
                                <small class="text-muted">Confidence: ${pred.confidence}</small>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-${isPositive ? 'warning' : 'success'}">${pred.confidence}</span>
                            </div>
                        </div>
                        <p class="mb-0 mt-2"><small>${pred.explanation}</small></p>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (predictions.success_probability) {
        const pred = predictions.success_probability;
        const successLevel = pred.prediction > 70 ? 'success' : pred.prediction > 40 ? 'warning' : 'danger';
        html += `
            <div class="col-12">
                <div class="card border-${successLevel}">
                    <div class="card-body p-3">
                        <h6 class="card-title text-${successLevel} mb-2">
                            <i class="fas fa-target me-2"></i>Success Probability
                        </h6>
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h4 class="mb-0 text-${successLevel}">${pred.prediction}%</h4>
                                <small class="text-muted">Confidence: ${pred.confidence}</small>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-${successLevel}">${pred.confidence}</span>
                            </div>
                        </div>
                        <p class="mb-0 mt-2"><small>${pred.explanation}</small></p>
                    </div>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    
    if (html === '<div class="row g-3"></div>') {
        html = '<div class="alert alert-info">No predictions available. Model may need more training data.</div>';
    }
    
    resultsDiv.innerHTML = html;
}

function detectAnomalies() {
    const resultsDiv = document.getElementById('anomalyResults');
    resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm" role="status"></div> Scanning for anomalies...</div>';
    
    const params = new URLSearchParams();
    if (currentUploadId) {
        params.append('upload_id', currentUploadId);
    }
    params.append('sheet_type', currentDashboard === 'hired' ? 'hired' : 'final');
    
    fetch(`/api/anomaly-detection?${params}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }
        
        displayAnomalies(data);
    })
    .catch(error => {
        console.error('Error detecting anomalies:', error);
        resultsDiv.innerHTML = '<div class="alert alert-danger">Error detecting anomalies</div>';
    });

// Color palette for charts
const COLORS = ['#062C3A', '#ABC100', '#5D858B', '#00617E', '#00A4A6', '#97B8BB', 
                '#F4A41D', '#71164C', '#E2EC57', '#75A1D2', '#344893', '#00A78B', '#C8313F'];

// Global variables
let hasHiredData = false;
let hasFinalData = false;
let currentDashboard = 'hired';
let currentUploadId = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeUpload();
    initializeFilters();
    initializeTabs();
    initializeDataView();
    initializeMatrix();
    loadRecentUploads();
    loadDatabaseStats();
});

// File Upload Functionality
function initializeUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');

    // Click to browse
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

function handleFileUpload(file) {
    const uploadStatus = document.getElementById('uploadStatus');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Validate file type
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        showAlert('Please upload an Excel file (.xlsx or .xls)', 'danger');
        return;
    }

    // Show loading
    loadingOverlay.classList.remove('d-none');

    // Create FormData
    const formData = new FormData();
    formData.append('file', file);

    // Upload file
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        loadingOverlay.classList.add('d-none');
        
        if (data.success) {
            hasHiredData = data.has_hired;
            hasFinalData = data.has_final;
            currentUploadId = data.upload_id;
            
            showAlert(data.message, 'success');
            showDashboard();
            setupDashboardTabs();
            loadFilterOptions();
            loadRecentUploads(); // Refresh the uploads list
            loadDatabaseStats(); // Update database stats
        } else {
            showAlert(data.error || 'Upload failed', 'danger');
        }
    })
    .catch(error => {
        loadingOverlay.classList.add('d-none');
        showAlert('Upload failed: ' + error.message, 'danger');
    });
}

function loadRecentUploads() {
    fetch('/api/recent-uploads')
    .then(response => response.json())
    .then(uploads => {
        createUploadsDropdown(uploads);
    })
    .catch(error => {
        console.error('Error loading recent uploads:', error);
    });
}

function createUploadsDropdown(uploads) {
    if (uploads.length === 0) return;
    
    const uploadSection = document.getElementById('uploadSection');
    
    // Add dropdown for recent uploads
    const recentUploadsHTML = `
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0"><i class="fas fa-history me-2"></i>Recent Uploads</h5>
                    </div>
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-8">
                                <select class="form-select" id="recentUploadsSelect">
                                    <option value="">Select a previous upload...</option>
                                    ${uploads.map(upload => `
                                        <option value="${upload.id}" data-hired="${upload.has_hired}" data-final="${upload.has_final}">
                                            ${upload.filename} - ${new Date(upload.upload_date).toLocaleDateString()}
                                            ${upload.has_hired ? '[Hired]' : ''} ${upload.has_final ? '[Pipeline]' : ''}
                                        </option>
                                    `).join('')}
                                </select>
                            </div>
                            <div class="col-md-4">
                                <button class="btn btn-primary" id="loadSelectedUpload">
                                    <i class="fas fa-download me-2"></i>Load Selected
                                </button>
                                <button class="btn btn-danger btn-sm ms-2" id="clearDatabaseBtn">
                                    <i class="fas fa-trash me-2"></i>Clear All Data
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    uploadSection.insertAdjacentHTML('afterend', recentUploadsHTML);
    
    // Add event listeners
    document.getElementById('loadSelectedUpload').addEventListener('click', function() {
        const select = document.getElementById('recentUploadsSelect');
        const uploadId = select.value;
        
        if (!uploadId) {
            showAlert('Please select an upload to load', 'warning');
            return;
        }
        
        loadSelectedUpload(uploadId, select);
    });
    
    document.getElementById('clearDatabaseBtn').addEventListener('click', function() {
        if (confirm('Are you sure you want to clear all data from the database? This action cannot be undone.')) {
            clearDatabase();
        }
    });
}

function loadSelectedUpload(uploadId, selectElement) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.classList.remove('d-none');
    
    fetch(`/api/load-upload/${uploadId}`)
    .then(response => response.json())
    .then(data => {
        loadingOverlay.classList.add('d-none');
        
        if (data.success) {
            hasHiredData = data.has_hired;
            hasFinalData = data.has_final;
            currentUploadId = data.upload_id;
            
            showAlert(data.message, 'success');
            showDashboard();
            setupDashboardTabs();
            loadFilterOptions();
        } else {
            showAlert(data.error || 'Failed to load upload', 'danger');
        }
    })
    .catch(error => {
        loadingOverlay.classList.add('d-none');
        showAlert('Failed to load upload: ' + error.message, 'danger');
    });
}

function clearDatabase() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.classList.remove('d-none');
    
    fetch('/api/clear-database', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        loadingOverlay.classList.add('d-none');
        
        if (data.success) {
            showAlert(data.message, 'success');
            // Reset UI
            document.getElementById('dashboardSection').classList.add('d-none');
            document.getElementById('exportBtn').disabled = true;
            hasHiredData = false;
            hasFinalData = false;
            currentUploadId = null;
            loadRecentUploads();
            loadDatabaseStats();
        } else {
            showAlert(data.error || 'Failed to clear database', 'danger');
        }
    })
    .catch(error => {
        loadingOverlay.classList.add('d-none');
        showAlert('Failed to clear database: ' + error.message, 'danger');
    });
}

function loadDatabaseStats() {
    fetch('/api/database-stats')
    .then(response => response.json())
    .then(stats => {
        displayDatabaseStats(stats);
    })
    .catch(error => {
        console.error('Error loading database stats:', error);
    });
}

function displayDatabaseStats(stats) {
    const statsHTML = `
        <div class="row mb-4">
            <div class="col-12">
                <div class="alert alert-info">
                    <div class="row text-center">
                        <div class="col-md-3">
                            <strong>${stats.upload_count}</strong><br>
                            <small>Total Uploads</small>
                        </div>
                        <div class="col-md-3">
                            <strong>${stats.hired_records.toLocaleString()}</strong><br>
                            <small>Hired Records</small>
                        </div>
                        <div class="col-md-3">
                            <strong>${stats.pipeline_records.toLocaleString()}</strong><br>
                            <small>Pipeline Records</small>
                        </div>
                        <div class="col-md-3">
                            <strong>${stats.database_size_mb} MB</strong><br>
                            <small>Database Size</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add or update stats display
    const existingStats = document.getElementById('databaseStats');
    if (existingStats) {
        existingStats.outerHTML = statsHTML;
    } else {
        const uploadSection = document.getElementById('uploadSection');
        uploadSection.insertAdjacentHTML('afterend', statsHTML);
    }
}

function showAlert(message, type) {
    const uploadStatus = document.getElementById('uploadStatus');
    uploadStatus.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

function showDashboard() {
    document.getElementById('dashboardSection').classList.remove('d-none');
    document.getElementById('exportBtn').disabled = false;
}

function setupDashboardTabs() {
    const hiredTab = document.getElementById('hired-tab');
    const pipelineTab = document.getElementById('pipeline-tab');
    
    // Enable/disable tabs based on data availability
    if (hasHiredData) {
        hiredTab.classList.remove('disabled');
        hiredTab.classList.add('active');
        document.getElementById('hired-content').classList.add('show', 'active');
        currentDashboard = 'hired';
    } else {
        hiredTab.classList.add('disabled');
    }
    
    if (hasFinalData) {
        pipelineTab.classList.remove('disabled');
        if (!hasHiredData) {
            pipelineTab.classList.add('active');
            document.getElementById('pipeline-content').classList.add('show', 'active');
            document.getElementById('hired-content').classList.remove('show', 'active');
            currentDashboard = 'pipeline';
        }
    } else {
        pipelineTab.classList.add('disabled');
    }
}

// Filter Functionality
function initializeFilters() {
    // Apply filters button
    document.getElementById('applyFilters').addEventListener('click', loadDashboardData);
    
    // Reset filters button
    document.getElementById('resetFilters').addEventListener('click', resetFilters);
}

function loadFilterOptions() {
    const params = new URLSearchParams();
    if (currentUploadId) {
        params.append('upload_id', currentUploadId);
    }
    
    fetch(`/api/filter-options/${currentDashboard}?${params}`)
    .then(response => response.json())
    .then(data => {
        populateFilterDropdown('filterHiringManager', data.hiring_manager || []);
        populateFilterDropdown('filterTAPartner', data.ta_partner || []);
        populateFilterDropdown('filterCountry', data.country || []);
        populateFilterDropdown('filterProject', data.project || []);
        
        if (data.date_range) {
            document.getElementById('startDate').value = data.date_range.min || '';
            document.getElementById('endDate').value = data.date_range.max || '';
        }
        
        // Load initial dashboard data
        loadDashboardData();
    })
    .catch(error => {
        console.error('Error loading filter options:', error);
    });
}

function populateFilterDropdown(elementId, options) {
    const select = document.getElementById(elementId);
    select.innerHTML = '';
    
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        select.appendChild(optionElement);
    });
}

function resetFilters() {
    document.getElementById('filterHiringManager').selectedIndex = -1;
    document.getElementById('filterTAPartner').selectedIndex = -1;
    document.getElementById('filterCountry').selectedIndex = -1;
    document.getElementById('filterProject').selectedIndex = -1;
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    
    loadDashboardData();
}

function getFilterParams() {
    const params = new URLSearchParams();
    
    // Get selected values from multi-select dropdowns
    const addMultiSelectParam = (elementId, paramName) => {
        const select = document.getElementById(elementId);
        const selected = Array.from(select.selectedOptions).map(option => option.value);
        if (selected.length > 0) {
            params.append(paramName, selected.join(','));
        }
    };
    
    addMultiSelectParam('filterHiringManager', 'hiring_manager');
    addMultiSelectParam('filterTAPartner', 'ta_partner');
    addMultiSelectParam('filterCountry', 'country');
    addMultiSelectParam('filterProject', 'project');
    
    // Date range
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    return params.toString();
}

// Tab Management
function initializeTabs() {
    // Dashboard tab switching
    document.getElementById('hired-tab').addEventListener('click', () => {
        if (hasHiredData) {
            currentDashboard = 'hired';
            loadFilterOptions();
        }
    });
    
    document.getElementById('pipeline-tab').addEventListener('click', () => {
        if (hasFinalData) {
            currentDashboard = 'pipeline';
            loadFilterOptions();
        }
    });
    
    // Data view tab
    document.getElementById('data-view-tab').addEventListener('click', () => {
        // Enable data view if any data is available
        if (hasHiredData || hasFinalData) {
            setupDataViewOptions();
        }
    });
    
    // Matrix tab
    document.getElementById('matrix-tab').addEventListener('click', () => {
        if (hasHiredData || hasFinalData) {
            setupMatrixOptions();
        }
    });
}

// Data View Functionality
function initializeDataView() {
    document.getElementById('dataSheetSelect').addEventListener('change', function() {
        const selectedSheet = this.value;
        if (selectedSheet) {
            loadRawData(selectedSheet);
        } else {
            document.getElementById('rawDataTable').innerHTML = '<p class="text-center text-muted">Select a sheet to view data</p>';
            document.getElementById('dataTableInfo').innerHTML = '';
        }
    });
}

function setupDataViewOptions() {
    const select = document.getElementById('dataSheetSelect');
    select.innerHTML = '<option value="">Select Sheet</option>';
    
    if (hasHiredData) {
        select.innerHTML += '<option value="hired">Hired Data</option>';
    }
    if (hasFinalData) {
        select.innerHTML += '<option value="final">Pipeline Data</option>';
    }
}

function loadRawData(sheetType) {
    const filterParams = getFilterParams();
    if (currentUploadId) {
        filterParams.append('upload_id', currentUploadId);
    }
    
    fetch(`/api/raw-data/${sheetType}?${filterParams}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('rawDataTable').innerHTML = `<p class="text-danger">${data.error}</p>`;
            return;
        }
        
        displayRawDataTable(data);
    })
    .catch(error => {
        console.error('Error loading raw data:', error);
        document.getElementById('rawDataTable').innerHTML = '<p class="text-danger">Error loading data</p>';
    });
}

function displayRawDataTable(data) {
    const infoDiv = document.getElementById('dataTableInfo');
    const tableDiv = document.getElementById('rawDataTable');
    
    // Show info about the data
    infoDiv.innerHTML = `
        <small>
            Showing ${data.displayed_rows.toLocaleString()} of ${data.total_rows.toLocaleString()} total rows
            ${data.total_rows > data.displayed_rows ? '(limited to first 1,000 for performance)' : ''}
        </small>
    `;
    
    if (data.data.length === 0) {
        tableDiv.innerHTML = '<p class="text-center text-muted">No data available with current filters</p>';
        return;
    }
    
    // Create table HTML
    let tableHTML = `
        <table class="table table-striped table-hover table-sm">
            <thead class="table-dark sticky-top">
                <tr>
    `;
    
    // Add headers
    data.columns.forEach(col => {
        tableHTML += `<th class="text-nowrap">${col.name}</th>`;
    });
    tableHTML += '</tr></thead><tbody>';
    
    // Add data rows
    data.data.forEach(row => {
        tableHTML += '<tr>';
        data.columns.forEach(col => {
            const cellValue = row[col.id] || '';
            tableHTML += `<td class="text-nowrap">${cellValue}</td>`;
        });
        tableHTML += '</tr>';
    });
    
    tableHTML += '</tbody></table>';
    tableDiv.innerHTML = tableHTML;
}

// Matrix Functionality
function initializeMatrix() {
    document.getElementById('matrixDataSelect').addEventListener('change', function() {
        const selectedData = this.value;
        setupMatrixMetrics(selectedData);
        if (selectedData && document.getElementById('matrixMetricSelect').value) {
            loadPartnerMatrix();
        }
    });
    
    document.getElementById('matrixMetricSelect').addEventListener('change', function() {
        const selectedData = document.getElementById('matrixDataSelect').value;
        if (selectedData && this.value) {
            loadPartnerMatrix();
        }
    });
}

function setupMatrixOptions() {
    const dataSelect = document.getElementById('matrixDataSelect');
    dataSelect.innerHTML = '<option value="">Select Data Source</option>';
    
    if (hasHiredData) {
        dataSelect.innerHTML += '<option value="hired">Hired Data</option>';
    }
    if (hasFinalData) {
        dataSelect.innerHTML += '<option value="pipeline">Pipeline Data</option>';
    }
}

function setupMatrixMetrics(dataSource) {
    const metricSelect = document.getElementById('matrixMetricSelect');
    metricSelect.innerHTML = '<option value="">Select Metric</option>';
    
    if (dataSource === 'hired') {
        metricSelect.innerHTML += `
            <option value="positions_filled">Positions Filled</option>
            <option value="avg_ttf">Average Time-to-Fill</option>
            <option value="avg_conversion">Average Conversion Rate</option>
            <option value="avg_budget_variance">Average Budget Variance</option>
        `;
    } else if (dataSource === 'pipeline') {
        metricSelect.innerHTML += `
            <option value="open_positions">Open Positions</option>
            <option value="avg_age">Average Position Age</option>
            <option value="avg_conversion">Average Conversion Rate</option>
        `;
    }
}

function loadPartnerMatrix() {
    const dataSource = document.getElementById('matrixDataSelect').value;
    const metric = document.getElementById('matrixMetricSelect').value;
    
    if (!dataSource || !metric) return;
    
    const filterParams = getFilterParams();
    if (currentUploadId) {
        filterParams.append('upload_id', currentUploadId);
    }
    
    fetch(`/api/partner-matrix/${dataSource}?${filterParams}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('partnerMatrix').innerHTML = `<p class="text-danger">${data.error}</p>`;
            return;
        }
        
        displayPartnerMatrix(data[metric], metric, dataSource);
    })
    .catch(error => {
        console.error('Error loading partner matrix:', error);
        document.getElementById('partnerMatrix').innerHTML = '<p class="text-danger">Error loading matrix data</p>';
    });
}

function displayPartnerMatrix(matrixData, metric, dataSource) {
    if (!matrixData || !matrixData.ta_partners || !matrixData.sourcing_partners) {
        document.getElementById('partnerMatrix').innerHTML = '<p class="text-center text-muted">No matrix data available</p>';
        return;
    }
    
    const { ta_partners, sourcing_partners, data } = matrixData;
    
    // Create matrix table HTML
    let tableHTML = `
        <div class="table-responsive">
            <table class="table table-bordered table-sm">
                <thead>
                    <tr class="table-dark">
                        <th class="sticky-left">TA Partner \\ Sourcing Partner</th>
    `;
    
    sourcing_partners.forEach(sp => {
        tableHTML += `<th class="text-center text-nowrap">${sp}</th>`;
    });
    tableHTML += '</tr></thead><tbody>';
    
    // Add data rows
    ta_partners.forEach((ta, i) => {
        tableHTML += `<tr><th class="sticky-left table-light">${ta}</th>`;
        sourcing_partners.forEach((sp, j) => {
            const value = data[i] && data[i][j] ? data[i][j] : 0;
            const formattedValue = formatMatrixValue(value, metric);
            const cellClass = getCellColorClass(value, metric);
            tableHTML += `<td class="text-center ${cellClass}">${formattedValue}</td>`;
        });
        tableHTML += '</tr>';
    });
    
    tableHTML += '</tbody></table></div>';
    
    // Add legend
    const legend = getMatrixLegend(metric, dataSource);
    
    document.getElementById('partnerMatrix').innerHTML = `
        <div class="mb-3">
            <h6>Matrix: ${getMetricDisplayName(metric)} by TA Partner and Sourcing Partner</h6>
            <small class="text-muted">${legend}</small>
        </div>
        ${tableHTML}
    `;
}

function formatMatrixValue(value, metric) {
    if (value === 0) return '-';
    
    switch (metric) {
        case 'positions_filled':
        case 'open_positions':
            return Math.round(value).toString();
        case 'avg_ttf':
        case 'avg_age':
            return value.toFixed(1) + ' days';
        case 'avg_conversion':
            return value.toFixed(1) + '%';
        case 'avg_budget_variance':
            return (value >= 0 ? '+' : '') + value.toFixed(1) + '%';
        default:
            return value.toFixed(1);
    }
}

function getCellColorClass(value, metric) {
    if (value === 0) return '';
    
    // Define color classes based on metric type and value ranges
    switch (metric) {
        case 'positions_filled':
        case 'open_positions':
            if (value >= 10) return 'table-success';
            if (value >= 5) return 'table-warning';
            return '';
        case 'avg_ttf':
        case 'avg_age':
            if (value > 60) return 'table-danger';
            if (value > 45) return 'table-warning';
            return 'table-success';
        case 'avg_conversion':
            if (value >= 25) return 'table-success';
            if (value >= 15) return 'table-warning';
            return 'table-danger';
        case 'avg_budget_variance':
            if (Math.abs(value) <= 5) return 'table-success';
            if (Math.abs(value) <= 15) return 'table-warning';
            return 'table-danger';
        default:
            return '';
    }
}

function getMetricDisplayName(metric) {
    const names = {
        'positions_filled': 'Positions Filled',
        'open_positions': 'Open Positions',
        'avg_ttf': 'Average Time-to-Fill',
        'avg_age': 'Average Position Age',
        'avg_conversion': 'Average Conversion Rate',
        'avg_budget_variance': 'Average Budget Variance'
    };
    return names[metric] || metric;
}

function getMatrixLegend(metric, dataSource) {
    const legends = {
        'positions_filled': 'Green: ≥10 positions, Yellow: 5-9 positions, White: <5 positions',
        'open_positions': 'Green: ≥10 positions, Yellow: 5-9 positions, White: <5 positions',
        'avg_ttf': 'Green: ≤45 days, Yellow: 46-60 days, Red: >60 days',
        'avg_age': 'Green: ≤45 days, Yellow: 46-60 days, Red: >60 days',
        'avg_conversion': 'Green: ≥25%, Yellow: 15-24%, Red: <15%',
        'avg_budget_variance': 'Green: ±5%, Yellow: ±6-15%, Red: >±15%'
    };
    return legends[metric] || '';
}

// Dashboard Data Loading
function loadDashboardData() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.classList.remove('d-none');
    
    const filterParams = getFilterParams();
    if (currentUploadId) {
        filterParams.append('upload_id', currentUploadId);
    }
    
    fetch(`/api/dashboard-data/${currentDashboard}?${filterParams}`)
    .then(response => response.json())
    .then(data => {
        loadingOverlay.classList.add('d-none');
        
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        if (currentDashboard === 'hired') {
            updateHiredDashboard(data);
        } else {
            updatePipelineDashboard(data);
        }
    })
    .catch(error => {
        loadingOverlay.classList.add('d-none');
        console.error('Error loading dashboard data:', error);
        showAlert('Error loading dashboard data', 'danger');
    });
}

// Hired Dashboard Updates
function updateHiredDashboard(data) {
    // Update KPIs
    if (data.kpis) {
        document.getElementById('totalFilled').textContent = data.kpis.total_filled.toLocaleString();
        document.getElementById('avgTTF').textContent = data.kpis.avg_ttf;
        document.getElementById('overallConversion').textContent = data.kpis.overall_conversion + '%';
        document.getElementById('avgBudgetVariance').textContent = 
            (data.kpis.avg_budget_variance >= 0 ? '+' : '') + data.kpis.avg_budget_variance + '%';
    }
    
    // Update commentary
    if (data.commentary) {
        document.getElementById('hiredCommentary').innerHTML = data.commentary;
    }
    
    // Update charts
    if (data.funnel) {
        createFunnelChart('funnelChart', data.funnel);
    }
    
    if (data.ttf_by_role) {
        createTTFChart('ttfChart', data.ttf_by_role);
    }
    
    if (data.financial) {
        createFinancialCharts(data.financial);
    }
    
    if (data.leaderboard) {
        createLeaderboardTable('leaderboardTable', data.leaderboard);
    }
}

// Pipeline Dashboard Updates
function updatePipelineDashboard(data) {
    // Update KPIs
    if (data.kpis) {
        document.getElementById('totalOpen').textContent = data.kpis.total_open.toLocaleString();
        document.getElementById('avgAge').textContent = data.kpis.avg_age;
        document.getElementById('positionsOver60').textContent = data.kpis.positions_over_60.toLocaleString();
        document.getElementById('bottleneckStage').textContent = data.kpis.bottleneck_stage;
    }
    
    // Update commentary
    if (data.commentary) {
        document.getElementById('pipelineCommentary').innerHTML = data.commentary;
    }
    
    // Update charts
    if (data.stage_distribution) {
        createStageDistributionChart('stageDistChart', data.stage_distribution);
    }
    
    if (data.active_funnel) {
        createFunnelChart('activeFunnelChart', data.active_funnel);
    }
    
    if (data.resource_distribution) {
        createResourceCharts(data.resource_distribution);
    }
}

// Chart Creation Functions
function createFunnelChart(elementId, data) {
    const trace = {
        type: 'funnel',
        y: data.stages,
        x: data.values,
        textinfo: 'value+percent initial',
        marker: {
            color: COLORS.slice(0, data.stages.length)
        }
    };

    const layout = {
        title: {
            text: 'Recruitment Funnel',
            font: { size: 18, color: COLORS[0] }
        },
        margin: { t: 60, l: 100, r: 50, b: 50 },
        font: { size: 12 }
    };

    Plotly.newPlot(elementId, [trace], layout, {responsive: true});
}

function createTTFChart(elementId, data) {
    const trace = {
        type: 'bar',
        x: data.values,
        y: data.roles,
        orientation: 'h',
        marker: {
            color: data.values,
            colorscale: [[0, COLORS[2]], [1, COLORS[0]]]
        }
    };

    const layout = {
        title: {
            text: 'Average Time-to-Fill by Role',
            font: { size: 18, color: COLORS[0] }
        },
        xaxis: { title: 'Days' },
        yaxis: { title: 'Role' },
        margin: { t: 60, l: 150, r: 50, b: 80 },
        font: { size: 12 }
    };

    Plotly.newPlot(elementId, [trace], layout, {responsive: true});
}

function createFinancialCharts(data) {
    // Budget vs Actual Scatter Plot
    if (data.budget_data && data.budget_data.length > 0) {
        const scatterTrace = {
            type: 'scatter',
            mode: 'markers',
            x: data.budget_data.map(d => d.max_budget),
            y: data.budget_data.map(d => d.accepted_salary),
            marker: {
                color: COLORS[0],
                size: 8,
                opacity: 0.7
            },
            name: 'Positions'
        };

        // Add diagonal line
        const minVal = Math.min(...data.budget_data.map(d => Math.min(d.max_budget, d.accepted_salary)));
        const maxVal = Math.max(...data.budget_data.map(d => Math.max(d.max_budget, d.accepted_salary)));
        
        const lineTrace = {
            type: 'scatter',
            mode: 'lines',
            x: [minVal, maxVal],
            y: [minVal, maxVal],
            line: {
                dash: 'dash',
                color: 'red',
                width: 2
            },
            name: 'Budget = Actual'
        };

        const scatterLayout = {
            title: {
                text: 'Budget vs Actual Salary',
                font: { size: 16, color: COLORS[0] }
            },
            xaxis: { title: 'Max Budget' },
            yaxis: { title: 'Accepted Salary' },
            margin: { t: 60, l: 80, r: 50, b: 80 },
            showlegend: true
        };

        Plotly.newPlot('budgetScatterChart', [scatterTrace, lineTrace], scatterLayout, {responsive: true});
    }

    // Variance Histogram
    if (data.variance_data && data.variance_data.length > 0) {
        const histTrace = {
            type: 'histogram',
            x: data.variance_data,
            marker: {
                color: COLORS[1],
                opacity: 0.7
            },
            nbinsx: 20
        };

        const histLayout = {
            title: {
                text: 'Budget Variance Distribution',
                font: { size: 16, color: COLORS[0] }
            },
            xaxis: { title: 'Budget Variance %' },
            yaxis: { title: 'Count' },
            margin: { t: 60, l: 80, r: 50, b: 80 }
        };

        Plotly.newPlot('varianceHistChart', [histTrace], histLayout, {responsive: true});
    }
}

function createLeaderboardTable(elementId, data) {
    if (!data || data.length === 0) {
        document.getElementById(elementId).innerHTML = '<p class="text-muted">No leaderboard data available</p>';
        return;
    }

    let tableHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>TA Partner</th>
                        <th>Avg TTF (days)</th>
                        <th>CV→Interview %</th>
                        <th>Interview→Offer %</th>
                        <th>Total Positions</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach((partner, index) => {
        const rankClass = index === 0 ? 'table-success' : '';
        tableHTML += `
            <tr class="${rankClass}">
                <td><strong>${index + 1}</strong></td>
                <td>${partner.ta_partner}</td>
                <td>${partner.avg_ttf || 'N/A'}</td>
                <td>${partner.cv_interview_rate || 'N/A'}</td>
                <td>${partner.interview_offer_rate || 'N/A'}</td>
                <td>${partner.total_positions}</td>
            </tr>
        `;
    });

    tableHTML += `
                </tbody>
            </table>
        </div>
    `;

    document.getElementById(elementId).innerHTML = tableHTML;
}

function createStageDistributionChart(elementId, data) {
    const trace = {
        type: 'bar',
        x: data.stages,
        y: data.values,
        marker: {
            color: COLORS.slice(0, data.stages.length)
        }
    };

    const layout = {
        title: {
            text: 'Open Positions by Stage',
            font: { size: 18, color: COLORS[0] }
        },
        xaxis: { title: 'Job State' },
        yaxis: { title: 'Number of Positions' },
        margin: { t: 60, l: 80, r: 50, b: 100 },
        font: { size: 12 }
    };

    Plotly.newPlot(elementId, [trace], layout, {responsive: true});
}

function createResourceCharts(data) {
    const chartConfigs = [
        { elementId: 'projectChart', data: data.project, title: 'Open Positions by Project' },
        { elementId: 'partnerChart', data: data.ta_partner, title: 'Open Positions by TA Partner' },
        { elementId: 'countryChart', data: data.country, title: 'Open Positions by Country' },
        { elementId: 'roleChart', data: data.role, title: 'Open Positions by Role' }
    ];

    chartConfigs.forEach((config, index) => {
        if (config.data && config.data.labels && config.data.values) {
            const trace = {
                type: 'bar',
                x: config.data.labels,
                y: config.data.values,
                marker: {
                    color: COLORS[index % COLORS.length]
                }
            };

            const layout = {
                title: {
                    text: config.title,
                    font: { size: 14, color: COLORS[0] }
                },
                margin: { t: 60, l: 60, r: 30, b: 80 },
                xaxis: { 
                    tickangle: -45,
                    tickfont: { size: 10 }
                },
                yaxis: { title: 'Count' },
                font: { size: 10 }
            };

            Plotly.newPlot(config.elementId, [trace], layout, {responsive: true});
        } else {
            document.getElementById(config.elementId).innerHTML = 
                '<p class="text-muted text-center">No data available</p>';
        }
    });
}

// Export Functionality
document.getElementById('exportBtn').addEventListener('click', function() {
    // This would implement the export functionality
    // For now, we'll show a placeholder
    alert('Export functionality would be implemented here using libraries like jsPDF or similar');
});

// Utility Functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatPercentage(num) {
    return parseFloat(num).toFixed(1) + '%';
}

function formatCurrency(num, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(num);
}

// Responsive chart handling
window.addEventListener('resize', function() {
    // Redraw all Plotly charts on window resize
    const chartIds = [
        'funnelChart', 'ttfChart', 'budgetScatterChart', 'varianceHistChart',
        'stageDistChart', 'activeFunnelChart', 'projectChart', 'partnerChart',
        'countryChart', 'roleChart'
    ];

    chartIds.forEach(id => {
        const element = document.getElementById(id);
        if (element && element.data) {
            Plotly.Plots.resize(id);
        }
    });
});

// Animation helpers
function animateValue(element, start, end, duration) {
    const startTime = performance.now();
    const change = end - start;

    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = start + (change * progress);
        element.textContent = Math.round(current).toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }

    requestAnimationFrame(updateValue);
}

// Add smooth animations to KPI updates
function animateKPI(elementId, value) {
    const element = document.getElementById(elementId);
    const currentValue = parseInt(element.textContent.replace(/,/g, '')) || 0;
    animateValue(element, currentValue, value, 1000);
}

// Enhanced error handling
function handleError(error, context) {
    console.error(`Error in ${context}:`, error);
    
    // Show user-friendly error message
    const errorMessage = error.message || 'An unexpected error occurred';
    showAlert(`${context}: ${errorMessage}`, 'danger');
    
    // Hide loading overlay if visible
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (!loadingOverlay.classList.contains('d-none')) {
        loadingOverlay.classList.add('d-none');
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+U for upload
    if (e.ctrlKey && e.key === 'u') {
        e.preventDefault();
        document.getElementById('fileInput').click();
    }
    
    // Ctrl+R for reset filters
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        resetFilters();
    }
    
    // Ctrl+E for export
    if (e.ctrlKey && e.key === 'e') {
        e.preventDefault();
        if (!document.getElementById('exportBtn').disabled) {
            document.getElementById('exportBtn').click();
        }
    }
});

// Accessibility improvements
function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

// Performance monitoring
function measurePerformance(label, fn) {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    
    console.log(`${label} took ${end - start} milliseconds`);
    return result;
}

// Initialize tooltips and popovers if using Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});