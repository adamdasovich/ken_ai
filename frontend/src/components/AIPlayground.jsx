import React, { useState } from 'react';
import ImageAnalyzer from './ImageAnalyzer';
import ChatInterface from './ChatInterface';
import ContentGenerator from './ContentGenerator';
import ModelHealthDashboard from './ModelHealthDashboard';
import './AIPlayground.css';

const AIPlayground = () => {
    const [activeTab, setActiveTab] = useState('image');

    const tabs = [
        { id: 'image', label: 'Image Analysis', component: ImageAnalyzer },
        { id: 'chat', label: 'Chat AI', component: ChatInterface },
        { id: 'generate', label: 'Content Generator', component: ContentGenerator },
        { id: 'health', label: 'Health Dashboard', component: ModelHealthDashboard },
    ];

    const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

    return (
        <div className="ai-playground">
            <div className="playground-header">
                <h1>AI Models Playground</h1>
                <p>Explore multiple AI capabilities with Hugging Face and LangChain integration</p>
            </div>

            <div className="tab-navigation">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="tab-content">
                {ActiveComponent && <ActiveComponent />}
            </div>
        </div>
    );
};

export default AIPlayground;