"""
Django signals for automatic speech-to-text processing
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import MediaFile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MediaFile)
def process_audio_transcription_signal(sender, instance, created, **kwargs):
    """
    Automatically process speech-to-text when audio file is uploaded
    """
    # Only process newly created audio files
    if not created or instance.file_type != 'audio':
        return
    
    # Check if auto-processing is enabled (default: True)
    auto_process = getattr(settings, 'SPEECH_TO_TEXT_AUTO_PROCESS', True)
    
    if not auto_process:
        logger.info(f"Auto-processing disabled for audio file {instance.id}")
        return
    
    # Process in background if possible, otherwise synchronously
    if hasattr(settings, 'CELERY_BROKER_URL'):
        # Use Celery if available
        try:
            from .tasks import process_audio_transcription_task
            process_audio_transcription_task.delay(instance.id)
            logger.info(f"Queued transcription task for audio file {instance.id}")
        except ImportError:
            # Fallback to synchronous processing
            process_synchronously(instance.id)
    else:
        # Process synchronously
        process_synchronously(instance.id)


def process_synchronously(media_file_id):
    """Process transcription synchronously"""
    from .speech_to_text import process_audio_transcription
    
    logger.info(f"Processing transcription synchronously for audio file {media_file_id}")
    
    try:
        success = process_audio_transcription(media_file_id)
        if success:
            logger.info(f"Transcription completed for audio file {media_file_id}")
        else:
            logger.warning(f"Transcription failed for audio file {media_file_id}")
    except Exception as e:
        logger.error(f"Error processing transcription for audio file {media_file_id}: {str(e)}")