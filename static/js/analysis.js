// Analysis Dashboard JavaScript for data visualization and interactive features

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs and filters
    initializeTabsAndFilters();
    
    // Load initial data
    loadAnalysisData();
    
    // Setup auto-refresh (every 2 minutes)
    setInterval(loadAnalysisData, 120000);
});

function initializeTabsAndFilters() {
    // Set up event listeners for trend time period buttons
    const trendWeekBtn = document.getElementById('trend-week');
    const trendMonthBtn = document.getElementById('trend-month');
    
    if (trendWeekBtn && trendMonthBtn) {
        trendWeekBtn.addEventListener('click', function() {
            setActiveTrendButton(trendWeekBtn, trendMonthBtn);
            loadTrendData('week');
        });
        
        trendMonthBtn.addEventListener('click', function() {
            setActiveTrendButton(trendMonthBtn, trendWeekBtn);
            loadTrendData('month');
        });
    }
}

function setActiveTrendButton(activeBtn, inactiveBtn) {
    activeBtn.classList.add('active');
    inactiveBtn.classList.remove('active');
}

function loadAnalysisData() {
    // Load incident trends data (default to week view)
    loadTrendData('week');
    
    // Load severity distribution data
    loadSeverityData();
    
    // Load team performance data if admin access is available
    const teamPerformanceChart = document.getElementById('teamPerformanceChart');
    if (teamPerformanceChart) {
        loadTeamPerformanceData();
    }
    
    // Load prediction data if admin access is available
    const predictionContainer = document.getElementById('predictionContainer');
    if (predictionContainer) {
        loadPredictionData();
    }
}

function loadTrendData(period) {
    fetch('/api/analysis/incident-trends')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateTrendChart(data, period);
            updateMetrics(data);
        })
        .catch(error => {
            console.error('Error loading trend data:', error);
            displayErrorMessage('Failed to load incident trend data');
        });
}

function updateTrendChart(data, period) {
    const trendsCanvas = document.getElementById('incidentTrendsChart');
    if (!trendsCanvas) return;
    
    // Process data based on period
    let filteredData = data.incidents_by_day;
    
    if (period === 'week') {
        // Filter to last 7 days
        filteredData = filteredData.slice(-7);
    } else if (period === 'month') {
        // Filter to last 30 days
        filteredData = filteredData.slice(-30);
    }
    
    const labels = filteredData.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', {month: 'short', day: 'numeric'});
    });
    
    const counts = filteredData.map(item => item.count);
    
    // Check if chart instance exists and destroy it
    if (window.trendsChart) {
        window.trendsChart.destroy();
    }
    
    // Create new chart
    const ctx = trendsCanvas.getContext('2d');
    window.trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Incidents',
                data: counts,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function updateMetrics(data) {
    // Update average resolution time
    const avgResolutionTimeElement = document.getElementById('avgResolutionTime');
    if (avgResolutionTimeElement) {
        avgResolutionTimeElement.textContent = data.avg_resolution_time 
            ? `${data.avg_resolution_time.toFixed(1)} hrs` 
            : 'N/A';
    }
    
    // Update total incidents
    const totalIncidentsElement = document.getElementById('totalIncidents');
    if (totalIncidentsElement && data.incidents_by_day) {
        const total = data.incidents_by_day.reduce((sum, item) => sum + item.count, 0);
        totalIncidentsElement.textContent = total;
    }
}

function loadSeverityData() {
    fetch('/api/analysis/incident-trends')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateSeverityChart(data.incidents_by_severity);
        })
        .catch(error => {
            console.error('Error loading severity data:', error);
            displayErrorMessage('Failed to load severity distribution data');
        });
}

