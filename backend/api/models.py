from django.db import models
import json

class AIModelResult(models.Model):
    MODEL_TYPES = [
        ('vision', 'Vision Model'),
        ('text', 'Text Model'),
        ('chat', 'Chat Model'),
        ('embedding', 'Embedding Model'),
    ]

    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    model_name = models.CharField(max_length=200)
    input_data = models.TextField()
    result = models.JSONField()
    confidence_score = models.FloatField(null=True, blank=True)
    processing_time = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class ConversationSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    context_summary = models.TextField(blank=True)
    message_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    sentiment_score = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
