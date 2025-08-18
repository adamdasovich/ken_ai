import React, { useState, useCallback } from 'react'
import { useImageAnalysis } from '../hooks/useAI'
import './ImageAnalyzer.css'

const ImageAnalyzer = () => {
    const [selectedImage, setSelectedImage] = useState(null)
    const [contextText, setContextText] = useState('')
    const [imagePreview, setImagePreview] = useState(null)
    const { analyzeImage, loading, result, error} = useImageAnalysis()

    const handleImageSelect = useCallback(event => {
        const file = event.target.files[0]
        if (file) {
            setSelectedImage(file)

            const reader = new FileReader()
            reader.onload = e => setImagePreview(e.target.result)
            reader.readAsDataURL(file)
        }
    }, [])

    const handleAnalyze = useCallback(async () => {
        if (!selectedImage) return;

        try {
            await analyzeImage(selectedImage, contextText)
        } catch (err) {
            console.error('Analysis failed: ', err)
        }
    }, [selectedImage, contextText, analyzeImage])

    const resetAnalysis = useCallback(() => {
        setSelectedImage(null)
        setImagePreview(null)
        setContextText(null)

    }, [])

    return(
             <div className="image-analyzer">
            <div className="upload-section">
                <h3>Image Analysis</h3>
                
                <div className="file-input-wrapper">
                    <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageSelect}
                        id="image-upload"
                        className="file-input"
                    />
                    <label htmlFor="image-upload" className="file-label">
                        Choose Image
                    </label>
                </div>

                {imagePreview && (
                    <div className="image-preview">
                        <img src={imagePreview} alt="Preview" className="preview-image" />
                        <button onClick={resetAnalysis} className="reset-btn">
                            Clear
                        </button>
                    </div>
                )}

                <div className="context-input">
                    <label htmlFor="context">Context (optional):</label>
                    <textarea
                        id="context"
                        value={contextText}
                        onChange={(e) => setContextText(e.target.value)}
                        placeholder="Provide additional context about the image..."
                        rows={3}
                    />
                </div>

                <button
                    onClick={handleAnalyze}
                    disabled={!selectedImage || loading}
                    className="analyze-btn"
                >
                    {loading ? 'Analyzing...' : 'Analyze Image'}
                </button>
            </div>

            {error && (
                <div className="error-message">
                    <strong>Error:</strong> {error}
                </div>
            )}

            {result && (
                <div className="analysis-results">
                    <h4>Analysis Results</h4>
                    
                    <div className="image-predictions">
                        <h5>Image Classification:</h5>
                        {result.analysis.image_analysis.predictions.map((pred, index) => (
                            <div key={index} className="prediction-item">
                                <span className="label">{pred.label}</span>
                                <span className="confidence">
                                    {(pred.score * 100).toFixed(1)}%
                                </span>
                                <div className="confidence-bar">
                                    <div 
                                        className="confidence-fill"
                                        style={{ width: `${pred.score * 100}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>

                    {result.analysis.text_analysis && (
                        <div className="text-analysis">
                            <h5>Context Analysis:</h5>
                            <div className="sentiment">
                                <strong>Sentiment:</strong> {result.analysis.text_analysis.sentiment[0].label}
                                ({(result.analysis.text_analysis.sentiment[0].score * 100).toFixed(1)}%)
                            </div>
                            
                            <div className="categories">
                                <strong>Categories:</strong>
                                {result.analysis.text_analysis.categories.labels.map((label, index) => (
                                    <span key={index} className="category-tag">
                                        {label} ({(result.analysis.text_analysis.categories.scores[index] * 100).toFixed(1)}%)
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="combined-description">
                        <h5>AI Description:</h5>
                        <p>{result.analysis.combined_description}</p>
                    </div>

                    <div className="processing-info">
                        <small>Processing time: {result.analysis.processing_time.toFixed(2)}s</small>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ImageAnalyzer

