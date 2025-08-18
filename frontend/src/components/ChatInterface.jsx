import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '../hooks/useAI';
import './ChatInterface.css';

const ChatInterface = ({ sessionId = 'default-session' }) => {
    const [inputMessage, setInputMessage] = useState('');
    const messagesEndRef = useRef(null);
    const { sendMessage, loadConversation, messages, loading, error } = useChat(sessionId);

    useEffect(() => {
        loadConversation();
    }, [loadConversation]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim() || loading) return;

        const message = inputMessage.trim();
        setInputMessage('');

        try {
            await sendMessage(message);
        } catch (err) {
            console.error('Failed to send message:', err);
        }
    };

    const getSentimentColor = (sentiment) => {
        if (!sentiment) return '#gray';
        
        const label = sentiment.label.toLowerCase();
        if (label.includes('positive')) return '#4CAF50';
        if (label.includes('negative')) return '#f44336';
        return '#FF9800';
    };

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <h3>AI Chat Assistant</h3>
                <div className="session-info">
                    Session: {sessionId} | Messages: {Math.floor(messages.length / 2)}
                </div>
            </div>

            <div className="messages-container">
                {messages.map((msg, index) => (
                    <div 
                        key={index} 
                        className={`message ${msg.isUser ? 'user-message' : 'ai-message'}`}
                    >
                        <div className="message-content">
                            {msg.isUser ? msg.message : msg.response}
                        </div>
                        
                        {!msg.isUser && msg.sentiment && (
                            <div className="sentiment-indicator">
                                <span 
                                    className="sentiment-badge"
                                    style={{ backgroundColor: getSentimentColor(msg.sentiment) }}
                                >
                                    {msg.sentiment.label} ({(msg.sentiment.score * 100).toFixed(0)}%)
                                </span>
                            </div>
                        )}
                        
                        <div className="message-timestamp">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                        </div>
                    </div>
                ))}
                
                {loading && (
                    <div className="message ai-message loading">
                        <div className="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                )}
                
                <div ref={messagesEndRef} />
            </div>

            {error && (
                <div className="chat-error">
                    <strong>Error:</strong> {error}
                </div>
            )}

            <form onSubmit={handleSendMessage} className="message-input-form">
                <div className="input-container">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder="Type your message..."
                        disabled={loading}
                        className="message-input"
                    />
                    <button 
                        type="submit" 
                        disabled={!inputMessage.trim() || loading}
                        className="send-button"
                    >
                        Send
                    </button>
                </div>
            </form>
        </div>
    );
};

export default ChatInterface;