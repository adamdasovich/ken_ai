from .ai_services import model_manager, MultiModalAnalyzer, ConversationalAI, ContentGenerator
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import AIModelResult, ConversationSession, ChatMessage
from .serializers import *

import uuid
import os
import json
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse

import time
import json
from PIL import Image
import io


# Initialize services
multimodal_analyzer = MultiModalAnalyzer(model_manager)
conversational_ai = ConversationalAI(model_manager)
content_generator = ContentGenerator(model_manager)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def analyze_image(request):
    """Multi-modal image analysis endpoint - Windows-safe memory-based approach"""
    serializer = ImageAnalysisSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if model manager is properly initialized
        print(f"DEBUG: model_manager exists: {model_manager is not None}")
        
        if model_manager is None:
            return Response({
                'error': 'AI models are not loaded. Please check server logs.',
                'status': 'error'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        print(f"DEBUG: model_manager has models attribute: {hasattr(model_manager, 'models')}")
        
        if not hasattr(model_manager, 'models'):
            return Response({
                'error': 'AI models are not properly initialized.',
                'status': 'error'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        image_file = serializer.validated_data['image']
        context_text = serializer.validated_data.get('context_text', '')
        
        # Open image directly from uploaded file
        image_file.seek(0)
        image = Image.open(io.BytesIO(image_file.read()))
        
        start_time = time.time()
        
        # Get vision model (this will trigger lazy loading)
        print("DEBUG: Getting vision model...")
        try:
            vision_model = model_manager.get_model('vision')
            print(f"DEBUG: Vision model loaded: {vision_model is not None}")
        except Exception as model_error:
            print(f"DEBUG: Error loading vision model: {model_error}")
            return Response({
                'error': f'Vision model failed to load: {str(model_error)}',
                'status': 'error'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if not vision_model:
            return Response({
                'error': 'Vision model not available',
                'available_models': list(model_manager.models.keys()),
                'status': 'error'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Image analysis
        print("DEBUG: Running vision model...")
        vision_results = vision_model(image)
        print(f"DEBUG: Vision results: {vision_results}")
        
        # Extract top predictions
        top_predictions = vision_results[:3] if vision_results else []
        image_labels = [pred['label'] for pred in top_predictions]
        
        # Context analysis if provided
        context_analysis = None
        if context_text:
            # Try to get sentiment model
            try:
                sentiment_model = model_manager.get_model('sentiment')
                if sentiment_model:
                    sentiment = sentiment_model(context_text)
                    context_analysis = {'sentiment': sentiment}
            except Exception as e:
                print(f"DEBUG: Sentiment analysis failed: {e}")
                context_analysis = {'sentiment': {'label': 'NEUTRAL', 'score': 0.5}}
        
        # Generate embeddings if model is available
        embeddings = None
        combined_text = f"Image contains: {', '.join(image_labels)}"
        if context_text:
            combined_text += f" Context: {context_text}"
        
        try:
            embeddings_model = model_manager.get_model('embeddings')
            if embeddings_model:
                embeddings = embeddings_model.encode([combined_text])
        except Exception as e:
            print(f"DEBUG: Embeddings failed: {e}")
        
        processing_time = time.time() - start_time
        
        result = {
            'image_analysis': {
                'predictions': top_predictions,
                'top_labels': image_labels
            },
            'text_analysis': context_analysis,
            'embeddings': embeddings[0].tolist() if embeddings is not None else None,
            'processing_time': processing_time,
            'combined_description': combined_text
        }
        
        # Save result to database
        ai_result = AIModelResult.objects.create(
            model_type='vision',
            model_name='multimodal_analyzer_memory',
            input_data=json.dumps({
                'image_name': image_file.name,
                'context': context_text
            }),
            result=result,
            confidence_score=top_predictions[0]['score'] if top_predictions else 0.0,
            processing_time=processing_time
        )
        
        return Response({
            'id': ai_result.id,
            'analysis': result,
            'status': 'success'
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in analyze_image: {error_details}")
        
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def chat_message(request):
    """Conversational AI endpoint"""
    serializer = ChatRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        session_id = serializer.validated_data['session_id']
        message = serializer.validated_data['message']
        
        # Get or create conversation session
        session, created = ConversationSession.objects.get_or_create(
            session_id=session_id,
            defaults={'message_count': 0}
        )
        
        # Process chat message
        chat_result = conversational_ai.chat(session_id, message)
        
        # Save message and response
        chat_message = ChatMessage.objects.create(
            session=session,
            message=message,
            response=chat_result['response'],
            sentiment_score=chat_result['sentiment']['score']
        )
        
        # Update session
        session.message_count += 1
        session.save()
        
        # Summarize conversation if it's getting long
        if session.message_count % 20 == 0:  # Every 20 messages
            summary = conversational_ai.summarize_conversation(session_id)
            if summary:
                session.context_summary = summary
                session.save()
        
        # Save AI result
        AIModelResult.objects.create(
            model_type='chat',
            model_name='conversational_ai',
            input_data=message,
            result=chat_result,
            confidence_score=chat_result['sentiment']['score'],
            processing_time=chat_result['processing_time']
        )
        
        return Response({
            'message_id': chat_message.id,
            'response': chat_result['response'],
            'sentiment': chat_result['sentiment'],
            'session_info': {
                'message_count': session.message_count,
                'has_summary': bool(session.context_summary)
            }
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_conversation(request, session_id):
    """Get conversation history"""
    try:
        session = ConversationSession.objects.get(session_id=session_id)
        serializer = ConversationSessionSerializer(session)
        return Response(serializer.data)
        
    except ConversationSession.DoesNotExist:
        # Return empty conversation instead of 404
        return Response({
            'session_id': session_id,
            'context_summary': '',
            'message_count': 0,
            'created_at': None,
            'messages': []
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_conversation: {error_details}")
        
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def generate_content(request):
    """Content generation with safety checks"""
    serializer = ContentGenerationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        prompt = serializer.validated_data['prompt']
        max_length = serializer.validated_data['max_length']
        
        # Generate content

        result = content_generator.generate_safe_content(prompt, max_length)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        # Save result
        ai_result = AIModelResult.objects.create(
            model_type='text',
            model_name='content_generator',
            input_data=prompt,
            result=result,
            confidence_score=result['safety_score'],
            processing_time=result['processing_time']
        )
        
        return Response({
            'id': ai_result.id,
            'generated_content': result['generated_text'],
            'sentiment': result['sentiment'],
            'safety_score': result['safety_score'],
            'status': 'success'
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def model_status(request):
    """Check model loading status"""
    try:
        status_info = {
            'model_manager_exists': model_manager is not None,
            'has_models_attribute': hasattr(model_manager, 'models') if model_manager else False,
            'available_models': [],
            'loading_errors': []
        }
        
        if model_manager and hasattr(model_manager, 'models'):
            status_info['available_models'] = list(model_manager.models.keys())
            status_info['models_count'] = len(model_manager.models)
        
        return Response(status_info)
        
    except Exception as e:
        return Response({
            'error': str(e),
            'model_manager_exists': model_manager is not None,
        })

@api_view(['GET'])
def model_health_check(request):
    """Check if all models are loaded and working"""
    try:
        if model_manager is None:
            return Response({
                'status': 'unhealthy',
                'error': 'Model manager not initialized',
                'timestamp': timezone.now().isoformat()
            })
        
        if not hasattr(model_manager, 'models'):
            return Response({
                'status': 'unhealthy', 
                'error': 'Models not loaded',
                'timestamp': timezone.now().isoformat()
            })
        
        # Test each model exists and is not None
        test_results = {
            'vision': model_manager.models.get('vision') is not None,
            'sentiment': model_manager.models.get('sentiment') is not None,
            'zero_shot': model_manager.models.get('zero_shot') is not None,
            'generator': model_manager.models.get('generator') is not None,
            'summarizer': model_manager.models.get('summarizer') is not None,
            'embeddings': model_manager.models.get('embeddings') is not None,
            'toxicity': model_manager.models.get('toxicity') is not None,
        }
        
        # Count how many models are loaded
        loaded_count = sum(test_results.values())
        total_models = len(test_results)
        
        # Determine status
        if loaded_count == total_models:
            status = 'healthy'
        elif loaded_count > 0:
            status = 'degraded'
        else:
            status = 'unhealthy'
        
        return Response({
            'status': status,
            'models': test_results,
            'loaded_models': loaded_count,
            'total_models': total_models,
            'device': getattr(model_manager, 'device', 'unknown'),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Health check error: {error_details}")
        
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def get_model_results(request):
    """Get recent AI model results with filtering"""
    model_type = request.GET.get('model_type')
    limit = int(request.GET.get('limit', 50))
    
    queryset = AIModelResult.objects.all()
    
    if model_type:
        queryset = queryset.filter(model_type=model_type)
    
    results = queryset[:limit]
    serializer = AIModelResultSerializer(results, many=True)
    
    return Response(serializer.data)