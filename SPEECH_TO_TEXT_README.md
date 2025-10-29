# 🎤 Speech-to-Text Feature for Django Journal App

This feature automatically converts audio recordings in your journal entries to text transcriptions using advanced speech recognition technology.

## ✨ Features

- **Automatic Transcription**: Audio files are automatically processed when uploaded
- **Multiple Engines**: Supports OpenAI Whisper, Google Speech Recognition, and CMU Sphinx
- **Confidence Scoring**: Shows transcription accuracy confidence levels
- **Manual Triggers**: Users can manually request transcription for existing audio files
- **Background Processing**: Supports both synchronous and asynchronous processing
- **Status Tracking**: Real-time status updates (pending, processing, completed, failed)
- **Non-Intrusive**: Doesn't modify existing core functionality

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
python setup_speech_to_text.py
```

### Option 2: Manual Installation
```bash
# Install speech recognition libraries
pip install -r requirements-speech.txt

# Check setup
python manage.py process_audio_transcriptions --check-setup
```

## 📦 Dependencies

### Core Dependencies
- **OpenAI Whisper** (Recommended): Most accurate, works offline
- **SpeechRecognition**: Google Speech API, requires internet
- **pydub**: Audio format conversion support

### Installation Commands
```bash
# Option 1: OpenAI Whisper (Best accuracy)
pip install openai-whisper pydub

# Option 2: Google Speech Recognition (Faster)
pip install SpeechRecognition pydub

# Option 3: Full compatibility
pip install openai-whisper SpeechRecognition pydub
```

## 🎯 How It Works

### Automatic Processing
1. User uploads audio file to journal
2. System automatically detects audio files
3. Background processing starts transcription
4. Results appear in journal details view

### Manual Processing
1. Click "Generate Transcription" button on audio files
2. System processes the audio file
3. Transcription appears below the audio player

### Management Commands
```bash
# Process all pending audio files
python manage.py process_audio_transcriptions --all

# Process specific file
python manage.py process_audio_transcriptions --id=123

# Reprocess failed transcriptions
python manage.py process_audio_transcriptions --all --reprocess

# Check system setup
python manage.py process_audio_transcriptions --check-setup
```

## 🔧 Configuration

### Settings (Optional)
Add to your `settings.py`:

```python
# Enable/disable automatic processing (default: True)
SPEECH_TO_TEXT_AUTO_PROCESS = True

# For background processing with Celery (optional)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
```

### Background Processing
If Celery is configured, transcriptions will be processed in the background. Otherwise, they process synchronously.

## 📊 Database Schema

The feature adds these fields to `MediaFile` model:
- `transcription`: TextField for the transcribed text
- `transcription_status`: CharField (pending, processing, completed, failed)
- `transcription_confidence`: FloatField for accuracy score

## 🎨 UI Integration

### Journal Details View
- Audio files show transcription status badges
- Completed transcriptions display below audio player
- Manual transcription buttons for pending/failed files
- Confidence scores shown for completed transcriptions

### Status Indicators
- ✓ **Completed**: Green badge with transcription text
- ⏳ **Processing**: Yellow badge with spinner
- ✗ **Failed**: Red badge with retry button
- 🎤 **Pending**: Blue button to start transcription

## 🔍 API Endpoints

### Transcribe Audio
```http
POST /media/transcribe/{media_id}/
```
Manually trigger transcription for an audio file.

### Check Status
```http
GET /media/transcription-status/{media_id}/
```
Get current transcription status and results.

## 🛠️ Troubleshooting

### Common Issues

1. **No engines available**
   ```bash
   python manage.py process_audio_transcriptions --check-setup
   ```

2. **Audio format not supported**
   - Install pydub: `pip install pydub`
   - Install FFmpeg system dependency

3. **Transcription fails**
   - Check audio file quality
   - Try different speech recognition engine
   - Check system resources (Whisper requires more memory)

### System Dependencies

**FFmpeg** (for audio conversion):
- Windows: Download from https://ffmpeg.org/
- macOS: `brew install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`

## 📈 Performance

### Engine Comparison

| Engine | Accuracy | Speed | Offline | Languages |
|--------|----------|-------|---------|-----------|
| OpenAI Whisper | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | 99+ |
| Google Speech | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | 120+ |
| CMU Sphinx | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | Limited |

### Recommendations
- **Best Accuracy**: Use OpenAI Whisper
- **Fastest Processing**: Use Google Speech Recognition
- **Offline Usage**: Use OpenAI Whisper or CMU Sphinx
- **Production**: Use Celery for background processing

## 🔒 Privacy & Security

- **Local Processing**: Whisper processes audio locally (no data sent to external servers)
- **Google API**: Google Speech Recognition sends audio to Google's servers
- **User Permissions**: Only file owners can trigger transcriptions
- **Data Storage**: Transcriptions stored in your database

## 🚀 Advanced Usage

### Custom Processing
```python
from media_manager.speech_to_text import process_audio_transcription

# Process specific file
success = process_audio_transcription(media_file_id)
```

### Batch Processing
```python
from media_manager.models import MediaFile

# Get all pending audio files
audio_files = MediaFile.objects.filter(
    file_type='audio',
    transcription_status='pending'
)

# Process each file
for media_file in audio_files:
    process_audio_transcription(media_file.id)
```

## 📝 Contributing

The speech-to-text feature is designed to be:
- **Non-intrusive**: Doesn't modify existing core functionality
- **Extensible**: Easy to add new speech recognition engines
- **Configurable**: Multiple options for different use cases
- **Maintainable**: Clean separation of concerns

## 🆘 Support

If you encounter issues:
1. Run the setup check: `python manage.py process_audio_transcriptions --check-setup`
2. Check the Django logs for error messages
3. Verify audio file formats are supported
4. Ensure required dependencies are installed

## 🎉 Success!

Once set up, your journal app will automatically transcribe voice recordings, making your audio content searchable and accessible!