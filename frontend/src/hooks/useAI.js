import { useState, useCallback } from 'react';
import { aiService } from '../services/aiService';

export const useImageAnalysis = () => {
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)

    const analyzeImage = useCallback(async (imageFile, contextText = '') => {
        setLoading(true)
        setError(null)
        try {
            const response = await aiService.analyzeImage(imageFile, contextText);
            setResult(response);
            return response;
        }
        catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false)
        }
    }, [])

    return { analyzeImage, loading, result, error}
};

export const useChat = (sessionId) => {
     const [loading, setLoading] = useState(false);
    const [messages, setMessages] = useState([]);
    const [error, setError] = useState(null);

    const sendMessage = useCallback(async (message) => {
        setLoading(true);
        setError(null);
        
        // Add user message immediately
        const userMessage = {
            message: message,
            response: null,
            timestamp: new Date().toISOString(),
            isUser: true
        };
        setMessages(prev => [...prev, userMessage]);

        try {
            const response = await aiService.sendChatMessage(sessionId, message);
            
            // Add AI response
            const aiMessage = {
                message: message,
                response: response.response,
                sentiment: response.sentiment,
                timestamp: new Date().toISOString(),
                isUser: false
            };
            
            setMessages(prev => [...prev.slice(0, -1), userMessage, aiMessage]);
            return response;
        } catch (err) {
            setError(err.message);
            // Remove the pending user message on error
            setMessages(prev => prev.slice(0, -1));
            throw err;
        } finally {
            setLoading(false);
        }
    }, [sessionId]);

    const loadConversation = useCallback(async () => {
        try {
            const conversation = await aiService.getConversation(sessionId);
            const formattedMessages = conversation.messages.flatMap(msg => [
                { ...msg, isUser: true },
                { ...msg, isUser: false }
            ]);
            setMessages(formattedMessages);
        } catch (err) {
            setError(err.message);
        }
    }, [sessionId]);

    return { sendMessage, loadConversation, messages, loading, error };
}

export const useContentGeneration = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const generateContent = useCallback(async (prompt, maxLength = 200) => {
        setLoading(true);
        setError(null);
        try {
            const response = await aiService.generateContent(prompt, maxLength);
            setResult(response);
            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return { generateContent, loading, result, error };
};