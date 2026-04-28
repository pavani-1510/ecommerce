/**
 * Main JavaScript for 3D Printing Store
 */

// API Base URL
const API_BASE_URL = '/api';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkUserAuthentication();
    updateNavigationMenu();
    updateCartButtonStates();
    updateCartCount();
});

/**
 * Check if user is authenticated
 */
function checkUserAuthentication() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    const accountMenu = document.getElementById('accountMenu');
    const adminControlsLink = document.getElementById('adminControlsLink');

    if (token && user) {
        const parsedUser = JSON.parse(user || '{}');
        document.getElementById('authLink').style.display = 'none';
        if (accountMenu) {
            accountMenu.style.display = 'block';
        }
        if (adminControlsLink) {
            adminControlsLink.style.display = parsedUser.is_admin ? 'block' : 'none';
        }
    } else {
        document.getElementById('authLink').style.display = 'block';
        if (accountMenu) {
            accountMenu.style.display = 'none';
        }
        if (adminControlsLink) {
            adminControlsLink.style.display = 'none';
        }
    }
}

/**
 * Update navigation menu
 */
function updateNavigationMenu() {
    const accountTrigger = document.getElementById('accountTrigger');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (accountTrigger) {
        accountTrigger.textContent = user.name || user.full_name || user.username || user.email || 'Account';
    }
}

function getLocalCartItems() {
    try {
        return JSON.parse(localStorage.getItem('cart') || '[]');
    } catch (error) {
        return [];
    }
}

function saveLocalCartItems(items) {
    localStorage.setItem('cart', JSON.stringify(items));
}

function getCartProductIds() {
    const token = localStorage.getItem('token');

    if (!token) {
        return Promise.resolve(getLocalCartItems().map(item => String(item.id || item.product_id)));
    }

    return apiRequest('/cart')
        .then(response => response ? response.json() : { items: [] })
        .then(data => (data.items || []).map(item => String(item.product_id || item.id)) )
        .catch(() => []);
}

async function isProductInCart(productId) {
    const ids = await getCartProductIds();
    return ids.includes(String(productId));
}

async function updateCartButtonStates() {
    const ids = await getCartProductIds();

    document.querySelectorAll('[data-product-id]').forEach(card => {
        const productId = String(card.dataset.productId);
        const button = card.querySelector('[data-add-to-cart-btn]');

        if (!button) return;

        if (ids.includes(productId)) {
            button.textContent = 'Go to Cart';
            button.classList.add('btn-success');
            button.onclick = () => window.location.href = '/cart';
        } else {
            button.textContent = 'Add to Cart';
            button.classList.remove('btn-success');
            button.onclick = () => addToCart(productId);
        }
    });
}

async function updateCartCount() {
    const badge = document.querySelector('[data-cart-count]');
    if (!badge) return;

    const token = localStorage.getItem('token');
    let count = 0;

    if (token) {
        try {
            const response = await apiRequest('/cart');
            if (response) {
                const data = await response.json();
                count = data.total || 0;
            }
        } catch (error) {
            count = 0;
        }
    } else {
        count = getLocalCartItems().length;
    }

    badge.textContent = String(count);
    badge.style.display = count > 0 ? 'inline-flex' : 'none';
}

/**
 * Make API request with authentication
 */
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    
    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
    const headers = {
        ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
        ...options.headers
    };

    if (isFormData && headers['Content-Type']) {
        delete headers['Content-Type'];
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    });

    // Handle authentication errors
    if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return null;
    }

    return response;
}

/**
 * Add product to cart
 */
