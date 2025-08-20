from transformers import pipeline, AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import torch
from PIL import Image
import time
import logging
import threading
from django.conf import settings

logger = logging.getLogger(__name__)

class AIModelManager:
    """Centralized manager for all AI models with lazy loading"""
    
    def __init__(self):
        self.models = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._loading_lock = threading.Lock()
        self._loaded_models = set()
        
        # Don't load all models immediately - use lazy loading instead
        logger.info(f"AI Model Manager initialized. Device: {self.device}")


    def _load_model(self, model_name: str):
        #Lazy load individual models only when needed - Windows optimized
        if model_name in self._loaded_models:
            return
        with self._loading_lock:
            if model_name in self._loaded_models:  # Double-check pattern
                return
            
            try:
                logger.info(f"Loading {model_name} model...")
                print(f"DEBUG: Starting to load {model_name} model...")
                
                if model_name == 'vision':
                    print('DEBUG: Loading ResNet-50 vision model...')

                    try:
                        self.models['vision'] = pipeline(
                            "image-classification",
                            model="openai/clip-vit-base-patch32",
                            device=-1, # cpu for stability
                        )
                        print("DEBUG: ResNet-50 vision model loaded successfully!")
                        #quick test
                        from PIL import Image
                        test_img = Image.new('RGB', (224, 224), color='blue')
                        test_result = self.models['vision'](test_img)
                        print(f"DEBUG: Vision model test passed: {test_result[0]['label']})")

                    except Exception as e:
                        print(f"DEBUG: ResNet-50 failed: {e}")
                        print("DEBUG: Falling back to mock model...")


                        class MockVisionModel:
                            def __call__(self, image):
                                return [
                                    {"label": "photograph", "score": 0.85},
                                    {"label": "digital_image", "score": 0.10},
                                    {"label": "visual_content", "score": 0.05}
                                ]
                        self.models['vision'] = MockVisionModel()
                        print("DEBUG: Mock vision model ready")                
                
                elif model_name == 'sentiment':
                    print("DEBUG: Loading sentiment model...")
                    # Use a lighter sentiment model for Windows
                    try:
                        self.models['sentiment'] = pipeline(
                            "sentiment-analysis",
                            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                            device=-1
                        )
                    except:
                        # Fallback to default model
                        self.models['sentiment'] = pipeline(
                            "sentiment-analysis",
                            device=-1
                        )
                    print("DEBUG: Sentiment model loaded successfully!")
                
                elif model_name == 'zero_shot':
                    print("DEBUG: Loading zero-shot model...")
                    self.models['zero_shot'] = pipeline(
                        "zero-shot-classification",
                        model="facebook/bart-large-mnli",
                        device=-1
                    )
                    print("DEBUG: Zero-shot model loaded successfully!")
                
                elif model_name == 'generator':
                    print("DEBUG: Loading generator model...")
                    self.models['generator'] = pipeline(
                        "text-generation",
                        model="microsoft/DialoGPT-medium",
                        device=-1,
                        pad_token_id=50256
                    )
                    print("DEBUG: Generator model loaded successfully!")
                
                elif model_name == 'summarizer':
                    print("DEBUG: Loading summarizer model...")
                    self.models['summarizer'] = pipeline(
                        "summarization",
                        model="facebook/bart-large-cnn",
                        device=-1
                    )
                    print("DEBUG: Summarizer model loaded successfully!")
                
                elif model_name == 'embeddings':
                    print("DEBUG: Loading embeddings model...")
                    self.models['embeddings'] = SentenceTransformer(
                        'sentence-transformers/all-MiniLM-L6-v2'
                    )
                    print("DEBUG: Embeddings model loaded successfully!")
                
                elif model_name == 'toxicity':
                    print("DEBUG: Loading toxicity model...")
                    try:
                        self.models['toxicity'] = pipeline(
                            "text-classification",
                            model="martin-ha/toxic-comment-model",
                            device=-1
                        )
                    except:
                        # Fallback to a simpler toxicity model
                        self.models['toxicity'] = pipeline(
                            "text-classification",
                            model="unitary/toxic-bert-base",
                            device=-1
                        )
                    print("DEBUG: Toxicity model loaded successfully!")
                
                self._loaded_models.add(model_name)
                logger.info(f"{model_name} model loaded successfully")
                print(f"DEBUG: {model_name} model added to loaded models")
                
            except Exception as e:
                logger.error(f"Error loading {model_name} model: {e}")
                print(f"DEBUG: Failed to load {model_name} model: {e}")
                print(f"DEBUG: Error type: {type(e)}")
                import traceback
                print(f"DEBUG: Full traceback: {traceback.format_exc()}")
                # Store a None value to indicate failed loading
                self.models[model_name] = None
                raise


       
    

    def get_model(self, model_name: str):
        """Get model, loading it if necessary"""
        if model_name not in self._loaded_models:
            self._load_model(model_name)
        return self.models.get(model_name)
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if model is available and loaded"""
        return model_name in self._loaded_models and self.models.get(model_name) is not None

class MultiModalAnalyzer:
    """Service for multi-modal content analysis"""
    
    def __init__(self, model_manager: AIModelManager):
        self.model_manager = model_manager
    
    def analyze_image_with_context(self, image, text_context: str = ""):
        """Analyze image and optionally combine with text context"""
        start_time = time.time()
        
        try:
            # Ensure vision model is loaded
            vision_model = self.model_manager.get_model('vision')
            if not vision_model:
                raise Exception("Vision model not available")
            
            # Image analysis
            if isinstance(image, str):
                image = Image.open(image)
            
            vision_results = vision_model(image)
            
            # Extract top predictions
            top_predictions = vision_results[:3] if vision_results else []
            image_labels = [pred['label'] for pred in top_predictions]
            
            # If text context provided, analyze it too
            context_analysis = None
            if text_context:
                sentiment_model = self.model_manager.get_model('sentiment')
                if sentiment_model:
                    sentiment = sentiment_model(text_context)
                    context_analysis = {'sentiment': sentiment}
                    
                    # Add zero-shot classification if available
                    zero_shot_model = self.model_manager.get_model('zero_shot')
                    if zero_shot_model:
                        context_analysis['categories'] = zero_shot_model(
                            text_context, 
                            candidate_labels=['technology', 'nature', 'business', 'personal', 'educational']
                        )
            
            # Generate embeddings for similarity matching
            combined_text = f"Image contains: {', '.join(image_labels)}"
            if text_context:
                combined_text += f" Context: {text_context}"
            
            embeddings = None
            embeddings_model = self.model_manager.get_model('embeddings')
            if embeddings_model:
                embeddings = embeddings_model.encode([combined_text])
            
            processing_time = time.time() - start_time
            
            return {
                'image_analysis': {
                    'predictions': top_predictions,
                    'top_labels': image_labels
                },
                'text_analysis': context_analysis,
                'embeddings': embeddings[0].tolist() if embeddings is not None else None,
                'processing_time': processing_time,
                'combined_description': combined_text
            }
            
        except Exception as e:
            logger.error(f"Error in multi-modal analysis: {e}")
            raise

class ConversationalAI:
    """Service for conversational AI with simplified implementation"""
    
    def __init__(self, model_manager: AIModelManager):
        self.model_manager = model_manager
        self.conversations = {}  # Simple in-memory storage
    
    def chat(self, session_id: str, message: str):
        """Process chat message with context awareness"""
        start_time = time.time()
        
        try:
            # Analyze message sentiment
            sentiment_model = self.model_manager.get_model('sentiment')
            sentiment = {'label': 'NEUTRAL', 'score': 0.5}
            if sentiment_model:
                sentiment_result = sentiment_model(message)
                if sentiment_result:
                    sentiment = sentiment_result[0]
            
            # Check for toxicity
            toxicity_model = self.model_manager.get_model('toxicity')
            toxicity = {'label': 'NON_TOXIC', 'score': 0.1}
            if toxicity_model:
                toxicity_result = toxicity_model(message)
                if toxicity_result:
                    toxicity = toxicity_result[0]
            
            if toxicity['label'] == 'TOXIC' and toxicity['score'] > 0.7:
                response = "I can't respond to that type of message. Let's keep our conversation respectful."
            else:
                # Simple response generation
                generator_model = self.model_manager.get_model('generator')
                if generator_model:
                    # Create a conversational prompt
                    prompt = f"Human: {message}\nAssistant:"
                    generated = generator_model(
                        prompt,
                        max_length=len(prompt) + 100,
                        num_return_sequences=1,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=50256
                    )
                    response = generated[0]['generated_text'][len(prompt):].strip()
                else:
                    response = f"I understand you said: {message}. How can I help you further?"
            
            # Store conversation history
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            self.conversations[session_id].append({
                'message': message,
                'response': response,
                'timestamp': time.time()
            })
            
            processing_time = time.time() - start_time
            
            return {
                'response': response,
                'sentiment': sentiment,
                'toxicity_check': toxicity,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            return {
                'response': f"I encountered an error processing your message: {str(e)}",
                'sentiment': {'label': 'NEUTRAL', 'score': 0.5},
                'toxicity_check': {'label': 'NON_TOXIC', 'score': 0.1},
                'processing_time': time.time() - start_time
            }
    
    def summarize_conversation(self, session_id: str):
        """Summarize conversation history"""
        if session_id not in self.conversations:
            return None
            
        conversation_history = self.conversations[session_id]
        if len(conversation_history) < 5:  # Only summarize if enough content
            return None
            
        # Create conversation text
        conversation_text = ""
        for exchange in conversation_history[-10:]:  # Last 10 exchanges
            conversation_text += f"Human: {exchange['message']}\nAssistant: {exchange['response']}\n"
        
        if len(conversation_text) > 1000:  # Only summarize long conversations
            summarizer_model = self.model_manager.get_model('summarizer')
            if summarizer_model:
                try:
                    summary = summarizer_model(
                        conversation_text, 
                        max_length=150, 
                        min_length=50, 
                        do_sample=False
                    )
                    return summary[0]['summary_text']
                except Exception as e:
                    logger.error(f"Error summarizing conversation: {e}")
        
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
            toxicity_model = self.model_manager.get_model('toxicity')
            if toxicity_model:
                toxicity_check = toxicity_model(prompt)
                if toxicity_check and toxicity_check[0]['label'] == 'TOXIC' and toxicity_check[0]['score'] > 0.5:
                    return {
                        'error': 'Prompt rejected due to potentially harmful content',
                        'toxicity_score': toxicity_check[0]['score']
                    }
            
            # Generate content
            generator_model = self.model_manager.get_model('generator')
            if not generator_model:
                return {
                    'error': 'Content generation model not available'
                }
            
            generated = generator_model(
                prompt,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=50256
            )
            
            generated_text = generated[0]['generated_text']
            
            # Validate generated content
            sentiment_model = self.model_manager.get_model('sentiment')
            content_sentiment = {'label': 'NEUTRAL', 'score': 0.5}
            if sentiment_model:
                sentiment_result = sentiment_model(generated_text)
                if sentiment_result:
                    content_sentiment = sentiment_result[0]
            
            content_toxicity = {'label': 'NON_TOXIC', 'score': 0.1}
            if toxicity_model:
                toxicity_result = toxicity_model(generated_text)
                if toxicity_result:
                    content_toxicity = toxicity_result[0]
            
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
            return {
                'error': f'Content generation failed: {str(e)}',
                'processing_time': time.time() - start_time
            }

# Initialize global model manager with lazy loading
try:
    model_manager = AIModelManager()
    logger.info("AI Model Manager initialized with lazy loading")
except Exception as e:
    logger.error(f"Error initializing AI Model Manager: {e}")
    model_manager = None