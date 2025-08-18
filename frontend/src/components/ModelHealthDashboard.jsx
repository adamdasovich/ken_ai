import React, { useState, useEffect } from 'react';
import { aiService } from '../services/aiService';
import './ModelHealthDashboard.css';

const ModelHealthDashboard = () => {
    const [healthStatus, setHealthStatus] = useState(null);
    const [modelResults, setModelResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedModelType, setSelectedModelType] = useState('');

    useEffect(() => {
        checkHealth();
        loadRecentResults();
    }, []);

    const checkHealth = async () => {
        setLoading(true);
        try {
            const health = await aiService.checkModelHealth();
            setHealthStatus(health);
        } catch (err) {
            console.error('Health check failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadRecentResults = async (modelType = '') => {
        try {
            const results = await aiService.getModelResults(modelType || null, 20);
            setModelResults(results);
        } catch (err) {
            console.error('Failed to load results:', err);
        }
    };

    const handleModelTypeFilter = (modelType) => {
        setSelectedModelType(modelType);
        loadRecentResults(modelType);
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'healthy': return '#4CAF50';
            case 'degraded': return '#FF9800';
            case 'unhealthy': return '#f44336';
            default: return '#gray';
        }
    };

    return (
        <div className="health-dashboard">
            <div className="dashboard-header">
                <h3>AI Models Health Dashboard</h3>
                <button onClick={checkHealth} disabled={loading} className="refresh-btn">
                    {loading ? 'Checking...' : 'Refresh'}
                </button>
            </div>

            {healthStatus && (
                <div className="health-overview">
                    <div className="overall-status">
                        <div 
                            className="status-indicator"
                            style={{ backgroundColor: getStatusColor(healthStatus.status) }}
                        >
                            {healthStatus.status.toUpperCase()}
                        </div>
                        <div className="device-info">
                            Running on: {healthStatus.device}
                        </div>
                    </div>

                    <div className="models-grid">
                        {Object.entries(healthStatus.models).map(([modelName, isHealthy]) => (
                            <div 
                                key={modelName} 
                                className={`model-card ${isHealthy ? 'healthy' : 'unhealthy'}`}
                            >
                                <div className="model-name">{modelName}</div>
                                <div className={`model-status ${isHealthy ? 'healthy' : 'unhealthy'}`}>
                                    {isHealthy ? '✓ Healthy' : '✗ Unhealthy'}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="results-section">
                <div className="results-header">
                    <h4>Recent Model Results</h4>
                    
                    <div className="filter-controls">
                        <select 
                            value={selectedModelType}
                            onChange={(e) => handleModelTypeFilter(e.target.value)}
                            className="model-filter"
                        >
                            <option value="">All Models</option>
                            <option value="vision">Vision</option>
                            <option value="text">Text</option>
                            <option value="chat">Chat</option>
                            <option value="embedding">Embedding</option>
                        </select>
                    </div>
                </div>

                <div className="results-list">
                    {modelResults.map((result) => (
                        <div key={result.id} className="result-item">
                            <div className="result-header">
                                <span className={`model-type ${result.model_type}`}>
                                    {result.model_type}
                                </span>
                                <span className="model-name">{result.model_name}</span>
                                <span className="timestamp">
                                    {new Date(result.created_at).toLocaleString()}
                                </span>
                            </div>
                            
                            <div className="result-metrics">
                                {result.confidence_score && (
                                    <div className="metric">
                                        <span>Confidence:</span>
                                        <span className="confidence">
                                            {(result.confidence_score * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                )}
                                
                                <div className="metric">
                                    <span>Processing Time:</span>
                                    <span className="processing-time">
                                        {result.processing_time.toFixed(2)}s
                                    </span>
                                </div>
                            </div>

                            <div className="result-preview">
                                {typeof result.input_data === 'string' 
                                    ? result.input_data.substring(0, 100) + '...'
                                    : JSON.stringify(result.input_data).substring(0, 100) + '...'
                                }
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ModelHealthDashboard;