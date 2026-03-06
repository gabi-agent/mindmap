// MindMap API Integration - Updated for Backend Integration

const API_BASE_URL = window.location.origin + '/api';

async function callApi(method, path, data = null, headers = {}) {
    const url = `${API_BASE_URL}/${path}`;
    
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            ...headers
        },
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const contentType = response.headers.get("content-type");
        
        if (response.status === 204) {
            return null;
        }
        
        if (contentType && contentType.includes("application/json")) {
            const jsonResponse = await response.json();
            if (!response.ok) {
                const errorDetail = jsonResponse.detail || 'Unknown API error';
                throw new Error(`API Error (${response.status}): ${errorDetail}`);
            }
            return jsonResponse;
        } else {
            const textResponse = await response.text();
            if (!response.ok) {
                throw new Error(`API Error (${response.status}): ${textResponse}`);
            }
            return textResponse;
        }
    } catch (error) {
        console.error(`Error calling API ${method} ${path}:`, error);
        throw error;
    }
}

// Get auth token from sessionStorage (more secure than localStorage)
function getAuthToken() {
    const token = sessionStorage.getItem('mindmap_token');
    return token ? `Bearer ${token}` : null;
}

// Get auth headers
function getAuthHeaders() {
    const token = getAuthToken();
    return token ? { 'Authorization': token } : {};
}

export const api = {
    // Auth Endpoints
    register: (username, email, password) => 
        callApi('POST', 'auth/register', { username, email, password }),
    
    login: (username, password) => 
        callApi('POST', 'auth/login', { username, password }),
    
    logout: async () => {
        const token = sessionStorage.getItem('mindmap_token');
        if (token) {
            await callApi('POST', 'auth/logout', {}, { 'Authorization': `Bearer ${token}` });
        }
    },
    
    // MindMap Endpoints
    getMindMaps: async (page = 1, limit = 20) => 
        callApi('GET', `mindmaps?page=${page}&limit=${limit}`, null, getAuthHeaders()),
    
    getMindMap: async (mindmapId) => 
        callApi('GET', `mindmaps/${mindmapId}`, null, getAuthHeaders()),
    
    createMindMap: (title, description, isPublic = false) => 
        callApi('POST', 'mindmaps', { title, description, is_public: isPublic }, getAuthHeaders()),
    
    updateMindMap: (mindmapId, title, description, isPublic) => 
        callApi('PUT', `mindmaps/${mindmapId}`, { title, description, is_public: isPublic }, getAuthHeaders()),
    
    deleteMindMap: (mindmapId) => 
        callApi('DELETE', `mindmaps/${mindmapId}`, null, getAuthHeaders()),
    
    // Node Endpoints
    getNodes: async (mindmapId) => 
        callApi('GET', `mindmaps/${mindmapId}/nodes`, null, getAuthHeaders()),
    
    createNode: (mindmapId, parentId, content, xPos, yPos, style) => 
        callApi('POST', `mindmaps/${mindmapId}/nodes`, { 
            parent_id: parentId, 
            content, 
            x_pos: xPos, 
            y_pos: yPos,
            style_json: JSON.stringify(style)
        }, getAuthHeaders()),
    
    updateNode: (nodeId, parentId, content, xPos, yPos, style) => 
        callApi('PUT', `nodes/${nodeId}`, { 
            parent_id: parentId, 
            content, 
            x_pos: xPos, 
            y_pos: yPos,
            style_json: JSON.stringify(style)
        }, getAuthHeaders()),
    
    deleteNode: (nodeId) => 
        callApi('DELETE', `nodes/${nodeId}`, null, getAuthHeaders()),
    
    batchUpdateNodes: (nodes) => 
        callApi('POST', 'nodes/batch', { nodes }, getAuthHeaders()),
};

// Token management (using sessionStorage for better security)
export const auth = {
    saveToken: (token, user) => {
        sessionStorage.setItem('mindmap_token', token);
        sessionStorage.setItem('mindmap_user', JSON.stringify(user));
    },
    
    clearToken: () => {
        sessionStorage.removeItem('mindmap_token');
        sessionStorage.removeItem('mindmap_user');
    },
    
    getUser: () => {
        const user = sessionStorage.getItem('mindmap_user');
        return user ? JSON.parse(user) : null;
    },
    
    isAuthenticated: () => {
        return !!sessionStorage.getItem('mindmap_token');
    }
};
