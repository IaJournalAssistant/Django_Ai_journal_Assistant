from rest_framework import serializers
from .models import Conversation, Message, Reflection

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'text', 'is_user', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'title', 'created_at', 'updated_at', 'messages']


class ReflectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reflection
        fields = [
            'id', 'user', 'title', 'content', 'reflection_type',
            'mood', 'ai_analysis', 'prompt_used', 'conversation', 'created_at'
        ]
        extra_kwargs = {
            'mood': {'required': False, 'allow_blank': True},
            'ai_analysis': {'required': False, 'allow_blank': True},
            'prompt_used': {'required': False, 'allow_blank': True},
            'reflection_type': {'required': False, 'default': 'emotion'},
            'conversation': {'required': False, 'allow_null': True},
        }
