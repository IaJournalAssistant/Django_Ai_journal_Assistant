#!/usr/bin/env python3
"""
Setup script for Speech-to-Text functionality in Django Journal App
Run with: python setup_speech_to_text.py
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def install_package(package):
    """Install a Python package using pip"""
    print(f"Installing {package}...")
    success, output = run_command(f"pip install {package}")
    if success:
        print(f"✓ {package} installed successfully")
        return True
    else:
        print(f"✗ Failed to install {package}: {output}")
        return False

def check_package(package):
    """Check if a package is already installed"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    print("🎤 Django Journal Speech-to-Text Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Installation options
    print("\nChoose installation option:")
    print("1. OpenAI Whisper (Recommended - Most accurate, works offline)")
    print("2. Google Speech Recognition (Requires internet)")
    print("3. Both (Full compatibility)")
    print("4. Minimal setup (SpeechRecognition only)")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    packages_to_install = []
    
    if choice == "1":
        packages_to_install = ["openai-whisper", "pydub"]
    elif choice == "2":
        packages_to_install = ["SpeechRecognition", "pydub"]
    elif choice == "3":
        packages_to_install = ["openai-whisper", "SpeechRecognition", "pydub"]
    elif choice == "4":
        packages_to_install = ["SpeechRecognition"]
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)
    
    # Install packages
    print(f"\nInstalling packages: {', '.join(packages_to_install)}")
    print("-" * 30)
    
    failed_packages = []
    for package in packages_to_install:
        if not install_package(package):
            failed_packages.append(package)
    
    # Check installation
    print("\n" + "=" * 50)
    print("Installation Summary:")
    
    # Check each package
    package_status = {
        'whisper': check_package('whisper'),
        'speech_recognition': check_package('speech_recognition'),
        'pydub': check_package('pydub')
    }
    
    for package, installed in package_status.items():
        status = "✓ Installed" if installed else "✗ Not installed"
        print(f"{package}: {status}")
    
    # Test the setup
    print("\n" + "=" * 50)
    print("Testing Speech-to-Text Setup...")
    
    try:
        # Import Django and run the check command
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a_core.settings')
        import django
        django.setup()
        
        from media_manager.speech_to_text import SpeechToTextService
        
        service = SpeechToTextService()
        available_engines = service.available_engines
        
        if available_engines:
            print(f"✓ Available engines: {', '.join(available_engines)}")
            print("\n🎉 Speech-to-Text setup completed successfully!")
            
            print("\nNext steps:")
            print("1. Upload an audio file to a journal entry")
            print("2. Click 'Generate Transcription' button")
            print("3. Or run: python manage.py process_audio_transcriptions --all")
            
        else:
            print("✗ No speech recognition engines available")
            print("Please check the installation and try again.")
            
    except Exception as e:
        print(f"✗ Setup test failed: {str(e)}")
        print("Please check your Django configuration.")
    
    # System dependencies note
    if 'pydub' in packages_to_install:
        print("\n" + "=" * 50)
        print("📋 System Dependencies (Optional):")
        print("For better audio format support, install FFmpeg:")
        print("- Windows: Download from https://ffmpeg.org/download.html")
        print("- macOS: brew install ffmpeg")
        print("- Linux: sudo apt-get install ffmpeg")

if __name__ == "__main__":
    main()