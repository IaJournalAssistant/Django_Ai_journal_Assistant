from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Conversation, Message, Reflection
from .serializers import ConversationSerializer, ReflectionSerializer
from .ml_model import generate_ai_response
from django.utils import timezone
import random

# ===== PAGE PRINCIPALE DU CHATBOT =====
def chatbot_view(request):
    """Vue pour la page principale du chatbot"""
    return render(request, 'chatbot/chatbot.html')


# ===== CONVERSATIONS =====
@api_view(['GET'])
@permission_classes([AllowAny])
def list_conversations(request):
    """Lister toutes les conversations de l'utilisateur"""
    if request.user.is_authenticated:
        conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
    else:
        conversations = Conversation.objects.all().order_by('-updated_at')
    
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def start_conversation(request):
    """Démarrer une nouvelle conversation"""
    conversation = Conversation.objects.create(
        user=request.user if request.user.is_authenticated else None,
        title="Nouvelle conversation"
    )
    serializer = ConversationSerializer(conversation)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_conversation(request, id):
    """Afficher une conversation spécifique"""
    try:
        conversation = Conversation.objects.get(id=id)
        if request.user.is_authenticated and conversation.user != request.user:
            return Response({"error": "Accès non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation non trouvée"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_conversation(request, id):
    """Supprimer une conversation"""
    try:
        conversation = Conversation.objects.get(id=id)
        if request.user.is_authenticated and conversation.user != request.user:
            return Response({"error": "Accès non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation non trouvée"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_ai_response_view(request, id):
    """Générer une réponse IA pour une conversation"""
    try:
        conversation = Conversation.objects.get(id=id)
        user_message = request.data.get('message', '').strip()
        
        if not user_message:
            return Response({"error": "Le message est requis"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Sauvegarder le message de l'utilisateur
        Message.objects.create(
            conversation=conversation,
            text=user_message,
            is_user=True
        )
        
        # Générer la réponse IA
        ai_response = generate_ai_response(user_message)
        
        # Sauvegarder la réponse IA
        Message.objects.create(
            conversation=conversation,
            text=ai_response,
            is_user=False
        )
        
        # Mettre à jour le titre si c'est le premier message
        if conversation.messages.count() == 2:  # User + AI
            conversation.title = user_message[:50] + "..."
            conversation.save()
        
        serializer = ConversationSerializer(conversation)
        return Response({
            "conversation": serializer.data,
            "ai_response": ai_response
        })
        
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation non trouvée"}, status=status.HTTP_404_NOT_FOUND)


# ===== REFLECTIONS =====
@api_view(['GET'])
@permission_classes([AllowAny])
def list_reflections(request):
    """Lister toutes les réflexions"""
    if request.user.is_authenticated:
        reflections = Reflection.objects.filter(user=request.user)
    else:
        reflections = Reflection.objects.all()
    
    serializer = ReflectionSerializer(reflections, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def save_reflection(request):
    """Sauvegarder une réflexion utilisateur ou IA"""
    serializer = ReflectionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user if request.user.is_authenticated else None)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_reflection(request, id):
    """Supprimer une réflexion"""
    try:
        reflection = Reflection.objects.get(id=id)
        if request.user.is_authenticated and reflection.user != request.user:
            return Response({"error": "Accès non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        reflection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Reflection.DoesNotExist:
        return Response({"error": "Reflection non trouvée"}, status=status.HTTP_404_NOT_FOUND)


# ===== PROMPTS GUIDÉS =====
REFLECTION_PROMPTS = {
    'gratitude': [
        "Liste 3 choses qui t'ont apporté de la joie aujourd'hui",
        "Quel moment t'a fait sourire cette semaine ?",
        "Remercie une personne qui a illuminé ta journée",
        "Quelles petites choses simples as-tu appréciées récemment ?"
    ],
    'emotion': [
        "Comment te sens-tu physiquement et émotionnellement en ce moment ?",
        "Décris ton état d'esprit actuel en 3 mots",
        "Quelle émotion domine en ce moment ? Explique pourquoi",
        "Qu'est-ce qui influence le plus ton humeur aujourd'hui ?"
    ],
    'cycle': [
        "Comment ton cycle influence-t-il ton humeur aujourd'hui ?",
        "Décris tes symptômes et ton état émotionnel",
        "As-tu remarqué des patterns dans tes émotions selon ton cycle ?",
        "Comment prends-tu soin de toi pendant cette phase de ton cycle ?"
    ],
    'mindfulness': [
        "Qu'as-tu remarqué autour de toi en cet instant ?",
        "Fais une pause et décris ce que tu entends, vois, ressens",
        "Quelle petite chose peux-tu apprécier en ce moment ?",
        "Qu'est-ce qui te rend reconnaissant·e en cet instant précis ?"
    ]
}


@api_view(['GET'])
@permission_classes([AllowAny])
def get_reflection_prompt(request):
    """Obtenir un prompt aléatoire selon le type de réflexion"""
    reflection_type = request.GET.get('type', 'emotion')
    if reflection_type not in REFLECTION_PROMPTS:
        return Response({"error": "Type de réflexion invalide"}, status=status.HTTP_400_BAD_REQUEST)
    
    prompt = random.choice(REFLECTION_PROMPTS[reflection_type])
    return Response({"prompt": prompt, "type": reflection_type})


@api_view(['POST'])
@permission_classes([AllowAny])
def save_guided_reflection(request):
    """Sauvegarder une réflexion guidée avec analyse IA"""
    serializer = ReflectionSerializer(data=request.data)
    if serializer.is_valid():
        user_text = serializer.validated_data.get('content', '')
        reflection_type = serializer.validated_data.get('reflection_type', 'emotion')
        
        ai_analysis = generate_simple_analysis(user_text, reflection_type)
        
        reflection = serializer.save(
            user=request.user if request.user.is_authenticated else None,
            ai_analysis=ai_analysis,
            title=f"Réflexion {reflection_type} - {timezone.now().strftime('%d/%m/%Y')}"
        )
        return Response(ReflectionSerializer(reflection).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def generate_simple_analysis(text, reflection_type):
    """Analyse basique d'une réflexion"""
    analyses = {
        'gratitude': "Merci d'avoir partagé ces moments de gratitude ✨",
        'emotion': "Merci pour ce partage émotionnel 💕", 
        'cycle': "Merci pour ce suivi de cycle 🌸",
        'mindfulness': "Belle pratique de pleine conscience 🌿"
    }
    return analyses.get(reflection_type, "Merci pour ta réflexion ❤️")


# ===== ENDPOINT DE TEST =====
@api_view(['POST'])
@permission_classes([AllowAny])
def test_api(request):
    """Endpoint pour tester si l'API fonctionne"""
    return Response({"message": "Chatbot API fonctionne !", "status": "success"})
