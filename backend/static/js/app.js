// ===== API Configuration =====
const API_BASE = '/api';
let authToken = localStorage.getItem('authToken');
let currentMindmapId = null;
let markmapInstance = null;

// ===== Utility Functions =====
function showLoading() {
    document.getElementById('loading-screen').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-screen').style.display = 'none';
}

function showAuthError(message) {
    const errorDiv = document.getElementById('auth-error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => errorDiv.style.display = 'none', 5000);
}

async function apiRequest(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetch(API_BASE + url, {
        ...options,
        headers
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
    }
    
    return response.json();
}

// ===== Authentication =====
async function register(username, email, password) {
    try {
        const response = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
        
        // Auto login after registration
        await login(username, password);
    } catch (error) {
        showAuthError(error.message);
    }
}

async function login(username, password) {
    try {
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        authToken = response.access_token;
        localStorage.setItem('authToken', authToken);
        
        showDashboard();
    } catch (error) {
        showAuthError(error.message);
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
    currentMindmapId = null;
    
    showAuthScreen();
}

// ===== Screen Navigation =====
function showAuthScreen() {
    document.getElementById('loading-screen').style.display = 'none';
    document.getElementById('auth-screen').style.display = 'flex';
    document.getElementById('dashboard-screen').classList.remove('active');
}

function showDashboard() {
    document.getElementById('loading-screen').style.display = 'none';
    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('dashboard-screen').classList.add('active');
    document.getElementById('dashboard-content').style.display = 'block';
    document.getElementById('editor-content').classList.remove('active');
    
    loadMindmaps();
}

function showEditor(mindmap = null) {
    document.getElementById('dashboard-content').style.display = 'none';
    document.getElementById('editor-content').classList.add('active');
    
    if (mindmap) {
        currentMindmapId = mindmap.id;
        document.getElementById('map-title').value = mindmap.title;
        document.getElementById('markdown-editor').value = mindmap.content;
    } else {
        currentMindmapId = null;
        document.getElementById('map-title').value = '';
        document.getElementById('markdown-editor').value = '# Main Topic\n\n## Subtopic 1\n\n## Subtopic 2\n';
    }
    
    updateMarkmap();
}

function showDashboardView() {
    document.getElementById('editor-content').classList.remove('active');
    document.getElementById('dashboard-content').style.display = 'block';
    
    loadMindmaps();
}

// ===== Mindmap CRUD =====
async function loadMindmaps() {
    try {
        const mindmaps = await apiRequest('/mindmaps');
        
        const grid = document.getElementById('mindmaps-grid');
        const emptyState = document.getElementById('empty-state');
        
        if (mindmaps.length === 0) {
            grid.innerHTML = '';
            emptyState.style.display = 'block';
        } else {
            emptyState.style.display = 'none';
            grid.innerHTML = mindmaps.map(map => `
                <div class="mindmap-card" data-id="${map.id}">
                    <h3>${escapeHtml(map.title)}</h3>
                    <p>${escapeHtml(map.content.substring(0, 100))}...</p>
                    <div class="date">Updated: ${new Date(map.updated_at).toLocaleDateString()}</div>
                </div>
            `).join('');
            
            // Add click handlers
            document.querySelectorAll('.mindmap-card').forEach(card => {
                card.addEventListener('click', () => {
                    const mapId = parseInt(card.dataset.id);
                    const mindmap = mindmaps.find(m => m.id === mapId);
                    showEditor(mindmap);
                });
            });
        }
    } catch (error) {
        console.error('Error loading mindmaps:', error);
    }
}

async function saveMindmap() {
    const title = document.getElementById('map-title').value.trim();
    const content = document.getElementById('markdown-editor').value.trim();
    
    if (!title || !content) {
        alert('Please fill in both title and content');
        return;
    }
    
    try {
        if (currentMindmapId) {
            // Update existing
            await apiRequest(`/mindmaps/${currentMindmapId}`, {
                method: 'PUT',
                body: JSON.stringify({ title, content })
            });
        } else {
            // Create new
            const response = await apiRequest('/mindmaps', {
                method: 'POST',
                body: JSON.stringify({ title, content })
            });
            currentMindmapId = response.id;
        }
        
        alert('Mind map saved!');
        showDashboardView();
    } catch (error) {
        alert('Error saving mind map: ' + error.message);
    }
}

async function deleteMindmap() {
    if (!currentMindmapId) return;
    
    if (!confirm('Are you sure you want to delete this mind map?')) return;
    
    try {
        await apiRequest(`/mindmaps/${currentMindmapId}`, {
            method: 'DELETE'
        });
        
        alert('Mind map deleted!');
        showDashboardView();
    } catch (error) {
        alert('Error deleting mind map: ' + error.message);
    }
}

// ===== Markmap Integration =====
function updateMarkmap() {
    const markdown = document.getElementById('markdown-editor').value;
    
    try {
        // Use markmap-lib Transformer
        const { Transformer } = markmap;
        const transformer = new Transformer();
        const { root } = transformer.transform(markdown);
        
        // Use markmap-view Markmap
        const { Markmap } = markmap;
        
        if (markmapInstance) {
            markmapInstance.setData(root);
            markmapInstance.fit();
        } else {
            const svg = document.querySelector('#markmap-view');
            if (svg) {
                markmapInstance = Markmap.create(svg, null, root);
            } else {
                console.error('Markmap container not found');
            }
        }
    } catch (error) {
        console.error('Error updating markmap:', error);
    }
}

// ===== Event Listeners =====
document.addEventListener('DOMContentLoaded', async () => {
    hideLoading();
    
    // Check authentication
    if (authToken) {
        try {
            await apiRequest('/auth/me');
            showDashboard();
        } catch {
            logout();
        }
    } else {
        showAuthScreen();
    }
    
    // Auth tabs
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`${tab.dataset.tab}-form`).classList.add('active');
        });
    });
    
    // Login form
    document.getElementById('login-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        login(formData.get('username'), formData.get('password'));
    });
    
    // Register form
    document.getElementById('register-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        register(formData.get('username'), formData.get('email'), formData.get('password'));
    });
    
    // Navbar
    document.getElementById('nav-dashboard').addEventListener('click', showDashboardView);
    document.getElementById('nav-new').addEventListener('click', () => showEditor());
    document.getElementById('nav-logout').addEventListener('click', logout);
    
    // Dashboard
    document.getElementById('btn-new-map').addEventListener('click', () => showEditor());
    
    // Editor
    document.getElementById('btn-back').addEventListener('click', showDashboardView);
    document.getElementById('btn-save').addEventListener('click', saveMindmap);
    document.getElementById('btn-delete').addEventListener('click', deleteMindmap);
    
    // Live preview
    document.getElementById('markdown-editor').addEventListener('input', debounce(updateMarkmap, 300));
});

// ===== Utility Functions =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
