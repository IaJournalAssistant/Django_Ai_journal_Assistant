@echo off
echo Setting up Docker environment for Django app with Ollama...

REM Create necessary directories
if not exist "data" mkdir data
if not exist "media" mkdir media
if not exist "staticfiles" mkdir staticfiles

echo Building and starting services...
docker-compose up --build -d

echo Waiting for services to be ready...
echo Downloading AI models (Ollama + Whisper)...
echo Migrations will run automatically...
timeout /t 60 /nobreak

echo Creating superuser (optional - you can skip this)...
echo Run: docker-compose exec web python manage.py createsuperuser

echo.
echo Setup complete! Your application should be running at:
echo - Django app: http://localhost:8000
echo - pgAdmin: http://localhost:5050 (admin@admin.com / admin123)
echo - PostgreSQL: localhost:5432
echo - Ollama API: http://localhost:11434
echo.
echo To check if Ollama model is ready:
echo curl http://localhost:11434/api/tags
echo.
echo To view logs:
echo docker-compose logs -f
echo.
echo To stop services:
echo docker-compose down

pause