async function addToCart(productId, quantity = 1) {
    const token = localStorage.getItem('token');

    if (await isProductInCart(productId)) {
        window.location.href = '/cart';
        return;
    }

    if (!token) {
        const items = getLocalCartItems();
        const existing = items.find(item => String(item.id || item.product_id) === String(productId));

        if (existing) {
            window.location.href = '/cart';
            return;
        }

        items.push({ id: productId, quantity: Number(quantity || 1) });
        saveLocalCartItems(items);
        showNotification('Added to cart! Go to Cart to review it.', 'success');
        updateCartButtonStates();
        updateCartCount();
        return;
    }

    try {
        const response = await apiRequest('/cart', {
            method: 'POST',
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        });

        if (!response) return;

        const data = await response.json();

        if (response.ok) {
            showNotification('Product added to cart!', 'success');
            updateCartButtonStates();
            updateCartCount();
        } else {
            showNotification(data.error || 'Failed to add to cart', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.maxWidth = '300px';

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

/**
 * Format currency
 */
function formatPrice(price) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(price);
}

/**
 * Logout user
 */
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/';
    }
}

window.updateCartButtonStates = updateCartButtonStates;
window.updateCartCount = updateCartCount;

/**
 * Format date
 */
function formatDate(dateString) {
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

/**
 * Validate email
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate phone number
 */
function validatePhone(phone) {
    const re = /^[0-9]{10}$/;
    return re.test(phone.replace(/\D/g, ''));
}

/**
 * Get cart count
 */
async function getCartCount() {
    try {
        const response = await apiRequest('/cart');
        if (!response) return 0;

        const data = await response.json();
        return data.total || 0;
    } catch (error) {
        console.error('Error getting cart count:', error);
        return 0;
    }
}

/**
 * Create order
 */
async function createOrder(shippingAddress, billingAddress, paymentMethod) {
    try {
        const response = await apiRequest('/orders', {
            method: 'POST',
            body: JSON.stringify({
                shipping_address: shippingAddress,
                billing_address: billingAddress,
                payment_method: paymentMethod
            })
        });

        if (!response) return null;

        const data = await response.json();

        if (response.ok) {
            return data.order;
        } else {
            showNotification(data.error || 'Failed to create order', 'error');
            return null;
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
        return null;
    }
}

/**
 * Create support ticket
 */
async function createSupportTicket(subject, message, category, priority, contactMethod) {
    try {
        const response = await apiRequest('/support/tickets', {
            method: 'POST',
            body: JSON.stringify({
                subject: subject,
                message: message,
                category: category,
                priority: priority,
                contact_method: contactMethod
            })
        });

        if (!response) return null;

        const data = await response.json();

        if (response.ok) {
            showNotification('Ticket created successfully!', 'success');
            return data.ticket;
        } else {
            showNotification(data.error || 'Failed to create ticket', 'error');
            return null;
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
        return null;
    }
}

/**
 * Initiate Razorpay payment
 */
async function initiateRazorpayPayment(orderId) {
    try {
        // Get Razorpay checkout details
        const response = await apiRequest(`/payment/razorpay/checkout`, {
            method: 'POST',
            body: JSON.stringify({ order_id: orderId })
        });

        if (!response) return false;

        const data = await response.json();

        if (!response.ok) {
            showNotification(data.error || 'Failed to initiate payment', 'error');
            return false;
        }

        // Initialize Razorpay
        const options = {
            key: 'YOUR_RAZORPAY_KEY_ID',
            amount: data.razorpay_order.amount,
            currency: data.currency,
            order_id: data.razorpay_order.id,
            handler: function (response) {
                verifyRazorpayPayment(orderId, response);
            }
        };

        const rzp = new Razorpay(options);
        rzp.open();
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

/**
 * Verify Razorpay payment
 */
async function verifyRazorpayPayment(orderId, paymentResponse) {
    try {
        const response = await apiRequest(`/payment/razorpay/verify`, {
            method: 'POST',
            body: JSON.stringify({
                order_id: orderId,
                payment_id: paymentResponse.razorpay_payment_id,
                signature: paymentResponse.razorpay_signature
            })
        });

        if (!response) return false;

        const data = await response.json();

        if (response.ok) {
            showNotification('Payment successful!', 'success');
            // Redirect to order details page
            setTimeout(() => {
                window.location.href = `/orders/${orderId}`;
            }, 2000);
            return true;
        } else {
            showNotification(data.error || 'Payment verification failed', 'error');
            return false;
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
        return false;
    }
}

/**
 * Load Razorpay script
 */
function loadRazorpayScript() {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    document.body.appendChild(script);
}

// Load Razorpay on page load
document.addEventListener('DOMContentLoaded', loadRazorpayScript);
