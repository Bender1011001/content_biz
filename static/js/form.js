// Initialize variables
let stripe;
let elements;
let paymentElement;
let form = document.getElementById('brief-form');
let submitButton = form.querySelector('button[type="submit"]');

// Initialize Stripe
async function initializeStripe() {
    try {
        // In a real implementation, the publishable key would be loaded from the server
        // For this demo, we use a placeholder
        const stripePublishableKey = 'pk_test_placeholder';
        
        // Initialize Stripe
        stripe = Stripe(stripePublishableKey);
        
        // Fetch client secret from the server
        const response = await fetch('/api/payments/create-intent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                amount: 75.00  // $75 fixed price
            })
        });
        
        const data = await response.json();
        const clientSecret = data.clientSecret;
        
        // Create Elements instance
        elements = stripe.elements({
            clientSecret,
            appearance: {
                theme: 'stripe',
                variables: {
                    colorPrimary: '#4a6cf7',
                    borderRadius: '4px'
                }
            }
        });
        
        // Create and mount the Payment Element
        paymentElement = elements.create('payment');
        paymentElement.mount('#payment-element');
        
    } catch (error) {
        console.error('Error initializing Stripe:', error);
        showError('Error initializing payment form. Please try again later.');
    }
}

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();
    
    if (!stripe || !elements) {
        showError('Payment processing not initialized. Please refresh the page.');
        return;
    }
    
    // Disable the submit button to prevent multiple submissions
    setLoading(true);
    
    // Validate form
    if (!validateForm()) {
        setLoading(false);
        return;
    }
    
    // Collect form data
    const formData = {
        client_name: document.getElementById('client_name').value,
        client_email: document.getElementById('client_email').value,
        brief_text: document.getElementById('brief_text').value,
        topic: document.getElementById('topic').value,
        tone: document.getElementById('tone').value,
        target_audience: document.getElementById('target_audience').value,
        word_count: parseInt(document.getElementById('word_count').value)
    };
    
    try {
        // Submit brief to server
        const briefResponse = await fetch('/api/briefs/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!briefResponse.ok) {
            throw new Error('Failed to submit brief');
        }
        
        const briefData = await briefResponse.json();
        
        // Confirm payment with Stripe
        const { error } = await stripe.confirmPayment({
            elements,
            confirmParams: {
                return_url: `${window.location.origin}/payment-success?brief_id=${briefData.brief_id}`
            }
        });
        
        if (error) {
            throw error;
        }
        
        // Payment succeeded (this won't execute as user will be redirected)
        
    } catch (error) {
        console.error('Error submitting form:', error);
        showError(error.message || 'An error occurred. Please try again.');
        setLoading(false);
    }
}

// Validate form inputs
function validateForm() {
    const requiredFields = ['client_name', 'client_email', 'brief_text', 'topic'];
    let isValid = true;
    
    requiredFields.forEach(field => {
        const element = document.getElementById(field);
        if (!element.value.trim()) {
            showError(`Please fill in the ${field.replace('_', ' ')} field.`);
            element.focus();
            isValid = false;
        }
    });
    
    const wordCount = parseInt(document.getElementById('word_count').value);
    if (isNaN(wordCount) || wordCount < 300 || wordCount > 3000) {
        showError('Word count must be between 300 and 3000.');
        document.getElementById('word_count').focus();
        isValid = false;
    }
    
    return isValid;
}

// Show error message
function showError(message) {
    // Check if error element already exists
    let errorElement = document.querySelector('.error-message');
    
    // Create error element if it doesn't exist
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.style.color = 'var(--danger-color)';
        errorElement.style.marginBottom = '20px';
        errorElement.style.padding = '10px';
        errorElement.style.backgroundColor = '#ffeeee';
        errorElement.style.borderRadius = 'var(--border-radius)';
        errorElement.style.borderLeft = '3px solid var(--danger-color)';
        
        // Insert at the top of the form
        form.insertBefore(errorElement, form.firstChild);
    }
    
    errorElement.textContent = message;
    errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Set loading state
function setLoading(isLoading) {
    if (isLoading) {
        submitButton.disabled = true;
        submitButton.textContent = 'Processing...';
    } else {
        submitButton.disabled = false;
        submitButton.textContent = 'Submit and Pay';
    }
}

// Initialize when the page loads
window.addEventListener('load', function() {
    // Temporarily comment out the Stripe initialization for demo purposes
    // initializeStripe();
    
    // For the demo, we'll just use a placeholder message
    const paymentElement = document.getElementById('payment-element');
    paymentElement.innerHTML = `
        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 4px; text-align: center;">
            <p>Stripe Payment Element would appear here in production.</p>
            <p style="color: #6c757d; font-size: 0.9rem;">This is a demo version.</p>
        </div>
    `;
    
    // Add submit handler
    form.addEventListener('submit', handleSubmit);
});
