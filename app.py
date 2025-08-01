#!/usr/bin/env python3
"""
Improved Flask Recruitment Analytics Dashboard
Now compatible with your specific Excel file structure
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import io
import base64
from werkzeug.utils import secure_filename
import os
import sqlite3
import hashlib
from contextlib import contextmanager
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'recruitment_data.db'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# Color palette for consistency
COLORS = ['#062C3A', '#ABC100', '#5D858B', '#00617E', '#00A4A6', '#97B8BB', 
          '#F4A41D', '#71164C', '#E2EC57', '#75A1D2', '#344893', '#00A78B', '#C8313F']

def create_clean_templates():
    """Create clean, separate template files"""
    
    # Create base.html - CLEAN VERSION
    base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Recruitment Analytics Dashboard{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    
    <style>
        :root {
            --primary-color: #062C3A;
            --secondary-color: #ABC100;
            --accent-1: #5D858B;
            --accent-2: #00617E;
        }
        
        body {
            background-color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;
        }
        
        .navbar {
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 1rem 0;
        }
        
        .text-primary {
            color: var(--primary-color) !important;
        }
        
        .btn-primary {
            background-color: var(--primary-color);
            border-color: var(--primary-color);
        }
        
        .btn-primary:hover {
            background-color: #051e26;
            border-color: #051e26;
        }
        
        .upload-area {
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            padding: 3rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            background-color: #fafafa;
        }
        
        .upload-area:hover {
            border-color: var(--primary-color);
            background-color: #f0f8ff;
        }
        
        .upload-area.dragover {
            border-color: var(--secondary-color);
            background-color: #f0fff0;
            transform: scale(1.02);
        }
        
        .kpi-card {
            background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
            border: 1px solid #dee2e6;
            border-radius: 12px;
            padding: 2rem 1.5rem;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .kpi-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
            line-height: 1;
        }
        
        .kpi-label {
            font-size: 0.9rem;
            color: #666;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            transition: box-shadow 0.3s ease;
        }
        
        .card:hover {
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        }
        
        .card-header {
            background-color: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            border-radius: 12px 12px 0 0 !important;
            padding: 1rem 1.5rem;
        }
        
        .nav-tabs {
            border-bottom: 2px solid #dee2e6;
        }
        
        .nav-tabs .nav-link {
            border: none;
            color: #666;
            font-weight: 500;
            padding: 1rem 1.5rem;
            transition: all 0.3s ease;
        }
        
        .nav-tabs .nav-link:hover {
            border-color: transparent;
            color: var(--primary-color);
            background-color: #f8f9fa;
        }
        
        .nav-tabs .nav-link.active {
            color: var(--primary-color);
            background-color: #fff;
            border-color: var(--primary-color) var(--primary-color) #fff;
            border-width: 0 0 3px 0;
            font-weight: 600;
        }
        
        .chart-container {
            min-height: 400px;
            padding: 1rem;
        }
        
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.9);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            flex-direction: column;
        }
        
        .debug-info {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            font-family: monospace;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .kpi-card {
                margin-bottom: 1rem;
                height: auto;
                padding: 1.5rem 1rem;
            }
            
            .kpi-value {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <nav class="navbar navbar-expand-lg navbar-light bg-white border-bottom">
        <div class="container-fluid">
            <div class="navbar-brand d-flex align-items-center">
                <i class="fas fa-chart-line fa-2x me-3 text-primary"></i>
                <h2 class="mb-0 text-primary">Recruitment Analytics Dashboard</h2>
            </div>
            <div class="navbar-nav ms-auto">
                <button class="btn btn-primary btn-sm" id="exportBtn" disabled>
                    <i class="fas fa-download me-2"></i>Export Report
                </button>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container-fluid mt-4">
        {% block content %}{% endblock %}
    </div>

    <!-- Loading Overlay -->
    <div id="loadingOverlay" class="loading-overlay d-none">
        <div class="loading-spinner">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Processing data...</p>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    {% block scripts %}{% endblock %}
</body>
</html>'''

    # Create index.html - CLEAN VERSION (extends base, no duplicate blocks)
    index_template = '''{% extends "base.html" %}

{% block content %}
<!-- File Upload Section -->
<div class="row mb-4" id="uploadSection">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-upload me-2"></i>Data Upload</h5>
            </div>
            <div class="card-body">
                <div class="upload-area" id="uploadArea">
                    <div class="upload-content">
                        <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                        <h5>Drag and Drop Excel File Here</h5>
                        <p class="text-muted">or click to browse</p>
                        <input type="file" id="fileInput" accept=".xlsx,.xls" style="display: none;">
                    </div>
                </div>
                <div id="uploadStatus" class="mt-3"></div>
                
                <!-- Debug Information -->
                <div id="debugInfo" class="debug-info d-none">
                    <h6>📊 File Analysis:</h6>
                    <div id="debugContent"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Dashboard Section -->
<div id="dashboardSection" class="d-none">
    <!-- Global Filters -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0"><i class="fas fa-filter me-2"></i>Global Filters</h5>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-3">
                            <label class="form-label">Hiring Manager</label>
                            <select class="form-select" id="filterHiringManager" multiple>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">TA Partner</label>
                            <select class="form-select" id="filterTAPartner" multiple>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Country</label>
                            <select class="form-select" id="filterCountry" multiple>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Project</label>
                            <select class="form-select" id="filterProject" multiple>
                            </select>
                        </div>
                    </div>
                    <div class="row g-3 mt-2">
                        <div class="col-md-6">
                            <label class="form-label">Date Range</label>
                            <div class="row">
                                <div class="col-6">
                                    <input type="date" class="form-control" id="startDate">
                                </div>
                                <div class="col-6">
                                    <input type="date" class="form-control" id="endDate">
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 d-flex align-items-end">
                            <button class="btn btn-secondary me-2" id="resetFilters">
                                <i class="fas fa-undo me-2"></i>Reset
                            </button>
                            <button class="btn btn-primary" id="applyFilters">
                                <i class="fas fa-search me-2"></i>Apply Filters
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Dashboard Tabs -->
    <div class="row">
        <div class="col-12">
            <ul class="nav nav-tabs" id="dashboardTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="hired-tab" data-bs-toggle="tab" data-bs-target="#hired-content" 
                            type="button" role="tab">
                        <i class="fas fa-chart-line me-2"></i>Hired Performance
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="pipeline-tab" data-bs-toggle="tab" data-bs-target="#pipeline-content" 
                            type="button" role="tab">
                        <i class="fas fa-tasks me-2"></i>Live Pipeline
                    </button>
                </li>
            </ul>
            
            <div class="tab-content" id="dashboardTabContent">
                <!-- Hired Performance Tab -->
                <div class="tab-pane fade" id="hired-content" role="tabpanel">
                    <!-- KPI Cards -->
                    <div class="row mb-4 mt-4">
                        <div class="col-md-3">
                            <div class="kpi-card">
                                <div class="kpi-value" id="totalFilled">-</div>
                                <div class="kpi-label">Total Positions Filled</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="kpi-card">
                                <div class="kpi-value" id="avgTTF">-</div>
                                <div class="kpi-label">Avg Time-to-Fill (days)</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="kpi-card">
                                <div class="kpi-value" id="overallConversion">-</div>
                                <div class="kpi-label">CV to Interview Rate (%)</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="kpi-card">
                                <div class="kpi-value" id="avgBudgetVariance">-</div>
                                <div class="kpi-label">Avg Budget Variance (%)</div>
                            </div>
                        </div>
                    </div>

                    <!-- AI Commentary -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="mb-0"><i class="fas fa-robot me-2"></i>AI Insights</h5>
                                </div>
                                <div class="card-body">
                                    <div id="hiredCommentary">Loading insights...</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Charts Row 1 -->
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="mb-0">Recruitment Funnel</h5>
                                </div>
                                <div class="card-body">
                                    <div id="funnelChart" class="chart-container"></div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="mb-0">Time-to-Fill Analysis</h5>
                                </div>
                                <div class="card-body">
                                    <div id="ttfChart" class="chart-container"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Charts Row 2 -->
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="mb-0">Financial Analysis</h5>
                                </div>
                                <div class="card-body">
                                    <div id="financialChart" class="chart-container"></div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="mb-0">Performance Leaderboard</h5>
                                </div>
                                <div class="card-body">
                                    <div id="leaderboardTable" class="chart-container"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Live Pipeline Tab -->
                <div class="tab-pane fade" id="pipeline-content" role="tabpanel">
                    <!-- KPI Cards -->
                    <div class="row mb-4 mt-4">
                        <div class="col-md-3">
                            <div class="kpi-card">
                                <div class="kpi-value" id="totalOpen">-</div>
                                <div class="kpi-label">Total Open Positions</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="kpi-card">
                                <div class="kpi-value" id="avgAge">-</div>
                                <div class="kpi-label">Avg Position Age (days)</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="kpi-card">
                                <div class="kpi-value" id="positionsOver60">-</div>
                                <div class="kpi-label">Positions >60 days</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="kpi-card">
                                <div class="kpi-value" id="bottleneckStage">-</div>
                                <div class="kpi-label">Most Common Stage</div>
                            </div>
                        </div>
                    </div>

                    <!-- AI Commentary -->
                    <div class="row mb-4">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="mb-0"><i class="fas fa-robot me-2"></i>AI Insights</h5>
                                </div>
                                <div class="card-body">
                                    <div id="pipelineCommentary">Loading insights...</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Charts -->
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="mb-0">Pipeline Stage Distribution</h5>
                                </div>
                                <div class="card-body">
                                    <div id="stageChart" class="chart-container"></div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5 class="mb-0">Resource Analysis</h5>
                                </div>
                                <div class="card-body">
                                    <div id="resourceChart" class="chart-container"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
// Professional Color Palette
const COLORS = ['#062C3A', '#ABC100', '#5D858B', '#00617E', '#00A4A6', '#97B8BB', 
                '#F4A41D', '#71164C', '#E2EC57', '#75A1D2', '#344893', '#00A78B', '#C8313F'];

// Global State Management
let dashboardState = {
    hasHiredData: false,
    hasFinalData: false,
    currentDashboard: 'hired',
    currentUploadId: null,
    isLoading: false,
    debugMode: true
};

// Application Initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Recruitment Analytics Dashboard...');
    initializeFileUpload();
    initializeFilters();
    initializeTabs();
    console.log('✅ Dashboard initialized successfully');
});

// File Upload System
function initializeFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleFileDrop);
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            processFileUpload(e.target.files[0]);
        }
    });
    
    console.log('📁 File upload system initialized');
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFileUpload(files[0]);
    }
}

function processFileUpload(file) {
    console.log('📤 Processing file upload:', file.name);
    
    // Show debug info
    if (dashboardState.debugMode) {
        showDebugInfo(`Processing: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
    }
    
    // Validate file type
    if (!file.name.match(/\\.(xlsx|xls)$/i)) {
        showNotification('Please upload an Excel file (.xlsx or .xls)', 'error');
        return;
    }
    
    // Validate file size (16MB limit)
    if (file.size > 16 * 1024 * 1024) {
        showNotification('File too large. Maximum size is 16MB.', 'error');
        return;
    }
    
    uploadFileToServer(file);
}

function uploadFileToServer(file) {
    dashboardState.isLoading = true;
    showLoadingState(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(handleUploadResponse)
    .catch(handleUploadError)
    .finally(() => {
        dashboardState.isLoading = false;
        showLoadingState(false);
    });
}

function handleUploadResponse(data) {
    if (data.success) {
        console.log('✅ File uploaded successfully');
        
        // Update dashboard state
        dashboardState.hasHiredData = data.has_hired;
        dashboardState.hasFinalData = data.has_final;
        dashboardState.currentUploadId = data.upload_id;
        
        // Show debug info
        if (dashboardState.debugMode && data.debug_info) {
            showDebugInfo(data.debug_info);
        }
        
        showNotification(data.message, 'success');
        initializeDashboard();
    } else {
        console.error('❌ Upload failed:', data.error);
        showNotification(data.error || 'Upload failed', 'error');
        
        // Show debug info for errors
        if (data.debug_info) {
            showDebugInfo(data.debug_info);
        }
    }
}

function handleUploadError(error) {
    console.error('❌ Upload error:', error);
    showNotification('Upload failed: ' + error.message, 'error');
}

function showDebugInfo(info) {
    const debugDiv = document.getElementById('debugInfo');
    const debugContent = document.getElementById('debugContent');
    
    debugContent.innerHTML = `<pre>${info}</pre>`;
    debugDiv.classList.remove('d-none');
}

// Dashboard Initialization
function initializeDashboard() {
    console.log('🎯 Initializing dashboard views...');
    
    // Show dashboard section
    document.getElementById('dashboardSection').classList.remove('d-none');
    document.getElementById('exportBtn').disabled = false;
    
    // Setup tabs based on available data
    setupDashboardTabs();
    
    // Load filter options
    loadFilterOptions();
    
    console.log('✅ Dashboard views initialized');
}

function setupDashboardTabs() {
    const hiredTab = document.getElementById('hired-tab');
    const pipelineTab = document.getElementById('pipeline-tab');
    
    // Reset tab states
    hiredTab.classList.remove('active', 'disabled');
    pipelineTab.classList.remove('active', 'disabled');
    
    if (dashboardState.hasHiredData) {
        console.log('📊 Hired data available - enabling hired tab');
        hiredTab.classList.add('active');
        document.getElementById('hired-content').classList.add('show', 'active');
        dashboardState.currentDashboard = 'hired';
        loadDashboardData('hired');
    } else {
        hiredTab.classList.add('disabled');
    }
    
    if (dashboardState.hasFinalData) {
        console.log('📈 Pipeline data available - enabling pipeline tab');
        if (!dashboardState.hasHiredData) {
            pipelineTab.classList.add('active');
            document.getElementById('pipeline-content').classList.add('show', 'active');
            document.getElementById('hired-content').classList.remove('show', 'active');
            dashboardState.currentDashboard = 'pipeline';
            loadDashboardData('pipeline');
        }
    } else {
        pipelineTab.classList.add('disabled');
    }
}

// Filter System
function initializeFilters() {
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('resetFilters').addEventListener('click', resetFilters);
    console.log('🔍 Filter system initialized');
}

function loadFilterOptions() {
    if (!dashboardState.currentUploadId) return;
    
    console.log('🔍 Loading filter options...');
    
    const params = new URLSearchParams();
    params.append('upload_id', dashboardState.currentUploadId);
    
    fetch(`/api/filter-options/${dashboardState.currentDashboard}?${params}`)
    .then(response => response.json())
    .then(populateFilterDropdowns)
    .catch(error => {
        console.error('❌ Error loading filter options:', error);
    });
}

function populateFilterDropdowns(data) {
    console.log('📝 Populating filter dropdowns');
    
    const filters = [
        { id: 'filterHiringManager', data: data.hiring_manager || [] },
        { id: 'filterTAPartner', data: data.ta_partner || [] },
        { id: 'filterCountry', data: data.country || [] },
        { id: 'filterProject', data: data.project || [] }
    ];
    
    filters.forEach(filter => {
        const select = document.getElementById(filter.id);
        select.innerHTML = '';
        
        filter.data.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            select.appendChild(optionElement);
        });
    });
    
    // Set date range
    if (data.date_range) {
        document.getElementById('startDate').value = data.date_range.min || '';
        document.getElementById('endDate').value = data.date_range.max || '';
    }
}

function applyFilters() {
    console.log('🔍 Applying filters...');
    loadDashboardData(dashboardState.currentDashboard);
}

function resetFilters() {
    console.log('🔄 Resetting filters...');
    
    // Clear all filter selections
    ['filterHiringManager', 'filterTAPartner', 'filterCountry', 'filterProject'].forEach(id => {
        document.getElementById(id).selectedIndex = -1;
    });
    
    // Clear date inputs
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    
    // Reload data
    loadDashboardData(dashboardState.currentDashboard);
}

// Tab Management
function initializeTabs() {
    document.getElementById('hired-tab').addEventListener('click', () => switchToTab('hired'));
    document.getElementById('pipeline-tab').addEventListener('click', () => switchToTab('pipeline'));
    console.log('📑 Tab system initialized');
}

function switchToTab(tabType) {
    if (tabType === 'hired' && !dashboardState.hasHiredData) return;
    if (tabType === 'pipeline' && !dashboardState.hasFinalData) return;
    
    console.log(`🔄 Switching to ${tabType} tab`);
    
    dashboardState.currentDashboard = tabType;
    loadDashboardData(tabType);
}

// Data Loading and Visualization
function loadDashboardData(dashboardType) {
    if (!dashboardState.currentUploadId) return;
    
    console.log(`📊 Loading ${dashboardType} dashboard data...`);
    showLoadingState(true);
    
    const params = buildFilterParams();
    
    fetch(`/api/dashboard-data/${dashboardType}?${params}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        
        if (dashboardType === 'hired') {
            renderHiredDashboard(data);
        } else {
            renderPipelineDashboard(data);
        }
        
        console.log(`✅ ${dashboardType} dashboard rendered`);
    })
    .catch(error => {
        console.error(`❌ Error loading ${dashboardType} data:`, error);
        showNotification('Error loading dashboard data', 'error');
    })
    .finally(() => {
        showLoadingState(false);
    });
}

function buildFilterParams() {
    const params = new URLSearchParams();
    params.append('upload_id', dashboardState.currentUploadId);
    
    // Add filter parameters
    const filters = [
        { id: 'filterHiringManager', param: 'hiring_manager' },
        { id: 'filterTAPartner', param: 'ta_partner' },
        { id: 'filterCountry', param: 'country' },
        { id: 'filterProject', param: 'project' }
    ];
    
    filters.forEach(filter => {
        const select = document.getElementById(filter.id);
        const selected = Array.from(select.selectedOptions).map(option => option.value);
        if (selected.length > 0) {
            params.append(filter.param, selected.join(','));
        }
    });
    
    // Add date range
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    return params.toString();
}

// Dashboard Rendering Functions
function renderHiredDashboard(data) {
    console.log('🎨 Rendering hired dashboard...');
    
    // Update KPIs
    if (data.kpis) {
        updateElement('totalFilled', data.kpis.total_filled.toLocaleString());
        updateElement('avgTTF', data.kpis.avg_ttf.toFixed(1));
        updateElement('overallConversion', data.kpis.overall_conversion.toFixed(1) + '%');
        updateElement('avgBudgetVariance', formatVariance(data.kpis.avg_budget_variance));
    }
    
    // Update commentary
    if (data.commentary) {
        updateElement('hiredCommentary', data.commentary);
    }
    
    // Render charts
    if (data.funnel) renderFunnelChart('funnelChart', data.funnel);
    if (data.ttf_by_role) renderTTFChart('ttfChart', data.ttf_by_role);
    if (data.financial) renderFinancialChart('financialChart', data.financial);
    if (data.leaderboard) renderLeaderboardTable('leaderboardTable', data.leaderboard);
}

function renderPipelineDashboard(data) {
    console.log('🎨 Rendering pipeline dashboard...');
    
    // Update KPIs
    if (data.kpis) {
        updateElement('totalOpen', data.kpis.total_open.toLocaleString());
        updateElement('avgAge', data.kpis.avg_age.toFixed(1));
        updateElement('positionsOver60', data.kpis.positions_over_60.toLocaleString());
        updateElement('bottleneckStage', data.kpis.bottleneck_stage);
    }
    
    // Update commentary
    if (data.commentary) {
        updateElement('pipelineCommentary', data.commentary);
    }
    
    // Render charts
    if (data.stage_distribution) renderStageChart('stageChart', data.stage_distribution);
    if (data.resource_distribution) renderResourceChart('resourceChart', data.resource_distribution);
}

// Chart Rendering Functions
function renderFunnelChart(elementId, data) {
    if (!data.stages || !data.values) return;
    
    const trace = {
        type: 'funnel',
        y: data.stages,
        x: data.values,
        textinfo: 'value+percent initial',
        marker: { color: COLORS.slice(0, data.stages.length) },
        connector: { line: { color: 'rgba(0,0,0,0.3)', width: 2 } }
    };

    const layout = {
        title: { text: 'Recruitment Funnel Analysis', font: { size: 16, color: COLORS[0] } },
        margin: { t: 60, l: 100, r: 50, b: 50 },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white'
    };

    Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
}

function renderTTFChart(elementId, data) {
    if (!data.roles || !data.values) return;
    
    const trace = {
        type: 'bar',
        x: data.values,
        y: data.roles,
        orientation: 'h',
        marker: { color: COLORS[0] },
        text: data.values.map(v => `${v.toFixed(1)} days`),
        textposition: 'inside',
        textfont: { color: 'white' }
    };

    const layout = {
        title: { text: 'Average Time-to-Fill by Role', font: { size: 16, color: COLORS[0] } },
        xaxis: { title: 'Days' },
        yaxis: { title: 'Role', automargin: true },
        margin: { t: 60, l: 150, r: 50, b: 80 },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white'
    };

    Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
}

function renderFinancialChart(elementId, data) {
    if (!data.variance_data || data.variance_data.length === 0) {
        document.getElementById(elementId).innerHTML = '<p class="text-muted text-center">No financial data available</p>';
        return;
    }
    
    const trace = {
        type: 'histogram',
        x: data.variance_data,
        marker: { color: COLORS[1], opacity: 0.8 },
        nbinsx: 15
    };

    const layout = {
        title: { text: 'Budget Variance Distribution', font: { size: 16, color: COLORS[0] } },
        xaxis: { title: 'Budget Variance (%)' },
        yaxis: { title: 'Number of Positions' },
        margin: { t: 60, l: 80, r: 50, b: 80 },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white'
    };

    Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
}

function renderStageChart(elementId, data) {
    if (!data.stages || !data.values) return;
    
    const trace = {
        type: 'bar',
        x: data.stages,
        y: data.values,
        marker: { color: COLORS.slice(0, data.stages.length) },
        text: data.values,
        textposition: 'outside'
    };

    const layout = {
        title: { text: 'Pipeline Stage Distribution', font: { size: 16, color: COLORS[0] } },
        xaxis: { title: 'Job State' },
        yaxis: { title: 'Number of Positions' },
        margin: { t: 60, l: 80, r: 50, b: 100 },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white'
    };

    Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
}

function renderResourceChart(elementId, data) {
    if (!data.stages || !data.values) return;
    
    const trace = {
        type: 'pie',
        labels: data.stages,
        values: data.values,
        marker: { colors: COLORS.slice(0, data.stages.length) },
        textinfo: 'label+percent',
        textposition: 'auto'
    };

    const layout = {
        title: { text: 'Resource Distribution', font: { size: 16, color: COLORS[0] } },
        margin: { t: 60, l: 50, r: 50, b: 50 },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white'
    };

    Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
}

function renderLeaderboardTable(elementId, data) {
    if (!data || data.length === 0) {
        document.getElementById(elementId).innerHTML = '<p class="text-muted text-center">No leaderboard data available</p>';
        return;
    }

    let tableHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>Rank</th>
                        <th>TA Partner</th>
                        <th>Avg TTF</th>
                        <th>CV-Interview %</th>
                        <th>Total Hires</th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach((partner, index) => {
        const rankClass = index === 0 ? 'table-success' : '';
        const rankIcon = index === 0 ? '🏆' : index === 1 ? '🥈' : index === 2 ? '🥉' : '';
        
        tableHTML += `
            <tr class="${rankClass}">
                <td><strong>${rankIcon} ${index + 1}</strong></td>
                <td>${partner.ta_partner}</td>
                <td>${typeof partner.avg_ttf === 'number' ? partner.avg_ttf.toFixed(1) : 'N/A'}</td>
                <td>${typeof partner.conversion_rate === 'number' ? partner.conversion_rate.toFixed(1) + '%' : 'N/A'}</td>
                <td>${partner.total_hires}</td>
            </tr>
        `;
    });

    tableHTML += '</tbody></table></div>';
    document.getElementById(elementId).innerHTML = tableHTML;
}

// Utility Functions
function updateElement(id, content) {
    const element = document.getElementById(id);
    if (element) {
        element.innerHTML = content;
    }
}

function formatVariance(value) {
    if (typeof value !== 'number') return 'N/A';
    return (value >= 0 ? '+' : '') + value.toFixed(1) + '%';
}

function showNotification(message, type = 'info') {
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
    
    const uploadStatus = document.getElementById('uploadStatus');
    uploadStatus.innerHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="${icon} me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    console.log(`📢 Notification: ${message} (${type})`);
}

function showLoadingState(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.remove('d-none');
    } else {
        overlay.classList.add('d-none');
    }
}

// Error Handling
window.addEventListener('error', function(e) {
    console.error('❌ JavaScript Error:', e.error);
    showNotification('An unexpected error occurred. Please refresh the page.', 'error');
});

// Console Welcome Message
console.log('%c🎯 Recruitment Analytics Dashboard', 'color: #062C3A; font-size: 20px; font-weight: bold;');
console.log('%c✨ Compatible with your Excel file structure', 'color: #ABC100; font-size: 14px;');
console.log('%c🚀 Ready for analysis', 'color: #5D858B; font-size: 12px;');
</script>
{% endblock %}'''

    # Write clean template files
    try:
        with open('templates/base.html', 'w', encoding='utf-8') as f:
            f.write(base_template)
        print("✅ Created clean base.html template")
        
        with open('templates/index.html', 'w', encoding='utf-8') as f:
            f.write(index_template)
        print("✅ Created clean index.html template")
        
        return True
    except Exception as e:
        print(f"❌ Error creating templates: {e}")
        return False

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize SQLite database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                has_hired_sheet BOOLEAN DEFAULT 0,
                has_final_sheet BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hired_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER,
                job_ref_id TEXT,
                ta_partner TEXT,
                position_created_date DATE,
                job_title TEXT,
                job_location_country TEXT,
                project_name TEXT,
                max_budgeted_salary REAL,
                accepted_salary REAL,
                accepted_salary_currency TEXT,
                sourcing_partner TEXT,
                hiring_manager TEXT,
                filled_date DATE,
                number_of_cvs_shared INTEGER,
                number_of_cvs_shortlisted INTEGER,
                number_of_candidates_interviewed INTEGER,
                number_of_candidates_offered INTEGER,
                number_of_candidates_accepted_offer INTEGER,
                job_state TEXT,
                business_line TEXT,
                service_line TEXT,
                time_to_fill INTEGER,
                budget_variance_pct REAL,
                cv_to_interview_rate REAL,
                FOREIGN KEY (upload_id) REFERENCES uploads (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS final_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER,
                job_ref_id TEXT,
                ta_partner TEXT,
                position_created_date DATE,
                job_title TEXT,
                job_location_country TEXT,
                project_name TEXT,
                max_budgeted_salary REAL,
                accepted_salary REAL,
                sourcing_partner TEXT,
                hiring_manager TEXT,
                number_of_cvs_shared INTEGER,
                number_of_cvs_shortlisted INTEGER,
                number_of_candidates_interviewed INTEGER,
                number_of_candidates_offered INTEGER,
                number_of_candidates_accepted_offer INTEGER,
                job_state TEXT,
                business_line TEXT,
                service_line TEXT,
                position_age INTEGER,
                cv_to_interview_rate REAL,
                FOREIGN KEY (upload_id) REFERENCES uploads (id)
            )
        ''')
        
        conn.commit()

def prepare_df(df, sheet_type):
    """Prepare and clean dataframe - Updated for your Excel structure"""
    if df is None or df.empty:
        return df, "DataFrame is empty"
        
    df = df.copy()
    debug_info = []
    
    debug_info.append(f"Original columns: {list(df.columns)}")
    debug_info.append(f"Original shape: {df.shape}")
    
    # Column mapping based on your Excel file structure
    if sheet_type == 'hired':
        column_mapping = {
            'Job Ref ID': 'job_ref_id',
            'TAPartner': 'ta_partner',
            'Position Created Date': 'position_created_date',
            'Job Title': 'job_title',
            'Job Location (country)': 'job_location_country',
            'Project Name': 'project_name',
            'Max budgeted salary': 'max_budgeted_salary',
            'Accepted salary': 'accepted_salary',
            'Accepted salary Currency': 'accepted_salary_currency',
            'Sourcing Partner': 'sourcing_partner',
            'Hiring Manager': 'hiring_manager',
            'Filled Date': 'filled_date',
            'Number of CVs shared': 'number_of_cvs_shared',
            'Number of CVs shortlisted': 'number_of_cvs_shortlisted',
            'Number of candidates interviewed': 'number_of_candidates_interviewed',
            'Number of candidates offered': 'number_of_candidates_offered',
            'Number of candidates accepted offer': 'number_of_candidates_accepted_offer',
            'Job State': 'job_state',
            'Business Line': 'business_line',
            'Service Line': 'service_line'
        }
    else:  # final
        column_mapping = {
            'Job Ref ID': 'job_ref_id',
            'TA Partner': 'ta_partner',
            'Position Created Date': 'position_created_date',
            'Job Title': 'job_title',
            'Job Location (country)': 'job_location_country',
            'Project Name': 'project_name',
            'Max budgeted salary': 'max_budgeted_salary',
            'Accepted salary': 'accepted_salary',
            'Sourcing Partner': 'sourcing_partner',
            'Hiring Manager': 'hiring_manager',
            'Number of CVs shared': 'number_of_cvs_shared',
            'Number of CVs shortlisted': 'number_of_cvs_shortlisted',
            'Number of candidates interviewed': 'number_of_candidates_interviewed',
            'Number of candidates offered': 'number_of_candidates_offered',
            'Number of candidates accepted offer': 'number_of_candidates_accepted_offer',
            'Job State': 'job_state',
            'Business Line': 'business_line',
            'Service Line': 'service_line'
        }
    
    # Apply column mapping
    columns_found = []
    columns_missing = []
    
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})
            columns_found.append(f"{old_col} -> {new_col}")
        else:
            columns_missing.append(old_col)
    
    debug_info.append(f"Columns mapped: {columns_found}")
    if columns_missing:
        debug_info.append(f"Columns missing: {columns_missing}")
    
    # Convert date columns
    date_cols = ['position_created_date']
    if sheet_type == 'hired':
        date_cols.append('filled_date')
    
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            debug_info.append(f"Converted {col} to datetime")
    
    # Convert numeric columns
    numeric_cols = ['number_of_cvs_shared', 'number_of_cvs_shortlisted', 
                   'number_of_candidates_interviewed', 'number_of_candidates_offered',
                   'number_of_candidates_accepted_offer', 'max_budgeted_salary', 'accepted_salary']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            debug_info.append(f"Converted {col} to numeric")
    
    # Calculate derived metrics
    if sheet_type == 'hired':
        if 'filled_date' in df.columns and 'position_created_date' in df.columns:
            df['time_to_fill'] = (df['filled_date'] - df['position_created_date']).dt.days
            debug_info.append("Calculated time_to_fill")
        
        if 'accepted_salary' in df.columns and 'max_budgeted_salary' in df.columns:
            df['budget_variance_pct'] = ((df['accepted_salary'] - df['max_budgeted_salary']) / df['max_budgeted_salary'] * 100)
            debug_info.append("Calculated budget_variance_pct")
    
    if sheet_type == 'final':
        if 'position_created_date' in df.columns:
            df['position_age'] = (datetime.now() - df['position_created_date']).dt.days
            debug_info.append("Calculated position_age")
    
    # Calculate conversion rates
    if all(col in df.columns for col in ['number_of_cvs_shared', 'number_of_candidates_interviewed']):
        df['cv_to_interview_rate'] = np.where(df['number_of_cvs_shared'] > 0, 
                                            df['number_of_candidates_interviewed'] / df['number_of_cvs_shared'] * 100, 0)
        debug_info.append("Calculated cv_to_interview_rate")
    
    # Fill missing values
    categorical_cols = ['ta_partner', 'job_location_country', 'project_name', 'business_line', 
                       'job_state', 'sourcing_partner', 'hiring_manager']
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown')
    
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    debug_info.append(f"Final shape: {df.shape}")
    debug_info.append(f"Final columns: {list(df.columns)}")
    
    return df, "\\n".join(debug_info)

def save_to_database(df, sheet_type, upload_id):
    """Save dataframe to database"""
    if df is None or df.empty:
        return
        
    with get_db_connection() as conn:
        df_clean = df.copy()
        df_clean['upload_id'] = upload_id
        
        # Convert datetime to string
        for col in df_clean.columns:
            if df_clean[col].dtype == 'datetime64[ns]':
                df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d').replace('NaT', None)
        
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        
        table_name = 'hired_data' if sheet_type == 'hired' else 'final_data'
        
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {table_name} WHERE upload_id = ?', (upload_id,))
        df_clean.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()

def load_from_database(sheet_type, upload_id=None):
    """Load data from database"""
    with get_db_connection() as conn:
        table_name = 'hired_data' if sheet_type == 'hired' else 'final_data'
        
        if upload_id:
            query = f'SELECT * FROM {table_name} WHERE upload_id = ?'
            df = pd.read_sql_query(query, conn, params=(upload_id,))
        else:
            query = f'''
                SELECT d.* FROM {table_name} d
                JOIN uploads u ON d.upload_id = u.id
                WHERE u.id = (SELECT MAX(id) FROM uploads)
            '''
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return None
            
        # Convert date strings back to datetime
        date_columns = ['position_created_date']
        if sheet_type == 'hired':
            date_columns.append('filled_date')
        
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df

# Initialize on startup
init_database()
if not create_clean_templates():
    print("❌ Failed to create templates")
    exit(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename and file.filename.endswith(('.xlsx', '.xls')):
        try:
            # Read and process file
            file_content = file.read()
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Check for existing file
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM uploads WHERE file_hash = ?', (file_hash,))
                existing = cursor.fetchone()
                
                if existing:
                    return jsonify({
                        'success': True,
                        'message': 'File already exists in database. Loading existing data.',
                        'has_hired': True,
                        'has_final': True,
                        'upload_id': existing['id']
                    })
            
            # Process new file
            file.seek(0)
            excel_file = pd.ExcelFile(io.BytesIO(file.read()))
            file.seek(0)
            
            debug_info = []
            debug_info.append(f"📊 Sheets found: {excel_file.sheet_names}")
            
            hired_data = None
            final_data = None
            has_hired = False
            has_final = False
            
            # Process sheets
            if 'Hired' in excel_file.sheet_names:
                try:
                    hired_df = pd.read_excel(file, sheet_name='Hired')
                    hired_data, hired_debug = prepare_df(hired_df, 'hired')
                    debug_info.append(f"✅ Hired sheet processed: {len(hired_data)} rows")
                    debug_info.append(hired_debug)
                    has_hired = True
                except Exception as e:
                    debug_info.append(f"❌ Error processing Hired sheet: {str(e)}")
            
            if 'Final' in excel_file.sheet_names:
                try:
                    final_df = pd.read_excel(file, sheet_name='Final')
                    final_data, final_debug = prepare_df(final_df, 'final')
                    debug_info.append(f"✅ Final sheet processed: {len(final_data)} rows")
                    debug_info.append(final_debug)
                    has_final = True
                except Exception as e:
                    debug_info.append(f"❌ Error processing Final sheet: {str(e)}")
            
            if not has_hired and not has_final:
                return jsonify({
                    'error': 'No "Hired" or "Final" sheets could be processed successfully',
                    'debug_info': "\n".join(debug_info)
                }), 400
            
            # Save to database
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO uploads (filename, file_hash, has_hired_sheet, has_final_sheet)
                    VALUES (?, ?, ?, ?)
                ''', (secure_filename(file.filename), file_hash, has_hired, has_final))
                upload_id = cursor.lastrowid
                conn.commit()
            
            # Save data
            if hired_data is not None and not hired_data.empty:
                save_to_database(hired_data, 'hired', upload_id)
                debug_info.append(f"💾 Saved {len(hired_data)} hired records to database")
            
            if final_data is not None and not final_data.empty:
                save_to_database(final_data, 'final', upload_id)
                debug_info.append(f"💾 Saved {len(final_data)} pipeline records to database")
            
            return jsonify({
                'success': True,
                'message': f'Successfully processed {file.filename}! Found {len(hired_data) if hired_data is not None else 0} hired records and {len(final_data) if final_data is not None else 0} pipeline records.',
                'has_hired': has_hired,
                'has_final': has_final,
                'upload_id': upload_id,
                'debug_info': "\n".join(debug_info)
            })
            
        except Exception as e:
            return jsonify({
                'error': f'Error processing file: {str(e)}',
                'debug_info': f"Critical error during file processing: {str(e)}"
            }), 500
    
    return jsonify({'error': 'Invalid file format. Please upload an Excel file'}), 400

@app.route('/api/filter-options/<dashboard_type>')
def get_filter_options(dashboard_type):
    upload_id = request.args.get('upload_id')
    df = load_from_database('hired' if dashboard_type == 'hired' else 'final', upload_id)
    
    if df is None or df.empty:
        return jsonify({})
    
    options = {}
    
    # Map to your actual column names
    filter_mapping = {
        'hiring_manager': 'hiring_manager',
        'ta_partner': 'ta_partner', 
        'country': 'job_location_country',
        'project': 'project_name'
    }
    
    for filter_key, col_name in filter_mapping.items():
        if col_name in df.columns:
            unique_values = sorted([str(val) for val in df[col_name].unique() if pd.notna(val) and str(val) != 'Unknown'])
            options[filter_key] = unique_values
    
    if 'position_created_date' in df.columns:
        min_date = df['position_created_date'].min().strftime('%Y-%m-%d') if pd.notna(df['position_created_date'].min()) else None
        max_date = df['position_created_date'].max().strftime('%Y-%m-%d') if pd.notna(df['position_created_date'].max()) else None
        options['date_range'] = {'min': min_date, 'max': max_date}
    
    return jsonify(options)

@app.route('/api/dashboard-data/<dashboard_type>')
def get_dashboard_data(dashboard_type):
    upload_id = request.args.get('upload_id')
    df = load_from_database('hired' if dashboard_type == 'hired' else 'final', upload_id)
    
    if df is None or df.empty:
        return jsonify({'error': 'No data available'})
    
    # Apply filters
    filtered_df = df.copy()
    
    # Filter mapping
    filter_mapping = {
        'hiring_manager': 'hiring_manager',
        'ta_partner': 'ta_partner',
        'country': 'job_location_country', 
        'project': 'project_name'
    }
    
    for param, col_name in filter_mapping.items():
        values = request.args.get(param)
        if values and col_name in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[col_name].isin(values.split(','))]
    
    # Filter by date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date and end_date and 'position_created_date' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['position_created_date'] >= start_date) & 
            (filtered_df['position_created_date'] <= end_date)
        ]
    
    if dashboard_type == 'hired':
        return get_hired_dashboard_data(filtered_df)
    else:
        return get_pipeline_dashboard_data(filtered_df)

def get_hired_dashboard_data(df):
    """Generate hired dashboard data"""
    data = {}
    
    # KPIs
    data['kpis'] = {
        'total_filled': len(df),
        'avg_ttf': df['time_to_fill'].mean() if 'time_to_fill' in df.columns else 0,
        'overall_conversion': df['cv_to_interview_rate'].mean() if 'cv_to_interview_rate' in df.columns else 0,
        'avg_budget_variance': df['budget_variance_pct'].mean() if 'budget_variance_pct' in df.columns else 0
    }
    
    # Commentary
    total_positions = len(df)
    avg_ttf = data['kpis']['avg_ttf']
    
    commentary = f"<strong>📊 Performance Overview:</strong> {total_positions:,} positions successfully filled<br><br>"
    
    if avg_ttf <= 30:
        commentary += f"<strong>⚡ Excellent Speed:</strong> Average time-to-fill of {avg_ttf:.1f} days indicates highly efficient recruitment"
    elif avg_ttf <= 45:
        commentary += f"<strong>✅ Good Performance:</strong> Time-to-fill of {avg_ttf:.1f} days meets industry standards"
    else:
        commentary += f"<strong>⚠️ Improvement Opportunity:</strong> Time-to-fill of {avg_ttf:.1f} days exceeds typical benchmarks"
    
    data['commentary'] = commentary
    
    # Funnel data - using your actual column names
    cvs_col = 'number_of_cvs_shared'
    interviews_col = 'number_of_candidates_interviewed'
    offers_col = 'number_of_candidates_offered'
    accepted_col = 'number_of_candidates_accepted_offer'
    
    if all(col in df.columns for col in [cvs_col, interviews_col, offers_col, accepted_col]):
        data['funnel'] = {
            'stages': ['CVs Shared', 'Interviews', 'Offers', 'Accepted'],
            'values': [
                int(df[cvs_col].sum()),
                int(df[interviews_col].sum()),
                int(df[offers_col].sum()),
                int(df[accepted_col].sum())
            ]
        }
    
    # TTF by role
    if 'time_to_fill' in df.columns and 'job_title' in df.columns:
        # Group by job title and calculate average TTF
        ttf_by_role = df.groupby('job_title')['time_to_fill'].mean().sort_values(ascending=True).head(10)
        data['ttf_by_role'] = {
            'roles': ttf_by_role.index.tolist(),
            'values': ttf_by_role.values.tolist()
        }
    
    # Financial data
    if 'budget_variance_pct' in df.columns:
        variance_data = df['budget_variance_pct'].dropna()
        if len(variance_data) > 0:
            data['financial'] = {
                'variance_data': variance_data.tolist()
            }
    
    # Leaderboard
    if 'ta_partner' in df.columns:
        leaderboard = df.groupby('ta_partner').agg({
            'time_to_fill': 'mean',
            'cv_to_interview_rate': 'mean',
            'job_ref_id': 'count'  # Count total hires
        }).round(1).reset_index()
        
        leaderboard.columns = ['ta_partner', 'avg_ttf', 'conversion_rate', 'total_hires']
        leaderboard = leaderboard.sort_values('avg_ttf').head(10)
        
        data['leaderboard'] = leaderboard.to_dict('records')
    
    return jsonify(data)

def get_pipeline_dashboard_data(df):
    """Generate pipeline dashboard data"""
    data = {}
    
    # KPIs
    data['kpis'] = {
        'total_open': len(df),
        'avg_age': df['position_age'].mean() if 'position_age' in df.columns else 0,
        'positions_over_60': len(df[df['position_age'] > 60]) if 'position_age' in df.columns else 0,
        'bottleneck_stage': df['job_state'].value_counts().index[0] if 'job_state' in df.columns and len(df) > 0 else 'None'
    }
    
    # Commentary
    total_open = len(df)
    avg_age = data['kpis']['avg_age']
    
    commentary = f"<strong>🎯 Pipeline Status:</strong> {total_open:,} active positions in recruitment pipeline<br><br>"
    
    if 'position_age' in df.columns:
        old_positions = df[df['position_age'] > 60]
        if len(old_positions) > 0:
            commentary += f"<strong>🔍 Action Required:</strong> {len(old_positions)} positions over 60 days need priority attention"
        else:
            commentary += f"<strong>📈 Healthy Pipeline:</strong> All positions under 60 days, average age {avg_age:.1f} days"
    
    data['commentary'] = commentary
    
    # Stage distribution
    if 'job_state' in df.columns:
        stage_counts = df['job_state'].value_counts()
        data['stage_distribution'] = {
            'stages': stage_counts.index.tolist(),
            'values': stage_counts.values.tolist()
        }
    
    # Resource distribution - by project
    if 'project_name' in df.columns:
        project_counts = df['project_name'].value_counts().head(10)
        data['resource_distribution'] = {
            'stages': project_counts.index.tolist(),
            'values': project_counts.values.tolist()
        }
    
    return jsonify(data)

if __name__ == '__main__':
    print("🚀 Starting Enhanced Recruitment Analytics Dashboard...")
    print("📊 Compatible with your Excel file structure")
    print("✨ Supports 'Hired' and 'Final' sheets")
    print("🎯 Access dashboard at: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)