// MindMap Authentication Logic

import { api, auth } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    
    if (path.endsWith('/login') || path.includes('login.html')) {
        setupLoginForm();
    } else if (path.endsWith('/register') || path.includes('register.html')) {
        setupRegisterForm();
    }
});

function setupLoginForm() {
    const form = document.getElementById('login-form');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        // Validate
        if (!username || !password) {
            alert('Please fill in all fields');
            return;
        }
        
        // Disable button
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Signing in...';
        submitBtn.disabled = true;
        
        try {
            const response = await api.login(username, password);
            
            // Save token
            auth.saveToken(response.access_token, response.user);
            
            // Redirect to dashboard
            alert(`Welcome back, ${response.user.username}!`);
            window.location.href = '/';
            
        } catch (error) {
            console.error('Login error:', error);
            alert(error.message || 'Login failed. Please check your credentials.');
            
            // Re-enable button
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
}

function setupRegisterForm() {
    const form = document.getElementById('register-form');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        // Validate
        if (!username || !email || !password || !confirmPassword) {
            alert('Please fill in all fields');
            return;
        }
        
        if (password !== confirmPassword) {
            alert('Passwords do not match');
            return;
        }
        
        if (password.length < 6) {
            alert('Password must be at least 6 characters');
            return;
        }
        
        if (username.length < 3) {
            alert('Username must be at least 3 characters');
            return;
        }
        
        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Please enter a valid email address');
            return;
        }
        
        // Disable button
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Creating account...';
        submitBtn.disabled = true;
        
        try {
            const response = await api.register(username, email, password);
            
            // Show success
            alert(`Account created successfully for ${response.username}! You can now sign in.`);
            
            // Redirect to login
            window.location.href = '/login';
            
        } catch (error) {
            console.error('Register error:', error);
            
            // Handle different error types
            if (error.message.includes('409')) {
                alert('Username or email already exists. Please try another.');
            } else {
                alert(error.message || 'Registration failed. Please try again.');
            }
            
            // Re-enable button
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
}

// Auto-redirect if already authenticated
if (auth.isAuthenticated()) {
    const path = window.location.pathname;
    if (path.endsWith('/login') || path.includes('login.html') || path.endsWith('/register') || path.includes('register.html')) {
        window.location.href = '/';
    }
}
