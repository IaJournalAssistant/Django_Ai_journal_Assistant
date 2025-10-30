# AI-Powered Bio Generation Setup

## Overview

Your Django app now automatically generates professional bios using Ollama AI when users sign up with extended profile information.

## Features Added

### 1. Extended Signup Fields
New fields added to the signup form:
- **First Name** - User's first name
- **Last Name** - User's last name  
- **Profession** - Job title or occupation
- **Location** - City, country, etc.
- **Interests** - Hobbies and interests (comma-separated)

### 2. AI Bio Generation
- Uses **Ollama** (local AI) to generate professional bios
- Generates automatically during signup
- Fallback to template-based bio if Ollama is unavailable
- Stored in `Profile.info` field

### 3. Files Created/Modified

**New Files:**
- `a_users/ai_service.py` - Ollama integration and bio generation
- `a_users/adapter.py` - Custom allauth adapter for extended signup
- `a_users/migrations/0002_profile_first_name_profile_interests_and_more.py` - Database migration

**Modified Files:**
- `a_users/models.py` - Added extended profile fields
- `a_users/signals.py` - Added auto-bio generation signal
- `a_core/settings.py` - Configured custom adapter and Ollama settings
- `requirements.txt` - Added `requests` dependency

## Setup Instructions

### 1. Install Dependencies

```bash
.\venv\Scripts\activate
pip install requests
```

### 2. Start Ollama

Make sure Ollama is running with your preferred model:

```bash
# Using Docker (if you have docker-compose setup)
docker-compose up ollama

# OR using Ollama directly
ollama run llama2
```

**Available models:**
- `llama2` (default, 7B parameters)
- `mistral` (faster, good quality)
- `codellama` (code-focused)
- `llama2:13b` (better quality, slower)

To change the model, update `OLLAMA_MODEL` in `settings.py`.

### 3. Verify Ollama is Running

```bash
curl http://localhost:11434/api/tags
```

Should return a list of available models.

### 4. Run the Server

```bash
python manage.py runserver
```

## How It Works

### Signup Flow

1. **User fills signup form** with extended fields
2. **Account is created** → triggers `user_postsave` signal
3. **Profile is created** → triggers `generate_bio_on_profile_update` signal
4. **AI service checks** if Ollama is available
5. **Bio is generated** using Ollama or fallback template
6. **Bio is saved** to `Profile.info` field

### AI Prompt Example

```
Generate a short, engaging professional bio (2-3 sentences, maximum 100 words) 
for a person with the following information:

Name: John Doe
Profession: Software Developer
Location: San Francisco, USA
Interests: Machine Learning, Photography, Hiking

Write a concise, friendly bio in third person...
```

### Generated Bio Example

> "John Doe is a Software Developer based in San Francisco, USA, with a passion 
> for Machine Learning. When not coding, he enjoys exploring the art of Photography 
> and discovering new Hiking trails in the Bay Area."

## Testing

### Test the Signup Flow

1. Go to: http://localhost:8000/accounts/signup/
2. Fill in the form:
   - Email: test@example.com
   - Username: testuser
   - First Name: John
   - Last Name: Doe
   - Profession: Software Developer
   - Location: New York, USA
   - Interests: Reading, Music, Coding
   - Password: (your password)
3. Click "Create Account"
4. Check the profile at: http://localhost:8000/@testuser/
5. The bio should be automatically generated in the "Info" section

### Test Without Ollama

If Ollama is not running, the system will:
1. Log a warning: "Ollama not available, using fallback bio"
2. Generate a simple template-based bio
3. Continue signup without errors

Example fallback bio:
> "John Doe is a Software Developer based in New York, USA with interests in 
> Reading, Music and Coding."

### Check Logs

```bash
# Watch for bio generation in console
python manage.py runserver

# You should see:
# INFO: Generating AI bio for user: testuser
# INFO: Bio generated successfully for: testuser
```

## Customization

### Change AI Model

In `a_core/settings.py`:

```python
# Use a different Ollama model
OLLAMA_MODEL = 'mistral'  # Faster
OLLAMA_MODEL = 'llama2:13b'  # Better quality
OLLAMA_MODEL = 'codellama'  # For technical bios
```

### Adjust Prompt

Edit `a_users/ai_service.py` → `_build_prompt()` method:

```python
def _build_prompt(self, user_data):
    # Customize the prompt here
    prompt = f"""Your custom prompt...
    
    Generate a bio that emphasizes: ...
    """
    return prompt
```

### Change Temperature/Length

In `a_users/ai_service.py` → `generate_bio()` method:

```python
"options": {
    "temperature": 0.7,  # 0.0-1.0 (lower = more focused)
    "max_tokens": 150,   # Maximum bio length
}
```

## Troubleshooting

### Ollama Connection Error

**Error:** `Could not connect to Ollama`

**Solutions:**
1. Check if Ollama is running: `curl http://localhost:11434`
2. Verify Docker container: `docker ps | grep ollama`
3. Check port: Default is `11434`
4. Restart Ollama: `docker-compose restart ollama`

### Bio Not Generated

**Check:**
1. Did user fill any extended fields? (needs at least one)
2. Is Ollama running?
3. Check logs: `python manage.py runserver` (look for errors)
4. Verify signal is connected: Check `a_users/apps.py` imports signals

### Empty Bio Field

**Causes:**
- Ollama timed out (> 30 seconds)
- Ollama returned empty response
- Network error

**Fix:**
- Increase timeout in `ai_service.py`
- Check Ollama model is downloaded: `ollama list`
- Pull model: `ollama pull llama2`

### Model Not Found

**Error:** `Model 'llama2' not found`

**Fix:**
```bash
# Pull the model
ollama pull llama2

# Verify it's available
ollama list
```

## API Reference

### OllamaBioGenerator Class

```python
from a_users.ai_service import OllamaBioGenerator

generator = OllamaBioGenerator(base_url="http://localhost:11434")

# Test connection
is_available = generator.test_connection()

# Generate bio
user_data = {
    'first_name': 'John',
    'last_name': 'Doe',
    'username': 'johndoe',
    'profession': 'Developer',
    'location': 'NYC',
    'interests': 'AI, Music'
}
bio = generator.generate_bio(user_data)
```

### Utility Function

```python
from a_users.ai_service import generate_user_bio

# Generate bio from profile instance
bio = generate_user_bio(profile_instance)
```

## Production Considerations

### 1. Performance
- Bio generation adds 2-5 seconds to signup (with Ollama)
- Consider async generation using Celery for production
- Cache frequently used prompts

### 2. Error Handling
- Always has fallback (template-based bio)
- Logs all errors for monitoring
- User signup never fails due to bio generation

### 3. Privacy
- All AI processing happens locally (Ollama)
- No data sent to external APIs
- User data never leaves your server

### 4. Scaling
- For high traffic, use task queue (Celery)
- Consider dedicated Ollama server
- Monitor Ollama resource usage

## Next Steps

- [ ] Test signup flow with various inputs
- [ ] Customize AI prompt for your use case
- [ ] Try different Ollama models
- [ ] Add manual "Regenerate Bio" button in profile settings
- [ ] Consider async processing for production

---

**Need Help?** Check the logs in your terminal when running the dev server for detailed error messages.

