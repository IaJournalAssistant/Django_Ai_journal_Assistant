"""
Django management command to test English transcription specifically
Usage: python manage.py test_english_transcription --id=123
"""

from django.core.management.base import BaseCommand, CommandError
from media_manager.models import MediaFile
from media_manager.speech_to_text import process_audio_transcription
import os


class Command(BaseCommand):
    help = 'Test English transcription for audio files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=int,
            help='Media file ID to test (optional - will process all pending if not specified)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if already completed',
        )

    def handle(self, *args, **options):
        if options['id']:
            self.test_single_file(options['id'], options['force'])
        else:
            self.test_all_files(options['force'])

    def test_single_file(self, file_id, force=False):
        """Test a single audio file"""
        try:
            media_file = MediaFile.objects.get(id=file_id)
            
            if media_file.file_type != 'audio':
                self.stdout.write(
                    self.style.ERROR(f'File {file_id} is not an audio file')
                )
                return
            
            if not force and media_file.transcription_status == 'completed':
                self.stdout.write(
                    self.style.WARNING(f'File {file_id} already transcribed. Use --force to reprocess.')
                )
                self.stdout.write(f'Current transcription: "{media_file.transcription}"')
                return
            
            self.stdout.write(f'Testing English transcription for file {file_id}: {media_file.file.name}')
            
            # Reset status
            media_file.transcription_status = 'pending'
            media_file.transcription = ''
            media_file.transcription_confidence = None
            media_file.save()
            
            # Process transcription
            success = process_audio_transcription(file_id)
            
            # Show results
            media_file.refresh_from_db()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Transcription completed')
                )
                self.stdout.write(f'Result: "{media_file.transcription}"')
                self.stdout.write(f'Confidence: {media_file.transcription_confidence:.2f}')
                
                # Analyze result
                if self._looks_like_english(media_file.transcription):
                    self.stdout.write(self.style.SUCCESS('✓ Result looks like English'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Result may not be English'))
                    
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Transcription failed')
                )
                
        except MediaFile.DoesNotExist:
            raise CommandError(f'MediaFile with id {file_id} does not exist')

    def test_all_files(self, force=False):
        """Test all audio files"""
        if force:
            audio_files = MediaFile.objects.filter(file_type='audio')
        else:
            audio_files = MediaFile.objects.filter(
                file_type='audio',
                transcription_status__in=['pending', 'failed']
            )
        
        if not audio_files.exists():
            self.stdout.write(
                self.style.WARNING('No audio files to process')
            )
            return
        
        self.stdout.write(f'Testing {audio_files.count()} audio files...')
        
        for media_file in audio_files:
            self.stdout.write(f'\nProcessing: {media_file.file.name}')
            
            if force:
                media_file.transcription_status = 'pending'
                media_file.transcription = ''
                media_file.transcription_confidence = None
                media_file.save()
            
            success = process_audio_transcription(media_file.id)
            
            media_file.refresh_from_db()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Success: "{media_file.transcription[:50]}..."')
                )
                
                if self._looks_like_english(media_file.transcription):
                    self.stdout.write(self.style.SUCCESS('  ✓ Looks like English'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠️  May not be English'))
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed')
                )

    def _looks_like_english(self, text):
        """Simple check if text looks like English"""
        if not text:
            return False
        
        import re
        
        # Count Latin characters
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(re.sub(r'[\s\.,!?;:\-\'"()]', '', text))
        
        if total_chars == 0:
            return False
        
        latin_ratio = latin_chars / total_chars
        
        # Check for common English words
        common_words = ['the', 'and', 'or', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from', 'not', 'word', 'but', 'what', 'some', 'we', 'can', 'out', 'other', 'were', 'all', 'there', 'when', 'up', 'use', 'your', 'how', 'said', 'an', 'each', 'which', 'she', 'do', 'one', 'their', 'time', 'will', 'about', 'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more', 'very', 'what', 'know', 'just', 'first', 'get', 'over', 'think', 'also', 'its', 'our', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'much', 'go', 'me', 'back', 'with', 'well', 'were', 'been', 'have', 'there', 'who', 'oil', 'sit', 'but', 'now']
        
        words = re.findall(r'\b\w+\b', text.lower())
        if words:
            english_word_count = sum(1 for word in words if word in common_words)
            english_word_ratio = english_word_count / len(words)
        else:
            english_word_ratio = 0
        
        # Consider it English if high Latin ratio or has English words
        return latin_ratio > 0.7 or (latin_ratio > 0.5 and english_word_ratio > 0.1)