"""
Celery tasks for background speech-to-text processing
Only used if Celery is configured in the project
"""

try:
    from celery import shared_task
    from .speech_to_text import process_audio_transcription
    import logging

    logger = logging.getLogger(__name__)

    @shared_task(bind=True, max_retries=3)
    def process_audio_transcription_task(self, media_file_id):
        """
        Background task to process audio transcription
        
        Args:
            media_file_id: ID of MediaFile to process
        """
        try:
            success = process_audio_transcription(media_file_id)
            
            if success:
                logger.info(f"Background transcription completed for media file {media_file_id}")
                return f"Transcription completed for media file {media_file_id}"
            else:
                logger.warning(f"Background transcription failed for media file {media_file_id}")
                raise Exception(f"Transcription failed for media file {media_file_id}")
                
        except Exception as exc:
            logger.error(f"Background transcription error for media file {media_file_id}: {str(exc)}")
            
            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

except ImportError:
    # Celery not available, define dummy functions
    def process_audio_transcription_task(media_file_id):
        """Dummy function when Celery is not available"""
        pass