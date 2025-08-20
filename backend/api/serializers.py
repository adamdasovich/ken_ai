from rest_framework import serializers
from .models import AIModelResult, ConversationSession, ChatMessage

class AIModelResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModelResult
        fields = '__all__'

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['message', 'response', 'sentiment_score', 'timestamp']

class ConversationSessionSerializer(serializers.ModelSerializer):
    # Fixed: Use the correct related name based on your model field
    messages = ChatMessageSerializer(many=True, read_only=True, source='chatmessage_set')
    
    class Meta:
        model = ConversationSession
        fields = ['session_id', 'context_summary', 'message_count', 'created_at', 'messages']

class ImageAnalysisSerializer(serializers.Serializer):
    image = serializers.ImageField()
    context_text = serializers.CharField(required=False, allow_blank=True)

class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=100)
    message = serializers.CharField()

class ContentGenerationSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    max_length = serializers.IntegerField(default=200, min_value=50, max_value=500)