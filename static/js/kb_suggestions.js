// Knowledge Base suggestions for incident creation

document.addEventListener('DOMContentLoaded', function() {
    // Elements for incident creation form
    const incidentForm = document.getElementById('incident-form');
    const titleInput = document.getElementById('title');
    const descriptionInput = document.getElementById('description');
    const severityInput = document.getElementById('severity');
    const suggestionsContainer = document.getElementById('kb-suggestions');
    
    if (!incidentForm || !suggestionsContainer) {
        return; // Not on the incident creation page
    }
    
    // Add debounce function to prevent too many requests
    function debounce(func, timeout = 500) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }
    
    // Function to fetch suggestions based on incident details
    const fetchSuggestions = debounce(() => {
        const title = titleInput.value.trim();
        const description = descriptionInput.value.trim();
        const severity = severityInput.value;
        
        // Only fetch suggestions if we have enough data
        if (title.length < 3 && description.length < 10) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        // Show loading state
        suggestionsContainer.innerHTML = `
            <div class="text-center py-3">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 mb-0">Looking for solutions...</p>
            </div>
        `;
        suggestionsContainer.style.display = 'block';
        
        // Fetch suggestions from API
        fetch('/kb/api/suggestions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                description: description,
                severity: severity
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success || !data.suggestions || data.suggestions.length === 0) {
                suggestionsContainer.innerHTML = `
                    <div class="alert alert-info mb-0">
                        <i class="fas fa-info-circle me-2"></i>
                        No solutions found for this issue. Continue with incident submission.
                    </div>
                `;
                return;
            }
            
            // Display suggestions
            let suggestionsHtml = `
                <h5 class="card-title mb-3">
                    <i class="fas fa-lightbulb me-2"></i>Potential Solutions Found
                </h5>
                <p class="text-muted mb-3">Our system found these potential solutions that might help resolve your issue:</p>
                <div class="list-group">
            `;
            
            data.suggestions.forEach(article => {
                suggestionsHtml += `
                    <a href="/kb/article/${article.id}" class="list-group-item list-group-item-action" target="_blank">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${article.title}</h6>
                            <span class="badge bg-primary">${article.category}</span>
                        </div>
                        <small class="text-muted">
                            <i class="fas fa-external-link-alt me-1"></i> Click to view solution
                        </small>
                    </a>
                `;
            });
            
            suggestionsHtml += `
                </div>
                <div class="mt-3">
                    <p class="mb-0 text-muted">If none of these solutions help, continue submitting your incident.</p>
                </div>
            `;
            
            suggestionsContainer.innerHTML = suggestionsHtml;
        })
        .catch(error => {
            console.error('Error fetching suggestions:', error);
            suggestionsContainer.style.display = 'none';
        });
    }, 800); // Debounce to wait 800ms after typing stops
    
    // Add event listeners to form inputs
    titleInput.addEventListener('input', fetchSuggestions);
    descriptionInput.addEventListener('input', fetchSuggestions);
    severityInput.addEventListener('change', fetchSuggestions);
});