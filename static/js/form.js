// Initialize variables
let stripe;
let elements;
let paymentElement;
let form = document.getElementById('brief-form');
let submitButton = form.querySelector('button[type="submit"]');
let paymentElementContainer = document.getElementById('payment-element');

// Appearance object for Stripe Elements
const appearance = {
    theme: 'stripe',
    variables: {
        colorPrimary: '#4a6cf7',
        borderRadius: '4px'
    }
};

// Initialize Stripe with Publishable Key
function initializeStripe() {
    const stripePublishableKey = document.body.dataset.stripeKey;
    if (!stripePublishableKey) {
        console.error('Stripe Publishable Key not found.');
        showError('Payment system configuration error. Please contact support.');
        submitButton.disabled = true; // Disable form if key is missing
        return;
    }
    try {
        stripe = Stripe(stripePublishableKey);
        console.log("Stripe initialized.");
    } catch (error) {
        console.error('Error initializing Stripe:', error);
        showError('Error initializing payment system. Please try again later.');
        submitButton.disabled = true;
    }
}

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();

    if (!stripe) {
        showError('Payment system not initialized. Please refresh the page or contact support.');
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
        // 1. Submit brief to server to get clientSecret
        console.log("Submitting brief data...");
        const briefResponse = await fetch('/api/briefs/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!briefResponse.ok) {
            const errorData = await briefResponse.json().catch(() => ({ detail: 'Failed to submit brief data.' }));
            throw new Error(errorData.detail || 'Failed to submit brief data.');
        }

        const briefData = await briefResponse.json();
        const clientSecret = briefData.payment_intent_client_secret;
        const briefId = briefData.brief_id;
        console.log("Brief submitted, clientSecret received:", clientSecret);

        if (!clientSecret) {
             throw new Error('Could not retrieve payment details. Please try again.');
        }

        // 2. Create and mount payment element *now*
        console.log("Creating and mounting Stripe Payment Element...");
        paymentElementContainer.innerHTML = ''; // Clear previous content if any
        elements = stripe.elements({ clientSecret, appearance });
        paymentElement = elements.create('payment');
        paymentElement.mount('#payment-element');
        console.log("Payment Element mounted.");

        // 3. Confirm payment with Stripe
        // Small delay to ensure element is fully rendered? May not be needed.
        // await new Promise(resolve => setTimeout(resolve, 100)); 
        
        console.log("Confirming payment...");
        const { error } = await stripe.confirmPayment({
            elements,
            confirmParams: {
                // Make sure to change this to your payment completion page
                // Pass brief_id to potentially show relevant info on success page
                return_url: `${window.location.origin}/payment-success?brief_id=${briefId}` 
            }
        });

        // This point will only be reached if there is an immediate error when
        // confirming the payment. Otherwise, your customer will be redirected to
        // your `return_url`. For some payment methods like iDEAL, your customer will
        // be redirected to an intermediate site first to authorize the payment, then
        // redirected to the `return_url`.
        if (error) {
             // Handle errors from stripe.confirmPayment
            console.error("Stripe confirmPayment error:", error);
            if (error.type === "card_error" || error.type === "validation_error") {
                showError(error.message);
            } else {
                showError("An unexpected error occurred during payment.");
            }
            setLoading(false); // Re-enable button on error
        }
        // If no error, the user is redirected by Stripe. setLoading(false) is not needed here.

    } catch (error) {
        console.error('Error during submission process:', error);
        showError(error.message || 'An error occurred. Please try again.');
        setLoading(false); // Re-enable button on error
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

// Initialize Stripe when the page loads
window.addEventListener('load', function() {
    initializeStripe();
    // Add submit handler
    form.addEventListener('submit', handleSubmit);
});
