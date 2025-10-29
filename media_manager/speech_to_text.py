"""
Speech-to-Text Service for Media Manager
Supports multiple speech recognition libraries with fallback options
"""

import os
import logging
from typing import Tuple, Optional
from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """
    Speech-to-text service with multiple backend support
    Priority: OpenAI Whisper > Google Speech Recognition > SpeechRecognition library
    """
    
    def __init__(self):
        self.available_engines = self._check_available_engines()
        logger.info(f"Available speech-to-text engines: {self.available_engines}")
    
    def _check_available_engines(self) -> list:
        """Check which speech recognition engines are available"""
        engines = []
        
        # Check for OpenAI Whisper (most accurate)
        try:
            import whisper
            engines.append('whisper')
        except ImportError:
            pass
        
        # Check for Google Speech Recognition
        try:
            import speech_recognition as sr
            engines.append('google')
        except ImportError:
            pass
        
        # Check for SpeechRecognition with offline support
        try:
            import speech_recognition as sr
            engines.append('sphinx')  # CMU Sphinx (offline)
        except ImportError:
            pass
        
        return engines
    
    def transcribe_audio(self, file_path: str) -> Tuple[Optional[str], float, str]:
        """
        Transcribe audio file to text
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (transcription_text, confidence_score, status)
        """
        if not self.available_engines:
            return None, 0.0, 'failed'
        
        # Try engines in order of preference
        for engine in ['whisper', 'google', 'sphinx']:
            if engine in self.available_engines:
                try:
                    return self._transcribe_with_engine(file_path, engine)
                except Exception as e:
                    logger.warning(f"Engine {engine} failed: {str(e)}")
                    continue
        
        return None, 0.0, 'failed'
    
    def _transcribe_with_engine(self, file_path: str, engine: str) -> Tuple[str, float, str]:
        """Transcribe using specific engine"""
        
        if engine == 'whisper':
            return self._transcribe_with_whisper(file_path)
        elif engine == 'google':
            return self._transcribe_with_google(file_path)
        elif engine == 'sphinx':
            return self._transcribe_with_sphinx(file_path)
        else:
            raise ValueError(f"Unknown engine: {engine}")
    
    def _transcribe_with_whisper(self, file_path: str) -> Tuple[str, float, str]:
        """Transcribe using OpenAI Whisper (most accurate)"""
        import whisper
        
        # Load model (base model for balance of speed/accuracy)
        model = whisper.load_model("base")
        
        # Transcribe
        result = model.transcribe(file_path)
        
        # Extract confidence from segments if available
        confidence = 0.9  # Whisper doesn't provide confidence, assume high
        if 'segments' in result and result['segments']:
            # Average confidence from segments if available
            confidences = [seg.get('confidence', 0.9) for seg in result['segments']]
            confidence = sum(confidences) / len(confidences) if confidences else 0.9
        
        return result['text'].strip(), confidence, 'completed'
    
    def _transcribe_with_google(self, file_path: str) -> Tuple[str, float, str]:
        """Transcribe using Google Speech Recognition"""
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        
        # Convert audio file to AudioFile
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
        
        # Recognize speech
        try:
            text = recognizer.recognize_google(audio, show_all=False)
            return text, 0.8, 'completed'  # Google doesn't provide confidence in free tier
        except sr.UnknownValueError:
            return "", 0.0, 'failed'
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {e}")
            raise
    
    def _transcribe_with_sphinx(self, file_path: str) -> Tuple[str, float, str]:
        """Transcribe using CMU Sphinx (offline)"""
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
        
        try:
            text = recognizer.recognize_sphinx(audio)
            return text, 0.6, 'completed'  # Sphinx generally less accurate
        except sr.UnknownValueError:
            return "", 0.0, 'failed'
        except sr.RequestError as e:
            logger.error(f"Sphinx error: {e}")
            raise
    
    def convert_audio_format(self, input_path: str, output_path: str) -> bool:
        """Convert audio to WAV format for better compatibility"""
        try:
            from pydub import AudioSegment
            
            # Load audio file
            audio = AudioSegment.from_file(input_path)
            
            # Convert to WAV with standard settings
            audio = audio.set_frame_rate(16000).set_channels(1)  # 16kHz mono
            audio.export(output_path, format="wav")
            
            return True
        except ImportError:
            logger.warning("pydub not available, skipping audio conversion")
            return False
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return False


def process_audio_transcription(media_file_id: int) -> bool:
    """
    Process speech-to-text for a media file
    This function can be called asynchronously or in background tasks
    
    Args:
        media_file_id: ID of MediaFile to process
        
    Returns:
        bool: Success status
    """
    from .models import MediaFile
    
    try:
        media_file = MediaFile.objects.get(id=media_file_id)
        
        # Only process audio files
        if media_file.file_type != 'audio':
            logger.info(f"Skipping non-audio file: {media_file.id}")
            return False
        
        # Update status to processing
        media_file.transcription_status = 'processing'
        media_file.save(update_fields=['transcription_status'])
        
        # Get file path
        file_path = media_file.file.path
        
        # Initialize service
        service = SpeechToTextService()
        
        # Convert audio format if needed
        converted_path = None
        if not file_path.lower().endswith('.wav'):
            converted_path = file_path.rsplit('.', 1)[0] + '_converted.wav'
            if service.convert_audio_format(file_path, converted_path):
                file_path = converted_path
        
        # Transcribe audio
        transcription, confidence, status = service.transcribe_audio(file_path)
        
        # Clean up converted file
        if converted_path and os.path.exists(converted_path):
            os.remove(converted_path)
        
        # Update media file
        media_file.transcription = transcription or ""
        media_file.transcription_confidence = confidence
        media_file.transcription_status = status
        media_file.save(update_fields=['transcription', 'transcription_confidence', 'transcription_status'])
        
        logger.info(f"Transcription completed for media file {media_file_id}: {status}")
        return status == 'completed'
        
    except MediaFile.DoesNotExist:
        logger.error(f"MediaFile {media_file_id} not found")
        return False
    except Exception as e:
        logger.error(f"Transcription failed for media file {media_file_id}: {str(e)}")
        
        # Update status to failed
        try:
            media_file = MediaFile.objects.get(id=media_file_id)
            media_file.transcription_status = 'failed'
            media_file.save(update_fields=['transcription_status'])
        except:
            pass
        
        return False


def get_installation_instructions() -> dict:
    """Get installation instructions for speech recognition libraries"""
    return {
        'whisper': {
            'command': 'pip install openai-whisper',
            'description': 'OpenAI Whisper - Most accurate, works offline',
            'pros': ['Highest accuracy', 'Works offline', 'Multiple languages'],
            'cons': ['Larger download', 'Slower processing']
        },
        'speech_recognition': {
            'command': 'pip install SpeechRecognition',
            'description': 'Google Speech Recognition - Good accuracy, requires internet',
            'pros': ['Good accuracy', 'Fast processing', 'Free tier available'],
            'cons': ['Requires internet', 'API limits']
        },
        'pydub': {
            'command': 'pip install pydub',
            'description': 'Audio format conversion support',
            'pros': ['Better audio compatibility', 'Format conversion'],
            'cons': ['Additional dependency']
        }
    }