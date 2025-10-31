# Docker Setup Guide

This guide will help you run the Django Smart Journal application with Ollama AI integration using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- At least 4GB of free disk space (for Ollama models)

## Quick Start

### Windows
```bash
docker-setup.bat
```

### Linux/Mac
```bash
chmod +x docker-setup.sh
./docker-setup.sh
```

## What Happens Automatically

The Docker setup includes automatic:
1. **PostgreSQL 17** database creation
2. **Smart Django migrations** - only creates new migrations if needed, always applies existing ones
3. **Cache table** creation (if it doesn't exist)
4. **Static files** collection
5. **Ollama model** download (gemma2:2b)
6. **Whisper model** download (small) for audio processing
7. **FFmpeg** installation (includes ffprobe) for audio file handling

### Smart Migration Logic
- Checks if new migrations are needed with `--dry-run --check`
- Only runs `makemigrations` if there are model changes
- Always applies existing migrations with `migrate`
- Safe to run multiple times without creating duplicate migrations

### Manual Setup

1. **Build and start services:**
   ```bash
   docker-compose up --build -d
   ```

2. **Wait for Ollama to download the model (this may take a few minutes):**
   ```bash
   docker-compose logs -f ollama-setup
   ```

3. **Migrations run automatically** - The setup includes automatic database initialization

4. **Create a superuser (optional):**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## Access Your Application

- **Django App:** http://localhost:8000
- **pgAdmin:** http://localhost:5050 (admin@admin.com / admin123)
- **PostgreSQL:** localhost:5432
- **Ollama API:** http://localhost:11434

## Useful Commands

### Check if Ollama model is ready:
```bash
curl http://localhost:11434/api/tags
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f ollama
```

### Stop services:
```bash
docker-compose down
```

### Restart services:
```bash
docker-compose restart
```

### Access Django shell:
```bash
docker-compose exec web python manage.py shell
```

### Manual database operations:
```bash
# Run migrations manually
docker-compose exec web python manage.py migrate

# Create new migrations
docker-compose exec web python manage.py makemigrations

# Use the initialization script
./init-db.sh  # Linux/Mac
init-db.bat   # Windows
```

### Connect to PostgreSQL via pgAdmin:
1. Open http://localhost:5050
2. Login with: admin@admin.com / admin123
3. Add new server with these settings:
   - **Name:** Django Database
   - **Host:** postgres
   - **Port:** 5432
   - **Database:** DjangoProjectIaJournal
   - **Username:** postgres
   - **Password:** postgres123

## Environment Variables

The application uses different environment files:
- `.env` - Local development
- `.env.docker` - Docker environment

Key variables:
- `DB_NAME` - PostgreSQL database name
- `DB_USER` - PostgreSQL username
- `DB_PASSWORD` - PostgreSQL password
- `DB_HOST` - PostgreSQL host (postgres for Docker)
- `DB_PORT` - PostgreSQL port (5432)
- `OLLAMA_BASE_URL` - Ollama service URL
- `OLLAMA_MODEL` - AI model to use (default: gemma2:2b)
- `DEBUG` - Django debug mode
- `SECRET_KEY` - Django secret key

## Troubleshooting

### Ollama model not downloading:
```bash
docker-compose exec ollama ollama pull gemma2:2b
```

### Reset everything:
```bash
docker-compose down -v
docker-compose up --build -d
```

### Check service health:
```bash
docker-compose ps
```

### Audio processing issues:
```bash
# Check if ffmpeg and ffprobe are installed
docker-compose exec web ffmpeg -version
docker-compose exec web ffprobe -version

# Re-download Whisper models
docker-compose exec web python -c "import whisper; whisper.load_model('small')"

# Check Whisper cache
docker-compose exec web ls -la /home/appuser/.cache/whisper/
```

## Data Persistence

The following volumes are created:
- `postgres_data` - PostgreSQL database data
- `pgadmin_data` - pgAdmin configuration and data
- `ollama_data` - Ollama models and data
- `whisper_cache` - Whisper AI models cache
- `./media` - User uploaded files (mounted directory)
- `./static` - Static files (mounted directory)

## Production Notes

For production deployment:
1. Change `SECRET_KEY` in `.env.docker`
2. Set `DEBUG=False`
3. Configure proper `ALLOWED_HOSTS`
4. Use a proper database (PostgreSQL)
5. Set up proper SSL/HTTPS
6. Remove `MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN`