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
        """Transcribe using OpenAI Whisper with improved English detection"""
        import whisper
        
        # Load a more accurate model (small is better than base for accuracy)
        model = whisper.load_model("small")
        
        logger.info("Starting multi-strategy transcription...")
        
        # Strategy 1: Try English first (most common case)
        logger.info("Strategy 1: Trying English transcription...")
        english_result = model.transcribe(
            file_path,
            language='en',  # Force English
            task='transcribe',
            temperature=0.0,
            initial_prompt="Hello, this is an English voice recording for a journal entry.",
            verbose=False
        )
        
        english_text = english_result['text'].strip()
        logger.info(f"English attempt result: '{english_text}'")
        
        # Check if English result looks good
        if self._is_likely_english(english_text) and not self._is_likely_gibberish(english_text):
            logger.info("English transcription looks good, using it")
            confidence = self._calculate_confidence(english_result)
            return self._clean_transcription(english_text), confidence, 'completed'
        
        # Strategy 2: Auto-detect language if English didn't work well
        logger.info("Strategy 2: Auto-detecting language...")
        detect_result = model.transcribe(
            file_path,
            language=None,  # Auto-detect language
            task='transcribe',
            temperature=0.0,
            verbose=False
        )
        
        detected_language = detect_result.get('language', 'en')
        detected_text = detect_result['text'].strip()
        logger.info(f"Auto-detected language: {detected_language}")
        logger.info(f"Auto-detect result: '{detected_text}'")
        
        # Strategy 3: Compare results and choose the best
        if detected_language == 'en' or self._is_likely_english(detected_text):
            # If auto-detect also suggests English, use the better result
            if len(detected_text) > len(english_text) and not self._is_likely_gibberish(detected_text):
                logger.info("Using auto-detect English result")
                result = detect_result
            else:
                logger.info("Using forced English result")
                result = english_result
        else:
            # Non-English language detected
            logger.info(f"Non-English language detected: {detected_language}")
            
            # Strategy 4: Try English one more time with different parameters
            logger.info("Strategy 4: Final English attempt with relaxed parameters...")
            final_english_result = model.transcribe(
                file_path,
                language='en',
                task='transcribe',
                temperature=0.2,  # Slightly higher temperature
                initial_prompt="This is an English voice message.",
                condition_on_previous_text=False,
                verbose=False
            )
            
            final_english_text = final_english_result['text'].strip()
            logger.info(f"Final English attempt: '{final_english_text}'")
            
            # Choose the best result
            if (self._is_likely_english(final_english_text) and 
                not self._is_likely_gibberish(final_english_text) and
                len(final_english_text) >= 3):
                logger.info("Using final English attempt")
                result = final_english_result
            elif not self._is_likely_gibberish(detected_text):
                logger.info(f"Using auto-detected {detected_language} result")
                result = detect_result
            else:
                logger.info("All attempts failed, using best available")
                # Choose the longest non-gibberish result
                candidates = [
                    (english_text, english_result),
                    (detected_text, detect_result),
                    (final_english_text, final_english_result)
                ]
                
                best_text, result = max(
                    [(text, res) for text, res in candidates if not self._is_likely_gibberish(text)],
                    key=lambda x: len(x[0]),
                    default=(english_text, english_result)
                )
        
        # Extract confidence from segments if available
        confidence = 0.9  # Default confidence
        if 'segments' in result and result['segments']:
            # Calculate average confidence from segments
            confidences = []
            for seg in result['segments']:
                if 'avg_logprob' in seg:
                    # Convert log probability to confidence (approximate)
                    conf = min(1.0, max(0.0, (seg['avg_logprob'] + 1.0)))
                    confidences.append(conf)
            
            if confidences:
                confidence = sum(confidences) / len(confidences)
        
        # Clean up the transcription
        text = result['text'].strip()
        
        # Log raw transcription for debugging
        logger.info(f"Raw Whisper output: '{text}'")
        logger.info(f"Detected language: {result.get('language', 'unknown')}")
        
        # Quality checks
        if not text or len(text.strip()) < 2:
            logger.warning("Transcription is empty or too short")
            return "", 0.1, 'completed'
        
        # Check if transcription looks like gibberish
        if self._is_likely_gibberish(text):
            logger.warning(f"Transcription may be gibberish: '{text}'")
            # Try again with different parameters
            logger.info("Retrying with English language forced...")
            retry_result = model.transcribe(
                file_path,
                language='en',  # Force English
                task='transcribe',
                temperature=0.2,  # Slightly higher temperature
                initial_prompt="Hello, this is an English voice recording.",
                verbose=False
            )
            
            retry_text = retry_result['text'].strip()
            logger.info(f"Retry result: '{retry_text}'")
            
            if not self._is_likely_gibberish(retry_text) and len(retry_text) > len(text):
                text = retry_text
                logger.info("Using retry result")
        
        # Basic text cleaning
        text = self._clean_transcription(text)
        
        logger.info(f"Final transcription: '{text}' (confidence: {confidence:.2f})")
        
        return text, confidence, 'completed'
    
    def _is_likely_english(self, text: str) -> bool:
        """Check if text looks like English"""
        if not text or len(text.strip()) < 2:
            return False
        
        import re
        
        # Count Latin characters (English uses Latin alphabet)
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(re.sub(r'[\s\.,!?;:\-\'"()]', '', text))
        
        if total_chars == 0:
            return False
        
        # If more than 80% are Latin characters, likely English
        latin_ratio = latin_chars / total_chars
        
        # Check for common English words
        common_english_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'hello', 'hi', 'yes', 'no', 'please', 'thank', 'thanks', 'sorry',
            'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'cannot', 'a', 'an'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        if words:
            english_word_count = sum(1 for word in words if word in common_english_words)
            english_word_ratio = english_word_count / len(words)
        else:
            english_word_ratio = 0
        
        # Consider it English if:
        # 1. High Latin character ratio (>80%) OR
        # 2. Decent Latin ratio (>60%) AND some English words (>10%)
        is_english = (latin_ratio > 0.8) or (latin_ratio > 0.6 and english_word_ratio > 0.1)
        
        logger.info(f"English detection - Latin ratio: {latin_ratio:.2f}, English words: {english_word_ratio:.2f}, Is English: {is_english}")
        
        return is_english
    
    def _is_likely_gibberish(self, text: str) -> bool:
        """Check if transcription looks like gibberish"""
        if not text:
            return True
        
        import re
        
        # Very short text is likely gibberish
        if len(text.strip()) < 2:
            return True
        
        # Count different character types
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        cyrillic_chars = len(re.findall(r'[а-яёА-ЯЁ]', text))
        arabic_chars = len(re.findall(r'[ء-ي]', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_special_chars = len(re.findall(r'[^\w\s\.,!?;:\-\'"()]', text))
        
        total_chars = len(re.sub(r'\s', '', text))
        
        if total_chars == 0:
            return True
        
        # Check for excessive repetition (like "مرحباً، مرحباً، مرحباً...")
        words = text.split()
        if len(words) > 3:
            unique_words = set(word.strip('.,!?;:') for word in words)
            repetition_ratio = 1 - (len(unique_words) / len(words))
            if repetition_ratio > 0.7:  # More than 70% repetition
                logger.info(f"High repetition detected: {repetition_ratio:.2f}")
                return True
        
        # Check for very short words (common in gibberish)
        if len(words) > 3:
            short_words = [w for w in words if len(w) <= 2 and w.isalpha()]
            if len(short_words) / len(words) > 0.8:
                logger.info("Too many short words detected")
                return True
        
        # Check for mixed scripts (unusual in normal speech)
        script_count = sum(1 for count in [latin_chars, cyrillic_chars, arabic_chars, chinese_chars] if count > 0)
        if script_count > 1 and total_chars < 50:  # Mixed scripts in short text
            logger.info("Mixed scripts detected in short text")
            return True
        
        return False
    
    def _calculate_confidence(self, result: dict) -> float:
        """Calculate confidence score from Whisper result"""
        confidence = 0.9  # Default confidence
        
        if 'segments' in result and result['segments']:
            # Calculate average confidence from segments
            confidences = []
            for seg in result['segments']:
                if 'avg_logprob' in seg:
                    # Convert log probability to confidence (approximate)
                    conf = min(1.0, max(0.0, (seg['avg_logprob'] + 1.0)))
                    confidences.append(conf)
            
            if confidences:
                confidence = sum(confidences) / len(confidences)
        
        return confidence
    
    def _clean_transcription(self, text: str) -> str:
        """Clean and improve transcription text"""
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common transcription artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove bracketed content
        text = re.sub(r'\(.*?\)', '', text)  # Remove parenthetical content
        
        # Fix common issues
        text = text.replace('  ', ' ')  # Double spaces
        text = text.strip()
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        return text
    
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
        """Convert and enhance audio for better transcription accuracy"""
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize, compress_dynamic_range
            
            # Load audio file
            audio = AudioSegment.from_file(input_path)
            
            # Audio enhancement for better transcription
            # 1. Normalize volume
            audio = normalize(audio)
            
            # 2. Apply dynamic range compression to even out volume levels
            audio = compress_dynamic_range(audio)
            
            # 3. Convert to optimal format for Whisper
            # Whisper works best with 16kHz mono WAV files
            audio = audio.set_frame_rate(16000)  # 16kHz sample rate
            audio = audio.set_channels(1)        # Mono channel
            audio = audio.set_sample_width(2)    # 16-bit depth
            
            # 4. Remove silence from beginning and end
            audio = audio.strip_silence(silence_len=500, silence_thresh=-40)
            
            # 5. Apply high-pass filter to remove low-frequency noise
            # This helps remove background hum and rumble
            if hasattr(audio, 'high_pass_filter'):
                audio = audio.high_pass_filter(80)  # Remove frequencies below 80Hz
            
            # Export with optimal settings
            audio.export(
                output_path, 
                format="wav",
                parameters=[
                    "-acodec", "pcm_s16le",  # 16-bit PCM encoding
                    "-ar", "16000",          # 16kHz sample rate
                    "-ac", "1"               # Mono channel
                ]
            )
            
            logger.info(f"Audio enhanced and converted: {input_path} -> {output_path}")
            return True
            
        except ImportError:
            logger.warning("pydub not available, skipping audio conversion")
            return False
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return False
    
    def preprocess_audio(self, input_path: str) -> str:
        """Preprocess audio file for optimal transcription"""
        try:
            from pydub import AudioSegment
            import tempfile
            import os
            
            # Create temporary file for processed audio
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"whisper_processed_{os.path.basename(input_path)}.wav")
            
            # Load and process audio
            audio = AudioSegment.from_file(input_path)
            
            # Check if audio is too quiet or too loud
            if audio.dBFS < -30:
                logger.info("Audio is very quiet, applying gain boost")
                audio = audio + (abs(audio.dBFS) - 20)  # Boost to -20dB
            elif audio.dBFS > -6:
                logger.info("Audio is very loud, applying gain reduction")
                audio = audio - (audio.dBFS + 12)  # Reduce to -12dB
            
            # Apply noise reduction if audio is very noisy
            if audio.dBFS > -10:
                from pydub.effects import normalize
                audio = normalize(audio)
            
            # Export processed audio
            audio.export(temp_path, format="wav", parameters=["-ar", "16000", "-ac", "1"])
            
            return temp_path
            
        except Exception as e:
            logger.warning(f"Audio preprocessing failed, using original: {e}")
            return input_path


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
        
        # Preprocess audio for better accuracy
        processed_path = service.preprocess_audio(file_path)
        
        # Convert audio format if needed
        converted_path = None
        if not processed_path.lower().endswith('.wav') or processed_path != file_path:
            converted_path = file_path.rsplit('.', 1)[0] + '_whisper_ready.wav'
            if service.convert_audio_format(processed_path, converted_path):
                file_path = converted_path
            else:
                file_path = processed_path
        
        # Transcribe audio
        transcription, confidence, status = service.transcribe_audio(file_path)
        
        # Clean up temporary files
        if converted_path and os.path.exists(converted_path):
            os.remove(converted_path)
        if processed_path != media_file.file.path and os.path.exists(processed_path):
            os.remove(processed_path)
        
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