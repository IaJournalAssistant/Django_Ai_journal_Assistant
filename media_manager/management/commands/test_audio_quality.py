"""
Django management command to test audio quality and transcription
Usage: python manage.py test_audio_quality --id=123
"""

from django.core.management.base import BaseCommand, CommandError
from media_manager.models import MediaFile
from media_manager.speech_to_text import SpeechToTextService
import os


class Command(BaseCommand):
    help = 'Test audio quality and transcription accuracy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=int,
            required=True,
            help='Media file ID to test',
        )

    def handle(self, *args, **options):
        try:
            media_file = MediaFile.objects.get(id=options['id'])
            
            if media_file.file_type != 'audio':
                self.stdout.write(
                    self.style.ERROR(f'File {options["id"]} is not an audio file')
                )
                return
            
            file_path = media_file.file.path
            
            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.ERROR(f'Audio file not found: {file_path}')
                )
                return
            
            self.stdout.write(f'Testing audio file: {media_file.file.name}')
            self.stdout.write(f'File path: {file_path}')
            
            # Analyze audio properties
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(file_path)
                
                self.stdout.write('\n' + self.style.SUCCESS('Audio Properties:'))
                self.stdout.write(f'  Duration: {len(audio) / 1000:.2f} seconds')
                self.stdout.write(f'  Sample Rate: {audio.frame_rate} Hz')
                self.stdout.write(f'  Channels: {audio.channels}')
                self.stdout.write(f'  Sample Width: {audio.sample_width} bytes')
                self.stdout.write(f'  Average dBFS: {audio.dBFS:.2f}')
                
                # Quality assessment
                if audio.dBFS < -40:
                    self.stdout.write(self.style.WARNING('  ⚠️  Audio is very quiet'))
                elif audio.dBFS > -6:
                    self.stdout.write(self.style.WARNING('  ⚠️  Audio is very loud'))
                else:
                    self.stdout.write(self.style.SUCCESS('  ✓ Audio volume is good'))
                
                if audio.frame_rate < 16000:
                    self.stdout.write(self.style.WARNING('  ⚠️  Low sample rate (may affect quality)'))
                else:
                    self.stdout.write(self.style.SUCCESS('  ✓ Sample rate is adequate'))
                
            except ImportError:
                self.stdout.write(self.style.WARNING('pydub not available, skipping audio analysis'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Audio analysis failed: {e}'))
            
            # Test transcription
            self.stdout.write('\n' + self.style.SUCCESS('Testing Transcription:'))
            
            service = SpeechToTextService()
            
            if not service.available_engines:
                self.stdout.write(self.style.ERROR('No speech recognition engines available'))
                return
            
            self.stdout.write(f'Available engines: {", ".join(service.available_engines)}')
            
            # Preprocess audio
            self.stdout.write('Preprocessing audio...')
            processed_path = service.preprocess_audio(file_path)
            
            # Test transcription
            self.stdout.write('Running transcription...')
            transcription, confidence, status = service.transcribe_audio(processed_path)
            
            # Clean up
            if processed_path != file_path and os.path.exists(processed_path):
                os.remove(processed_path)
            
            # Results
            self.stdout.write('\n' + self.style.SUCCESS('Transcription Results:'))
            self.stdout.write(f'Status: {status}')
            self.stdout.write(f'Confidence: {confidence:.2f}')
            self.stdout.write(f'Text: "{transcription}"')
            
            if status == 'completed':
                if confidence > 0.8:
                    self.stdout.write(self.style.SUCCESS('✓ High confidence transcription'))
                elif confidence > 0.6:
                    self.stdout.write(self.style.WARNING('⚠️  Medium confidence transcription'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Low confidence transcription'))
                
                # Text quality checks
                if len(transcription.strip()) < 5:
                    self.stdout.write(self.style.WARNING('⚠️  Transcription is very short'))
                
                words = transcription.split()
                if len(words) > 0:
                    avg_word_length = sum(len(word) for word in words) / len(words)
                    if avg_word_length < 3:
                        self.stdout.write(self.style.WARNING('⚠️  Average word length is short (possible gibberish)'))
                    else:
                        self.stdout.write(self.style.SUCCESS('✓ Word length looks normal'))
            
            # Recommendations
            self.stdout.write('\n' + self.style.SUCCESS('Recommendations:'))
            
            if status != 'completed':
                self.stdout.write('• Check if the audio file is corrupted')
                self.stdout.write('• Ensure the audio contains clear speech')
            elif confidence < 0.7:
                self.stdout.write('• Try recording in a quieter environment')
                self.stdout.write('• Speak more clearly and slowly')
                self.stdout.write('• Check microphone quality')
                self.stdout.write('• Ensure good audio levels (not too quiet or loud)')
            else:
                self.stdout.write('• Audio quality and transcription look good!')
                
        except MediaFile.DoesNotExist:
            raise CommandError(f'MediaFile with id {options["id"]} does not exist')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Test failed: {str(e)}'))
            raise