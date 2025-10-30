@echo off
echo Initializing Django database...

REM Check if there are any changes that need migrations
echo Checking for migration changes...
docker-compose exec web python manage.py makemigrations --dry-run --check
if %errorlevel% equ 0 (
    echo No new migrations needed.
) else (
    echo Creating new migrations...
    docker-compose exec web python manage.py makemigrations
)

REM Run migrations
echo Applying migrations...
docker-compose exec web python manage.py migrate

REM Create cache table
echo Creating cache table if it doesn't exist...
docker-compose exec web python manage.py createcachetable

REM Collect static files
echo Collecting static files...
docker-compose exec web python manage.py collectstatic --noinput

REM Create superuser (interactive)
echo Creating superuser...
docker-compose exec web python manage.py createsuperuser

echo Database initialization complete!
pause