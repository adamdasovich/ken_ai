from transformers import pipeline, AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
from langchain.llms import HuggingFacePipeline
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage
import torch
from PIL import Image
import time
import logging

logger = logging.getLogger(__name__)

class AIModelManager:
    """Centralized manager for all AI models"""
    
    def __init__(self):
        self.models = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_models()
    
    def _load_models(self):
        """Initialize all models - consider lazy loading for production"""
        try:
            # Vision model
            self.models['vision'] = pipeline(
                "image-classification",
                model="google/vit-base-patch16-224",
                device=0 if self.device == "cuda" else -1
            )
            
            # Text classification
            self.models['sentiment'] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1
            )
            
            # Zero-shot classification
            self.models['zero_shot'] = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if self.device == "cuda" else -1
            )
            
            # Text generation
            self.models['generator'] = pipeline(
                "text-generation",
                model="gpt2",
                device=0 if self.device == "cuda" else -1,
                pad_token_id=50256
            )
            
            # Summarization
            self.models['summarizer'] = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if self.device == "cuda" else -1
            )
            
            # Embeddings
            self.models['embeddings'] = SentenceTransformer(
                'sentence-transformers/all-MiniLM-L6-v2'
            )
            
            # Toxicity detection
            self.models['toxicity'] = pipeline(
                "text-classification",
                model="martin-ha/toxic-comment-model",
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("All AI models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

class MultiModalAnalyzer:
    """Service for multi-modal content analysis"""
    
    def __init__(self, model_manager: AIModelManager):
        self.model_manager = model_manager
    
    def analyze_image_with_context(self, image_path: str, text_context: str = ""):
        """Analyze image and optionally combine with text context"""
        start_time = time.time()
        
        try:
            # Image analysis
            image = Image.open(image_path)
            vision_results = self.model_manager.models['vision'](image)
            
            # Extract top predictions
            top_predictions = vision_results[:3]
            image_labels = [pred['label'] for pred in top_predictions]
            
            # If text context provided, analyze it too
            context_analysis = None
            if text_context:
                sentiment = self.model_manager.models['sentiment'](text_context)
                context_analysis = {
                    'sentiment': sentiment,
                    'categories': self.model_manager.models['zero_shot'](
                        text_context, 
                        candidate_labels=['technology', 'nature', 'business', 'personal', 'educational']
                    )
                }
            
            # Generate embeddings for similarity matching
            combined_text = f"Image contains: {', '.join(image_labels)}"
            if text_context:
                combined_text += f" Context: {text_context}"
            
            embeddings = self.model_manager.models['embeddings'].encode([combined_text])
            
            processing_time = time.time() - start_time
            
            return {
                'image_analysis': {
                    'predictions': top_predictions,
                    'top_labels': image_labels
                },
                'text_analysis': context_analysis,
                'embeddings': embeddings[0].tolist(),
                'processing_time': processing_time,
                'combined_description': combined_text
            }
            
        except Exception as e:
            logger.error(f"Error in multi-modal analysis: {e}")
            raise

class ConversationalAI:
    """Service for conversational AI with memory"""
    
    def __init__(self, model_manager: AIModelManager):
        self.model_manager = model_manager
        self.conversations = {}
    
    def get_or_create_conversation(self, session_id: str):
        """Get existing conversation or create new one"""
        if session_id not in self.conversations:
            # Create HuggingFace pipeline for LangChain
            hf_pipeline = HuggingFacePipeline.from_model_id(
                model_id="microsoft/DialoGPT-medium",
                task="text-generation",
                device=0 if torch.cuda.is_available() else -1,
                model_kwargs={
                    "temperature": 0.7,
                    "max_length": 1000,
                    "do_sample": True
                }
            )
            
            # Create conversation chain with memory
            memory = ConversationBufferWindowMemory(k=10)  # Remember last 10 exchanges
            self.conversations[session_id] = ConversationChain(
                llm=hf_pipeline,
                memory=memory,
                verbose=True
            )
        
        return self.conversations[session_id]
    
    def chat(self, session_id: str, message: str):
        """Process chat message with context awareness"""
        start_time = time.time()
        
        try:
            # Get conversation chain
            conversation = self.get_or_create_conversation(session_id)
            
            # Analyze message sentiment first
            sentiment = self.model_manager.models['sentiment'](message)[0]
            
            # Check for toxicity
            toxicity = self.model_manager.models['toxicity'](message)[0]
            
            if toxicity['label'] == 'TOXIC' and toxicity['score'] > 0.7:
                response = "I can't respond to that type of message. Let's keep our conversation respectful."
            else:
                # Generate response using conversation chain
                response = conversation.predict(input=message)
            
            processing_time = time.time() - start_time
            
            return {
                'response': response,
                'sentiment': sentiment,
                'toxicity_check': toxicity,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            raise
    
    def summarize_conversation(self, session_id: str):
        """Summarize conversation history"""
        if session_id in self.conversations:
            conversation = self.conversations[session_id]
            chat_history = conversation.memory.buffer
            
            if len(chat_history) > 100:  # Only summarize if substantial content
                summary = self.model_manager.models['summarizer'](
                    chat_history, 
                    max_length=150, 
                    min_length=50, 
                    do_sample=False
                )
                return summary[0]['summary_text']
        
        return None

class ContentGenerator:
    """Service for content generation with validation"""
    
    def __init__(self, model_manager: AIModelManager):
        self.model_manager = model_manager
    
    def generate_safe_content(self, prompt: str, max_length: int = 200):
        """Generate content with safety checks"""
        start_time = time.time()
        
        try:
            # Check input prompt for toxicity
            toxicity_check = self.model_manager.models['toxicity'](prompt)[0]
            
            if toxicity_check['label'] == 'TOXIC' and toxicity_check['score'] > 0.5:
                return {
                    'error': 'Prompt rejected due to potentially harmful content',
                    'toxicity_score': toxicity_check['score']
                }
            
            # Generate content
            generated = self.model_manager.models['generator'](
                prompt,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=50256
            )
            
            generated_text = generated[0]['generated_text']
            
            # Validate generated content
            content_sentiment = self.model_manager.models['sentiment'](generated_text)[0]
            content_toxicity = self.model_manager.models['toxicity'](generated_text)[0]
            
            # Filter out toxic content
            if content_toxicity['label'] == 'TOXIC' and content_toxicity['score'] > 0.5:
                return {
                    'error': 'Generated content failed safety check',
                    'reason': 'High toxicity score'
                }
            
            processing_time = time.time() - start_time
            
            return {
                'generated_text': generated_text,
                'sentiment': content_sentiment,
                'safety_score': 1 - content_toxicity['score'],
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in content generation: {e}")
            raise

# Initialize global model manager (consider using Django's app registry)
try:
    model_manager = AIModelManager()
    print("AI Model Manager initialized successfully")
except Exception as e:
    print(f"Error initializing AI Model Manager: {e}")
    model_manager = None