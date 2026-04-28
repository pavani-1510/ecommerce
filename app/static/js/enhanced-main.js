/**
 * 🚀 Mantra Made 3D Arts - Enhanced JavaScript Utilities
 * Modern, accessible, and feature-rich functionality
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
    API_BASE: window.location.origin + '/api',
    TOKEN_KEY: 'auth_token',
    USER_KEY: 'current_user',
    TOAST_DURATION: 3000,
    DEBOUNCE_DELAY: 300,
    ANIMATION_DURATION: 300
};

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const AppState = {
    user: null,
    cart: [],
    isLoading: false,
    
    init() {
        this.loadUser();
        this.loadCart();
    },
    
    loadUser() {
        try {
            const userData = localStorage.getItem(CONFIG.USER_KEY);
            this.user = userData ? JSON.parse(userData) : null;
        } catch (e) {
            console.error('Error loading user:', e);
            this.user = null;
        }
    },
    
    saveUser(user) {
        this.user = user;
        localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(user));
    },
    
    clearUser() {
        this.user = null;
        localStorage.removeItem(CONFIG.USER_KEY);
        localStorage.removeItem(CONFIG.TOKEN_KEY);
    },
    
    loadCart() {
        try {
            const cartData = localStorage.getItem('cart');
            this.cart = cartData ? JSON.parse(cartData) : [];
        } catch (e) {
            console.error('Error loading cart:', e);
            this.cart = [];
        }
    },
    
    saveCart() {
        localStorage.setItem('cart', JSON.stringify(this.cart));
    },
    
    addToCart(product) {
        const existing = this.cart.find(item => item.id === product.id);
        if (existing) {
            existing.quantity += (product.quantity || 1);
        } else {
            this.cart.push({ ...product, quantity: product.quantity || 1 });
        }
        this.saveCart();
    },
    
    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.id !== productId);
        this.saveCart();
    },
    
    updateCartQuantity(productId, quantity) {
        const item = this.cart.find(item => item.id === productId);
        if (item) {
            item.quantity = Math.max(1, quantity);
            this.saveCart();
        }
    }
};

// ============================================================================
// API UTILITIES
// ============================================================================

/**
 * Make API requests with automatic token handling
 */
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem(CONFIG.TOKEN_KEY);
    const url = endpoint.startsWith('http') 
        ? endpoint 
        : CONFIG.API_BASE + endpoint;
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            // Unauthorized - clear auth
            AppState.clearUser();
            window.location.href = '/login';
            return null;
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || `HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * GET request
 */
async function apiGet(endpoint) {
    return apiRequest(endpoint, { method: 'GET' });
}

/**
 * POST request
 */
async function apiPost(endpoint, data) {
    return apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * PUT request
 */
async function apiPut(endpoint, data) {
    return apiRequest(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

/**
 * DELETE request
 */
async function apiDelete(endpoint) {
    return apiRequest(endpoint, { method: 'DELETE' });
}

// ============================================================================
// NOTIFICATION SYSTEM
// ============================================================================

class NotificationManager {
    constructor() {
        this.container = null;
        this.init();
    }
    
    init() {
        this.container = document.createElement('div');
        this.container.setAttribute('aria-live', 'polite');
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-width: 400px;
        `;
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', duration = CONFIG.TOAST_DURATION) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.style.cssText = `
            animation: slideInRight 0.3s ease-out;
            max-width: 100%;
        `;
        
        const content = document.createElement('div');
        content.textContent = message;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'alert-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = () => this.remove(notification);
        
        notification.appendChild(content);
        notification.appendChild(closeBtn);
        this.container.appendChild(notification);
        
        if (duration > 0) {
            setTimeout(() => this.remove(notification), duration);
        }
        
        return notification;
    }
    
    remove(notification) {
        notification.style.animation = 'fadeOut 0.3s ease-out forwards';
        setTimeout(() => notification.remove(), 300);
    }
    
    success(message) { return this.show(message, 'success'); }
    error(message) { return this.show(message, 'error'); }
    warning(message) { return this.show(message, 'warning'); }
    info(message) { return this.show(message, 'info'); }
}

const Notification = new NotificationManager();

// ============================================================================
// FORM VALIDATION
// ============================================================================

const Validators = {
    email(value) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(value);
    },
    
    phone(value) {
        const regex = /^[\d\s\-\+\(\)]{10,}$/;
        return regex.test(value);
    },
    
    minLength(value, length) {
        return value && value.length >= length;
    },
    
    maxLength(value, length) {
        return value && value.length <= length;
    },
    
    required(value) {
        return value && value.trim().length > 0;
    },
    
    match(value, targetValue) {
        return value === targetValue;
    },
    
    password(value) {
        // At least 8 chars, 1 uppercase, 1 lowercase, 1 number
        return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(value);
    },
    
    url(value) {
        try {
            new URL(value);
            return true;
        } catch {
            return false;
        }
    },
    
    number(value) {
        return !isNaN(value) && value.trim() !== '';
    },
    
    integer(value) {
        return Number.isInteger(Number(value));
    }
};

class FormValidator {
    constructor(formElement) {
        this.form = formElement;
        this.fields = {};
        this.errors = {};
        this.setupListeners();
    }
    
    setupListeners() {
        this.form.querySelectorAll('input, textarea, select').forEach(field => {
            field.addEventListener('blur', () => this.validateField(field));
            field.addEventListener('input', () => this.clearError(field));
        });
    }
    
    addField(name, rules) {
        this.fields[name] = rules;
    }
    
    validateField(field) {
        const name = field.name;
        const value = field.value;
        const rules = this.fields[name];
        
        if (!rules) return true;
        
        for (const [rule, params] of Object.entries(rules)) {
            const validator = Validators[rule];
            if (!validator) continue;
            
            const isValid = params 
                ? validator(value, params)
                : validator(value);
            
            if (!isValid) {
                this.showError(field, `Invalid ${name}`);
                return false;
            }
        }
        
        this.clearError(field);
        return true;
    }
    
    validate() {
        let isValid = true;
        this.errors = {};
        
        Object.keys(this.fields).forEach(name => {
            const field = this.form.elements[name];
            if (field && !this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    showError(field, message) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        
        const errorEl = field.nextElementSibling?.classList.contains('form-error')
            ? field.nextElementSibling
            : null;
        
        if (errorEl) {
            errorEl.textContent = message;
        }
        
        this.errors[field.name] = message;
    }
    
    clearError(field) {
        field.classList.remove('is-invalid');
        const errorEl = field.nextElementSibling?.classList.contains('form-error')
            ? field.nextElementSibling
            : null;
        
        if (errorEl) {
            errorEl.textContent = '';
        }
        
        delete this.errors[field.name];
    }
    
    getErrors() {
        return this.errors;
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Format price as INR currency
 */
function formatPrice(price) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0
    }).format(price);
}

/**
 * Format date
 */
function formatDate(date) {
    return new Intl.DateTimeFormat('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(new Date(date));
}

/**
 * Debounce function
 */
function debounce(func, delay = CONFIG.DEBOUNCE_DELAY) {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit = CONFIG.DEBOUNCE_DELAY) {
    let inThrottle;
    return (...args) => {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Get URL parameters
 */
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const obj = {};
    params.forEach((value, key) => {
        obj[key] = value;
    });
    return obj;
}

/**
 * Show loading spinner in element
 */
function showLoading(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.innerHTML = '<div class="spinner"></div>';
    }
}

/**
 * Clear element
 */
function clearElement(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.innerHTML = '';
    }
}

/**
 * Add animation class
 */
function animateElement(element, animationName, duration = CONFIG.ANIMATION_DURATION) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (!element) return;
    
    element.style.animation = `${animationName} ${duration}ms ease-out`;
    setTimeout(() => {
        element.style.animation = '';
    }, duration);
}

/**
 * Check if element is in viewport
 */
function isElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= document.documentElement.clientHeight &&
        rect.right <= document.documentElement.clientWidth
    );
}

/**
 * Scroll to element smoothly
 */
function scrollToElement(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ============================================================================
// AUTHENTICATION
// ============================================================================

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!localStorage.getItem(CONFIG.TOKEN_KEY);
}

/**
 * Get current user
 */
function getCurrentUser() {
    return AppState.user;
}

/**
 * Login user
 */
async function login(email, password) {
    try {
        AppState.isLoading = true;
        const data = await apiPost('/auth/login', { email, password });
        
        localStorage.setItem(CONFIG.TOKEN_KEY, data.token);
        AppState.saveUser(data.user);
        
        Notification.success('Login successful!');
        return data;
    } catch (error) {
        Notification.error(error.message);
        throw error;
    } finally {
        AppState.isLoading = false;
    }
}

/**
 * Register user
 */
async function register(userData) {
    try {
        AppState.isLoading = true;
        const data = await apiPost('/auth/register', userData);
        
        localStorage.setItem(CONFIG.TOKEN_KEY, data.token);
        AppState.saveUser(data.user);
        
        Notification.success('Account created successfully!');
        return data;
    } catch (error) {
        Notification.error(error.message);
        throw error;
    } finally {
        AppState.isLoading = false;
    }
}

/**
 * Logout user
 */
function logout() {
    AppState.clearUser();
    Notification.success('Logged out successfully!');
    setTimeout(() => {
        window.location.href = '/';
    }, 500);
}

/**
 * Update navigation menu based on auth state
 */
function updateNavigationMenu() {
    const isAuth = isAuthenticated();
    const user = getCurrentUser();
    
    // Update navbar links based on auth state
    const authLinks = document.querySelectorAll('[data-auth-only]');
    const guestLinks = document.querySelectorAll('[data-guest-only]');
    
    authLinks.forEach(link => {
        link.style.display = isAuth ? '' : 'none';
    });
    
    guestLinks.forEach(link => {
        link.style.display = isAuth ? 'none' : '';
    });
    
    // Update user info display
    const userNameEl = document.querySelector('[data-user-name]');
    if (userNameEl && isAuth && user) {
        userNameEl.textContent = user.name || user.email;
    }
}

// ============================================================================
// DOM UTILITIES
// ============================================================================

/**
 * Create element from HTML string
 */
function createElementFromHTML(htmlString) {
    const div = document.createElement('div');
    div.innerHTML = htmlString.trim();
    return div.firstChild;
}

/**
 * Toggle class
 */
function toggleClass(element, className) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.classList.toggle(className);
    }
}

/**
 * Add class
 */
function addClass(element, className) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.classList.add(className);
    }
}

/**
 * Remove class
 */
function removeClass(element, className) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    if (element) {
        element.classList.remove(className);
    }
}

/**
 * Delegate event listener
 */
function on(selector, eventType, callback) {
    document.addEventListener(eventType, (event) => {
        const targetElement = event.target.closest(selector);
        if (targetElement) {
            callback.call(targetElement, event);
        }
    });
}

// ============================================================================
// CART MANAGEMENT
// ============================================================================

/**
 * Check if product is already in cart
 */
function isProductInCart(productId) {
    return AppState.cart.some(item => item.id === productId);
}

/**
 * Add product to cart or navigate to cart if already added
 */
async function addToCart(productId, quantity = 1) {
    try {
        // Check if product is already in cart
        if (isProductInCart(productId)) {
            // Navigate to cart page
            window.location.href = '/cart';
            return;
        }
        
        if (isAuthenticated()) {
            // Add to server cart
            await apiPost('/api/cart', { product_id: productId, quantity });
        } else {
            // Add to local cart
            const product = { id: productId, quantity };
            AppState.addToCart(product);
        }
        
        Notification.success('Added to cart!');
        updateCartCount();
        updateProductCardButtons(); // Update button text throughout page
    } catch (error) {
        Notification.error('Failed to add to cart');
    }
}

/**
 * Update all product card buttons on page
 */
function updateProductCardButtons() {
    document.querySelectorAll('[data-product-id]').forEach(card => {
        const productId = parseInt(card.dataset.productId);
        const btn = card.querySelector('[data-add-to-cart-btn]');
        
        if (btn) {
            if (isProductInCart(productId)) {
                btn.textContent = '🛒 Go to Cart';
                btn.onclick = () => window.location.href = '/cart';
                btn.classList.add('btn-success');
            } else {
                btn.textContent = '🛒 Add to Cart';
                btn.onclick = () => addToCart(productId);
                btn.classList.remove('btn-success');
            }
        }
    });
}

/**
 * Remove product from cart
 */
async function removeFromCart(productId) {
    try {
        if (isAuthenticated()) {
            await apiDelete(`/api/cart/${productId}`);
        } else {
            AppState.removeFromCart(productId);
        }
        
        Notification.success('Removed from cart');
        updateCartCount();
    } catch (error) {
        Notification.error('Failed to remove from cart');
    }
}

/**
 * Get cart count
 */
async function getCartCount() {
    if (isAuthenticated()) {
        try {
            const data = await apiGet('/api/cart');
            return data.items?.length || 0;
        } catch {
            return 0;
        }
    } else {
        return AppState.cart.length;
    }
}

/**
 * Update cart count display
 */
async function updateCartCount() {
    const count = await getCartCount();
    const cartBadge = document.querySelector('[data-cart-count]');
    if (cartBadge) {
        cartBadge.textContent = count;
        cartBadge.style.display = count > 0 ? '' : 'none';
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize app on DOMContentLoaded
 */
function initializeApp() {
    AppState.init();
    updateNavigationMenu();
    updateCartCount();
    setupMobileMenu();
    updateProductCardButtons(); // Update button states on page load
}

/**
 * Setup mobile menu toggle
 */
function setupMobileMenu() {
    const toggle = document.querySelector('.navbar-mobile-toggle');
    const menu = document.querySelector('.nav-menu');
    
    if (toggle && menu) {
        toggle.addEventListener('click', () => {
            menu.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.navbar')) {
                menu.classList.remove('active');
            }
        });
    }
}

// Run initialization when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

// ============================================================================
// EXPORTS (for modular use)
// ============================================================================

window.App = {
    apiRequest,
    apiGet,
    apiPost,
    apiPut,
    apiDelete,
    Notification,
    FormValidator,
    Validators,
    formatPrice,
    formatDate,
    debounce,
    throttle,
    getUrlParams,
    showLoading,
    clearElement,
    animateElement,
    isElementInViewport,
    scrollToElement,
    isAuthenticated,
    getCurrentUser,
    login,
    register,
    logout,
    addToCart,
    removeFromCart,
    getCartCount,
    updateCartCount,
    isProductInCart,
    updateProductCardButtons,
    toggleClass,
    addClass,
    removeClass,
    createElementFromHTML,
    on
};
