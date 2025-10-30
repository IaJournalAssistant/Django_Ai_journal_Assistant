from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import logging
import random
from collections import deque

logger = logging.getLogger(__name__)

# 🧠 Nouveau modèle empathique
MODEL_NAME = "AliiaR/DialoGPT-medium-empathetic-dialogues"
_chat_pipeline = None

# 🗣️ Petite mémoire contextuelle (3 derniers échanges)
conversation_history = deque(maxlen=3)


def get_chat_pipeline():
    """Initialise et met en cache le pipeline du modèle de chat."""
    global _chat_pipeline
    if _chat_pipeline is None:
        try:
            logger.info("Loading empathetic chatbot model...")
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

            _chat_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=-1  # CPU
            )
            logger.info("Model loaded successfully ✅")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            _chat_pipeline = None
    return _chat_pipeline


def generate_ai_response(user_input, max_length=200):
    """Génère une réponse émotionnelle et humaine du chatbot."""
    try:
        chat_pipeline = get_chat_pipeline()
        if chat_pipeline is None:
            return "I'm here for you. Tell me more about what’s on your mind 💬"

        # Ajouter la requête utilisateur à l'historique
        conversation_history.append(f"User: {user_input}")

        # Contexte conversationnel + ton émotionnel
        context = "\n".join(list(conversation_history))
        emotional_prompt = (
            "You are a compassionate and emotionally intelligent AI journal companion. "
            "You listen deeply, respond with empathy, and use warm, reflective, and comforting language. "
            "Your replies should feel human, heartfelt, and supportive. Avoid robotic or repetitive phrasing.\n\n"
            f"Conversation so far:\n{context}\nAI:"
        )

        outputs = chat_pipeline(
            emotional_prompt,
            max_length=max_length,
            do_sample=True,
            temperature=0.85,
            top_p=0.9,
            repetition_penalty=1.7,
            num_return_sequences=1
        )

        response = outputs[0]["generated_text"].split("AI:")[-1].strip()

        # 🧹 Nettoyage et amélioration du ton
        if len(response) < 25 or any(x in response.lower() for x in ["i can feel", "i'm sorry", "it's okay"]):
            possible_responses = [
                "That sounds really heavy. It’s okay to feel like this sometimes 🌧️",
                "You’re doing your best, even when it feels like too much 💜",
                "I hear you. Take a deep breath — this feeling will pass 💫",
                "You don’t have to face it all at once. One moment at a time 🤍",
                "It’s okay to feel sad. It just means your heart still cares 🌿"
            ]
            response = random.choice(possible_responses)

        conversation_history.append(f"AI: {response}")
        return response

    except Exception as e:
        logger.error(f"Error during generation: {e}")
        fallback_responses = [
            "I'm here to listen. How do you feel right now? 💫",
            "That sounds important. Would you like to tell me more? 🌿",
            "You’re doing your best, and that’s enough for today 💜"
        ]
        return random.choice(fallback_responses)