function updateSeverityChart(severityData) {
    const canvas = document.getElementById('severityChart');
    if (!canvas) return;
    
    // Map severities to display names and colors
    const severityLabels = severityData.map(item => {
        const label = item.severity.charAt(0).toUpperCase() + item.severity.slice(1);
        return label;
    });
    
    const severityCounts = severityData.map(item => item.count);
    
    const backgroundColors = severityData.map(item => {
        switch(item.severity) {
            case 'critical': return 'rgba(220, 53, 69, 0.7)';
            case 'high': return 'rgba(255, 193, 7, 0.7)';
            case 'medium': return 'rgba(23, 162, 184, 0.7)';
            case 'low': return 'rgba(40, 167, 69, 0.7)';
            default: return 'rgba(108, 117, 125, 0.7)';
        }
    });
    
    const borderColors = severityData.map(item => {
        switch(item.severity) {
            case 'critical': return 'rgb(220, 53, 69)';
            case 'high': return 'rgb(255, 193, 7)';
            case 'medium': return 'rgb(23, 162, 184)';
            case 'low': return 'rgb(40, 167, 69)';
            default: return 'rgb(108, 117, 125)';
        }
    });
    
    // Check if chart instance exists and destroy it
    if (window.severityChart) {
        window.severityChart.destroy();
    }
    
    // Create new chart
    const ctx = canvas.getContext('2d');
    window.severityChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: severityLabels,
            datasets: [{
                data: severityCounts,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function loadTeamPerformanceData() {
    fetch('/api/analysis/performance')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateTeamPerformanceChart(data);
            updateTeamResolutionTable(data.team_resolution_times);
        })
        .catch(error => {
            console.error('Error loading team performance data:', error);
            displayErrorMessage('Failed to load team performance data');
        });
}

function updateTeamPerformanceChart(data) {
    const canvas = document.getElementById('teamPerformanceChart');
    if (!canvas) return;
    
    const teamLabels = data.team_incident_counts.map(item => `Team ${item.team_id}`);
    const incidentCounts = data.team_incident_counts.map(item => item.count);
    
    // Check if chart instance exists and destroy it
    if (window.teamPerformanceChart) {
        window.teamPerformanceChart.destroy();
    }
    
    // Create new chart
    const ctx = canvas.getContext('2d');
    window.teamPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: teamLabels,
            datasets: [{
                label: 'Incidents Handled',
                data: incidentCounts,
                backgroundColor: 'rgba(106, 90, 205, 0.7)',
                borderColor: 'rgba(106, 90, 205, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function updateTeamResolutionTable(resolutionData) {
    const container = document.getElementById('teamPerformanceMetrics');
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    if (resolutionData.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No resolution time data available</p>';
        return;
    }
    
    // Find maximum resolution time for scaling the progress bars
    const maxResolutionTime = Math.max(...resolutionData.map(item => item.resolution_time));
    const scaleFactor = maxResolutionTime > 0 ? 100 / maxResolutionTime : 0;
    
    // Sort by resolution time (ascending)
    resolutionData.sort((a, b) => a.resolution_time - b.resolution_time);
    
    // Add each team's metrics
    resolutionData.forEach(item => {
        const teamName = `Team ${item.team_id}`;
        const resolutionTime = item.resolution_time.toFixed(1);
        
        const progressWidth = Math.max(5, item.resolution_time * scaleFactor); // Ensure at least 5% width for visibility
        
        const progressBar = document.createElement('div');
        progressBar.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span>${teamName}</span>
                <span class="badge bg-primary rounded-pill">${resolutionTime} hrs</span>
            </div>
            <div class="progress mb-3" style="height: 10px;">
                <div class="progress-bar bg-info" role="progressbar" 
                     style="width: ${progressWidth}%;" 
                     aria-valuenow="${item.resolution_time}" 
                     aria-valuemin="0" 
                     aria-valuemax="${maxResolutionTime}"></div>
            </div>
        `;
        container.appendChild(progressBar);
    });
}

function loadPredictionData() {
    fetch('/api/analysis/prediction')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updatePredictionCards(data.predictions);
        })
        .catch(error => {
            console.error('Error loading prediction data:', error);
            displayErrorMessage('Failed to load incident predictions');
        });
}

function updatePredictionCards(predictions) {
    const container = document.getElementById('predictionContainer');
    if (!container) return;
    
    // Clear container
    container.innerHTML = '';
    
    if (predictions.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No prediction data available</p>';
        return;
    }
    
    // Create cards for each prediction
    predictions.forEach(prediction => {
        const count = prediction.predicted_incidents;
        
        // Determine severity based on predicted count
        let severityClass = 'prediction-low';
        let severityText = 'Low';
        let badgeClass = 'bg-success';
        
        if (count >= 5) {
            severityClass = 'prediction-high';
            severityText = 'High';
            badgeClass = 'bg-danger';
        } else if (count >= 3) {
            severityClass = 'prediction-medium';
            severityText = 'Medium';
            badgeClass = 'bg-warning text-dark';
        }
        
        // Format date
        const dateObj = new Date(prediction.date);
        const formattedDate = dateObj.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        });
        
        // Create card
        const cardDiv = document.createElement('div');
        cardDiv.className = 'col-md-4 mb-3';
        cardDiv.innerHTML = `
            <div class="card prediction-card ${severityClass}">
                <div class="card-body text-center">
                    <h6 class="card-title">${formattedDate}</h6>
                    <h2 class="display-4">${count}</h2>
                    <span class="badge ${badgeClass}">${severityText}</span>
                </div>
            </div>
        `;
        
        container.appendChild(cardDiv);
    });
}

function displayErrorMessage(message) {
    // Create a dismissible alert for error messages
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        <i class="fas fa-exclamation-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find the first .chart-container and insert before it
    const chartContainer = document.querySelector('.chart-container');
    if (chartContainer && chartContainer.parentNode) {
        chartContainer.parentNode.insertBefore(alertDiv, chartContainer);
        
        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 300);
        }, 10000);
    }
}
