// Dashboard JavaScript for real-time updates and interactive features

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-refresh dashboard data every 30 seconds
    setInterval(refreshDashboardData, 30000);
    
    // Initialize dashboard charts
    initDashboardCharts();
});

function refreshDashboardData() {
    // Fetch updated stats
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            // Update total incidents
            document.querySelector('.card.bg-primary .display-4').textContent = data.total;
            
            // Update open & assigned
            document.querySelector('.card.bg-warning .display-4').textContent = 
                data.by_status.open + data.by_status.assigned;
            
            // Update in progress
            document.querySelector('.card.bg-info .display-4').textContent = 
                data.by_status.in_progress;
            
            // Update resolved & closed
            document.querySelector('.card.bg-success .display-4').textContent = 
                data.by_status.resolved + data.by_status.closed;
            
            // Update severity counts
            document.querySelectorAll('.bg-opacity-25 h3')[0].textContent = data.by_severity.critical;
            document.querySelectorAll('.bg-opacity-25 h3')[1].textContent = data.by_severity.high;
            document.querySelectorAll('.bg-opacity-25 h3')[2].textContent = data.by_severity.medium;
            document.querySelectorAll('.bg-opacity-25 h3')[3].textContent = data.by_severity.low;
            
            // Update severity chart
            updateSeverityChart(data.by_severity);
        })
        .catch(error => console.error('Error refreshing dashboard data:', error));
    
    // Fetch recent activities
    fetch('/api/activities?limit=10')
        .then(response => response.json())
        .then(data => {
            const activityTimeline = document.querySelector('.activity-timeline');
            
            // Clear existing activities
            activityTimeline.innerHTML = '';
            
            // Add new activities
            if (data.activities && data.activities.length > 0) {
                data.activities.forEach(activity => {
                    const date = new Date(activity.timestamp);
                    const formattedDate = date.toLocaleString();
                    
                    const activityItem = document.createElement('div');
                    activityItem.className = `activity-item ${activity.action_type}`;
                    activityItem.innerHTML = `
                        <small class="text-muted">${formattedDate}</small>
                        <p class="mb-0">${activity.description}</p>
                    `;
                    
                    activityTimeline.appendChild(activityItem);
                });
            } else {
                activityTimeline.innerHTML = '<p class="text-muted text-center">No activities yet</p>';
            }
        })
        .catch(error => console.error('Error refreshing activities:', error));
}

function initDashboardCharts() {
    // Get severity chart data from the existing HTML elements
    const critical = parseInt(document.querySelectorAll('.bg-opacity-25 h3')[0].textContent);
    const high = parseInt(document.querySelectorAll('.bg-opacity-25 h3')[1].textContent);
    const medium = parseInt(document.querySelectorAll('.bg-opacity-25 h3')[2].textContent);
    const low = parseInt(document.querySelectorAll('.bg-opacity-25 h3')[3].textContent);
    
    // Initialize severity chart if it doesn't exist yet
    if (document.getElementById('severityChart')) {
        updateSeverityChart({
            critical: critical,
            high: high,
            medium: medium,
            low: low
        });
    }
}

function updateSeverityChart(severityData) {
    const ctx = document.getElementById('severityChart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.severityChart) {
        window.severityChart.destroy();
    }
    
    // Create new chart
    window.severityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Critical', 'High', 'Medium', 'Low'],
            datasets: [{
                label: 'Incidents by Severity',
                data: [
                    severityData.critical, 
                    severityData.high, 
                    severityData.medium, 
                    severityData.low
                ],
                backgroundColor: [
                    'rgba(220, 53, 69, 0.7)',
                    'rgba(255, 193, 7, 0.7)',
                    'rgba(23, 162, 184, 0.7)',
                    'rgba(40, 167, 69, 0.7)'
                ],
                borderColor: [
                    'rgb(220, 53, 69)',
                    'rgb(255, 193, 7)',
                    'rgb(23, 162, 184)',
                    'rgb(40, 167, 69)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}
