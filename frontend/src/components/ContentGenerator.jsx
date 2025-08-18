import React, { useState } from 'react';
import { useContentGeneration } from '../hooks/useAI';
import './ContentGenerator.css';

const ContentGenerator = () => {
    const [prompt, setPrompt] = useState('');
    const [maxLength, setMaxLength] = useState(200);
    const [generationHistory, setGenerationHistory] = useState([]);
    const { generateContent, loading, result, error } = useContentGeneration();

    const handleGenerate = async (e) => {
        e.preventDefault();
        if (!prompt.trim() || loading) return;

        try {
            const response = await generateContent(prompt, maxLength);
            setGenerationHistory(prev => [{
                prompt: prompt,
                result: response,
                timestamp: new Date().toISOString()
            }, ...prev.slice(0, 9)]); // Keep last 10 generations
            
            setPrompt('');
        } catch (err) {
            console.error('Generation failed:', err);
        }
    };

    const getSafetyColor = (score) => {
        if (score >= 0.8) return '#4CAF50';
        if (score >= 0.6) return '#FF9800';
        return '#f44336';
    };

    return (
        <div className="content-generator">
            <div className="generator-header">
                <h3>AI Content Generator</h3>
                <p>Generate safe, contextual content with sentiment analysis</p>
            </div>

            <form onSubmit={handleGenerate} className="generator-form">
                <div className="form-group">
                    <label htmlFor="prompt">Content Prompt:</label>
                    <textarea
                        id="prompt"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder="Enter your content prompt here..."
                        rows={4}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="maxLength">Max Length:</label>
                    <input
                        type="range"
                        id="maxLength"
                        min="50"
                        max="500"
                        value={maxLength}
                        onChange={(e) => setMaxLength(parseInt(e.target.value))}
                    />
                    <span className="length-display">{maxLength} characters</span>
                </div>

                <button 
                    type="submit" 
                    disabled={!prompt.trim() || loading}
                    className="generate-button"
                >
                    {loading ? 'Generating...' : 'Generate Content'}
                </button>
            </form>

            {error && (
                <div className="error-message">
                    <strong>Error:</strong> {error}
                </div>
            )}

            {result && (
                <div className="generation-result">
                    <h4>Generated Content</h4>
                    
                    <div className="generated-text">
                        {result.generated_content}
                    </div>

                    <div className="result-metrics">
                        <div className="metric">
                            <span className="metric-label">Sentiment:</span>
                            <span className={`sentiment-badge ${result.sentiment.label.toLowerCase()}`}>
                                {result.sentiment.label} ({(result.sentiment.score * 100).toFixed(1)}%)
                            </span>
                        </div>

                        <div className="metric">
                            <span className="metric-label">Safety Score:</span>
                            <span 
                                className="safety-score"
                                style={{ color: getSafetyColor(result.safety_score) }}
                            >
                                {(result.safety_score * 100).toFixed(1)}%
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {generationHistory.length > 0 && (
                <div className="generation-history">
                    <h4>Recent Generations</h4>
                    {generationHistory.map((item, index) => (
                        <div key={index} className="history-item">
                            <div className="history-prompt">
                                <strong>Prompt:</strong> {item.prompt}
                            </div>
                            <div className="history-result">
                                {item.result.generated_content}
                            </div>
                            <div className="history-meta">
                                <span className="timestamp">
                                    {new Date(item.timestamp).toLocaleString()}
                                </span>
                                <span className={`sentiment ${item.result.sentiment.label.toLowerCase()}`}>
                                    {item.result.sentiment.label}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ContentGenerator;