// MindMap Dashboard Logic

import { api, auth } from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    if (!auth.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    
    // Display user info
    const user = auth.getUser();
    document.getElementById('user-display').textContent = `Welcome, ${user.username}`;
    
    // Load mindmaps
    await loadMindMaps();
    
    // Setup event listeners
    setupEventListeners();
});

async function loadMindMaps() {
    try {
        const response = await api.getMindMaps();
        const mindmaps = response.mindmaps || [];
        
        const container = document.getElementById('mindmaps-container');
        const emptyState = document.getElementById('empty-state');
        
        if (mindmaps.length === 0) {
            container.innerHTML = '';
            emptyState.classList.remove('hidden');
            // Do NOT force open modal here
            return;
        }
        
        emptyState.classList.add('hidden');
        
        // Render mindmap cards
        container.innerHTML = mindmaps.map(map => `
            <div class="mindmap-card" data-id="${map.id}">
                <h3 class="mindmap-title">${escapeHtml(map.title)}</h3>
                <p class="mindmap-desc">${escapeHtml(map.description || 'No description')}</p>
                <div class="mindmap-meta">
                    <span class="node-count">
                        📊 ${map.node_count || 0} nodes
                    </span>
                    <span>
                        ${map.is_public ? '🌍 Public' : '🔒 Private'}
                    </span>
                </div>
                <div class="mindmap-actions" style="margin-top: 12px;">
                    <button class="icon-btn view" onclick="viewMindMap(${map.id})" title="View">
                        👁️ View
                    </button>
                    <button class="icon-btn edit" onclick="editMindMap(${map.id})" title="Edit">
                        ✏️ Edit
                    </button>
                    <button class="icon-btn delete" onclick="deleteMindMap(${map.id})" title="Delete">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading mindmaps:', error);
        alert('Failed to load mindmaps. Please try again.');
    }
}

function setupEventListeners() {
    // Create mindmap button
    document.getElementById('create-mindmap-btn').addEventListener('click', () => {
        openModal('mindmap-modal');
    });
    
    // Cancel button
    document.getElementById('cancel-mindmap-btn').addEventListener('click', () => {
        closeModal('mindmap-modal');
    });
    
    // Create mindmap form
    document.getElementById('mindmap-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const editId = e.target.dataset.editId;
        
        if (editId) {
            await updateExistingMindMap(editId);
        } else {
            await createMindMap();
        }
    });
    
    // Logout button
    document.getElementById('logout-btn').addEventListener('click', async () => {
        try {
            await api.logout();
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            auth.clearToken();
            window.location.href = '/login';
        }
    });
}

async function createMindMap() {
    const title = document.getElementById('mindmap-title').value.trim();
    const description = document.getElementById('mindmap-desc').value.trim();
    const isPublic = document.getElementById('is-public').checked;
    
    if (!title) {
        alert('Please enter a title');
        return;
    }
    
    try {
        const response = await api.createMindMap(title, description, isPublic);
        
        // Close modal and reset form FIRST
        closeModal('mindmap-modal');
        document.getElementById('mindmap-form').reset();
        
        // THEN reload mindmaps to ensure UI updates
        await loadMindMaps();
        
        // Show success message
        alert(`MindMap "${title}" created successfully!`);
        
        // Ask user if they want to open the new mindmap
        if (confirm(`MindMap "${title}" created! Would you like to open it now?`)) {
            viewMindMap(response.id);
        }
        
    } catch (error) {
        console.error('Error creating mindmap:', error);
        alert(error.message || 'Failed to create mindmap. Please try again.');
    }
}

// Global functions for card actions
window.viewMindMap = function(id) {
    window.location.href = `/workspace?id=${id}`;
};

window.editMindMap = async function(id) {
    try {
        const mindmap = await api.getMindMap(id);
        
        // Populate modal
        document.getElementById('mindmap-title').value = mindmap.title;
        document.getElementById('mindmap-desc').value = mindmap.description || '';
        document.getElementById('is-public').checked = mindmap.is_public;
        
        // Store ID for update
        document.getElementById('mindmap-form').dataset.editId = id;
        
        // Change modal title
        document.querySelector('#mindmap-modal .modal-header').textContent = 'Edit MindMap';
        
        openModal('mindmap-modal');
        
    } catch (error) {
        console.error('Error loading mindmap:', error);
        alert('Failed to load mindmap for editing.');
    }
};

window.deleteMindMap = async function(id) {
    if (!confirm('Are you sure you want to delete this mindmap? This action cannot be undone.')) {
        return;
    }
    
    try {
        await api.deleteMindMap(id);
        alert('MindMap deleted successfully');
        await loadMindMaps();
    } catch (error) {
        console.error('Error deleting mindmap:', error);
        alert('Failed to delete mindmap. Please try again.');
    }
};

async function updateExistingMindMap(editId) {
    const title = document.getElementById('mindmap-title').value.trim();
    const description = document.getElementById('mindmap-desc').value.trim();
    const isPublic = document.getElementById('is-public').checked;
    
    try {
        await api.updateMindMap(editId, title, description, isPublic);
        alert('MindMap updated successfully!');
        
        // Reset form
        const form = document.getElementById('mindmap-form');
        delete form.dataset.editId;
        document.querySelector('#mindmap-modal .modal-header').textContent = 'Create New MindMap';
        form.reset();
        
        closeModal('mindmap-modal');
        await loadMindMaps();
        
    } catch (error) {
        console.error('Error updating mindmap:', error);
        alert(error.message || 'Failed to update mindmap.');
    }
}

// Helper functions
function openModal(modalId) {
    console.log('Opening modal:', modalId);
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    console.log('Closing modal:', modalId);
    document.getElementById(modalId).classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
