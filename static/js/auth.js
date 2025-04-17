// Authentication-related JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form validation for login and registration
    initFormValidation();
    
    // Setup password visibility toggle
    setupPasswordToggles();
    
    // Setup password strength meter
    setupPasswordStrengthMeter();
});

function initFormValidation() {
    // Get the login and registration forms
    const loginForm = document.querySelector('form[action*="login"]');
    const registerForm = document.querySelector('form[action*="register"]');
    const profileForm = document.querySelector('form[action*="update_profile"]');
    
    // Validate login form
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            const username = loginForm.querySelector('input[name="username"]');
            const password = loginForm.querySelector('input[name="password"]');
            
            let isValid = true;
            
            // Clear previous error messages
            clearValidationErrors(loginForm);
            
            // Username validation
            if (!username.value.trim()) {
                displayValidationError(username, 'Username is required');
                isValid = false;
            }
            
            // Password validation
            if (!password.value) {
                displayValidationError(password, 'Password is required');
                isValid = false;
            }
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    }
    
    // Validate registration form
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const username = registerForm.querySelector('input[name="username"]');
            const email = registerForm.querySelector('input[name="email"]');
            const password = registerForm.querySelector('input[name="password"]');
            const passwordConfirm = registerForm.querySelector('input[name="password_confirm"]');
            
            let isValid = true;
            
            // Clear previous error messages
            clearValidationErrors(registerForm);
            
            // Username validation
            if (!username.value.trim()) {
                displayValidationError(username, 'Username is required');
                isValid = false;
            } else if (username.value.length < 3) {
                displayValidationError(username, 'Username must be at least 3 characters');
                isValid = false;
            }
            
            // Email validation
            if (!email.value.trim()) {
                displayValidationError(email, 'Email is required');
                isValid = false;
            } else if (!isValidEmail(email.value)) {
                displayValidationError(email, 'Please enter a valid email address');
                isValid = false;
            }
            
            // Password validation
            if (!password.value) {
                displayValidationError(password, 'Password is required');
                isValid = false;
            } else if (password.value.length < 6) {
                displayValidationError(password, 'Password must be at least 6 characters');
                isValid = false;
            }
            
            // Password confirmation
            if (password.value !== passwordConfirm.value) {
                displayValidationError(passwordConfirm, 'Passwords do not match');
                isValid = false;
            }
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    }
    
    // Validate profile update form
    if (profileForm) {
        profileForm.addEventListener('submit', function(event) {
            const email = profileForm.querySelector('input[name="email"]');
            const currentPassword = profileForm.querySelector('input[name="current_password"]');
            const newPassword = profileForm.querySelector('input[name="new_password"]');
            const confirmPassword = profileForm.querySelector('input[name="confirm_password"]');
            
            let isValid = true;
            
            // Clear previous error messages
            clearValidationErrors(profileForm);
            
            // Email validation if present
            if (email && email.value.trim() && !isValidEmail(email.value)) {
                displayValidationError(email, 'Please enter a valid email address');
                isValid = false;
            }
            
            // Password validation if attempting to change password
            if (currentPassword && currentPassword.value) {
                // New password is required if current password is provided
                if (!newPassword.value) {
                    displayValidationError(newPassword, 'New password is required');
                    isValid = false;
                } else if (newPassword.value.length < 6) {
                    displayValidationError(newPassword, 'Password must be at least 6 characters');
                    isValid = false;
                }
                
                // Password confirmation
                if (newPassword.value !== confirmPassword.value) {
                    displayValidationError(confirmPassword, 'Passwords do not match');
                    isValid = false;
                }
            }
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    }
}

function isValidEmail(email) {
    // Simple email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function displayValidationError(inputElement, errorMessage) {
    // Create error element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.innerText = errorMessage;
    
    // Add error class to input
    inputElement.classList.add('is-invalid');
    
    // Insert error message after input element's parent (which is the input-group)
    const parent = inputElement.closest('.input-group') || inputElement;
    parent.parentNode.insertBefore(errorDiv, parent.nextSibling);
}

function clearValidationErrors(form) {
    // Remove all error messages
    const errorMessages = form.querySelectorAll('.invalid-feedback');
    errorMessages.forEach(error => error.remove());
    
    // Remove error class from inputs
    const invalidInputs = form.querySelectorAll('.is-invalid');
    invalidInputs.forEach(input => input.classList.remove('is-invalid'));
}

function setupPasswordToggles() {
    // Find all password fields
    const passwordFields = document.querySelectorAll('input[type="password"]');
    
    passwordFields.forEach(field => {
        // Create the toggle button
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'btn btn-outline-secondary password-toggle';
        toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
        toggleButton.title = 'Show password';
        
        // Add event listener to toggle password visibility
        toggleButton.addEventListener('click', function() {
            if (field.type === 'password') {
                field.type = 'text';
                this.innerHTML = '<i class="fas fa-eye-slash"></i>';
                this.title = 'Hide password';
            } else {
                field.type = 'password';
                this.innerHTML = '<i class="fas fa-eye"></i>';
                this.title = 'Show password';
            }
        });
        
        // Find the input-group and append the button
        const inputGroup = field.closest('.input-group');
        if (inputGroup) {
            toggleButton.classList.add('password-toggle-btn');
            inputGroup.appendChild(toggleButton);
        }
    });
    
    // Add CSS for the toggle button
    addPasswordToggleStyles();
}

function addPasswordToggleStyles() {
    // Check if styles already exist
    if (document.getElementById('password-toggle-styles')) {
        return;
    }
    
    // Create style element
    const style = document.createElement('style');
    style.id = 'password-toggle-styles';
    style.textContent = `
        .password-toggle-btn {
            z-index: 10;
        }
        .password-toggle {
            border-left: none;
        }
    `;
    
    // Append to head
    document.head.appendChild(style);
}

function setupPasswordStrengthMeter() {
    // Find password field in registration form
    const registerForm = document.querySelector('form[action*="register"]');
    if (!registerForm) return;
    
    const passwordField = registerForm.querySelector('input[name="password"]');
    if (!passwordField) return;
    
    // Create strength meter elements
    const meterContainer = document.createElement('div');
    meterContainer.className = 'password-strength mt-2';
    meterContainer.innerHTML = `
        <div class="progress" style="height: 5px;">
            <div class="progress-bar bg-danger" role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
        </div>
        <small class="text-muted password-strength-text">Password strength: Too weak</small>
    `;
    
    // Insert after password input
    const inputGroup = passwordField.closest('.input-group') || passwordField;
    inputGroup.parentNode.insertBefore(meterContainer, inputGroup.nextSibling);
    
    // Get meter elements
    const progressBar = meterContainer.querySelector('.progress-bar');
    const strengthText = meterContainer.querySelector('.password-strength-text');
    
    // Add event listener to password field
    passwordField.addEventListener('input', function() {
        const strength = calculatePasswordStrength(this.value);
        updatePasswordStrengthMeter(strength, progressBar, strengthText);
    });
}

function calculatePasswordStrength(password) {
    if (!password) return 0;
    
    let score = 0;
    
    // Length check
    if (password.length >= 8) score += 25;
    else if (password.length >= 6) score += 15;
    else if (password.length >= 4) score += 5;
    
    // Complexity checks
    if (/[A-Z]/.test(password)) score += 25; // Uppercase
    if (/[a-z]/.test(password)) score += 15; // Lowercase
    if (/[0-9]/.test(password)) score += 20; // Numbers
    if (/[^A-Za-z0-9]/.test(password)) score += 25; // Special characters
    
    // Limit score to 100
    return Math.min(100, score);
}

function updatePasswordStrengthMeter(strength, progressBar, strengthText) {
    // Update progress bar
    progressBar.style.width = strength + '%';
    progressBar.setAttribute('aria-valuenow', strength);
    
    // Update colors and text
    if (strength < 25) {
        progressBar.className = 'progress-bar bg-danger';
        strengthText.textContent = 'Password strength: Too weak';
    } else if (strength < 50) {
        progressBar.className = 'progress-bar bg-warning';
        strengthText.textContent = 'Password strength: Weak';
    } else if (strength < 75) {
        progressBar.className = 'progress-bar bg-info';
        strengthText.textContent = 'Password strength: Good';
    } else {
        progressBar.className = 'progress-bar bg-success';
        strengthText.textContent = 'Password strength: Strong';
    }
}
