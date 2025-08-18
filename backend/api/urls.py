from django.urls import path
from . import views

urlpatterns = [
    path('ai/analyze-image/', views.analyze_image, name='analyze_image'),
    path('ai/chat/', views.chat_message, name='chat_message'),
    path('ai/conversation/<str:session_id>/', views.get_conversation, name='get_conversation'),
    path('ai/generate-content/', views.generate_content, name='generate_content'),
    path('ai/health/', views.model_health_check, name='model_health'),
    path('ai/results/', views.get_model_results, name='model_results'),
    path('ai/model-status/', views.model_status, name='model_status'),
    path('ai/analyzeImage/', views.analyze_image, name='analyze_image_camel'),
]