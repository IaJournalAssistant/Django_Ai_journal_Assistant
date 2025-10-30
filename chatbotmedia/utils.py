import pytesseract
from PIL import Image
from transformers import pipeline

# Configuration OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Pipelines Hugging Face
sentiment_pipeline = pipeline("sentiment-analysis")
emotion_model = pipeline("image-classification", model="trpakov/vit-face-expression")

def extract_text_from_image(image_path):
    """Extrait le texte d'une image via Tesseract OCR."""
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        print("Erreur OCR:", e)
        return ""

def analyze_sentiment(text):
    """Analyse le sentiment du texte extrait."""
    if text:
        try:
            result = sentiment_pipeline(text)
            return result[0]['label']
        except Exception as e:
            print("Erreur sentiment:", e)
            return "unknown"
    return "unknown"

def analyze_emotion(image_path):
    """Analyse l'émotion de l'image via le modèle trpakov/vit-face-expression."""
    try:
        image = Image.open(image_path).convert("RGB")
        result = emotion_model(image)
        top_emotion = max(result, key=lambda x: x["score"])
        return top_emotion["label"]
    except Exception as e:
        print("Erreur emotion:", e)
        return "unknown"
