"""
Django management command to process audio transcriptions
Usage: python manage.py process_audio_transcriptions [--all] [--id=123]
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from media_manager.models import MediaFile
from media_manager.speech_to_text import process_audio_transcription, get_installation_instructions


class Command(BaseCommand):
    help = 'Process speech-to-text transcription for audio files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all pending audio files',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='Process specific media file by ID',
        )
        parser.add_argument(
            '--reprocess',
            action='store_true',
            help='Reprocess files that previously failed',
        )
        parser.add_argument(
            '--check-setup',
            action='store_true',
            help='Check speech recognition setup and show installation instructions',
        )

    def handle(self, *args, **options):
        if options['check_setup']:
            self.check_setup()
            return

        if options['id']:
            self.process_single_file(options['id'])
        elif options['all']:
            self.process_all_files(options['reprocess'])
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --all or --id=<file_id> or --check-setup')
            )

    def check_setup(self):
        """Check speech recognition setup"""
        self.stdout.write(self.style.SUCCESS('Checking speech recognition setup...'))
        
        from media_manager.speech_to_text import SpeechToTextService
        
        service = SpeechToTextService()
        
        if service.available_engines:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Available engines: {", ".join(service.available_engines)}')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ No speech recognition engines available')
            )
        
        self.stdout.write('\n' + self.style.WARNING('Installation Instructions:'))
        instructions = get_installation_instructions()
        
        for engine, info in instructions.items():
            self.stdout.write(f'\n{engine.upper()}:')
            self.stdout.write(f'  Command: {info["command"]}')
            self.stdout.write(f'  Description: {info["description"]}')
            self.stdout.write(f'  Pros: {", ".join(info["pros"])}')
            self.stdout.write(f'  Cons: {", ".join(info["cons"])}')

    def process_single_file(self, file_id):
        """Process a single media file"""
        try:
            media_file = MediaFile.objects.get(id=file_id)
            
            if media_file.file_type != 'audio':
                self.stdout.write(
                    self.style.ERROR(f'File {file_id} is not an audio file')
                )
                return
            
            self.stdout.write(f'Processing file {file_id}: {media_file.file.name}')
            
            success = process_audio_transcription(file_id)
            
            if success:
                media_file.refresh_from_db()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Transcription completed')
                )
                if media_file.transcription:
                    self.stdout.write(f'Transcription: {media_file.transcription[:100]}...')
                    self.stdout.write(f'Confidence: {media_file.transcription_confidence:.2f}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Transcription failed')
                )
                
        except MediaFile.DoesNotExist:
            raise CommandError(f'MediaFile with id {file_id} does not exist')

    def process_all_files(self, reprocess=False):
        """Process all pending audio files"""
        
        # Build query
        query = Q(file_type='audio')
        
        if reprocess:
            query &= Q(transcription_status__in=['pending', 'failed'])
        else:
            query &= Q(transcription_status='pending')
        
        audio_files = MediaFile.objects.filter(query)
        
        if not audio_files.exists():
            self.stdout.write(
                self.style.WARNING('No audio files to process')
            )
            return
        
        self.stdout.write(f'Found {audio_files.count()} audio files to process')
        
        success_count = 0
        failed_count = 0
        
        for media_file in audio_files:
            self.stdout.write(f'Processing: {media_file.file.name}')
            
            success = process_audio_transcription(media_file.id)
            
            if success:
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Success')
                )
            else:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: {success_count} successful, {failed_count} failed'
            )
        )