from django.db import models
from django.contrib.auth.models import User


class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} - {self.title or 'Sans titre'}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    is_user = models.BooleanField(default=True)  # True = user, False = AI
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{'User' if self.is_user else 'AI'}: {self.text[:50]}..."


class Reflection(models.Model):
    REFLECTION_TYPES = [
        ('gratitude', '😊 Gratitude'),
        ('emotion', '🎭 Émotions'),
        ('cycle', '🌙 Cycle & Humeur'),
        ('mindfulness', '🧘 Pleine Conscience'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    reflection_type = models.CharField(max_length=20, choices=REFLECTION_TYPES, default='emotion')
    mood = models.CharField(max_length=50, blank=True)
    ai_analysis = models.TextField(blank=True)
    prompt_used = models.TextField(blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
