const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class AIServiceDebug {
    constructor() {
        this.baseURL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;
        console.log('AI Service initialized with baseURL:', this.baseURL);
    }

    async analyzeImage(imageFile, contextText = '') {
        console.log('Attempting to analyze image:', imageFile.name);
        console.log('Base URL:', this.baseURL);
        
        const formData = new FormData();
        formData.append('image', imageFile);
        if (contextText) {
            formData.append('context_text', contextText);
        }

        const url = `${this.baseURL}/ai/analyze-image/`;
        console.log('Full URL:', url);

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
            });

            console.log('Response status:', response.status);
            console.log('Response headers:', Object.fromEntries(response.headers.entries()));

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
            }

            const result = await response.json();
            console.log('Success result:', result);
            return result;
        } catch (error) {
            console.error('Fetch error:', error);
            throw error;
        }
    }

    // Test connectivity
    async testConnection() {
        try {
            const response = await fetch(`${this.baseURL}/ai/health/`);
            console.log('Health check response:', response.status);
            if (response.ok) {
                const data = await response.json();
                console.log('Health check data:', data);
                return data;
            }
        } catch (error) {
            console.error('Connection test failed:', error);
            throw error;
        }
    }
}

class AIService {
    constructor() {
        this.baseURL = `${API_BASE_URL}/api`;
    }

    async analyzeImage(imageFile, contextText = '') {
        const formData = new FormData();
        formData.append('image', imageFile);
        if (contextText) {
            formData.append('context_text', contextText);
        }
        
        const response = await fetch(`${this.baseURL}/ai/analyze-image/`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    async sendChatMessage(sessionId, message) {
        const response = await fetch(`${this.baseURL}/ai/chat/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    async getConversation(sessionId) {
        const response = await fetch(`${this.baseURL}/ai/conversation/${sessionId}/`);

        if (!response.ok) {
            if (response.status === 404) {
                // Return empty conversation if not found
                return {
                    session_id: sessionId,
                    messages: [],
                    message_count: 0,
                    context_summary: '',
                    created_at: null
                };
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    // FIXED: Method name and logic
    async generateContent(prompt, maxLength = 200) {
        const response = await fetch(`${this.baseURL}/ai/generate-content/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                max_length: maxLength
            })
        });
        
        // FIXED: Changed from 'if (response.ok)' to 'if (!response.ok)'
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    async checkModelHealth() {
        const response = await fetch(`${this.baseURL}/ai/health/`);
        
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }
        return await response.json();
    }

    async getModelResults(modelType = null, limit = 50) {
        const params = new URLSearchParams();
        if (modelType) params.append('model_type', modelType);
        params.append('limit', limit.toString());

        const response = await fetch(`${this.baseURL}/ai/results/?${params}`);
        
        if (!response.ok) {
            throw new Error(`Failed to get model results: ${response.status}`);
        }
        return await response.json();
    }

    // Additional useful methods
    async getModelStatus() {
        const response = await fetch(`${this.baseURL}/ai/model-status/`);
        
        if (!response.ok) {
            throw new Error(`Model status failed: ${response.status}`);
        }
        return await response.json();
    }
}

export const aiService = new AIService();
export const aiServiceDebug = new AIServiceDebug(); // For debugging