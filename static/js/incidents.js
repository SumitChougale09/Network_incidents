// Incidents page JavaScript 

document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to status and severity filters
    const statusFilter = document.getElementById('status');
    const severityFilter = document.getElementById('severity');
    
    if (statusFilter) {
        statusFilter.addEventListener('change', applyFilters);
    }
    
    if (severityFilter) {
        severityFilter.addEventListener('change', applyFilters);
    }
    
    // Setup table sorting
    setupTableSorting();
});

function applyFilters() {
    const statusFilter = document.getElementById('status').value;
    const severityFilter = document.getElementById('severity').value;
    
    // Redirect to filtered URL
    window.location.href = `/incidents?status=${statusFilter}&severity=${severityFilter}`;
}

function setupTableSorting() {
    const table = document.querySelector('table');
    
    if (!table) return;
    
    const headers = table.querySelectorAll('th');
    
    headers.forEach((header, index) => {
        if (index === 0 || index === 5) return; // Skip # and Actions columns
        
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            sortTable(index);
        });
        
        // Add sort indicator
        const span = document.createElement('span');
        span.innerHTML = ' &#8597;'; // Default unsorted arrow
        span.classList.add('sort-indicator');
        header.appendChild(span);
    });
}

function sortTable(columnIndex) {
    const table = document.querySelector('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Get current sort direction
    const th = table.querySelectorAll('th')[columnIndex];
    const currentDirection = th.getAttribute('data-sort') === 'asc' ? 'desc' : 'asc';
    
    // Update all headers to show unsorted state
    table.querySelectorAll('th').forEach(header => {
        header.setAttribute('data-sort', '');
        const indicator = header.querySelector('.sort-indicator');
        if (indicator) {
            indicator.innerHTML = ' &#8597;';
        }
    });
    
    // Update clicked header
    th.setAttribute('data-sort', currentDirection);
    const indicator = th.querySelector('.sort-indicator');
    if (indicator) {
        indicator.innerHTML = currentDirection === 'asc' ? ' &#8593;' : ' &#8595;';
    }
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Handle date sorting (for column 4 - Reported date)
        if (columnIndex === 4) {
            const aDate = new Date(aValue);
            const bDate = new Date(bValue);
            return currentDirection === 'asc' ? aDate - bDate : bDate - aDate;
        }
        
        // Default string comparison
        if (aValue < bValue) {
            return currentDirection === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
            return currentDirection === 'asc' ? 1 : -1;
        }
        return 0;
    });
    
    // Remove existing rows
    rows.forEach(row => {
        tbody.removeChild(row);
    });
    
    // Add sorted rows back to table
    rows.forEach(row => {
        tbody.appendChild(row);
    });
}
