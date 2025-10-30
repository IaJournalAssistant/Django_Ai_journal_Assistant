from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import ImageEntry
from .serializers import ImageEntrySerializer
from .utils import extract_text_from_image, analyze_sentiment, analyze_emotion


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def analyze_image(request):
    """
    Endpoint pour analyser une image :
    - GET : affiche la page d'upload
    - POST : analyse l'image
    """
    if request.method == "GET":
        return render(request, "chatbotmedia/upload.html")

    if request.method == "POST" and request.FILES.get("image"):
        image_file = request.FILES["image"]
        user = request.user

        image_entry = ImageEntry.objects.create(user=user, image=image_file)

        # OCR
        image_path = image_entry.image.path
        extracted_text = extract_text_from_image(image_path)

        # Analyse du sentiment et de l’émotion
        sentiment = analyze_sentiment(extracted_text)
        emotion = analyze_emotion(image_path)

        image_entry.extracted_text = extracted_text
        image_entry.sentiment = sentiment
        image_entry.emotion = emotion
        image_entry.save()

        serializer = ImageEntrySerializer(image_entry, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response({"error": "Aucune image reçue"}, status=status.HTTP_400_BAD_REQUEST)
