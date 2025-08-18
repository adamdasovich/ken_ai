from django.contrib import admin
from .models import AIModelResult, ConversationSession, ChatMessage

# Register your models here.
admin.site.register(AIModelResult)
admin.site.register(ConversationSession)
admin.site.register(ChatMessage)
