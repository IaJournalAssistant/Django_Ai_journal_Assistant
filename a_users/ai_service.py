"""
AI Service for generating user bios using Ollama
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class OllamaBioGenerator:
    """Generate user bios using Ollama AI"""
    
    def __init__(self, base_url="http://localhost:11434"):
        """
        Initialize Ollama service
        
        Args:
            base_url: Ollama API endpoint (default: http://localhost:11434)
        """
        self.base_url = base_url
        self.model = getattr(settings, 'OLLAMA_MODEL', 'llama2')
        
    def generate_bio(self, user_data):
        """
        Generate a professional bio from user data
        
        Args:
            user_data: Dictionary containing user information
                - first_name: User's first name
                - last_name: User's last name
                - username: Username
                - interests: User's interests
                - profession: User's profession
                - location: User's location
                
        Returns:
            str: Generated bio or None if generation fails
        """
        try:
            # Build the prompt
            prompt = self._build_prompt(user_data)
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 150,
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                bio = result.get('response', '').strip()
                logger.info(f"Successfully generated bio for user: {user_data.get('username')}")
                return bio
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to Ollama. Make sure Ollama is running.")
            return None
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating bio: {str(e)}")
            return None
    
    def _build_prompt(self, user_data):
        """Build the AI prompt from user data"""
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        username = user_data.get('username', '')
        interests = user_data.get('interests', '')
        profession = user_data.get('profession', '')
        location = user_data.get('location', '')
        
        # Build name string
        name_parts = []
        if first_name:
            name_parts.append(first_name)
        if last_name:
            name_parts.append(last_name)
        full_name = ' '.join(name_parts) if name_parts else username
        
        # Build prompt
        prompt = f"""Generate a short, engaging professional bio (2-3 sentences, maximum 100 words) for a person with the following information:

Name: {full_name}
"""
        
        if profession:
            prompt += f"Profession: {profession}\n"
        if location:
            prompt += f"Location: {location}\n"
        if interests:
            prompt += f"Interests: {interests}\n"
        
        prompt += """
Write a concise, friendly bio in third person. Make it engaging and professional. Do not use quotes around the bio. Just return the bio text itself.

Bio:"""
        
        return prompt
    
    def test_connection(self):
        """Test if Ollama is accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


def generate_user_bio(user_profile):
    """
    Convenience function to generate bio for a user profile
    
    Args:
        user_profile: Profile model instance
        
    Returns:
        str: Generated bio or fallback bio
    """
    generator = OllamaBioGenerator()
    
    # Check if Ollama is running
    if not generator.test_connection():
        logger.warning("Ollama not available, using fallback bio")
        return _generate_fallback_bio(user_profile)
    
    # Prepare user data
    user_data = {
        'first_name': user_profile.first_name or '',
        'last_name': user_profile.last_name or '',
        'username': user_profile.user.username,
        'interests': user_profile.interests or '',
        'profession': user_profile.profession or '',
        'location': user_profile.location or '',
    }
    
    # Generate bio
    bio = generator.generate_bio(user_data)
    
    # Use fallback if generation fails
    if not bio:
        logger.warning("Bio generation failed, using fallback")
        return _generate_fallback_bio(user_profile)
    
    return bio


def _generate_fallback_bio(user_profile):
    """Generate a simple fallback bio without AI"""
    parts = []
    
    # Name
    if user_profile.first_name or user_profile.last_name:
        name = f"{user_profile.first_name or ''} {user_profile.last_name or ''}".strip()
        parts.append(name)
    else:
        parts.append(user_profile.user.username)
    
    # Profession and location
    if user_profile.profession and user_profile.location:
        parts.append(f"is a {user_profile.profession} based in {user_profile.location}")
    elif user_profile.profession:
        parts.append(f"is a {user_profile.profession}")
    elif user_profile.location:
        parts.append(f"is based in {user_profile.location}")
    else:
        parts.append("is a Smart Journal user")
    
    # Interests
    if user_profile.interests:
        interests_list = [i.strip() for i in user_profile.interests.split(',')[:3]]
        if len(interests_list) > 1:
            interests_str = ', '.join(interests_list[:-1]) + f' and {interests_list[-1]}'
        else:
            interests_str = interests_list[0]
        parts.append(f"with interests in {interests_str}")
    
    bio = ' '.join(parts) + '.'
    return bio

